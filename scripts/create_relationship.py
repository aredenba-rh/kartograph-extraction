#!/usr/bin/env python3
"""
Create Relationship Script
Adds a new relationship to a partition's relationship ontology file.

Usage:
    python scripts/create_relationship.py <partition_number> <type> <source_entity_type> \\
        <target_entity_type> <description> <example_file> <example_in_file>

Example:
    python scripts/create_relationship.py 1 "DOCUMENTS" "KCS Article" "Red Hat Product" \\
        "Indicates that a KCS Article documents troubleshooting steps for a Red Hat Product" \\
        "data/rosa-kcs/kcs_solutions/example.md" \\
        "KCS 5682881 -> DOCUMENTS -> Openshift Container Platform 4"

The relationship will be added to ontologies/partition_01_relationship_ontology.json
"""

import json
import sys
from pathlib import Path


def load_relationship_ontology(partition_number: int) -> dict:
    """Load the relationship ontology for a partition."""
    filename = f"partition_{partition_number:02d}_relationship_ontology.json"
    ontology_path = Path("ontologies") / filename
    
    if not ontology_path.exists():
        print(f"❌ Relationship ontology not found: {ontology_path}")
        print(f"   Run init_partition_ontologies.py first to create the ontology files.")
        sys.exit(1)
    
    with open(ontology_path, 'r') as f:
        return json.load(f)


def save_relationship_ontology(partition_number: int, ontology_data: dict):
    """Save the relationship ontology for a partition."""
    filename = f"partition_{partition_number:02d}_relationship_ontology.json"
    ontology_path = Path("ontologies") / filename
    
    with open(ontology_path, 'w') as f:
        json.dump(ontology_data, f, indent=2)


def get_next_relationship_id(relationships: list) -> str:
    """Get the next available relationship ID."""
    if not relationships:
        return "1"
    
    max_id = 0
    for relationship in relationships:
        try:
            relationship_id = int(relationship.get("relationship_id", 0))
            if relationship_id > max_id:
                max_id = relationship_id
        except (ValueError, TypeError):
            continue
    
    return str(max_id + 1)


def relationship_exists(relationships: list, relationship_type: str, 
                       source_type: str, target_type: str) -> bool:
    """
    Check if a relationship with the same type and entity types already exists.
    
    Args:
        relationships: List of existing relationships
        relationship_type: The type of relationship to check for
        source_type: The source entity type
        target_type: The target entity type
        
    Returns:
        True if a matching relationship already exists
    """
    for rel in relationships:
        if (rel.get("type", "").lower() == relationship_type.lower() and
            rel.get("source_entity_type", "").lower() == source_type.lower() and
            rel.get("target_entity_type", "").lower() == target_type.lower()):
            return True
    return False


def create_relationship(partition_number: int, relationship_type: str, 
                       source_entity_type: str, target_entity_type: str,
                       description: str, example_file: str, example_in_file: str) -> dict:
    """
    Create a new relationship in the partition's relationship ontology.
    
    Args:
        partition_number: The partition number (1-6)
        relationship_type: Type of relationship (e.g., "DOCUMENTS", "RESOLVES")
        source_entity_type: The source entity type in the relationship
        target_entity_type: The target entity type in the relationship
        description: Description of what this relationship represents
        example_file: Path to an example file containing this relationship
        example_in_file: Example showing how this relationship appears
        
    Returns:
        The created relationship object
    """
    ontology = load_relationship_ontology(partition_number)
    relationships = ontology.get("relationships", [])
    
    # Check for duplicates
    if relationship_exists(relationships, relationship_type, source_entity_type, target_entity_type):
        print(f"⚠️  Relationship '{relationship_type}' ({source_entity_type} -> {target_entity_type})")
        print(f"   already exists in partition {partition_number}. Skipping duplicate.")
        # Find and return the existing relationship
        for rel in relationships:
            if (rel.get("type", "").lower() == relationship_type.lower() and
                rel.get("source_entity_type", "").lower() == source_entity_type.lower() and
                rel.get("target_entity_type", "").lower() == target_entity_type.lower()):
                return rel
    
    # Get next ID
    relationship_id = get_next_relationship_id(relationships)
    
    # Create relationship object
    relationship = {
        "relationship_id": relationship_id,
        "type": relationship_type,
        "source_entity_type": source_entity_type,
        "target_entity_type": target_entity_type,
        "description": description,
        "example_file": example_file,
        "example_in_file": example_in_file
    }
    
    # Add to relationships list
    relationships.append(relationship)
    ontology["relationships"] = relationships
    
    # Save updated ontology
    save_relationship_ontology(partition_number, ontology)
    
    print(f"✅ Created relationship in partition {partition_number}:")
    print(f"   ID: {relationship_id}")
    print(f"   Type: {relationship_type}")
    print(f"   {source_entity_type} -> {target_entity_type}")
    
    return relationship


def main():
    """Command-line interface for creating relationships."""
    if len(sys.argv) < 8:
        print("Usage: python scripts/create_relationship.py <partition_number> <type> \\")
        print("       <source_entity_type> <target_entity_type> <description> \\")
        print("       <example_file> <example_in_file>")
        print("\nArguments:")
        print("  partition_number    - The partition number (e.g., 1, 2, 3)")
        print("  type                - Relationship type (e.g., 'DOCUMENTS', 'RESOLVES')")
        print("  source_entity_type  - The source entity type")
        print("  target_entity_type  - The target entity type")
        print("  description         - Description of this relationship")
        print("  example_file        - Path to a file containing an example")
        print("  example_in_file     - Example showing how the relationship appears")
        print("\nExample:")
        print('  python scripts/create_relationship.py 1 "DOCUMENTS" "KCS Article" \\')
        print('    "Red Hat Product" "KCS Article documents troubleshooting for a product" \\')
        print('    "data/rosa-kcs/kcs_solutions/example.md" \\')
        print('    "KCS 5682881 -> DOCUMENTS -> Openshift Container Platform 4"')
        sys.exit(1)
    
    try:
        partition_number = int(sys.argv[1])
    except ValueError:
        print(f"❌ Invalid partition number: {sys.argv[1]}")
        sys.exit(1)
    
    relationship_type = sys.argv[2]
    source_entity_type = sys.argv[3]
    target_entity_type = sys.argv[4]
    description = sys.argv[5]
    example_file = sys.argv[6]
    example_in_file = sys.argv[7]
    
    try:
        relationship = create_relationship(
            partition_number, relationship_type, source_entity_type,
            target_entity_type, description, example_file, example_in_file
        )
        print(f"\n📋 Relationship created successfully!")
        print(json.dumps(relationship, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error creating relationship: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

