#!/usr/bin/env python3
"""
Validates that partition files correctly cover the data/ folder.

Checks:
1. All partitions are valid JSON matching the schema
2. All files in data/ are included in exactly one partition (disjoint coverage)
3. No file appears in multiple partitions
4. No non-existent files are referenced

Note: Partition files use relative paths (e.g., "kcs_solutions/file.md") which are
resolved against the data_source path from extraction_config.json (e.g., "data/rosa-kcs/").
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple


def load_extraction_config() -> Dict:
    """Load extraction configuration to get data source."""
    config_file = Path("extraction_config.json")
    if not config_file.exists():
        print("❌ extraction_config.json not found")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if 'data_source' not in config:
        print("❌ 'data_source' field missing in extraction_config.json")
        sys.exit(1)
    
    return config


def get_data_source_path() -> str:
    """Get the full data source path (e.g., 'data/rosa-kcs')."""
    config = load_extraction_config()
    data_source = config['data_source']
    return f"data/{data_source}"


def load_partition_files(partitions_dir: str = "partitions") -> List[Dict]:
    """Load all partition JSON files."""
    partition_files = []
    partitions_path = Path(partitions_dir)

    if not partitions_path.exists():
        print(f"❌ Partitions directory '{partitions_dir}' does not exist")
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


def get_all_data_files(data_source_path: str) -> Set[str]:
    """
    Get all files in the data source directory (excluding .git).
    
    Args:
        data_source_path: Full path to data source (e.g., 'data/rosa-kcs')
    
    Returns:
        Set of relative paths from the data source root
    """
    data_files = set()
    data_path = Path(data_source_path)

    if not data_path.exists():
        print(f"❌ Data source directory '{data_source_path}' does not exist")
        return data_files

    for file_path in data_path.rglob("*"):
        # Skip .git directory and directories themselves
        if ".git" not in file_path.parts and file_path.is_file():
            # Store relative path from data source root (not project root)
            rel_path = file_path.relative_to(data_path)
            data_files.add(str(rel_path))

    return data_files


def expand_partition_paths(partition_paths: List[str], data_source_path: str) -> Set[str]:
    """
    Expand partition paths to include all actual files.
    
    Paths ending with '/' are treated as directory references and expanded
    to include all files within that directory.
    
    Args:
        partition_paths: List of relative paths from partition JSON (may include directory refs)
        data_source_path: Full path to data source (e.g., 'data/rosa-kcs')
        
    Returns:
        Set of relative file paths (from data source root)
    """
    expanded_files = set()
    data_source_base = Path(data_source_path)
    
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


def validate_partitions(partitions: List[Dict], data_files: Set[str], data_source_path: str) -> Tuple[bool, Dict]:
    """
    Validate that partitions form a complete, disjoint cover of data files.

    Args:
        partitions: List of partition dictionaries
        data_files: Set of relative file paths from data source
        data_source_path: Full path to data source (e.g., 'data/rosa-kcs')
        
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
        expanded_files = expand_partition_paths(paths, data_source_path)
        
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
    and are resolved against the data source path from extraction_config.json.
    
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


def print_results(is_valid: bool, results: Dict, data_source_path: str):
    """Print validation results in a human-readable format."""
    print("\n" + "="*60)
    print("PARTITION VALIDATION RESULTS")
    print("="*60)
    
    print(f"\nData source: {data_source_path}")
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
            print(f"    Appears in: {', '.join(partition_ids)}")

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
    # Get data source path from config
    data_source_path = get_data_source_path()
    
    # Load partition files
    partitions = load_partition_files()
    if not partitions:
        print("⚠️  No partition files found or error loading them")
        return 1

    # Get all data files
    data_files = get_all_data_files(data_source_path)
    if not data_files:
        print("⚠️  No data files found")
        return 1

    # Validate
    is_valid, results = validate_partitions(partitions, data_files, data_source_path)

    # Print results
    print_results(is_valid, results, data_source_path)
    
    # Return structured error message for Claude SDK integration
    # Exit code 0 = valid, 1 = invalid
    return 0 if is_valid else 1


def validate_and_get_errors() -> tuple[bool, str]:
    """
    Validation function for use by other scripts (e.g., Claude SDK workflow).
    
    Returns:
        Tuple of (is_valid, error_message_string)
    """
    # Get data source path from config
    data_source_path = get_data_source_path()
    
    # Load partition files
    partitions = load_partition_files()
    if not partitions:
        return False, "No partition files found or error loading them"

    # Get all data files
    data_files = get_all_data_files(data_source_path)
    if not data_files:
        return False, f"No data files found in {data_source_path}"

    # Validate
    is_valid, results = validate_partitions(partitions, data_files, data_source_path)
    
    if is_valid:
        return True, "All partitions valid"
    else:
        error_message = get_validation_error_message(results)
        return False, error_message


if __name__ == "__main__":
    sys.exit(main())
