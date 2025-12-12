"""
Checklist management utilities for the extraction workflow.

Provides functions for:
- Loading and saving checklists
- Resetting checklist items
- Marking items and sub-items as complete
"""

import json
from pathlib import Path
from typing import Dict


def load_checklist(checklist_id: str) -> Dict:
    """Load a specific checklist file"""
    checklist_path = Path(f"checklists/{checklist_id}.json")
    
    if not checklist_path.exists():
        raise FileNotFoundError(f"Checklist {checklist_id} not found")
    
    with open(checklist_path, 'r') as f:
        return json.load(f)


def save_checklist(checklist_id: str, checklist_data: Dict):
    """Save checklist to JSON file."""
    checklist_path = Path(f"checklists/{checklist_id}.json")
    
    with open(checklist_path, 'w') as f:
        json.dump(checklist_data, f, indent=2)
    print(f"  ✓ Reset checklist: {checklist_id}")


def reset_checklist(checklist_id: str):
    """Reset all items in a checklist to completed=false"""
    checklist = load_checklist(checklist_id)
    
    # Set all items to completed=false
    for item in checklist.get("items", []):
        item["completed"] = False
    
    save_checklist(checklist_id, checklist)


def mark_checklist_item_complete(checklist_id: str, item_id: str):
    """
    Mark a specific checklist item as complete.
    
    This function supports both simple items and items with sub_items.
    For future compatibility, it will also mark all sub_items as complete.
    
    Args:
        checklist_id: The ID of the checklist (e.g., "01_create_file_partitions")
        item_id: The ID of the item to mark as complete (e.g., "1.1")
    """
    checklist = load_checklist(checklist_id)
    
    # Find and mark the item as complete
    for item in checklist.get("items", []):
        if item.get("item_id") == item_id:
            item["completed"] = True
            
            # Future support: mark all sub_items as complete if they exist
            if "sub_items" in item:
                for sub_item in item["sub_items"]:
                    sub_item["completed"] = True
            
            break
    
    save_checklist(checklist_id, checklist)
    print(f"  ✓ Marked {checklist_id} item {item_id} as complete")


def mark_master_checklist_step_complete(step_id: str):
    """
    Mark a step in the master checklist as complete.
    
    This should be called when all items (and sub_items) in a step's
    sub-checklist have been successfully completed.
    
    Args:
        step_id: The step ID to mark as complete (e.g., "step_01", "step_02")
    """
    mark_checklist_item_complete("master_checklist", step_id)
    print(f"  ✓ Step {step_id} fully complete!")

