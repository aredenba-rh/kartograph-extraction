#!/usr/bin/env python3
"""
Start Extraction Workflow
Loads config flags and displays appropriate workflow steps
"""

import json
import sys
from pathlib import Path

def load_config():
    """Load extraction configuration"""
    config_file = Path("extraction_config.json")
    
    if not config_file.exists():
        print("⚠️  No extraction_config.json found. Creating default...")
        default_config = {
            "use_current_partition": False,
            "use_current_ontologies": False
        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    with open(config_file, 'r') as f:
        return json.load(f)

def show_workflow_steps(config):
    """Display workflow steps based on config flags"""
    
    print("Configuration:")
    print("  " + "─" * 56)
    for key, value in config.items():
        status = "✓ ON " if value else "✗ OFF"
        print(f"  {key:30s} {status}")
    print()
    
    print("Workflow Steps:")
    print("  " + "─" * 56)
    print()
    
    use_current_partition = config.get('use_current_partition', False)
    use_current_ontologies = config.get('use_current_ontologies', False)
    
    if use_current_partition:
        print("  ⊘ SKIPPED: Step 1 - Create file partitions (using existing)")
        print()
    else:
        print("  Step 1: Create file partitions")
        print("    └─ Analyze data/, identify groupings, create partition JSONs")
        print()
    
    if use_current_ontologies:
        print("  ⊘ SKIPPED: Step 2 - Create ontologies for each partition (using existing)")
        print()
    else:
        if use_current_partition:
            print("  → Starting at: Step 2 - Create ontologies for each partition")
        else:
            print("  Step 2: Create ontologies for each partition")
        print("    └─ Define entity & relationship ontologies")
        print("    └─ Update master ontologies")
        print()
    
    print("Available Tools:")
    print("  " + "─" * 56)
    print("  • confirm_acceptable_partition.py - Validate partition coverage")
    print("  • check_master_ontology.py        - Check for similar ontology elements")
    print("  • update_master_ontology.py       - Update master ontologies")
    print("  • manage_checklist.py             - Track progress")
    print()
    
    print("Next Actions:")
    print("  " + "─" * 56)
    
    use_current_partition = config.get('use_current_partition', False)
    use_current_ontologies = config.get('use_current_ontologies', False)
    
    if use_current_partition and use_current_ontologies:
        print("  ⚠️  Both workflow steps are skipped!")
        print("  1. Review existing partitions in partitions/ directory")
        print("  2. Review existing ontologies in ontologies/ directory")
        print("  3. Ready to proceed to extraction phase (when implemented)")
    elif use_current_partition and not use_current_ontologies:
        print("  1. Review existing partitions in partitions/ directory")
        print("  2. Create ontologies for each partition")
        print("  3. Use 'make view-checklist CHECKLIST=02_create_ontologies_for_each_partition'")
    elif not use_current_partition and use_current_ontologies:
        print("  1. Use Claude Agent SDK to analyze data/ folder")
        print("  2. Create partition files in partitions/ directory")
        print("  3. Run 'make validate-partitions' to verify coverage")
        print("  4. Review existing ontologies in ontologies/ directory")
        print("  5. Use 'make view-checklist CHECKLIST=01_create_file_partitions'")
    else:
        print("  1. Use Claude Agent SDK to analyze data/ folder")
        print("  2. Create partition files in partitions/ directory")
        print("  3. Run 'make validate-partitions' to verify coverage")
        print("  4. Create ontologies for each partition")
        print("  5. Use 'make view-checklist' to track progress")
    
    print()
    print("💡 Tip: Run 'make extraction-preview' anytime to see status")
    print()

def main():
    config = load_config()
    show_workflow_steps(config)

if __name__ == "__main__":
    main()

