"""
Step 3: Create Ontologies for Each Partition

This module handles the ontology creation workflow step, which:
1. Resets the ontology/ folder (removes existing ontology files)
2. Generates the checklist dynamically from partitions
3. Initializes empty master ontology files
4. Spawns one Claude agent per partition to create ontologies
5. Waits for all agents to complete
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List

from ..helpers.logging import print_usage_summary
from ..helpers.config import get_data_source_path
from ..helpers.checklist import load_checklist, save_checklist
from ..helpers.filesystem import reset_ontology_folder
from ..agents.ontology_agent import run_ontology_agent


def get_all_partitions() -> List[Dict]:
    """
    Get list of all partition files with their data.
    
    Returns:
        List of partition dictionaries with partition_id, title, paths, etc.
    """
    partitions_dir = Path("partitions")
    
    if not partitions_dir.exists():
        return []
    
    partitions = []
    for file_path in sorted(partitions_dir.glob("partition_*.json")):
        with open(file_path, 'r') as f:
            data = json.load(f)
            data["_file_path"] = str(file_path)
            partitions.append(data)
    
    return partitions


def generate_ontology_checklist(partitions: List[Dict], data_source_path: str) -> Dict:
    """
    Generate the 03_create_ontologies_for_each_partition.json checklist dynamically.
    
    Creates a checklist where each partition is an item, and each file in the partition
    is a subtask. The first subtask is always the partition JSON file itself.
    
    Args:
        partitions: List of partition data dictionaries
        data_source_path: Path to the data source directory
        
    Returns:
        The generated checklist dictionary
    """
    checklist = {
        "checklist_id": "03_create_ontologies_for_each_partition",
        "title": "Create Ontologies for Each Partition",
        "description": "Define entity and relationship ontologies for each partition",
        "special_commands": [
            "python scripts/create_entity.py",
            "python scripts/create_relationship.py",
            "python scripts/mark_subtask.py",
            "python scripts/all_subtasks_done.py"
        ],
        "items": []
    }
    
    for partition in partitions:
        partition_id = partition.get("partition_id")
        title = partition.get("title", "Unknown")
        paths = partition.get("paths", [])
        
        # Create item ID (e.g., "3.1" for partition 1, "3.2" for partition 2)
        item_id = f"3.{partition_id}"
        
        # Create the item for this partition
        item = {
            "item_id": item_id,
            "description": f"Create entity and relationship ontologies for partition_{partition_id:02d}.json: {title}",
            "completed": False,
            "subtasks": []
        }
        
        # First subtask is always the partition JSON file itself
        item["subtasks"].append({
            "item_id": f"{item_id}.1",
            "file": f"partitions/partition_{partition_id:02d}.json",
            "description": f"Review entire partition and create complete ontologies",
            "completed": False
        })
        
        # Add a subtask for each file in the partition
        subtask_num = 2
        for path in paths:
            # Build full path relative to data source
            full_path = f"{data_source_path}/{path}" if not path.startswith(data_source_path) else path
            
            item["subtasks"].append({
                "item_id": f"{item_id}.{subtask_num}",
                "file": full_path,
                "completed": False
            })
            subtask_num += 1
        
        checklist["items"].append(item)
    
    return checklist


def init_master_ontologies() -> bool:
    """
    Initialize empty master ontology files.
    
    Returns:
        True if files were created successfully
    """
    ontology_dir = Path("ontology")
    ontology_dir.mkdir(parents=True, exist_ok=True)
    
    # Create master entity ontology file
    entity_path = ontology_dir / "master_entity_ontology.json"
    entity_ontology = {"entities": []}
    
    with open(entity_path, 'w') as f:
        json.dump(entity_ontology, f, indent=2)
    
    # Create master relationship ontology file
    relationship_path = ontology_dir / "master_relationship_ontology.json"
    relationship_ontology = {"relationships": []}
    
    with open(relationship_path, 'w') as f:
        json.dump(relationship_ontology, f, indent=2)
    
    print(f"  ✓ Created master ontology files")
    return True


def step_3_create_ontologies_for_each_partition() -> bool:
    """
    Execute step 3: Create ontologies for each partition using Claude Code Agent SDK
    
    This function:
    1. Resets the ontology/ folder (removes existing ontology files)
    2. Generates the checklist dynamically from partitions
    3. Initializes empty master ontology files
    4. Spawns one Claude agent per partition to create ontologies
    5. Waits for all agents to complete
    
    Returns:
        True if all ontologies were created successfully
    """
    # ========================================================================
    # RESET: Clear existing ontologies and generate checklist
    # ========================================================================
    print("\n" + "=" * 60)
    print("PREPARING STEP 3: ONTOLOGY CREATION")
    print("=" * 60)
    print()
    
    # Get data source path
    data_source_path = get_data_source_path()
    
    # Get all partitions
    partitions = get_all_partitions()
    
    if not partitions:
        print("❌ No partitions found. Run Step 1 first.")
        return False
    
    print(f"  Found {len(partitions)} partitions")
    
    # Reset ontology folder
    reset_ontology_folder()
    
    # Initialize empty master ontology files
    init_master_ontologies()
    
    # Generate the checklist dynamically
    checklist = generate_ontology_checklist(partitions, data_source_path)
    save_checklist("03_create_ontologies_for_each_partition", checklist)
    print(f"  ✓ Generated checklist with {len(checklist['items'])} items")
    
    # Count total subtasks
    total_subtasks = sum(len(item.get("subtasks", [])) for item in checklist["items"])
    print(f"  ✓ Total subtasks: {total_subtasks}")
    
    print()
    
    # ========================================================================
    # STEP 3: Create Ontologies (spawn agent per partition)
    # ========================================================================
    
    print("=" * 60)
    print("STEP 3: Creating Ontologies for Each Partition")
    print("=" * 60)
    print()
    print(f"📋 Spawning {len(partitions)} agents (one per partition)")
    print(f"   Data source: {data_source_path}")
    print()
    
    async def run_all_agents():
        """Run all partition agents concurrently."""
        tasks = [run_ontology_agent(partition, data_source_path) for partition in partitions]
        results = await asyncio.gather(*tasks)
        return results
    
    # Run all agents
    print(f"\n{'='*60}")
    print("Running Agents...")
    print(f"{'='*60}\n")
    
    results = asyncio.run(run_all_agents())
    
    # Process results
    print(f"\n{'='*60}")
    print("Agent Results")
    print(f"{'='*60}\n")
    
    all_success = True
    for partition_id, success, error in results:
        if success:
            print(f"  ✅ Partition {partition_id}: Success")
        else:
            print(f"  ❌ Partition {partition_id}: Failed - {error}")
            all_success = False
    
    # Verify all checklist items are complete
    print(f"\n{'='*60}")
    print("Verifying Checklist Completion")
    print(f"{'='*60}\n")
    
    final_checklist = load_checklist("03_create_ontologies_for_each_partition")
    incomplete_items = []
    
    for item in final_checklist.get("items", []):
        if not item.get("completed", False):
            incomplete_subtasks = [
                st for st in item.get("subtasks", []) 
                if not st.get("completed", False)
            ]
            if incomplete_subtasks:
                incomplete_items.append({
                    "item_id": item.get("item_id"),
                    "incomplete_count": len(incomplete_subtasks)
                })
    
    if incomplete_items:
        print("⚠️  Some items are not fully complete:")
        for item in incomplete_items:
            print(f"   - {item['item_id']}: {item['incomplete_count']} incomplete subtask(s)")
        print()
    else:
        print("✅ All checklist items are complete!")
        print()
    
    # Check master ontology files
    ontology_dir = Path("ontology")
    entity_file = ontology_dir / "master_entity_ontology.json"
    relationship_file = ontology_dir / "master_relationship_ontology.json"
    
    print(f"📊 Master Ontology Files:")
    print(f"   Entity ontology: {'✓' if entity_file.exists() else '✗'} {entity_file}")
    print(f"   Relationship ontology: {'✓' if relationship_file.exists() else '✗'} {relationship_file}")
    print()
    
    if all_success and not incomplete_items:
        print("✅ STEP 3 COMPLETE!")
        print("All ontologies have been created for all partitions.")
        return True
    else:
        print("⚠️  Step 3 completed with some issues.")
        print("Review the results and incomplete items above.")
        return all_success
