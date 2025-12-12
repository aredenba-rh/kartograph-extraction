"""
Step 1: Create File Partitions

This module handles the partition creation workflow step, which:
1. Resets the partitions/ folder (removes existing partitions)
2. Resets the checklist (marks all items as incomplete)
3. Creates new partitions using Claude Agent SDK
4. Validates the partitions with a retry loop
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

from ..helpers.logging import log_prompt_to_file, finalize_attempt_log, print_usage_summary
from ..helpers.config import get_data_source_path
from ..helpers.checklist import load_checklist, reset_checklist, mark_checklist_item_complete
from ..helpers.filesystem import reset_partitions_folder
from ..prompts.partition_prompts import build_partition_creation_prompt
from ..agents.partition_agent import run_partition_creation_attempt


def step_1_create_file_partitions() -> bool:
    """
    Execute step 1: Create file partitions using Claude Code Agent SDK
    
    This function:
    1. Resets the partitions/ folder (removes existing partitions)
    2. Resets the checklist (marks all items as incomplete)
    3. Creates new partitions using Claude Agent SDK
    4. Validates the partitions
    
    Returns:
        True if partitions were created and validated successfully
    """
    # ========================================================================
    # RESET: Clear existing partitions and checklist before starting
    # ========================================================================
    print("\n" + "=" * 60)
    print("RESETTING STEP 1 ARTIFACTS")
    print("=" * 60)
    print()
    
    # Remove existing partitions (only when we're recreating them)
    reset_partitions_folder()
    
    # Reset the checklist for this step
    reset_checklist("01_create_file_partitions")
    
    print()
    
    # ========================================================================
    # STEP 1.1: Create File Partitions
    # ========================================================================
    
    # Import validation function
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from confirm_acceptable_partition import validate_and_get_errors
    
    # Get data source path
    data_source_path = get_data_source_path()
    
    # Load checklist to get special commands for step 1.1
    checklist = load_checklist("01_create_file_partitions")
    step_1_1 = checklist["items"][0]  # First item is 1.1
    special_commands = step_1_1.get("special_commands", [])
    
    # Build the initial prompt
    user_message = build_partition_creation_prompt(data_source_path, special_commands)
    
    # Log the initial prompt to a text file (only once, before retry loop)
    log_prompt_to_file("step_1_1_file_partitions_prompt", user_message)
    
    step_name = "step_1.1_file_partitions"
    
    print("=" * 60)
    print("STEP 1.1: Creating File Partitions")
    print("=" * 60)
    print(f"Data source: {data_source_path}")
    print(f"Special commands: {', '.join(special_commands)}")
    print()
    
    print(f"🔗 Using Claude Agent SDK")
    print()
    
    max_attempts = 3
    attempt = 0
    
    # Main retry loop
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"Attempt {attempt}/{max_attempts}")
        print(f"{'='*60}\n")
        
        # Set started timestamp
        log_file = Path("logging") / "logging.json"
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
            if step_name in logs:
                attempts = logs[step_name]["attempts"]
                if len(attempts) >= attempt and attempts[attempt - 1]["started_at"] is None:
                    attempts[attempt - 1]["started_at"] = datetime.utcnow().isoformat() + "Z"
                    with open(log_file, 'w') as f:
                        json.dump(logs, f, indent=2)
        
        # Run the partition creation attempt
        success, error = asyncio.run(run_partition_creation_attempt(user_message, step_name, attempt))
        
        if not success:
            finalize_attempt_log(step_name, attempt, "failed", error)
            print(f"\n❌ Attempt {attempt} failed: {error}")
            if attempt < max_attempts:
                print(f"🔄 Will retry...")
            continue
        
        # Validate the partitions
        print(f"\n{'='*60}")
        print("Validating Partitions...")
        print(f"{'='*60}\n")
        
        is_valid, error_message = validate_and_get_errors()
        
        if is_valid:
            # Log successful attempt
            finalize_attempt_log(step_name, attempt, "success")
            
            # Mark checklist item 1.1 as complete
            print()
            mark_checklist_item_complete("01_create_file_partitions", "1.1")
            print()
            
            # Show message summary
            print(f"\n{'='*60}")
            print("📊 Session Summary")
            print(f"{'='*60}")
            print_usage_summary(step_name)
            
            print("✅ VALIDATION PASSED!")
            print("Partitions are complete and disjoint.")
            print(f"\n{'='*60}")
            print("PROCEEDING TO STEP 2.1: Create Ontologies")
            print(f"{'='*60}\n")
            return True
        else:
            # Log failed attempt
            finalize_attempt_log(step_name, attempt, "failed", error_message)
            
            # Show message summary for this attempt
            print(f"\n{'='*60}")
            print("📊 Session Summary")
            print(f"{'='*60}")
            print_usage_summary(step_name)
            
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
3. Create corrected partitions using `make create-partition` command
4. Ensure complete and disjoint coverage of all files in {data_source_path}

Remember:
- Each file must appear in exactly ONE partition (no duplicates)
- ALL files must be covered (no missing files)
- Use "path/to/directory/" (with trailing slash) to include all files in a directory

Once you've fixed the issues, run `make validate-partitions` to verify.
"""
            else:
                print(f"\n❌ Maximum attempts ({max_attempts}) reached.")
                print("Please review the errors and create partitions manually.")
                return False
    
    return False

