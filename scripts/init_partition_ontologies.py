#!/usr/bin/env python3
"""
Initialize Partition Ontologies Script
Creates empty entity and relationship ontology files for each partition.

Usage:
    python scripts/init_partition_ontologies.py

This will create:
    - ontologies/partition_01_entity_ontology.json
    - ontologies/partition_01_relationship_ontology.json
    - ... for each partition in partitions/
"""

import json
import sys
from pathlib import Path


def get_all_partitions() -> list:
    """Get list of all partition files."""
    partitions_dir = Path("partitions")
    
    if not partitions_dir.exists():
        return []
    
    partitions = []
    for file_path in sorted(partitions_dir.glob("partition_*.json")):
        with open(file_path, 'r') as f:
            data = json.load(f)
            partitions.append({
                "path": file_path,
                "partition_id": data.get("partition_id"),
                "title": data.get("title", "Unknown")
            })
    
    return partitions


def init_partition_ontologies() -> int:
    """
    Initialize empty ontology files for each partition.
    
    Returns:
        Number of ontology file pairs created
    """
    ontologies_dir = Path("ontologies")
    ontologies_dir.mkdir(parents=True, exist_ok=True)
    
    partitions = get_all_partitions()
    
    if not partitions:
        print("❌ No partitions found in partitions/ directory")
        print("   Run Step 1 first to create partitions.")
        return 0
    
    created_count = 0
    
    for partition in partitions:
        partition_id = partition["partition_id"]
        
        # Create entity ontology file
        entity_filename = f"partition_{partition_id:02d}_entity_ontology.json"
        entity_path = ontologies_dir / entity_filename
        
        entity_ontology = {
            "entities": []
        }
        
        with open(entity_path, 'w') as f:
            json.dump(entity_ontology, f, indent=2)
        
        # Create relationship ontology file
        relationship_filename = f"partition_{partition_id:02d}_relationship_ontology.json"
        relationship_path = ontologies_dir / relationship_filename
        
        relationship_ontology = {
            "relationships": []
        }
        
        with open(relationship_path, 'w') as f:
            json.dump(relationship_ontology, f, indent=2)
        
        print(f"✅ Created ontologies for partition {partition_id}: {partition['title']}")
        print(f"   - {entity_filename}")
        print(f"   - {relationship_filename}")
        
        created_count += 1
    
    return created_count


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("INITIALIZING PARTITION ONTOLOGY FILES")
    print("="*60 + "\n")
    
    count = init_partition_ontologies()
    
    print(f"\n✅ Created {count} ontology file pairs")
    print(f"   Total files: {count * 2}")
    
    return 0 if count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

