#!/usr/bin/env python3
"""
Initialize Master Ontologies Script
Creates empty master entity and relationship ontology files.

Usage:
    python scripts/init_partition_ontologies.py

This will create:
    - ontology/master_entity_ontology.json
    - ontology/master_relationship_ontology.json
"""

import json
import sys
from pathlib import Path


def init_master_ontologies() -> bool:
    """
    Initialize empty master ontology files.
    
    Returns:
        True if files were created successfully
    """
    ontology_dir = Path("ontology")
    ontology_dir.mkdir(parents=True, exist_ok=True)
    
    # Create master entity ontology file
    entity_path = ontology_dir / "master_entity_ontology.json"
    entity_ontology = {"entities": []}
    
    with open(entity_path, 'w') as f:
        json.dump(entity_ontology, f, indent=2)
    
    print(f"✅ Created {entity_path}")
    
    # Create master relationship ontology file
    relationship_path = ontology_dir / "master_relationship_ontology.json"
    relationship_ontology = {"relationships": []}
    
    with open(relationship_path, 'w') as f:
        json.dump(relationship_ontology, f, indent=2)
    
    print(f"✅ Created {relationship_path}")
    
    return True


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("INITIALIZING MASTER ONTOLOGY FILES")
    print("="*60 + "\n")
    
    success = init_master_ontologies()
    
    if success:
        print(f"\n✅ Created master ontology files:")
        print(f"   - ontology/master_entity_ontology.json")
        print(f"   - ontology/master_relationship_ontology.json")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
