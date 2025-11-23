#!/usr/bin/env python3
"""
Validates that partition files correctly cover the data/ folder.

Checks:
1. All partitions are valid JSON matching the schema
2. All files in data/ are included in exactly one partition (disjoint coverage)
3. No file appears in multiple partitions
4. No non-existent files are referenced
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple


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


def get_all_data_files(data_dir: str = "data") -> Set[str]:
    """Get all files in the data/ directory (excluding .git)."""
    data_files = set()
    data_path = Path(data_dir)

    if not data_path.exists():
        print(f"❌ Data directory '{data_dir}' does not exist")
        return data_files

    for file_path in data_path.rglob("*"):
        # Skip .git directory and directories themselves
        if ".git" not in file_path.parts and file_path.is_file():
            # Store relative path from project root
            data_files.add(str(file_path))

    return data_files


def validate_partitions(partitions: List[Dict], data_files: Set[str]) -> Tuple[bool, Dict]:
    """
    Validate that partitions form a complete, disjoint cover of data files.

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

        # Check each path
        for path in paths:
            # Normalize path
            normalized_path = str(Path(path))

            # Track which partition(s) contain this file
            if normalized_path not in file_to_partitions:
                file_to_partitions[normalized_path] = []
            file_to_partitions[normalized_path].append(partition_id)

            results["files_in_partitions"].add(normalized_path)

            # Check if file actually exists
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


def print_results(is_valid: bool, results: Dict):
    """Print validation results in a human-readable format."""
    print("\n" + "="*60)
    print("PARTITION VALIDATION RESULTS")
    print("="*60)

    print(f"\nTotal partitions: {results['total_partitions']}")
    print(f"Total files in data/: {results['total_data_files']}")
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
        print("  (Files in data/ not covered by any partition)")
        for file_path in sorted(results["missing_files"])[:20]:  # Show first 20
            print(f"  - {file_path}")
        if len(results["missing_files"]) > 20:
            print(f"  ... and {len(results['missing_files']) - 20} more")

    if results["invalid_files"]:
        print(f"\n❌ INVALID FILES ({len(results['invalid_files'])}):")
        print("  (Files referenced in partitions but not found in data/)")
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
    # Load partition files
    partitions = load_partition_files()
    if not partitions:
        print("⚠️  No partition files found or error loading them")
        return 1

    # Get all data files
    data_files = get_all_data_files()
    if not data_files:
        print("⚠️  No data files found")
        return 1

    # Validate
    is_valid, results = validate_partitions(partitions, data_files)

    # Print results
    print_results(is_valid, results)

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
