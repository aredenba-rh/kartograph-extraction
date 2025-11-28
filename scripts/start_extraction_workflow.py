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
    Currently hardcoded to rosa-kcs, but could be made configurable.
    """
    # TODO: Make this configurable via extraction_config.json
    return "data/rosa-kcs"


def build_partition_creation_prompt(data_source_path: str) -> str:
    """
    Build the user message prompt for Claude to create partitions.
    
    Args:
        data_source_path: Path to the data source directory
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""I'm creating a "ROSA Ask-SRE" Assistant. ROSA indicates "RedHat OpenShift on AWS" and an SRE is a "Site Reliability Engineer" - so, in other words, I'm building an AI chat bot which should have mastery understanding of the 3 datasources in this repo (openshift-docs, ops-sop, rosa-kcs) -> which will then be used to assist our employees to solve our customer's issues.

To do this we are going to create a knowledge graph from {data_source_path}. 

## Your Task

Analyze the contents at {data_source_path}, and create a partition of the files/paths there.

## What are Partitions?

The partitions should be **logical groupings** of files/paths that could be handled similarly by an agent creating a knowledge graph. Each partition will have an entity ontology and a relationship ontology built for it. 

However, when we get to the entity/relationship creation portion of this KG-creation - we will have dynamic ontologies (meaning that any and all entity-types, relationship-types, and attributes will be captured - so the purpose of the ontologies being created right now is to grab the most common types that will appear for each partition - which we will eventually merge across all partitions in order to standardize our types to eliminate ontology-type-redundancy).

## Partitioning Strategy

- If the data_source is just a single folder of files with a similar structure - they can exist in a single partition
- If the data source is larger with distinct content types or purposes, create those logical groupings as you see fit
- Each file in {data_source_path} must appear in exactly ONE partition (disjoint partitions)
- All files must be covered (complete coverage)

## How to Create Partitions

Use the `create_partition.py` script located in the `scripts/` directory. Call it once for each partition you create.

**Function signature:**
```bash
python scripts/create_partition.py <title> <description> <path1> [path2] [path3] ...
```

**Important Path Notation:**
- Use **trailing slash** for directory paths: `"data/rosa-kcs/kcs_solutions/"` means ALL files in that directory
- Use **specific file paths** for individual files: `"data/rosa-kcs/config.yaml"`
- All paths should be relative from the project root

**Example:**
```bash
# Partition covering all files in a directory plus specific files
python scripts/create_partition.py \\
  "AWS Integration Documentation" \\
  "Files related to AWS service integration and configurations" \\
  "data/rosa-kcs/kcs_solutions/" \\
  "data/rosa-kcs/README.md"

# Partition with only specific files
python scripts/create_partition.py \\
  "Configuration Files" \\
  "System configuration and setup files" \\
  "data/rosa-kcs/config.yaml" \\
  "data/rosa-kcs/setup.yaml"
```

## Examples

Check the `examples/partition_example/` directory for a clear demonstration of:
- How to structure partitions
- Directory vs. file path notation
- Complete and disjoint coverage

## Success Criteria

A successful partition structure must:
1. ✅ Cover ALL files in {data_source_path}
2. ✅ Have NO duplicate coverage (each file in exactly one partition)
3. ✅ Have NO missing files
4. ✅ Use logical groupings that make sense for knowledge graph extraction

After you create your partitions, the system will automatically validate them. If there are issues, you'll receive detailed feedback about which files are duplicated or missing.

Good luck! Start by exploring the contents of {data_source_path}, then create appropriate partitions using the create_partition.py script.
"""
    return prompt


def execute_step_1_1_create_partitions(data_source_path: str, available_tools: List[str]) -> bool:
    """
    Execute step 1.1: Create file partitions using Claude Code Agent SDK
    
    Args:
        data_source_path: Path to the data source directory
        available_tools: List of available tool names for Claude
        
    Returns:
        True if partitions were created and validated successfully
    """
    from claude_agent_sdk import create_agent
    
    # Import validation function
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from confirm_acceptable_partition import validate_and_get_errors
    
    # Build the prompt
    user_message = build_partition_creation_prompt(data_source_path)
    
    print("=" * 60)
    print("STEP 1.1: Creating File Partitions")
    print("=" * 60)
    print(f"Data source: {data_source_path}")
    print(f"Available tools: {', '.join(available_tools)}")
    print()
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"Attempt {attempt}/{max_attempts}")
        print(f"{'='*60}\n")
        
        # Create Claude agent
        # Note: The claude-agent-sdk should be properly configured
        # This is a basic integration - adjust based on actual SDK API
        agent = create_agent(
            name="partition_creator",
            instructions="You are a data partitioning expert helping to create logical file groupings for knowledge graph extraction.",
        )
        
        # Run the agent with the prompt
        print("🤖 Invoking Claude Code Agent SDK...")
        print(f"\nPrompt:\n{user_message}\n")
        
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


def execute_step_2_1_create_ontologies() -> bool:
    """
    Execute step 2.1: Create ontologies for each partition
    
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
    
    use_current_partition = config.get('use_current_partition', False)
    use_current_ontologies = config.get('use_current_ontologies', False)
    
    # Determine which step to execute
    if use_current_partition and use_current_ontologies:
        print("⚠️  Both workflow steps are skipped!")
        print("Review existing partitions and ontologies, then proceed to extraction.")
        return 0
        
    elif use_current_partition and not use_current_ontologies:
        print("→ Starting at: Step 2 - Create ontologies for each partition")
        # Load checklist to get available tools
        checklist = load_checklist("02_create_ontologies_for_each_partition")
        # Execute step 2.1
        success = execute_step_2_1_create_ontologies()
        return 0 if success else 1
        
    elif not use_current_partition:
        print("→ Starting at: Step 1 - Create file partitions")
        
        # Get data source path
        data_source_path = get_data_source_path()
        
        # Load checklist to get available tools for step 1.1
        checklist = load_checklist("01_create_file_partitions")
        step_1_1 = checklist["items"][0]  # First item is 1.1
        available_tools = step_1_1.get("available_tools", [])
        
        # Execute step 1.1
        success = execute_step_1_1_create_partitions(data_source_path, available_tools)
        
        if success:
            # If partitions were created successfully, proceed to step 2.1
            if not use_current_ontologies:
                execute_step_2_1_create_ontologies()
            return 0
        else:
            print("\n❌ Failed to create valid partitions.")
            print("Please review the errors and try again.")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
