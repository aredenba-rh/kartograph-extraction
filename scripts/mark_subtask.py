#!/usr/bin/env python3
"""
Mark Subtask Complete Script
Marks a specific subtask as complete in the 03_create_ontologies_for_each_partition checklist.

Usage:
    python scripts/mark_subtask.py <subtask_item_id>
    
The item_item_id (e.g., "3.1") is determined from the PARTITION_ITEM_ID environment variable,
which should be set when spawning the agent for a specific partition.

Example:
    PARTITION_ITEM_ID=3.1 python scripts/mark_subtask.py 3.1.3
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone


CHECKLIST_ID = "03_create_ontologies_for_each_partition"


def load_checklist() -> dict:
    """Load the ontology creation checklist."""
    checklist_path = Path("checklists") / f"{CHECKLIST_ID}.json"
    
    if not checklist_path.exists():
        print(f"❌ Checklist not found: {checklist_path}")
        sys.exit(1)
    
    with open(checklist_path, 'r') as f:
        return json.load(f)


def save_checklist(checklist_data: dict):
    """Save the checklist to JSON file."""
    checklist_path = Path("checklists") / f"{CHECKLIST_ID}.json"
    
    with open(checklist_path, 'w') as f:
        json.dump(checklist_data, f, indent=2)


def mark_subtask_complete(item_item_id: str, subtask_item_id: str) -> bool:
    """
    Mark a specific subtask as complete.
    
    Args:
        item_item_id: The parent item ID (e.g., "2.1" for partition 1)
        subtask_item_id: The subtask ID to mark complete (e.g., "2.1.3")
        
    Returns:
        True if successful, False otherwise
    """
    checklist = load_checklist()
    
    # Find the parent item
    parent_found = False
    subtask_found = False
    
    for item in checklist.get("items", []):
        if item.get("item_id") == item_item_id:
            parent_found = True
            
            # Find and mark the subtask
            for subtask in item.get("subtasks", []):
                if subtask.get("item_id") == subtask_item_id:
                    subtask["completed"] = True
                    subtask["completed_at"] = datetime.now(timezone.utc).isoformat()
                    subtask_found = True
                    break
            
            # Check if ALL subtasks are now complete
            all_complete = all(st.get("completed", False) for st in item.get("subtasks", []))
            if all_complete:
                item["completed"] = True
                item["completed_at"] = datetime.now(timezone.utc).isoformat()
                print(f"  ✓ All subtasks complete for {item_item_id} - marking parent item complete")
            
            break
    
    if not parent_found:
        print(f"❌ Item '{item_item_id}' not found in checklist")
        return False
    
    if not subtask_found:
        print(f"❌ Subtask '{subtask_item_id}' not found under item '{item_item_id}'")
        return False
    
    # Save updated checklist
    save_checklist(checklist)
    print(f"✅ Marked subtask {subtask_item_id} as complete")
    return True


def main():
    """Command-line interface for marking subtasks complete."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/mark_subtask.py <subtask_item_id>")
        print("\nThe parent item_id is read from PARTITION_ITEM_ID environment variable.")
        print("\nExample:")
        print("  PARTITION_ITEM_ID=2.1 python scripts/mark_subtask.py 2.1.3")
        sys.exit(1)
    
    subtask_item_id = sys.argv[1]
    
    # Get the parent item ID from environment variable
    item_item_id = os.environ.get("PARTITION_ITEM_ID")
    
    if not item_item_id:
        print("❌ PARTITION_ITEM_ID environment variable not set")
        print("   This should be set when the agent is spawned for a specific partition")
        print("\nAlternatively, you can pass both IDs:")
        print("  python scripts/mark_subtask.py <item_item_id> <subtask_item_id>")
        print("\nExample:")
        print("  python scripts/mark_subtask.py 3.1 3.1.3")
        
        # Allow passing both as fallback
        if len(sys.argv) >= 3:
            item_item_id = sys.argv[1]
            subtask_item_id = sys.argv[2]
        else:
            sys.exit(1)
    
    success = mark_subtask_complete(item_item_id, subtask_item_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

