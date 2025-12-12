"""
Logging utilities for the extraction workflow.

Provides functions for:
- Logging key-value pairs to JSON
- Logging prompts to text files
- Tracking message statistics and token usage
- Finalizing attempt logs with validation results
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


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

