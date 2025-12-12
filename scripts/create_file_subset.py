#!/usr/bin/env python3
"""
Create File Subset Script
Creates a new file subset JSON file with auto-incrementing ID.
Called by Claude Code Agent SDK during partition creation workflow.

Usage:
    python scripts/create_file_subset.py "<data_source>" "<title>" "<description>" <path1> [path2] ...
    
    Example:
        python scripts/create_file_subset.py "openshift-docs" "AWS Integration" "Files related to AWS" folder1/ file.md
"""

import json
import sys
from pathlib import Path
from typing import List


def get_next_partition_id(data_source: str) -> int:
    """
    Get the next available partition ID by checking existing file subsets for a data source.
    
    Args:
        data_source: Name of the data source (e.g., "openshift-docs")
        
    Returns:
        The next integer ID.
    """
    partitions_dir = Path("partitions") / data_source
    
    if not partitions_dir.exists():
        partitions_dir.mkdir(parents=True, exist_ok=True)
        return 1
    
    # Find highest existing partition ID
    max_id = 0
    for file_path in partitions_dir.glob("file_subset_*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                partition_id = data.get("partition_id", 0)
                if isinstance(partition_id, int) and partition_id > max_id:
                    max_id = partition_id
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    return max_id + 1


def create_partition(data_source: str, title: str, description: str, paths: List[str]) -> dict:
    """
    Create a new file subset JSON file for a specific data source.
    
    Args:
        data_source: Name of the data source (e.g., "openshift-docs")
        title: One sentence summary of the partition
        description: Detailed description of how files in this partition relate
        paths: List of relative file paths from the data source root
        
    Returns:
        Dictionary containing the created partition data
        
    Note:
        - Paths should be RELATIVE to the data source (e.g., "kcs_solutions/file.md" 
          not "data/rosa-kcs/kcs_solutions/file.md")
        - The data source folder is determined by the first argument
        - Paths ending with "/" (e.g., "kcs_solutions/") indicate all files within that directory.
        - entity_ontology and relationship_ontology are initialized as empty arrays.
    """
    # Input validation
    if not data_source or not isinstance(data_source, str):
        raise ValueError("Data source must be a non-empty string")
    
    if not title or not isinstance(title, str):
        raise ValueError("Title must be a non-empty string")
    
    if not description or not isinstance(description, str):
        raise ValueError("Description must be a non-empty string")
    
    if not paths or not isinstance(paths, list) or len(paths) == 0:
        raise ValueError("Paths must be a non-empty list")
    
    # Get next partition ID for this data source
    partition_id = get_next_partition_id(data_source)
    
    # Create partition data structure
    partition_data = {
        "partition_id": partition_id,
        "title": title,
        "description": description,
        "paths": paths,
        "entity_ontology": [],
        "relationship_ontology": []
    }
    
    # Create filename in data source subfolder
    partitions_dir = Path("partitions") / data_source
    partitions_dir.mkdir(parents=True, exist_ok=True)
    filename = partitions_dir / f"file_subset_{partition_id:02d}.json"
    
    # Write partition file
    with open(filename, 'w') as f:
        json.dump(partition_data, f, indent=2)
    
    print(f"✅ Created file subset {partition_id}: {filename}")
    print(f"   Title: {title}")
    print(f"   Files/paths: {len(paths)}")
    
    return partition_data


def main():
    """Command-line interface for create_file_subset."""
    if len(sys.argv) < 5:
        print('Usage: python scripts/create_file_subset.py "<data_source>" "<title>" "<description>" <path1> [path2] ...')
        print("\nExample:")
        print('  python scripts/create_file_subset.py "openshift-docs" "AWS Integration" "Files related to AWS" aws_folder/ config/settings.yaml')
        print("\nNote:")
        print("  - Paths should be RELATIVE to the data source (e.g., 'folder/' not 'data/source/folder/')")
        print("  - Use trailing slash for directory paths (e.g., 'folder/') to include all files in that directory")
        print("  - Files are created in partitions/<data_source>/file_subset_XX.json")
        sys.exit(1)
    
    data_source = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3]
    paths = sys.argv[4:]
    
    try:
        partition_data = create_partition(data_source, title, description, paths)
        print(f"\n📋 File subset created successfully!")
        print(json.dumps(partition_data, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error creating partition: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
