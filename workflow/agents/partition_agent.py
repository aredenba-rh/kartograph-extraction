"""
Partition creation agent.

Provides the async function to run a Claude agent session for partition creation.
"""

from pathlib import Path
from typing import Optional

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ToolUseBlock, TextBlock

from ..helpers.logging import log_message, finalize_attempt_log


async def run_partition_creation_attempt(
    prompt: str,
    step_name: str,
    attempt_num: int
) -> tuple[bool, Optional[str]]:
    """
    Run a single attempt at partition creation with Claude Agent SDK.
    
    Args:
        prompt: The prompt to send to Claude
        step_name: Name of the workflow step for logging
        attempt_num: Current attempt number (1-indexed)
    
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

