#!/usr/bin/env python3
"""
Validates that partition files correctly cover a specific data source.

Usage:
    python scripts/validate_partition.py <data_source>
    
    Example:
        python scripts/validate_partition.py openshift-docs

Checks:
1. All partitions in partitions/{data_source}/ are valid JSON matching the schema
2. All files in data/{data_source}/ are included in exactly one partition (disjoint coverage)
3. No file appears in multiple partitions
4. No non-existent files are referenced

Note: Partition files use relative paths (e.g., "kcs_solutions/file.md") which are
resolved against the data source path (e.g., "data/openshift-docs/").
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple


def load_partition_files(data_source: str) -> List[Dict]:
    """
    Load all partition JSON files for a specific data source.
    
    Args:
        data_source: Name of the data source (e.g., "openshift-docs")
        
    Returns:
        List of partition dictionaries with file path and data
    """
    partition_files = []
    partitions_path = Path("partitions") / data_source

    if not partitions_path.exists():
        print(f"❌ Partitions directory '{partitions_path}' does not exist")
        return []

    for file_path in sorted(partitions_path.glob("*.json")):
        try:
            with open(file_path, 'r') as f:
                partition_data = json.load(f)
                partition_files.append({
                    "file": str(file_path),
                    "data": partition_data
                })
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return []

    return partition_files


def get_all_data_files(data_source: str) -> Set[str]:
    """
    Get all files in the data source directory (excluding .git).
    
    Args:
        data_source: Name of the data source (e.g., "openshift-docs")
    
    Returns:
        Set of relative paths from the data source root
    """
    data_files = set()
    data_path = Path("data") / data_source

    if not data_path.exists():
        print(f"❌ Data source directory 'data/{data_source}' does not exist")
        return data_files

    for file_path in data_path.rglob("*"):
        # Skip .git directory and directories themselves
        if ".git" not in file_path.parts and file_path.is_file():
            # Store relative path from data source root (not project root)
            rel_path = file_path.relative_to(data_path)
            data_files.add(str(rel_path))

    return data_files


def expand_partition_paths(partition_paths: List[str], data_source: str) -> Set[str]:
    """
    Expand partition paths to include all actual files.
    
    Paths ending with '/' are treated as directory references and expanded
    to include all files within that directory.
    
    Args:
        partition_paths: List of relative paths from partition JSON (may include directory refs)
        data_source: Name of the data source (e.g., "openshift-docs")
        
    Returns:
        Set of relative file paths (from data source root)
    """
    expanded_files = set()
    data_source_base = Path("data") / data_source
    
    for path in partition_paths:
        # Check if path ends with '/' (directory reference)
        if path.endswith('/'):
            # This is a directory reference - expand to all files in that directory
            dir_path = data_source_base / path.rstrip('/')
            
            if dir_path.exists() and dir_path.is_dir():
                # Add all files in this directory recursively
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and ".git" not in file_path.parts:
                        # Get relative path from data source root
                        rel_path = file_path.relative_to(data_source_base)
                        expanded_files.add(str(rel_path))
            # If directory doesn't exist, we'll catch it in invalid_files check
        else:
            # This is a specific file reference - use as-is (relative path)
            expanded_files.add(path)
    
    return expanded_files


def validate_partitions(partitions: List[Dict], data_files: Set[str], data_source: str) -> Tuple[bool, Dict]:
    """
    Validate that partitions form a complete, disjoint cover of data files.

    Args:
        partitions: List of partition dictionaries
        data_files: Set of relative file paths from data source
        data_source: Name of the data source (e.g., "openshift-docs")

    Returns:
        Tuple of (is_valid, results_dict)
    """
    results = {
        "total_partitions": len(partitions),
        "total_data_files": len(data_files),
        "files_in_partitions": set(),
        "duplicate_files": {},
        "missing_files": set(),
        "invalid_files": set(),
        "errors": []
    }

    # Track which files appear in which partitions
    file_to_partitions = {}

    for partition_info in partitions:
        partition_file = partition_info["file"]
        partition = partition_info["data"]

        # Validate required fields
        required_fields = ["partition_id", "title", "description", "paths",
                          "entity_ontology", "relationship_ontology"]
        missing_fields = [f for f in required_fields if f not in partition]
        if missing_fields:
            results["errors"].append(
                f"{partition_file}: Missing required fields: {missing_fields}"
            )
            continue

        partition_id = partition["partition_id"]
        paths = partition["paths"]

        # Expand directory references to actual files
        expanded_files = expand_partition_paths(paths, data_source)
        
        # Check each expanded file
        for file_path in expanded_files:
            # Normalize path
            normalized_path = str(Path(file_path))

            # Track which partition(s) contain this file
            if normalized_path not in file_to_partitions:
                file_to_partitions[normalized_path] = []
            file_to_partitions[normalized_path].append(partition_id)

            results["files_in_partitions"].add(normalized_path)

            # Check if file actually exists (relative to data source)
            if normalized_path not in data_files:
                results["invalid_files"].add(normalized_path)

    # Find duplicates (files in multiple partitions)
    for file_path, partition_ids in file_to_partitions.items():
        if len(partition_ids) > 1:
            results["duplicate_files"][file_path] = partition_ids

    # Find missing files (in data/ but not in any partition)
    results["missing_files"] = data_files - results["files_in_partitions"]

    # Determine if valid
    is_valid = (
        len(results["errors"]) == 0 and
        len(results["duplicate_files"]) == 0 and
        len(results["missing_files"]) == 0 and
        len(results["invalid_files"]) == 0
    )

    return is_valid, results


def get_validation_error_message(results: Dict) -> str:
    """
    Generate a detailed error message for Claude SDK to fix partitioning issues.
    
    Note: File paths in partitions are relative (e.g., "kcs_solutions/file.md")
    and are resolved against the data source path.
    
    Returns:
        A formatted error message string
    """
    error_parts = []
    
    if results["errors"]:
        error_parts.append("SCHEMA/STRUCTURAL ERRORS:")
        for error in results["errors"]:
            error_parts.append(f"  - {error}")
    
    if results["duplicate_files"]:
        error_parts.append("\nDUPLICATE FILES (appearing in multiple partitions):")
        for file_path, partition_ids in sorted(results["duplicate_files"].items()):
            error_parts.append(f"  - {file_path}")
            error_parts.append(f"    Found in partitions: {', '.join(map(str, partition_ids))}")
            error_parts.append(f"    ⚠️  Please remove this file from all but ONE partition")
    
    if results["missing_files"]:
        error_parts.append("\nMISSING FILES (in data source but not in any partition):")
        missing_list = sorted(results["missing_files"])
        for file_path in missing_list[:30]:  # Show first 30
            error_parts.append(f"  - {file_path}")
        if len(missing_list) > 30:
            error_parts.append(f"  ... and {len(missing_list) - 30} more files")
        error_parts.append(f"\n⚠️  Please add these {len(results['missing_files'])} files to appropriate partitions")
    
    if results["invalid_files"]:
        error_parts.append("\nINVALID FILES (referenced in partitions but not found in data source):")
        for file_path in sorted(results["invalid_files"]):
            error_parts.append(f"  - {file_path}")
        error_parts.append(f"\n⚠️  Please remove these {len(results['invalid_files'])} invalid references from partitions")
    
    return "\n".join(error_parts)


def print_results(is_valid: bool, results: Dict, data_source: str):
    """Print validation results in a human-readable format."""
    print("\n" + "="*60)
    print("PARTITION VALIDATION RESULTS")
    print("="*60)

    print(f"\nData source: {data_source}")
    print(f"Partitions directory: partitions/{data_source}/")
    print(f"Total partitions: {results['total_partitions']}")
    print(f"Total files in data source: {results['total_data_files']}")
    print(f"Files covered by partitions: {len(results['files_in_partitions'])}")

    if results["errors"]:
        print(f"\n❌ ERRORS ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  - {error}")

    if results["duplicate_files"]:
        print(f"\n❌ DUPLICATE FILES ({len(results['duplicate_files'])}):")
        print("  (Files appearing in multiple partitions)")
        for file_path, partition_ids in results["duplicate_files"].items():
            print(f"  - {file_path}")
            print(f"    Appears in: {', '.join(str(p) for p in partition_ids)}")

    if results["missing_files"]:
        print(f"\n❌ MISSING FILES ({len(results['missing_files'])}):")
        print("  (Files in data source not covered by any partition)")
        for file_path in sorted(results["missing_files"])[:20]:  # Show first 20
            print(f"  - {file_path}")
        if len(results["missing_files"]) > 20:
            print(f"  ... and {len(results['missing_files']) - 20} more")

    if results["invalid_files"]:
        print(f"\n❌ INVALID FILES ({len(results['invalid_files'])}):")
        print("  (Files referenced in partitions but not found in data source)")
        for file_path in sorted(results["invalid_files"]):
            print(f"  - {file_path}")

    print("\n" + "="*60)
    if is_valid:
        print("✅ VALIDATION PASSED - Partitions form a complete, disjoint cover!")
    else:
        print("❌ VALIDATION FAILED - Please fix the issues above")
    print("="*60 + "\n")


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_partition.py <data_source>")
        print("Example: python scripts/validate_partition.py openshift-docs")
        sys.exit(1)
    
    data_source = sys.argv[1]
    
    # Load partition files for this data source
    partitions = load_partition_files(data_source)
    if not partitions:
        print(f"⚠️  No partition files found in partitions/{data_source}/ or error loading them")
        return 1

    # Get all data files for this data source
    data_files = get_all_data_files(data_source)
    if not data_files:
        print(f"⚠️  No data files found in data/{data_source}/")
        return 1

    # Validate
    is_valid, results = validate_partitions(partitions, data_files, data_source)

    # Print results
    print_results(is_valid, results, data_source)
    
    # Return structured error message for Claude SDK integration
    # Exit code 0 = valid, 1 = invalid
    return 0 if is_valid else 1


def validate_and_get_errors(data_source: str) -> tuple[bool, str]:
    """
    Validation function for use by other scripts (e.g., Claude SDK workflow).
    
    Args:
        data_source: Name of the data source to validate (e.g., "openshift-docs")
    
    Returns:
        Tuple of (is_valid, error_message_string)
    """
    # Load partition files for this data source
    partitions = load_partition_files(data_source)
    if not partitions:
        return False, f"No partition files found in partitions/{data_source}/ or error loading them"

    # Get all data files for this data source
    data_files = get_all_data_files(data_source)
    if not data_files:
        return False, f"No data files found in data/{data_source}/"

    # Validate
    is_valid, results = validate_partitions(partitions, data_files, data_source)
    
    if is_valid:
        return True, "All partitions valid"
    else:
        error_message = get_validation_error_message(results)
        return False, error_message


if __name__ == "__main__":
    sys.exit(main())
