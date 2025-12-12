"""
Filesystem utilities for the extraction workflow.

Provides functions for:
- Resetting the partitions folder
- Resetting the logging file
- Resetting the ontologies folder
"""

import json
from pathlib import Path


def reset_partitions_folder():
    """Remove all partition JSON files from partitions/ folder"""
    partitions_dir = Path("partitions")
    
    if not partitions_dir.exists():
        partitions_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created partitions/ directory")
        return
    
    # Remove all partition JSON files
    partition_files = list(partitions_dir.glob("partition_*.json"))
    
    if partition_files:
        for partition_file in partition_files:
            partition_file.unlink()
        print(f"  ✓ Removed {len(partition_files)} existing partition file(s)")
    else:
        print(f"  ✓ Partitions folder already empty")


def reset_logging():
    """Reset the logging.json file to start fresh"""
    log_dir = Path("logging")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "logging.json"
    
    # Overwrite with empty JSON object
    with open(log_file, 'w') as f:
        json.dump({}, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Reset logging file")


def reset_ontologies_folder():
    """Remove all ontology JSON files from ontologies/ folder"""
    ontologies_dir = Path("ontologies")
    
    if not ontologies_dir.exists():
        ontologies_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created ontologies/ directory")
        return
    
    # Remove all partition ontology JSON files
    entity_files = list(ontologies_dir.glob("partition_*_entity_ontology.json"))
    relationship_files = list(ontologies_dir.glob("partition_*_relationship_ontology.json"))
    all_files = entity_files + relationship_files
    
    if all_files:
        for ontology_file in all_files:
            ontology_file.unlink()
        print(f"  ✓ Removed {len(all_files)} existing ontology file(s)")
    else:
        print(f"  ✓ Ontologies folder already empty")

