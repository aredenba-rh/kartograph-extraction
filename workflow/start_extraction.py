#!/usr/bin/env python3
"""
Start Extraction Workflow
Orchestrates the knowledge graph extraction process using Claude Code Agent SDK.

This script:
1. Loads configuration flags
2. Determines which workflow step to execute
3. Invokes Claude Code Agent SDK with appropriate prompts and tools
4. Implements validation loop for partition creation

Usage:
    python -m workflow.start_extraction
    
    Or from project root:
    python workflow/start_extraction.py
"""

import sys
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import from submodules
from .helpers import (
    load_config,
    get_data_source_path,
    get_data_sources,
    configure_claude_agent_settings,
    reset_checklist,
    reset_logging,
    mark_master_checklist_step_complete,
)
from .steps import (
    step_1_create_file_partitions,
    step_3_create_ontologies_for_each_partition,
)


def show_workflow_status(config: Dict):
    """Display current workflow status"""
    print("\n" + "=" * 60)
    print("EXTRACTION WORKFLOW STATUS")
    print("=" * 60)
    print()
    print("Configuration:")
    print("  " + "─" * 56)
    
    # Flag display names and their corresponding step numbers
    flag_info = {
        "use_current_partition": ("use_current_partition", "01"),
        "use_current_ontologies": ("use_current_ontologies", "03")
    }
    
    for key, value in config.items():
        display_name, step_num = flag_info.get(key, (key, "??"))
        status = "--SKIP--" if value else f"Step {step_num}"
        print(f"  {display_name:30s} {status}")
    print()


def main():
    """Main workflow orchestration"""
    # ========================================================================
    # RESET: Reset all workflow artifacts at the beginning
    # ========================================================================
    print("\n" + "=" * 60)
    print("INITIALIZING EXTRACTION WORKFLOW")
    print("=" * 60)
    print()
    
    # Reset the logging file for a fresh start
    reset_logging()
    
    # Configure Claude agent settings (allow/deny rules)
    data_source_path = get_data_source_path()
    data_sources = get_data_sources()
    configure_claude_agent_settings(data_source_path, data_sources)
    
    print()
    
    # ========================================================================
    # Load Configuration and Show Status
    # ========================================================================
    
    # Load configuration
    config = load_config()
    show_workflow_status(config)

    # Reset the master checklist before running any steps
    reset_checklist("master_checklist")
    
    # Determine which steps to execute (True = execute, False = skip)
    step_1 = not config.get('use_current_partition', False)
    step_3 = not config.get('use_current_ontologies', False)
    
    # If all steps are skipped
    if not step_1 and not step_3:
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
        else:
            # Mark step_01 as complete in master checklist
            print()
            mark_master_checklist_step_complete("step_01")
            print()
    
    # Execute Step 3: Create ontologies for each partition
    if step_3:
        print("→ Executing: Step 3 - Create ontologies for each partition")
        success = step_3_create_ontologies_for_each_partition()
        if not success:
            print("\n❌ Failed to create ontologies.")
            return 1
        else:
            # Mark step_03 as complete in master checklist
            print()
            mark_master_checklist_step_complete("step_03")
            print()
    
    return 0


if __name__ == "__main__":
    # When running as a script, ensure the parent directory is in the path
    # so that relative imports work correctly
    script_dir = Path(__file__).parent.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    # Re-import with proper path
    from workflow.start_extraction import main as run_main
    sys.exit(run_main())

