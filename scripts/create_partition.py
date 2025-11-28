#!/usr/bin/env python3
"""
Create Partition Script
Creates a new partition JSON file with auto-incrementing ID.
Called by Claude Code Agent SDK during partition creation workflow.
"""

import json
import sys
from pathlib import Path
from typing import List


def get_next_partition_id() -> int:
    """
    Get the next available partition ID by checking existing partitions.
    Returns the next integer ID.
    """
    partitions_dir = Path("partitions")
    
    if not partitions_dir.exists():
        partitions_dir.mkdir(parents=True, exist_ok=True)
        return 1
    
    # Find highest existing partition ID
    max_id = 0
    for file_path in partitions_dir.glob("partition_*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                partition_id = data.get("partition_id", 0)
                if isinstance(partition_id, int) and partition_id > max_id:
                    max_id = partition_id
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    return max_id + 1


def create_partition(title: str, description: str, paths: List[str]) -> dict:
    """
    Create a new partition JSON file.
    
    Args:
        title: One sentence summary of the partition
        description: Detailed description of how files in this partition relate
        paths: List of file paths or directory paths (directory paths should end with /)
        
    Returns:
        Dictionary containing the created partition data
        
    Note:
        - Paths ending with "/" (e.g., "data/rosa-kcs/kcs_solutions/") indicate 
          all files within that directory.
        - Individual file paths should be relative from the project root.
        - entity_ontology and relationship_ontology are initialized as empty arrays.
    """
    # Input validation
    if not title or not isinstance(title, str):
        raise ValueError("Title must be a non-empty string")
    
    if not description or not isinstance(description, str):
        raise ValueError("Description must be a non-empty string")
    
    if not paths or not isinstance(paths, list) or len(paths) == 0:
        raise ValueError("Paths must be a non-empty list")
    
    # Get next partition ID
    partition_id = get_next_partition_id()
    
    # Create partition data structure
    partition_data = {
        "partition_id": partition_id,
        "title": title,
        "description": description,
        "paths": paths,
        "entity_ontology": [],
        "relationship_ontology": []
    }
    
    # Create filename
    partitions_dir = Path("partitions")
    partitions_dir.mkdir(parents=True, exist_ok=True)
    filename = partitions_dir / f"partition_{partition_id:02d}.json"
    
    # Write partition file
    with open(filename, 'w') as f:
        json.dump(partition_data, f, indent=2)
    
    print(f"✅ Created partition {partition_id}: {filename}")
    print(f"   Title: {title}")
    print(f"   Files/paths: {len(paths)}")
    
    return partition_data


def main():
    """Command-line interface for create_partition."""
    if len(sys.argv) < 4:
        print("Usage: create_partition.py <title> <description> <path1> [path2] [path3] ...")
        print("\nExample:")
        print('  create_partition.py "AWS Integration" "Files related to AWS service integration" "data/rosa-kcs/kcs_solutions/" "data/config.yaml"')
        print("\nNote: Use trailing slash for directory paths (e.g., 'data/folder/') to include all files in that directory")
        sys.exit(1)
    
    title = sys.argv[1]
    description = sys.argv[2]
    paths = sys.argv[3:]
    
    try:
        partition_data = create_partition(title, description, paths)
        print(f"\n📋 Partition created successfully!")
        print(json.dumps(partition_data, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error creating partition: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

