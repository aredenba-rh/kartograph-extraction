#!/usr/bin/env python3
"""
Create Entity Script
Adds a new entity to a partition's entity ontology file.

Usage:
    python scripts/create_entity.py <partition_number> <type> <description> <example_file> <example_in_file>

Example:
    python scripts/create_entity.py 1 "Red Hat Product" "A Red Hat product involved in the KCS article" \\
        "data/rosa-kcs/kcs_solutions/example.md" "Openshift Container Platform 4"

The entity will be added to ontologies/partition_01_entity_ontology.json
"""

import json
import sys
from pathlib import Path


def load_entity_ontology(partition_number: int) -> dict:
    """Load the entity ontology for a partition."""
    filename = f"partition_{partition_number:02d}_entity_ontology.json"
    ontology_path = Path("ontologies") / filename
    
    if not ontology_path.exists():
        print(f"❌ Entity ontology not found: {ontology_path}")
        print(f"   Run init_partition_ontologies.py first to create the ontology files.")
        sys.exit(1)
    
    with open(ontology_path, 'r') as f:
        return json.load(f)


def save_entity_ontology(partition_number: int, ontology_data: dict):
    """Save the entity ontology for a partition."""
    filename = f"partition_{partition_number:02d}_entity_ontology.json"
    ontology_path = Path("ontologies") / filename
    
    with open(ontology_path, 'w') as f:
        json.dump(ontology_data, f, indent=2)


def get_next_entity_id(entities: list) -> str:
    """Get the next available entity ID."""
    if not entities:
        return "1"
    
    max_id = 0
    for entity in entities:
        try:
            entity_id = int(entity.get("entity_id", 0))
            if entity_id > max_id:
                max_id = entity_id
        except (ValueError, TypeError):
            continue
    
    return str(max_id + 1)


def entity_exists(entities: list, entity_type: str) -> bool:
    """
    Check if an entity with the same type already exists.
    
    Args:
        entities: List of existing entities
        entity_type: The type of entity to check for
        
    Returns:
        True if an entity with this type already exists
    """
    for entity in entities:
        if entity.get("type", "").lower() == entity_type.lower():
            return True
    return False


def create_entity(partition_number: int, entity_type: str, description: str, 
                  example_file: str, example_in_file: str) -> dict:
    """
    Create a new entity in the partition's entity ontology.
    
    Args:
        partition_number: The partition number (1-6)
        entity_type: Type of entity (e.g., "Red Hat Product", "KCS Article")
        description: Description of what this entity represents
        example_file: Path to an example file containing this entity
        example_in_file: Example text showing how this entity appears in the file
        
    Returns:
        The created entity object
    """
    ontology = load_entity_ontology(partition_number)
    entities = ontology.get("entities", [])
    
    # Check for duplicates
    if entity_exists(entities, entity_type):
        print(f"⚠️  Entity type '{entity_type}' already exists in partition {partition_number}")
        print(f"   Skipping duplicate entity creation.")
        # Find and return the existing entity
        for entity in entities:
            if entity.get("type", "").lower() == entity_type.lower():
                return entity
    
    # Get next ID
    entity_id = get_next_entity_id(entities)
    
    # Create entity object
    entity = {
        "entity_id": entity_id,
        "type": entity_type,
        "example_file": example_file,
        "description": description,
        "example_in_file": example_in_file
    }
    
    # Add to entities list
    entities.append(entity)
    ontology["entities"] = entities
    
    # Save updated ontology
    save_entity_ontology(partition_number, ontology)
    
    print(f"✅ Created entity in partition {partition_number}:")
    print(f"   ID: {entity_id}")
    print(f"   Type: {entity_type}")
    print(f"   Description: {description[:60]}...")
    
    return entity


def main():
    """Command-line interface for creating entities."""
    if len(sys.argv) < 6:
        print("Usage: python scripts/create_entity.py <partition_number> <type> <description> <example_file> <example_in_file>")
        print("\nArguments:")
        print("  partition_number  - The partition number (e.g., 1, 2, 3)")
        print("  type              - Entity type (e.g., 'Red Hat Product', 'KCS Article')")
        print("  description       - Description of what this entity represents")
        print("  example_file      - Path to a file containing an example of this entity")
        print("  example_in_file   - Example text showing how this entity appears")
        print("\nExample:")
        print('  python scripts/create_entity.py 1 "Red Hat Product" \\')
        print('    "A Red Hat product involved in the KCS article" \\')
        print('    "data/rosa-kcs/kcs_solutions/example.md" \\')
        print('    "Openshift Container Platform 4"')
        sys.exit(1)
    
    try:
        partition_number = int(sys.argv[1])
    except ValueError:
        print(f"❌ Invalid partition number: {sys.argv[1]}")
        sys.exit(1)
    
    entity_type = sys.argv[2]
    description = sys.argv[3]
    example_file = sys.argv[4]
    example_in_file = sys.argv[5]
    
    try:
        entity = create_entity(partition_number, entity_type, description, example_file, example_in_file)
        print(f"\n📋 Entity created successfully!")
        print(json.dumps(entity, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error creating entity: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

