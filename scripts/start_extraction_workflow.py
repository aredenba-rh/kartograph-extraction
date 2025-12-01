#!/usr/bin/env python3
"""
Start Extraction Workflow
Orchestrates the knowledge graph extraction process using Claude Code Agent SDK.

This script:
1. Loads configuration flags
2. Determines which workflow step to execute
3. Invokes Claude Code Agent SDK with appropriate prompts and tools
4. Implements validation loop for partition creation
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional


def log_to_file(key: str, value: str):
    """
    Log a key-value pair to logging/logging.json
    
    Args:
        key: The log entry key
        value: The log entry value
    """
    log_dir = Path("logging")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "logging.json"
    
    # Load existing logs or create new dict
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)
    else:
        logs = {}
    
    # Add new entry
    logs[key] = value
    
    # Write back
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


def load_config() -> Dict:
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


def load_checklist(checklist_id: str) -> Dict:
    """Load a specific checklist file"""
    checklist_path = Path(f"checklists/{checklist_id}.json")
    
    if not checklist_path.exists():
        raise FileNotFoundError(f"Checklist {checklist_id} not found")
    
    with open(checklist_path, 'r') as f:
        return json.load(f)


def get_data_source_path() -> str:
    """
    Get the data source path to extract from.
    Returns the first (and only) folder found in data/ directory.
    """
    data_dir = Path("data")
    
    if not data_dir.exists():
        raise FileNotFoundError("data/ directory does not exist")
    
    # Get all subdirectories in data/
    subdirs = [d for d in data_dir.iterdir() if d.is_dir()]
    
    if len(subdirs) == 0:
        raise FileNotFoundError("No subdirectories found in data/")
    
    if len(subdirs) > 1:
        raise ValueError(f"Multiple data sources found in data/: {[d.name for d in subdirs]}. Expected only one.")
    
    return str(subdirs[0])


def build_partition_creation_prompt(data_source_path: str, example_partition_path: str = "examples/partition_example") -> str:
    """
    Build the user message prompt for Claude to create partitions.
    
    Args:
        data_source_path: Path to the data source directory
        example_partition_path: Path to example partition structure
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""I'm building an Knowledge Graph-powered AI Assistant to answer customer questions. We're creating this Knowledge Graph from the data source located at {data_source_path}.

## Your Task

Step 1 of this Knowledge Graph creation process: Create a partition of all files/paths at {data_source_path}. 
The ontology ontology creation and entity/relationship extraction come later.

## Example Partition Structure

See `{example_partition_path}/` for a working example:
- **Data**: 7 files in `{example_partition_path}/data/data_source_repo_name/` (2 folders, 3 top-level files)
- **Partitions**: 2 partition files demonstrating complete, disjoint coverage
  - `partition_01.json`: Uses directory path `folderA/` (all files) + specific files from `folderB/` + 2 top-level files
  - `partition_02.json`: Remaining file from `folderB/` + 1 top-level file
- **Key Rule**: Every file appears exactly once across all partitions

## How to Create Partitions

Call `scripts/create_partition.py` once per partition:

```bash
python scripts/create_partition.py <title> <description> <path1> [path2] ...
```

**Arguments:**
- `<title>`: Concise label/title (≤8 words) describing the partition's content (Title should concisely indicate the purpose of this group of files).
- `<description>`: 3-4 sentences describing the files in this partition - their common characteristics, and their role relative to all the files at {data_source_path}.
- `<path1> [path2] ...`: One or more file/directory paths to include

**Path notation:**
- Directory (with `/`): `"{data_source_path}/subfolder/"` = ALL files in that directory
- Specific file: `"{data_source_path}/file.md"` = single file
- All paths relative from project root

**Example** (see `{example_partition_path}/partition_01.json` for actual structure):
```bash
python scripts/create_partition.py \\
  "Core Documentation" \\
  "Primary documentation files ..." \\
  "data/data_source_repo_name/folderA/" \\
  "data/data_source_repo_name/folderB/fileBA.md" \\
  "data/data_source_repo_name/fileA.md"
```

## Success Criteria

A successful partition structure must:
1. ✅ Cover ALL files in {data_source_path}
2. ✅ Have NO duplicate coverage (each file in exactly one partition)
3. ✅ Have NO missing files
4. ✅ Use logical groupings that make sense for knowledge graph extraction

After you create your partitions, the system will automatically validate them. If there are issues, you'll receive detailed feedback about which files are duplicated or missing.

Good luck! Start by exploring the contents of {data_source_path}, then create appropriate partitions using the create_partition.py script. 
Once you've created your partitions, run the `make validate-partitions` command to validate them.
If there are issues, you'll receive detailed feedback about which files are duplicated or missing.

**When complete**: After you've created all necessary partitions, and validated them, your task is done - the system will check your work and proceed to the next step.
"""
    return prompt


def step_1_create_file_partitions() -> bool:
    """
    Execute step 1: Create file partitions using Claude Code Agent SDK
    
    Returns:
        True if partitions were created and validated successfully
    """
    from claude_agent_sdk import create_agent
    
    # Import validation function
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from confirm_acceptable_partition import validate_and_get_errors
    
    # Get data source path
    data_source_path = get_data_source_path()
    
    # Load checklist to get available tools for step 1.1
    checklist = load_checklist("01_create_file_partitions")
    step_1_1 = checklist["items"][0]  # First item is 1.1
    available_tools = step_1_1.get("available_tools", [])
    
    # Build the initial prompt
    user_message = build_partition_creation_prompt(data_source_path)
    
    # Log the initial prompt (only once, before retry loop)
    log_to_file("1.1 File Partitions Prompt", user_message)
    
    print("=" * 60)
    print("STEP 1.1: Creating File Partitions")
    print("=" * 60)
    print(f"Data source: {data_source_path}")
    print(f"Available tools: {', '.join(available_tools)}")
    print()
    
    # Create Claude agent once (maintains memory across retry attempts)
    agent = create_agent(
        name="partition_creator",
        instructions="You are a data partitioning expert helping to create logical file groupings for knowledge graph extraction.",
    )
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"Attempt {attempt}/{max_attempts}")
        print(f"{'='*60}\n")
        
        # Run the agent with the prompt
        print("🤖 Invoking Claude Code Agent SDK...")
        
        try:
            # Execute Claude agent
            # The agent will have access to run terminal commands
            result = agent.run(user_message)
            
            print(f"\n✅ Claude agent completed execution")
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"❌ Error executing Claude agent: {e}")
            return False
        
        # Validate the partitions
        print(f"\n{'='*60}")
        print("Validating Partitions...")
        print(f"{'='*60}\n")
        
        is_valid, error_message = validate_and_get_errors()
        
        if is_valid:
            print("✅ VALIDATION PASSED!")
            print("Partitions are complete and disjoint.")
            print(f"\n{'='*60}")
            print("PROCEEDING TO STEP 2.1: Create Ontologies")
            print(f"{'='*60}\n")
            return True
        else:
            print("❌ VALIDATION FAILED!")
            print("\nErrors found:")
            print(error_message)
            
            if attempt < max_attempts:
                print(f"\n🔄 Retrying... (Attempt {attempt + 1}/{max_attempts})")
                print("Sending error feedback to Claude agent...")
                
                # Update user message with error feedback for next iteration
                user_message = f"""The partitions you created have validation errors. Please fix them.

VALIDATION ERRORS:
{error_message}

Please:
1. Review the errors above
2. Delete the problematic partition files in partitions/ directory
3. Create corrected partitions using the create_partition.py script
4. Ensure complete and disjoint coverage of all files in {data_source_path}

Remember:
- Each file must appear in exactly ONE partition (no duplicates)
- ALL files must be covered (no missing files)
- Use "path/to/directory/" (with trailing slash) to include all files in a directory
"""
            else:
                print(f"\n❌ Maximum attempts ({max_attempts}) reached.")
                print("Please review the errors and create partitions manually.")
                return False
    
    return False


def step_2_create_ontologies_for_each_partition() -> bool:
    """
    Execute step 2: Create ontologies for each partition
    
    This is a placeholder for the ontology creation workflow.
    """
    print("=" * 60)
    print("STEP 2.1: Create Ontologies for Each Partition")
    print("=" * 60)
    print()
    print("📋 This step will create entity and relationship ontologies")
    print("   for each partition created in the previous step.")
    print()
    print("⚠️  Ontology creation workflow not yet implemented.")
    print("   This will be implemented in a future iteration.")
    print()
    
    return True


def show_workflow_status(config: Dict):
    """Display current workflow status"""
    print("\n" + "=" * 60)
    print("EXTRACTION WORKFLOW STATUS")
    print("=" * 60)
    print()
    print("Configuration:")
    print("  " + "─" * 56)
    for key, value in config.items():
        status = "✓ ON " if value else "✗ OFF"
        print(f"  {key:30s} {status}")
    print()


def main():
    """Main workflow orchestration"""
    # Load configuration
    config = load_config()
    show_workflow_status(config)
    
    # Determine which steps to execute (True = execute, False = skip)
    step_1 = not config.get('use_current_partition', False)
    step_2 = not config.get('use_current_ontologies', False)
    
    # If all steps are skipped
    if not step_1 and not step_2:
        print("⚠️  All workflow steps are skipped!")
        print("Review existing partitions and ontologies, then proceed to extraction.")
        return 0
    
    # Execute Step 1: Create file partitions
    if step_1:
        print("→ Executing: Step 1 - Create file partitions")
        success = step_1_create_file_partitions()
        if not success:
            print("\n❌ Failed to create valid partitions.")
            print("Please review the errors and try again.")
            return 1
    
    # Execute Step 2: Create ontologies for each partition
    if step_2:
        print("→ Executing: Step 2 - Create ontologies for each partition")
        success = step_2_create_ontologies_for_each_partition()
        if not success:
            print("\n❌ Failed to create ontologies.")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
