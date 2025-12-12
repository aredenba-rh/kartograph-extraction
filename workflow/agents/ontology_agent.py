"""
Ontology creation agent.

Provides the async function to run a Claude agent session for ontology creation.
"""

from pathlib import Path
from typing import Dict, Optional

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ToolUseBlock

from ..helpers.logging import log_message, log_prompt_to_file, finalize_attempt_log
from ..prompts.ontology_prompts import build_ontology_creation_prompt


async def run_ontology_agent(
    partition: Dict,
    data_source_path: str,
    attempt_num: int = 1
) -> tuple[int, bool, Optional[str]]:
    """
    Run a Claude agent to create ontologies for a single partition.
    
    Args:
        partition: The partition data dictionary
        data_source_path: Path to the data source directory
        attempt_num: Attempt number for logging
        
    Returns:
        Tuple of (partition_id, success, error_message)
    """
    partition_id = partition.get("partition_id")
    item_id = f"2.{partition_id}"
    step_name = f"step_2.{partition_id}_ontology_creation"
    
    # Build the prompt for this partition
    prompt = build_ontology_creation_prompt(partition, data_source_path, item_id)
    
    # Log the prompt
    log_prompt_to_file(f"step_2_{partition_id}_ontology_prompt", prompt)
    
    # Configure Claude Agent SDK options with partition-specific environment
    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Read", "Write"],
        permission_mode="acceptEdits",
        cwd=str(Path.cwd()),
        env={
            "PARTITION_ITEM_ID": item_id
        }
    )
    
    message_count = 0
    processed_message_ids = set()
    
    print(f"🤖 Starting agent for Partition {partition_id}: {partition.get('title', 'Unknown')}")
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            # Send initial query
            await client.query(prompt)
            
            # Receive all messages until completion
            async for message in client.receive_messages():
                message_count += 1
                
                # Determine message type for logging
                message_type = type(message).__name__
                
                # Log the message
                log_message(step_name, attempt_num, message_count, message, message_type, processed_message_ids)
                
                # Handle different message types (minimal output to avoid spam)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            if block.name == "Bash":
                                command = block.input.get('command', 'N/A')
                                cmd_preview = command if len(command) <= 60 else command[:57] + "..."
                                print(f"  [P{partition_id}] 🔧 {cmd_preview}")
                
                # Check for completion
                if hasattr(message, 'subtype'):
                    if message.subtype == 'success':
                        print(f"  [P{partition_id}] ✅ Completed ({message_count} messages)")
                        finalize_attempt_log(step_name, attempt_num, "success")
                        return partition_id, True, None
                    elif message.subtype == 'error':
                        error_msg = str(getattr(message, 'result', 'Unknown error'))
                        print(f"  [P{partition_id}] ❌ Error: {error_msg[:50]}...")
                        finalize_attempt_log(step_name, attempt_num, "failed", error_msg)
                        return partition_id, False, error_msg
            
            # If we exit the loop without a result message, task is complete
            print(f"  [P{partition_id}] ✅ Session completed ({message_count} messages)")
            finalize_attempt_log(step_name, attempt_num, "success")
            return partition_id, True, None
            
    except Exception as e:
        error_msg = str(e)
        print(f"  [P{partition_id}] ❌ Exception: {error_msg[:50]}...")
        finalize_attempt_log(step_name, attempt_num, "failed", error_msg)
        return partition_id, False, error_msg

