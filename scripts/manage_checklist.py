#!/usr/bin/env python3
"""
Manage checklists for the KGaaS extraction workflow.

Supports:
- Viewing checklist status
- Checking off items
- Generating dynamic checklists (e.g., per-file preprocessing)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def load_checklist(checklist_id: str) -> Optional[Dict]:
    """Load a checklist JSON file."""
    checklist_path = Path("checklists") / f"{checklist_id}.json"

    if not checklist_path.exists():
        print(f"❌ Checklist not found: {checklist_path}")
        return None

    with open(checklist_path, 'r') as f:
        return json.load(f)


def save_checklist(checklist_id: str, checklist_data: Dict):
    """Save checklist to JSON file."""
    checklist_path = Path("checklists") / f"{checklist_id}.json"

    with open(checklist_path, 'w') as f:
        json.dump(checklist_data, f, indent=2)


def view_checklist(checklist_id: str, recursive: bool = False, indent: int = 0):
    """
    View checklist status.

    Args:
        checklist_id: ID of checklist to view
        recursive: If True, expand sub-checklists
        indent: Indentation level for nested display
    """
    checklist = load_checklist(checklist_id)
    if not checklist:
        return

    prefix = "  " * indent

    if indent == 0:
        print("\n" + "="*60)
        print(f"CHECKLIST: {checklist['title']}")
        if "description" in checklist:
            print(f"{checklist.get('description', '')}")
        print("="*60 + "\n")

    total_items = len(checklist["items"])
    completed_items = sum(1 for item in checklist["items"] if item["completed"])

    print(f"{prefix}📋 {checklist['title']}")
    print(f"{prefix}   Progress: {completed_items}/{total_items} "
          f"({100*completed_items//total_items if total_items > 0 else 0}%)\n")

    for item in checklist["items"]:
        status_icon = "✅" if item["completed"] else "⬜"
        print(f"{prefix}{status_icon} [{item['item_id']}] {item['description']}")

        # Show metadata if present
        if "metadata" in item and item["metadata"]:
            meta = item["metadata"]
            if "completed_at" in meta:
                print(f"{prefix}   Completed: {meta['completed_at']}")
            if "file_path" in meta:
                print(f"{prefix}   File: {meta['file_path']}")

        # Recursively show sub-checklist if requested
        if recursive and "sub_checklist" in item:
            sub_id = item["sub_checklist"].replace(".json", "")
            print(f"{prefix}   └─ Sub-checklist: {item['sub_checklist']}")
            view_checklist(sub_id, recursive=True, indent=indent+2)

        print()


def check_off_item(checklist_id: str, item_id: str, metadata: Optional[Dict] = None):
    """Mark a checklist item as completed."""
    checklist = load_checklist(checklist_id)
    if not checklist:
        return False

    # Find the item
    item_found = False
    for item in checklist["items"]:
        if item["item_id"] == item_id:
            item["completed"] = True
            item.setdefault("metadata", {})
            item["metadata"]["completed_at"] = datetime.utcnow().isoformat() + "Z"

            # Add additional metadata if provided
            if metadata:
                item["metadata"].update(metadata)

            item_found = True
            break

    if not item_found:
        print(f"❌ Item '{item_id}' not found in checklist '{checklist_id}'")
        return False

    # Save updated checklist
    save_checklist(checklist_id, checklist)

    print(f"✅ Checked off [{item_id}] in {checklist_id}")
    return True


def generate_preprocessing_checklist(partition_files: List[str]):
    """
    Generate the preprocessing checklist based on partition files.

    Args:
        partition_files: List of partition IDs to create items for
    """
    checklist = {
        "checklist_id": "02_preprocess_each_partition",
        "title": "Preprocess Each Partition",
        "description": "Per-partition preprocessing checklist - validate ontologies and prepare for extraction",
        "items": []
    }

    for partition_id in sorted(partition_files):
        # Load partition to get file count
        partition_path = Path("partitions") / f"{partition_id}.json"
        if partition_path.exists():
            with open(partition_path, 'r') as f:
                partition_data = json.load(f)
                file_count = len(partition_data.get("paths", []))
                title = partition_data.get("title", "Unknown")
        else:
            file_count = 0
            title = "Unknown"

        item = {
            "item_id": partition_id,
            "description": f"Preprocess {partition_id}: {title} ({file_count} files)",
            "completed": False,
            "metadata": {
                "partition_id": partition_id,
                "file_count": file_count
            }
        }
        checklist["items"].append(item)

    save_checklist("02_preprocess_each_partition", checklist)
    print(f"✅ Generated preprocessing checklist with {len(checklist['items'])} items")


def get_all_partitions() -> List[str]:
    """Get list of all partition IDs."""
    partitions_path = Path("partitions")
    if not partitions_path.exists():
        return []

    partition_ids = []
    for file_path in sorted(partitions_path.glob("*.json")):
        partition_ids.append(file_path.stem)

    return partition_ids


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  View checklist:          python manage_checklist.py view <checklist_id> [--recursive]")
        print("  Check off item:          python manage_checklist.py check <checklist_id> <item_id>")
        print("  Generate preprocessing:  python manage_checklist.py generate-preprocessing")
        print("\nExamples:")
        print("  python manage_checklist.py view master_checklist --recursive")
        print("  python manage_checklist.py check 01_create_file_partition 1.1")
        print("  python manage_checklist.py generate-preprocessing")
        return 1

    command = sys.argv[1]

    if command == "view":
        if len(sys.argv) < 3:
            print("❌ Error: Please specify checklist_id")
            return 1

        checklist_id = sys.argv[2]
        recursive = "--recursive" in sys.argv or "-r" in sys.argv
        view_checklist(checklist_id, recursive=recursive)

    elif command == "check":
        if len(sys.argv) < 4:
            print("❌ Error: Please specify checklist_id and item_id")
            return 1

        checklist_id = sys.argv[2]
        item_id = sys.argv[3]
        check_off_item(checklist_id, item_id)

    elif command == "generate-preprocessing":
        partition_ids = get_all_partitions()
        if not partition_ids:
            print("⚠️  No partitions found. Create partitions first.")
            return 1

        generate_preprocessing_checklist(partition_ids)

    else:
        print(f"❌ Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
