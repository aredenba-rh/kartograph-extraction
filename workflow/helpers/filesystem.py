"""
Filesystem utilities for the extraction workflow.

Provides functions for:
- Resetting the partitions folder
- Resetting the logging file
- Resetting the ontologies folder
"""

import json
import shutil
from pathlib import Path


def reset_partitions_folder():
    """Remove all partition subfolders and file subsets from partitions/ folder"""
    partitions_dir = Path("partitions")
    
    if not partitions_dir.exists():
        partitions_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created partitions/ directory")
        return
    
    # Remove all data source subdirectories (e.g., partitions/openshift-docs/)
    subdirs = [d for d in partitions_dir.iterdir() if d.is_dir()]
    
    if subdirs:
        for subdir in subdirs:
            shutil.rmtree(subdir)
        print(f"  ✓ Removed {len(subdirs)} existing partition folder(s)")
    else:
        print(f"  ✓ Partitions folder already empty")


def reset_logging():
    """Reset the logging/step_1/ directory to start fresh"""
    log_dir = Path("logging")
    step_1_dir = log_dir / "step_1"
    
    # Remove the entire step_1 directory if it exists
    if step_1_dir.exists():
        shutil.rmtree(step_1_dir)
    
    # Create fresh step_1 directory
    step_1_dir.mkdir(parents=True, exist_ok=True)
    
    # Create empty logging.json
    log_file = step_1_dir / "logging.json"
    with open(log_file, 'w') as f:
        json.dump({}, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Reset logging/step_1/ directory")


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

