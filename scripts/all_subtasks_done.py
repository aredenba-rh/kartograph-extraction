#!/usr/bin/env python3
"""
All Subtasks Done Script
Verifies that all subtasks for a specific partition item are complete.

Usage:
    python scripts/all_subtasks_done.py [item_item_id]
    
If item_item_id is not provided, it reads from PARTITION_ITEM_ID environment variable.

Example:
    python scripts/all_subtasks_done.py 2.1
    PARTITION_ITEM_ID=2.1 python scripts/all_subtasks_done.py

Returns exit code 0 if all subtasks are complete, 1 otherwise.
"""

import json
import os
import sys
from pathlib import Path


CHECKLIST_ID = "02_create_ontologies_for_each_partition"


def load_checklist() -> dict:
    """Load the ontology creation checklist."""
    checklist_path = Path("checklists") / f"{CHECKLIST_ID}.json"
    
    if not checklist_path.exists():
        print(f"❌ Checklist not found: {checklist_path}")
        sys.exit(1)
    
    with open(checklist_path, 'r') as f:
        return json.load(f)


def check_all_subtasks_done(item_item_id: str) -> tuple[bool, list]:
    """
    Check if all subtasks for a specific item are complete.
    
    Args:
        item_item_id: The parent item ID (e.g., "2.1" for partition 1)
        
    Returns:
        Tuple of (all_complete, list_of_incomplete_subtasks)
    """
    checklist = load_checklist()
    
    # Find the parent item
    for item in checklist.get("items", []):
        if item.get("item_id") == item_item_id:
            subtasks = item.get("subtasks", [])
            incomplete = []
            
            for subtask in subtasks:
                if not subtask.get("completed", False):
                    incomplete.append({
                        "item_id": subtask.get("item_id"),
                        "file": subtask.get("file", subtask.get("description", "Unknown"))
                    })
            
            return len(incomplete) == 0, incomplete
    
    print(f"❌ Item '{item_item_id}' not found in checklist")
    return False, []


def main():
    """Command-line interface for checking subtask completion."""
    # Get the parent item ID from argument or environment variable
    item_item_id = None
    
    if len(sys.argv) >= 2:
        item_item_id = sys.argv[1]
    else:
        item_item_id = os.environ.get("PARTITION_ITEM_ID")
    
    if not item_item_id:
        print("Usage: python scripts/all_subtasks_done.py [item_item_id]")
        print("\nOr set PARTITION_ITEM_ID environment variable.")
        print("\nExample:")
        print("  python scripts/all_subtasks_done.py 2.1")
        print("  PARTITION_ITEM_ID=2.1 python scripts/all_subtasks_done.py")
        sys.exit(1)
    
    all_complete, incomplete = check_all_subtasks_done(item_item_id)
    
    print(f"\n{'='*60}")
    print(f"SUBTASK COMPLETION CHECK: {item_item_id}")
    print(f"{'='*60}\n")
    
    if all_complete:
        print(f"✅ ALL SUBTASKS COMPLETE for {item_item_id}!")
        print(f"\n   You have successfully completed all ontology tasks for this partition.")
        print(f"   The agent session can now end.\n")
        sys.exit(0)
    else:
        print(f"❌ INCOMPLETE SUBTASKS FOUND for {item_item_id}:")
        print()
        
        for idx, task in enumerate(incomplete, 1):
            print(f"   {idx}. [{task['item_id']}] {task['file']}")
        
        print(f"\n   Total incomplete: {len(incomplete)} subtask(s)")
        print(f"\n   Please complete these subtasks before ending the session:")
        print(f"   - For each file, ensure all entities and relationships are created")
        print(f"   - Run: python scripts/mark_subtask.py {item_item_id} <subtask_item_id>")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

