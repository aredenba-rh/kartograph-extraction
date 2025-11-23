#!/usr/bin/env python3
"""
Update master ontology with elements from a partition ontology.

This script merges a partition's entity or relationship ontology into the
master ontology, consolidating similar types and maintaining source tracking.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def load_json(file_path: Path) -> Dict:
    """Load JSON file."""
    if not file_path.exists():
        return {}
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(file_path: Path, data: Dict):
    """Save JSON file with formatting."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def update_master_ontology(
    partition_id: str,
    partition_elements: List[Dict],
    master_ontology: Dict,
    ontology_type: str
) -> Dict:
    """
    Update master ontology with partition elements.

    Args:
        partition_id: ID of the partition being added
        partition_elements: Elements from the partition ontology
        master_ontology: Current master ontology
        ontology_type: "entity" or "relationship"

    Returns:
        Updated master ontology
    """
    if not master_ontology:
        master_ontology = {
            "ontology_type": ontology_type,
            "version": "0.1.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "elements": []
        }

    master_elements = master_ontology.get("elements", [])

    # Track updates
    stats = {
        "added": 0,
        "updated": 0,
        "skipped": 0
    }

    for partition_element in partition_elements:
        element_type = partition_element["type"]

        # Find if this type already exists in master
        existing_element = None
        for elem in master_elements:
            if elem["type"].lower() == element_type.lower():
                existing_element = elem
                break

        if existing_element:
            # Update existing element
            if partition_id not in existing_element.get("source_partitions", []):
                existing_element.setdefault("source_partitions", []).append(partition_id)

            # Add example files
            example_files = partition_element.get("example_files", [])
            existing_examples = existing_element.setdefault("all_example_files", [])

            # For relationships, example_files is a tuple
            if ontology_type == "relationship":
                # Convert to tuple for comparison
                example_tuple = tuple(example_files)
                if example_tuple not in [tuple(e) if isinstance(e, list) else e
                                         for e in existing_examples]:
                    existing_examples.append(example_files)
            else:
                # For entities, example_files is a list of paths
                for file_path in example_files:
                    if file_path not in existing_examples:
                        existing_examples.append(file_path)

            # Update description (append if different)
            partition_desc = partition_element.get("example_files_description", "")
            existing_desc = existing_element.get("description", "")

            if partition_desc and partition_desc not in existing_desc:
                if existing_desc:
                    existing_element["description"] = existing_desc + " | " + partition_desc
                else:
                    existing_element["description"] = partition_desc

            stats["updated"] += 1

        else:
            # Add new element
            new_element = {
                "type": element_type,
                "source_partitions": [partition_id],
                "all_example_files": partition_element.get("example_files", []),
                "description": partition_element.get("example_files_description", "")
            }
            master_elements.append(new_element)
            stats["added"] += 1

    # Update metadata
    master_ontology["elements"] = master_elements
    master_ontology["last_updated"] = datetime.utcnow().isoformat() + "Z"

    # Increment patch version
    version_parts = master_ontology["version"].split(".")
    version_parts[-1] = str(int(version_parts[-1]) + 1)
    master_ontology["version"] = ".".join(version_parts)

    return master_ontology, stats


def main():
    """Main update function."""
    if len(sys.argv) < 3:
        print("Usage: python update_master_ontology.py <partition_id> <entity|relationship|both>")
        print("\nExample:")
        print("  python update_master_ontology.py partition_01 both")
        print("  python update_master_ontology.py partition_02 entity")
        return 1

    partition_id = sys.argv[1]
    update_type = sys.argv[2]

    if update_type not in ["entity", "relationship", "both"]:
        print("❌ Error: update_type must be 'entity', 'relationship', or 'both'")
        return 1

    # Load partition file
    partition_path = Path("partitions") / f"{partition_id}.json"
    if not partition_path.exists():
        print(f"❌ Partition file not found: {partition_path}")
        return 1

    partition_data = load_json(partition_path)

    print("\n" + "="*60)
    print(f"UPDATING MASTER ONTOLOGY FROM: {partition_id}")
    print("="*60)

    # Update entity ontology
    if update_type in ["entity", "both"]:
        print("\n📊 Updating Entity Ontology...")
        master_entity_path = Path("ontologies") / "master_entity_ontology.json"
        master_entity = load_json(master_entity_path)

        partition_entities = partition_data.get("entity_ontology", [])
        updated_entity, entity_stats = update_master_ontology(
            partition_id,
            partition_entities,
            master_entity,
            "entity"
        )

        save_json(master_entity_path, updated_entity)

        print(f"  ✅ Added: {entity_stats['added']} elements")
        print(f"  🔄 Updated: {entity_stats['updated']} elements")
        print(f"  Total elements: {len(updated_entity['elements'])}")

    # Update relationship ontology
    if update_type in ["relationship", "both"]:
        print("\n📊 Updating Relationship Ontology...")
        master_rel_path = Path("ontologies") / "master_relationship_ontology.json"
        master_rel = load_json(master_rel_path)

        partition_relationships = partition_data.get("relationship_ontology", [])
        updated_rel, rel_stats = update_master_ontology(
            partition_id,
            partition_relationships,
            master_rel,
            "relationship"
        )

        save_json(master_rel_path, updated_rel)

        print(f"  ✅ Added: {rel_stats['added']} elements")
        print(f"  🔄 Updated: {rel_stats['updated']} elements")
        print(f"  Total elements: {len(updated_rel['elements'])}")

    print("\n" + "="*60)
    print("✅ MASTER ONTOLOGY UPDATE COMPLETE")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
