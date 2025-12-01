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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def log_to_file(key: str, value):
    """
    Log a key-value pair to logging/logging.json
    
    Args:
        key: The log entry key
        value: The log entry value (can be string or dict/list)
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
    
    # Update the log entry
    logs[key] = value
    
    # Write back to file
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


def log_usage(step_name: str, attempt_num: int, iteration_num: int, response, stop_reason: str):
    """
    Log token usage for a specific iteration within an attempt.
    
    Args:
        step_name: Name of the workflow step (e.g., "step_1.1_file_partitions")
        attempt_num: Current attempt number (1-indexed)
        iteration_num: Current iteration number (1-indexed)
        response: The API response object
        stop_reason: The stop reason for this iteration
    """
    log_dir = Path("logging")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "logging.json"
    
    # Load existing logs
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)
    else:
        logs = {}
    
    # Initialize step structure if needed
    if step_name not in logs:
        logs[step_name] = {
            "attempts": []
        }
    
    # Initialize attempt structure if needed
    attempts = logs[step_name]["attempts"]
    if len(attempts) < attempt_num:
        attempts.append({
            "attempt_number": attempt_num,
            "started_at": None,
            "completed_at": None,
            "validation_result": None,
            "validation_errors": None,
            "iterations": []
        })
    
    current_attempt = attempts[attempt_num - 1]
    
    # Extract usage data from response
    usage_data = {
        "iteration": iteration_num,
        "stop_reason": stop_reason
    }
    
    if hasattr(response, 'usage'):
        usage = response.usage
        usage_data["usage"] = {
            "input_tokens": getattr(usage, 'input_tokens', 0),
            "output_tokens": getattr(usage, 'output_tokens', 0),
        }
        
        # Optional fields (may not always be present)
        if hasattr(usage, 'cache_creation_input_tokens'):
            usage_data["usage"]["cache_creation_input_tokens"] = usage.cache_creation_input_tokens
        if hasattr(usage, 'cache_read_input_tokens'):
            usage_data["usage"]["cache_read_input_tokens"] = usage.cache_read_input_tokens
    
    # Add iteration data
    current_attempt["iterations"].append(usage_data)
    
    # Write back to file
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


def finalize_attempt_log(step_name: str, attempt_num: int, validation_result: str, validation_errors: Optional[str] = None):
    """
    Finalize an attempt by adding validation results and calculating totals.
    
    Args:
        step_name: Name of the workflow step
        attempt_num: Current attempt number (1-indexed)
        validation_result: "success" or "failed"
        validation_errors: Error message if validation failed
    """
    from datetime import datetime
    
    log_dir = Path("logging")
    log_file = log_dir / "logging.json"
    
    if not log_file.exists():
        return
    
    with open(log_file, 'r') as f:
        logs = json.load(f)
    
    if step_name not in logs or len(logs[step_name]["attempts"]) < attempt_num:
        return
    
    current_attempt = logs[step_name]["attempts"][attempt_num - 1]
    
    # Set completion timestamp and validation results
    current_attempt["completed_at"] = datetime.utcnow().isoformat() + "Z"
    current_attempt["validation_result"] = validation_result
    if validation_errors:
        current_attempt["validation_errors"] = validation_errors
    
    # Calculate totals for this attempt
    total_input = 0
    total_output = 0
    total_cache_creation = 0
    total_cache_read = 0
    
    for iteration in current_attempt["iterations"]:
        if "usage" in iteration:
            usage = iteration["usage"]
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
            total_cache_creation += usage.get("cache_creation_input_tokens", 0)
            total_cache_read += usage.get("cache_read_input_tokens", 0)
    
    current_attempt["total_usage"] = {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cache_creation_input_tokens": total_cache_creation,
        "cache_read_input_tokens": total_cache_read,
        "total_iterations": len(current_attempt["iterations"])
    }
    
    # Calculate cumulative usage across all attempts for this step
    cumulative_input = 0
    cumulative_output = 0
    cumulative_cache_creation = 0
    cumulative_cache_read = 0
    cumulative_iterations = 0
    successful_attempt = None
    
    for idx, attempt in enumerate(logs[step_name]["attempts"]):
        if "total_usage" in attempt:
            cumulative_input += attempt["total_usage"]["input_tokens"]
            cumulative_output += attempt["total_usage"]["output_tokens"]
            cumulative_cache_creation += attempt["total_usage"]["cache_creation_input_tokens"]
            cumulative_cache_read += attempt["total_usage"]["cache_read_input_tokens"]
            cumulative_iterations += attempt["total_usage"]["total_iterations"]
        
        if attempt.get("validation_result") == "success":
            successful_attempt = idx + 1
    
    logs[step_name]["cumulative_usage"] = {
        "total_attempts": len(logs[step_name]["attempts"]),
        "successful_attempt": successful_attempt,
        "total_iterations": cumulative_iterations,
        "total_input_tokens": cumulative_input,
        "total_output_tokens": cumulative_output,
        "total_cache_creation_tokens": cumulative_cache_creation,
        "total_cache_read_tokens": cumulative_cache_read
    }
    
    # Write back to file
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


def print_usage_summary(step_name: str):
    """
    Print a summary of token usage for a step from the log file.
    
    Args:
        step_name: Name of the workflow step
    """
    log_file = Path("logging") / "logging.json"
    
    if not log_file.exists():
        return
    
    with open(log_file, 'r') as f:
        logs = json.load(f)
    
    if step_name not in logs or "cumulative_usage" not in logs[step_name]:
        return
    
    cumulative = logs[step_name]["cumulative_usage"]
    
    print(f"Attempts: {cumulative.get('total_attempts', 0)}")
    if cumulative.get('successful_attempt'):
        print(f"Successful attempt: #{cumulative.get('successful_attempt')}")
    print(f"Total iterations: {cumulative.get('total_iterations', 0)}")
    print(f"Total input tokens: {cumulative.get('total_input_tokens', 0):,}")
    print(f"Total output tokens: {cumulative.get('total_output_tokens', 0):,}")
    
    if cumulative.get('total_cache_read_tokens', 0) > 0:
        print(f"Cache read tokens: {cumulative.get('total_cache_read_tokens', 0):,}")
    if cumulative.get('total_cache_creation_tokens', 0) > 0:
        print(f"Cache creation tokens: {cumulative.get('total_cache_creation_tokens', 0):,}")
    print()


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

## Available Tools

You have access to a **bash tool** that allows you to execute shell commands. Use it to:
- Explore the file system (`ls`, `tree`, `find`, etc.)
- Run scripts like `make create-partition`
- Execute validation commands like `make validate-partitions`

## Example Partition Structure

See `{example_partition_path}/` for a working example:
- **Data**: 7 files in `{example_partition_path}/data/data_source_repo_name/` (2 folders, 3 top-level files)
- **Partitions**: 2 partition files demonstrating complete, disjoint coverage
  - `partition_01.json`: Uses directory path `folderA/` (all files) + specific files from `folderB/` + 2 top-level files
  - `partition_02.json`: Remaining file from `folderB/` + 1 top-level file
- **Key Rule**: Every file appears exactly once across all partitions

## How to Create Partitions

Call `make create-partition` with the required arguments:

```bash
make create-partition TITLE='<title>' DESC='<description>' PATHS='<path1> [path2] ...'
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
make create-partition \\
  TITLE='Core Documentation' \\
  DESC='Primary documentation files ...' \\
  PATHS='data/data_source_repo_name/folderA/ data/data_source_repo_name/folderB/fileBA.md data/data_source_repo_name/fileA.md'
```

## Success Criteria

A successful partition structure must:
1. ✅ Cover ALL files in {data_source_path}
2. ✅ Have NO duplicate coverage (each file in exactly one partition)
3. ✅ Have NO missing files
4. ✅ Use logical groupings that make sense for knowledge graph extraction

After you create your partitions, the system will automatically validate them. If there are issues, you'll receive detailed feedback about which files are duplicated or missing.

Good luck! Start by exploring the contents of {data_source_path}, then create appropriate partitions using make create-partition. 
Once you've created your partitions, run `make validate-partitions` to validate them.
If there are issues, you'll receive detailed feedback about which files are duplicated or missing.

**When complete**: After you've created all necessary partitions and validated them, your task is done. At that point, send a response WITHOUT using any tools (response.stop_reason == "end_turn") to signal completion.
"""
    return prompt


def step_1_create_file_partitions() -> bool:
    """
    Execute step 1: Create file partitions using Claude Code Agent SDK
    
    Returns:
        True if partitions were created and validated successfully
    """
    from anthropic import AnthropicVertex
    from datetime import datetime
    
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
    log_to_file("step_1.1_file_partitions_prompt", user_message)
    
    step_name = "step_1.1_file_partitions"
    
    print("=" * 60)
    print("STEP 1.1: Creating File Partitions")
    print("=" * 60)
    print(f"Data source: {data_source_path}")
    print(f"Available tools: {', '.join(available_tools)}")
    print()
    
    # Initialize Anthropic Vertex client
    project_id = os.environ.get("VERTEX_PROJECT_ID")
    region = os.environ.get("VERTEX_REGION")
    
    if not project_id or not region:
        print("❌ Error: VERTEX_PROJECT_ID and VERTEX_REGION must be set in .env file")
        return False
    
    client = AnthropicVertex(project_id=project_id, region=region)
    print(f"📡 Connected to Vertex AI (Project: {project_id}, Region: {region})")
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"Attempt {attempt}/{max_attempts}")
        print(f"{'='*60}\n")
        
        # Run Claude agent with bash tool for executing commands
        print("🤖 Invoking Claude via Vertex AI...")
        
        try:
            # Define the bash tool for Claude to execute commands
            tools = [
                {
                    "type": "bash_20241022",
                    "name": "bash",
                    "cache_control": {"type": "ephemeral"}  # Cache tool definition
                }
            ]
            
            # Start conversation with Claude
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message,
                            # Mark the initial prompt for caching
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                }
            ]
            
            # Agent loop - Claude executes commands until complete
            max_iterations = 50
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                print(f"\n--- Iteration {iteration} ---")
                
                # Call Claude API
                ## Enable 1M token context window (beta feature)
                ## extra_headers={"anthropic-beta": "context-1m-2025-08-07"}
                response = client.messages.create(
                    model="claude-sonnet-4-5@20250929",
                    max_tokens=8096,
                    thinking={
                        "type": "enabled",
                        "budget_tokens": 25000  # Extended thinking for strategic planning and problem-solving
                    },
                    tools=tools,
                    messages=messages
                )

                
                
                print(f"Stop reason: {response.stop_reason}")
                
                # Log token usage for this iteration
                log_usage(step_name, attempt, iteration, response, response.stop_reason)
                
                # Monitor token usage (especially thinking tokens)
                if hasattr(response, 'usage'):
                    usage = response.usage
                    print(f"📊 Token Usage:")
                    print(f"   Input: {usage.input_tokens}")
                    print(f"   Output: {usage.output_tokens}")
                    
                    # Check for thinking token usage (extended thinking feature)
                    if hasattr(usage, 'cache_creation_input_tokens'):
                        print(f"   Cache creation: {usage.cache_creation_input_tokens}")
                    if hasattr(usage, 'cache_read_input_tokens'):
                        print(f"   Cache read: {usage.cache_read_input_tokens}")
                    
                    # WARNING: Check if we're hitting thinking token limits
                    # Note: The API doesn't expose thinking tokens directly in usage yet,
                    # but we can infer issues if output is unexpectedly truncated
                    if usage.output_tokens >= 8000:  # Close to max_tokens limit
                        print("   ⚠️  WARNING: Close to output token limit!")
                
                # Add assistant's response to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Check if Claude is done
                if response.stop_reason == "end_turn":
                    print("✅ Claude completed the task")
                    break
                
                # Execute any tool uses Claude requested
                if response.stop_reason == "tool_use":
                    tool_results = []
                    
                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input
                            
                            print(f"\n🔧 Tool: {tool_name}")
                            print(f"Command: {tool_input.get('command', 'N/A')}")
                            
                            if tool_name == "bash":
                                # Execute bash command
                                import subprocess
                                command = tool_input.get("command", "")
                                
                                try:
                                    result = subprocess.run(
                                        command,
                                        shell=True,
                                        capture_output=True,
                                        text=True,
                                        timeout=60
                                    )
                                    
                                    output = result.stdout if result.stdout else result.stderr
                                    print(f"Output: {output[:200]}..." if len(output) > 200 else f"Output: {output}")
                                    
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": content_block.id,
                                        "content": output or "Command completed with no output"
                                    })
                                except subprocess.TimeoutExpired:
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": content_block.id,
                                        "content": "Error: Command timed out after 60 seconds"
                                    })
                                except Exception as e:
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": content_block.id,
                                        "content": f"Error: {str(e)}"
                                    })
                    
                    # Add tool results to messages
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                else:
                    # Unexpected stop reason
                    print(f"⚠️  Unexpected stop reason: {response.stop_reason}")
                    break
            
            if iteration >= max_iterations:
                print(f"⚠️  Reached maximum iterations ({max_iterations})")
                print("Claude may not have completed the task")
            
            print(f"\n✅ Claude agent execution finished")
            
        except Exception as e:
            print(f"❌ Error executing Claude agent: {e}")
            return False
        
        # Validate the partitions
        print(f"\n{'='*60}")
        print("Validating Partitions...")
        print(f"{'='*60}\n")
        
        is_valid, error_message = validate_and_get_errors()
        
        if is_valid:
            # Log successful attempt
            finalize_attempt_log(step_name, attempt, "success")
            
            # Show token usage summary
            print(f"\n{'='*60}")
            print("📊 Token Usage Summary")
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
            
            # Show token usage summary for this attempt
            print(f"\n{'='*60}")
            print("📊 Token Usage Summary")
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
