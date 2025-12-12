"""
Step 1: Create File Partitions

This module handles the partition creation workflow step, which:
1. Resets the partitions/ folder (removes existing partitions)
2. Resets the checklist (marks all items as incomplete)
3. Creates new partitions using Claude Agent SDK (once per data source)
4. Validates the partitions with a retry loop
"""

import sys
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from ..helpers.logging import log_prompt_to_file, finalize_attempt_log, print_usage_summary, STEP_1_LOG_DIR
from ..helpers.config import get_data_source_path, get_data_sources
from ..helpers.checklist import load_checklist, reset_checklist, mark_checklist_item_complete
from ..helpers.filesystem import reset_partitions_folder
from ..prompts.partition_prompts import build_partition_creation_prompt
from ..agents.partition_agent import run_partition_creation_attempt


def run_partition_agent_for_data_source(
    data_source: str,
    data_source_path: str,
    special_commands: list,
    max_attempts: int = 3
) -> bool:
    """
    Run the partition creation agent for a single data source.
    
    Args:
        data_source: Name of the data source (e.g., "openshift-docs")
        data_source_path: Full path to the data source (e.g., "data/openshift-docs")
        special_commands: List of make commands available to the agent
        max_attempts: Maximum number of retry attempts
        
    Returns:
        True if partitions were created successfully for this data source
    """
    # Import validation function
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    from validate_partition import validate_and_get_errors
    
    # Build the initial prompt for this data source
    user_message = build_partition_creation_prompt(data_source, data_source_path, special_commands)
    
    # Log the initial prompt to a text file (file_partition_{data_source}_prompt.txt)
    log_prompt_to_file(data_source, user_message)
    
    step_name = f"step_1.1_file_subsets_{data_source}"
    
    print("=" * 60)
    print(f"STEP 1.1: Creating File Subsets for '{data_source}'")
    print("=" * 60)
    print(f"Data path: {data_source_path}")
    print(f"Special commands: {', '.join(special_commands)}")
    print()
    
    print(f"🔗 Using Claude Agent SDK")
    print()
    
    attempt = 0
    
    # Main retry loop
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"Attempt {attempt}/{max_attempts} for '{data_source}'")
        print(f"{'='*60}\n")
        
        # Set started timestamp
        log_file = STEP_1_LOG_DIR / "logging.json"
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
            if step_name in logs:
                attempts = logs[step_name]["attempts"]
                if len(attempts) >= attempt and attempts[attempt - 1]["started_at"] is None:
                    attempts[attempt - 1]["started_at"] = datetime.now(timezone.utc).isoformat()
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
        
        # Validate the file subsets for this data source
        print(f"\n{'='*60}")
        print(f"Validating File Subsets for '{data_source}'...")
        print(f"{'='*60}\n")
        
        is_valid, error_message = validate_and_get_errors(data_source)
        
        if is_valid:
            # Log successful attempt
            finalize_attempt_log(step_name, attempt, "success")
            
            # Show message summary
            print(f"\n{'='*60}")
            print(f"📊 Session Summary for '{data_source}'")
            print(f"{'='*60}")
            print_usage_summary(step_name)
            
            print(f"✅ VALIDATION PASSED for '{data_source}'!")
            print("File subsets are complete and disjoint.")
            return True
        else:
            # Log failed attempt
            finalize_attempt_log(step_name, attempt, "failed", error_message)
            
            # Show message summary for this attempt
            print(f"\n{'='*60}")
            print(f"📊 Session Summary for '{data_source}'")
            print(f"{'='*60}")
            print_usage_summary(step_name)
            
            print("❌ VALIDATION FAILED!")
            print("\nErrors found:")
            print(error_message)
            
            if attempt < max_attempts:
                print(f"\n🔄 Retrying... (Attempt {attempt + 1}/{max_attempts})")
                print("Sending error feedback to Claude agent...")
                
                # Update user message with error feedback for next iteration
                user_message = f"""The file subsets you created have validation errors. Please fix them.

VALIDATION ERRORS:
{error_message}

Please:
1. Review the errors above
2. Delete the problematic file subset files in partitions/{data_source}/ directory
3. Create corrected file subsets using: python3 scripts/create_file_subset.py "{data_source}" "<title>" "<description>" <paths>
4. Ensure complete and disjoint coverage of all files in {data_source_path}

Remember:
- Each file must appear in exactly ONE file subset (no duplicates)
- ALL files must be covered (no missing files)
- Use "path/to/directory/" (with trailing slash) to include all files in a directory
- Paths are relative to {data_source_path} (do NOT include "{data_source}/" prefix in paths)

Once you've fixed the issues, run `python3 scripts/validate_partition.py {data_source}` to verify.
"""
            else:
                print(f"\n❌ Maximum attempts ({max_attempts}) reached for '{data_source}'.")
                print("Please review the errors and create file subsets manually.")
                return False
    
    return False


def step_1_create_file_partitions() -> bool:
    """
    Execute step 1: Create file subsets using Claude Code Agent SDK
    
    This function:
    1. Resets the partitions/ folder (removes existing file subsets)
    2. Resets the checklist (marks all items as incomplete)
    3. Creates new file subsets using Claude Agent SDK (once per data source)
    4. Validates the file subsets
    
    Returns:
        True if file subsets were created and validated successfully for all data sources
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
    # STEP 1.1: Create File Partitions (once per data source)
    # ========================================================================
    
    # Get data source path and list of data sources
    base_data_path = get_data_source_path()
    data_sources = get_data_sources()
    
    # Load checklist to get special commands for step 1.1
    checklist = load_checklist("01_create_file_partitions")
    step_1_1 = checklist["items"][0]  # First item is 1.1
    special_commands = step_1_1.get("special_commands", [])
    
    print("=" * 60)
    print("STEP 1.1: Creating File Subsets")
    print("=" * 60)
    print(f"Base data path: {base_data_path}")
    print(f"Data sources to process: {', '.join(data_sources)}")
    print(f"Special commands: {', '.join(special_commands)}")
    print()
    
    # Process each data source sequentially
    all_success = True
    for idx, data_source in enumerate(data_sources, 1):
        print(f"\n{'#'*60}")
        print(f"# Processing data source {idx}/{len(data_sources)}: {data_source}")
        print(f"{'#'*60}\n")
        
        data_source_path = f"{base_data_path}/{data_source}"
        
        success = run_partition_agent_for_data_source(
            data_source=data_source,
            data_source_path=data_source_path,
            special_commands=special_commands,
            max_attempts=3
        )
        
        if not success:
            print(f"\n❌ Failed to create file subsets for '{data_source}'")
            all_success = False
            # Continue to next data source instead of stopping
            continue
        
        print(f"\n✅ Successfully created file subsets for '{data_source}'")
    
    if all_success:
        # Mark checklist item 1.1 as complete
        print()
        mark_checklist_item_complete("01_create_file_partitions", "1.1")
        print()
        
        print(f"\n{'='*60}")
        print("PROCEEDING TO STEP 2.1: Create Ontologies")
        print(f"{'='*60}\n")
        return True
    else:
        print(f"\n{'='*60}")
        print("❌ Some data sources failed file subset creation")
        print(f"{'='*60}\n")
        return False

