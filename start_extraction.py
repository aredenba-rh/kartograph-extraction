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
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted, start fresh
            print("⚠️  Warning: logging.json was corrupted, starting fresh log file")
            logs = {}
    else:
        logs = {}
    
    # Update the log entry
    logs[key] = value
    
    # Write back to file with ensure_ascii=False to preserve readability
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def log_prompt_to_file(prompt_name: str, prompt_content: str):
    """
    Log a prompt to a separate text file for better readability.
    
    Args:
        prompt_name: Name of the prompt (used as filename)
        prompt_content: The actual prompt text content
    """
    log_dir = Path("logging")
    log_dir.mkdir(exist_ok=True)
    
    # Create filename from prompt name
    prompt_file = log_dir / f"{prompt_name}.txt"
    
    # Write prompt as plain text with actual newlines
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt_content)
    
    print(f"  ✓ Logged prompt to {prompt_file}")


def log_message(step_name: str, attempt_num: int, message_num: int, message, message_type: str, processed_message_ids: set):
    """
    Log messages from Claude Agent SDK interactions.
    
    Tracks token usage from assistant messages (deduplicating by message ID) and
    logs the final ResultMessage with complete content.
    
    Args:
        step_name: Name of the workflow step (e.g., "step_1.1_file_partitions")
        attempt_num: Current attempt number (1-indexed)
        message_num: Current message number (1-indexed)
        message: The SDK message object
        message_type: Type of message (AssistantMessage, ToolUseBlock, ToolResultBlock, TextBlock, ResultMessage, etc.)
        processed_message_ids: Set of message IDs already processed for token tracking
    """
    from datetime import datetime, timezone
    
    log_dir = Path("logging")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "logging.json"
    
    # Load existing logs
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted, start fresh
            logs = {}
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
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "validation_result": None,
            "validation_errors": None,
            "result_message": None,
            "message_count": 0,
            "token_usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            }
        })
    
    current_attempt = attempts[attempt_num - 1]
    
    # Update message count
    current_attempt["message_count"] = message_num
    
    # Track token usage from AssistantMessage (avoiding double-counting)
    # Per SDK docs: usage is a dictionary, access with .get()
    if message_type == "AssistantMessage" and hasattr(message, 'usage') and hasattr(message, 'id'):
        message_id = message.id
        
        # Only process this message ID once to avoid double-counting parallel tool uses
        if message_id not in processed_message_ids:
            processed_message_ids.add(message_id)
            
            usage = message.usage
            # Debug: Print what we're seeing in the usage object
            print(f"[DEBUG] Captured usage from AssistantMessage {message_id}: {usage}")
            
            # Usage is a dictionary - use .get() for access
            if isinstance(usage, dict):
                current_attempt["token_usage"]["input_tokens"] += usage.get("input_tokens", 0)
                current_attempt["token_usage"]["output_tokens"] += usage.get("output_tokens", 0)
                current_attempt["token_usage"]["cache_creation_input_tokens"] += usage.get("cache_creation_input_tokens", 0)
                current_attempt["token_usage"]["cache_read_input_tokens"] += usage.get("cache_read_input_tokens", 0)
            else:
                # Fallback to getattr if it's an object
                current_attempt["token_usage"]["input_tokens"] += getattr(usage, 'input_tokens', 0)
                current_attempt["token_usage"]["output_tokens"] += getattr(usage, 'output_tokens', 0)
                current_attempt["token_usage"]["cache_creation_input_tokens"] += getattr(usage, 'cache_creation_input_tokens', 0)
                current_attempt["token_usage"]["cache_read_input_tokens"] += getattr(usage, 'cache_read_input_tokens', 0)
    
    # Store the final ResultMessage (full content) and extract cumulative usage
    if message_type == "ResultMessage":
        result_data = {
            "message_type": "ResultMessage",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Extract result information
        if hasattr(message, 'subtype'):
            result_data["subtype"] = message.subtype
        
        # Store the FULL result content (not truncated)
        if hasattr(message, 'result'):
            result_data["content"] = str(message.result)
        
        # Per SDK docs: ResultMessage has total_cost_usd directly on it
        if hasattr(message, 'total_cost_usd'):
            result_data["total_cost_usd"] = message.total_cost_usd
            print(f"[DEBUG] Captured total_cost_usd from ResultMessage: ${message.total_cost_usd}")
        
        # Extract cumulative usage from ResultMessage (this is the authoritative source)
        if hasattr(message, 'usage'):
            usage = message.usage
            print(f"[DEBUG] Captured cumulative usage from ResultMessage: {usage}")
            
            # ResultMessage contains total cumulative usage - replace attempt totals
            # Usage is a dictionary - use .get() for access
            if isinstance(usage, dict):
                current_attempt["token_usage"]["input_tokens"] = usage.get("input_tokens", 0)
                current_attempt["token_usage"]["output_tokens"] = usage.get("output_tokens", 0)
                current_attempt["token_usage"]["cache_creation_input_tokens"] = usage.get("cache_creation_input_tokens", 0)
                current_attempt["token_usage"]["cache_read_input_tokens"] = usage.get("cache_read_input_tokens", 0)
            else:
                # Fallback to getattr if it's an object
                current_attempt["token_usage"]["input_tokens"] = getattr(usage, 'input_tokens', 0)
                current_attempt["token_usage"]["output_tokens"] = getattr(usage, 'output_tokens', 0)
                current_attempt["token_usage"]["cache_creation_input_tokens"] = getattr(usage, 'cache_creation_input_tokens', 0)
                current_attempt["token_usage"]["cache_read_input_tokens"] = getattr(usage, 'cache_read_input_tokens', 0)
        
        current_attempt["result_message"] = result_data
    
    # Write back to file with ensure_ascii=False for readability
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def finalize_attempt_log(step_name: str, attempt_num: int, validation_result: str, validation_errors: Optional[str] = None):
    """
    Finalize an attempt by adding validation results and calculating totals.
    
    Args:
        step_name: Name of the workflow step
        attempt_num: Current attempt number (1-indexed)
        validation_result: "success" or "failed"
        validation_errors: Error message if validation failed
    """
    from datetime import datetime, timezone
    
    log_dir = Path("logging")
    log_file = log_dir / "logging.json"
    
    if not log_file.exists():
        return
    
    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
    except json.JSONDecodeError:
        # If the file is corrupted, we can't finalize
        return
    
    if step_name not in logs or len(logs[step_name]["attempts"]) < attempt_num:
        return
    
    current_attempt = logs[step_name]["attempts"][attempt_num - 1]
    
    # Set completion timestamp and validation results using timezone-aware datetime
    current_attempt["completed_at"] = datetime.now(timezone.utc).isoformat()
    current_attempt["validation_result"] = validation_result
    if validation_errors:
        current_attempt["validation_errors"] = validation_errors
    
    # Get token usage from attempt
    token_usage = current_attempt.get("token_usage", {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0
    })
    
    # Calculate cumulative statistics across all attempts for this step
    cumulative_messages = 0
    cumulative_input_tokens = 0
    cumulative_output_tokens = 0
    cumulative_cache_creation_tokens = 0
    cumulative_cache_read_tokens = 0
    cumulative_cost = 0.0
    successful_attempt = None
    
    for idx, attempt in enumerate(logs[step_name]["attempts"]):
        cumulative_messages += attempt.get("message_count", 0)
        
        # Accumulate token usage from attempt
        if "token_usage" in attempt:
            token_data = attempt["token_usage"]
            cumulative_input_tokens += token_data.get("input_tokens", 0)
            cumulative_output_tokens += token_data.get("output_tokens", 0)
            cumulative_cache_creation_tokens += token_data.get("cache_creation_input_tokens", 0)
            cumulative_cache_read_tokens += token_data.get("cache_read_input_tokens", 0)
        
        # Sum the SDK-reported cost from each attempt's ResultMessage (authoritative)
        if "result_message" in attempt and attempt["result_message"]:
            cumulative_cost += attempt["result_message"].get("total_cost_usd", 0) or 0
        
        if attempt.get("validation_result") == "success":
            successful_attempt = idx + 1
    
    cumulative_token_usage = {
        "input_tokens": cumulative_input_tokens,
        "output_tokens": cumulative_output_tokens,
        "cache_creation_input_tokens": cumulative_cache_creation_tokens,
        "cache_read_input_tokens": cumulative_cache_read_tokens
    }
    logs[step_name]["cumulative_summary"] = {
        "total_attempts": len(logs[step_name]["attempts"]),
        "successful_attempt": successful_attempt,
        "total_messages": cumulative_messages,
        "cumulative_token_usage": cumulative_token_usage,
        "total_cost_usd": round(cumulative_cost, 6)
    }
    
    # Write back to file with ensure_ascii=False for readability
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


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


def reset_partitions_folder():
    """Remove all partition JSON files from partitions/ folder"""
    partitions_dir = Path("partitions")
    
    if not partitions_dir.exists():
        partitions_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created partitions/ directory")
        return
    
    # Remove all partition JSON files
    partition_files = list(partitions_dir.glob("partition_*.json"))
    
    if partition_files:
        for partition_file in partition_files:
            partition_file.unlink()
        print(f"  ✓ Removed {len(partition_files)} existing partition file(s)")
    else:
        print(f"  ✓ Partitions folder already empty")


def reset_logging():
    """Reset the logging.json file to start fresh"""
    log_dir = Path("logging")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "logging.json"
    
    # Overwrite with empty JSON object
    with open(log_file, 'w') as f:
        json.dump({}, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Reset logging file")


def print_usage_summary(step_name: str):
    """
    Print a summary of message statistics and costs for a step from the log file.
    
    Args:
        step_name: Name of the workflow step
    """
    log_file = Path("logging") / "logging.json"
    
    if not log_file.exists():
        return
    
    with open(log_file, 'r') as f:
        logs = json.load(f)
    
    if step_name not in logs or "cumulative_summary" not in logs[step_name]:
        return
    
    cumulative = logs[step_name]["cumulative_summary"]
    
    print(f"Attempts: {cumulative.get('total_attempts', 0)}")
    if cumulative.get('successful_attempt'):
        print(f"Successful attempt: #{cumulative.get('successful_attempt')}")
    print(f"Total messages exchanged: {cumulative.get('total_messages', 0)}")
    
    # Display token usage and cost
    token_usage = cumulative.get('cumulative_token_usage', {})
    if token_usage:
        print(f"\nToken Usage:")
        print(f"  Input tokens: {token_usage.get('input_tokens', 0):,}")
        print(f"  Output tokens: {token_usage.get('output_tokens', 0):,}")
        cache_creation = token_usage.get('cache_creation_input_tokens', 0)
        cache_read = token_usage.get('cache_read_input_tokens', 0)
        if cache_creation > 0:
            print(f"  Cache creation tokens: {cache_creation:,}")
        if cache_read > 0:
            print(f"  Cache read tokens: {cache_read:,}")
        
        total_cost = cumulative.get('total_cost_usd', 0)
        print(f"\nTotal Cost: ${total_cost:.6f} USD")
    
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


def build_partition_creation_prompt(data_source_path: str, special_commands: List[str], example_partition_path: str = "examples/partition_example") -> str:
    """
    Build the user message prompt for Claude to create partitions.
    
    Args:
        data_source_path: Path to the data source directory
        special_commands: List of make commands available to the agent
        example_partition_path: Path to example partition structure
        
    Returns:
        Formatted prompt string
    """
    # Format special commands for display
    commands_list = "\n".join([f"  - `{cmd}`" for cmd in special_commands])
    
    prompt = f"""I'm building a Knowledge Graph from {data_source_path}.

## Success Pattern (Follow These Steps)
1. **Explore**: Quick `ls`/`find` of {data_source_path} to understand structure and content relationships
2. **Decide**: Single partition (flat/homogeneous content) OR multiple (distinct domains)
3. **Plan**: Create scratch files in `/tmp/` to track which files go in each partition title
4. **Create**: Run `make create-partition` for each partition
5. **Validate**: Run `make validate-partitions`
6. **Complete**: Respond without tools when validation passes

**Target**: ≤20 bash commands. Single partition is valid for flat directories with related content.

## Your Task
Create partitions for all files in {data_source_path}. Each file must appear in exactly one partition. 


## Available Commands
You have access to a **bash tool** that allows you to execute shell commands. However, you should ONLY use these specific make commands:
{commands_list}
**Important:** Do NOT run scripts directly from the `scripts/` folder. Use only the make commands listed above.


## Example Partition Structure
**You will treat the {data_source_path} similar to how {example_partition_path}/data/data_source_repo_name/ is treated.

See `{example_partition_path}/data/data_source_repo_name/` for a working example (You will treat ):
- **Data**: 7 files in `{example_partition_path}/data/data_source_repo_name/` (2 folders, 3 top-level files)
- **Partitions**: 2 partition files (`partition_01.json`, and `partition_02.json`) created using the `make create-partition` command.
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

**Path notation (CRITICAL - paths are relative to {data_source_path}):**
- Directory: `"subfolder/"` = ALL files in {data_source_path}/subfolder/
- Directory: `"subfolder/nested/"` = ALL files in nested directory
- Specific file: `"subfolder/file.md"` = single file
- Top-level files: `"file.md"`

**DO NOT include `{data_source_path}` in PATHS - it's automatically prepended**

**Shell escaping**: Filenames containing special characters like `(` or `)` must be escaped with a backslash when using the 'make create-partition' command. (e.g. `file-(name).md` -> `file-\(name\).md`)

**Example** (see `{example_partition_path}/partition_01.json` for actual structure):
```bash
make create-partition \\
  TITLE='Installation and Provisioning' \\
  DESC='Documentation focused on cluster installation ...' \\
  PATHS='folderA/ folderB/fileBA.md fileA.md'
```


Complete the steps of **Success Pattern** above.
"""
    return prompt


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
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ToolUseBlock, ToolResultBlock, TextBlock
    from datetime import datetime
    import asyncio
    
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
    sys.path.insert(0, str(Path(__file__).parent / "scripts"))
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
    
    async def run_partition_creation_attempt(attempt_num: int, prompt: str) -> tuple[bool, Optional[str]]:
        """
        Run a single attempt at partition creation with Claude Agent SDK.
        
        Returns:
            Tuple of (success, error_message)
        """
        # Configure Claude Agent SDK options
        options = ClaudeAgentOptions(
            allowed_tools=["Bash"],  # Allow Claude to run bash commands
            permission_mode="acceptEdits",  # Auto-accept tool executions
            cwd=str(Path.cwd())  # Set working directory to project root
        )
        
        message_count = 0
        processed_message_ids = set()  # Track message IDs to avoid double-counting token usage
        
        try:
            async with ClaudeSDKClient(options=options) as client:
                print(f"🤖 Starting Claude Agent SDK session...")
                
                # Send initial query
                await client.query(prompt)
                
                print(f"📡 Claude is working on creating partitions...")
                print(f"    (Claude will run bash commands as needed)")
                print()
                
                # Receive all messages until completion
                async for message in client.receive_messages():
                    message_count += 1
                    
                    # Determine message type for logging
                    message_type = type(message).__name__
                    
                    # Log the message
                    log_message(step_name, attempt_num, message_count, message, message_type, processed_message_ids)
                    
                    # Handle different message types
                    if isinstance(message, AssistantMessage):
                        # Process assistant message blocks
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Claude is explaining what it's doing
                                text_preview = block.text[:150].replace('\n', ' ')
                                print(f"💭 Claude: {text_preview}...")
                            elif isinstance(block, ToolUseBlock):
                                # Claude is using a tool
                                if block.name == "Bash":
                                    command = block.input.get('command', 'N/A')
                                    # Truncate long commands for display
                                    cmd_preview = command if len(command) <= 80 else command[:77] + "..."
                                    print(f"🔧 Running: {cmd_preview}")
                            elif isinstance(block, ToolResultBlock):
                                # Tool execution result
                                if hasattr(block, 'content') and block.content:
                                    result_text = str(block.content)[:100].replace('\n', ' ')
                                    print(f"   ✓ Result: {result_text}...")
                    
                    # Check for completion
                    if hasattr(message, 'subtype'):
                        if message.subtype == 'success':
                            print(f"\n✅ Claude completed the task successfully!")
                            print(f"   Total messages exchanged: {message_count}")
                            return True, None
                        elif message.subtype == 'error':
                            error_msg = str(getattr(message, 'result', 'Unknown error'))
                            print(f"\n❌ Claude encountered an error: {error_msg}")
                            return False, error_msg
                
                # If we exit the loop without a result message, task is complete
                print(f"\n✅ Claude agent session completed")
                print(f"   Total messages exchanged: {message_count}")
                return True, None
                
        except Exception as e:
            print(f"❌ Error during Claude Agent SDK execution: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    # Main retry loop
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"Attempt {attempt}/{max_attempts}")
        print(f"{'='*60}\n")
        
        # Set started timestamp
        from datetime import datetime
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
        success, error = asyncio.run(run_partition_creation_attempt(attempt, user_message))
        
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


def step_2_create_ontologies_for_each_partition() -> bool:
    """
    Execute step 2: Create ontologies for each partition
    
    This is a placeholder for the ontology creation workflow.
    """
    # ========================================================================
    # RESET: Reset checklist for step 2
    # ========================================================================
    print("\n" + "=" * 60)
    print("PREPARING STEP 2: ONTOLOGY CREATION")
    print("=" * 60)
    print()
    
    # Reset the checklist for this step
    reset_checklist("02_create_ontologies_for_each_partition")
    
    print()
    
    # ========================================================================
    # STEP 2.1: Create Ontologies
    # ========================================================================
    
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
    
    # Flag display names and their corresponding step numbers
    flag_info = {
        "use_current_partition": ("use_current_partition", "01"),
        "use_current_ontologies": ("use_current_ontologies", "02")
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
    
    # Reset the master checklist
    reset_checklist("master_checklist")
    
    print()
    
    # ========================================================================
    # Load Configuration and Show Status
    # ========================================================================
    
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
        else:
            # Mark step_01 as complete in master checklist
            print()
            mark_master_checklist_step_complete("step_01")
            print()
    
    # Execute Step 2: Create ontologies for each partition
    if step_2:
        print("→ Executing: Step 2 - Create ontologies for each partition")
        success = step_2_create_ontologies_for_each_partition()
        if not success:
            print("\n❌ Failed to create ontologies.")
            return 1
        else:
            # Mark step_02 as complete in master checklist
            print()
            mark_master_checklist_step_complete("step_02")
            print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
