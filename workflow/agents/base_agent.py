"""
Base agent utilities for Claude Agent SDK interactions.

Provides shared utilities and message handling patterns for agent sessions.
"""

from claude_agent_sdk import AssistantMessage, ToolUseBlock, ToolResultBlock, TextBlock


def handle_assistant_message(message: AssistantMessage, prefix: str = "") -> None:
    """
    Handle and display an AssistantMessage from the Claude Agent SDK.
    
    Args:
        message: The AssistantMessage to handle
        prefix: Optional prefix for output lines (e.g., "[P1] " for partition 1)
    """
    for block in message.content:
        if isinstance(block, TextBlock):
            # Claude is explaining what it's doing
            text_preview = block.text[:150].replace('\n', ' ')
            print(f"{prefix}💭 Claude: {text_preview}...")
        elif isinstance(block, ToolUseBlock):
            # Claude is using a tool
            if block.name == "Bash":
                command = block.input.get('command', 'N/A')
                # Truncate long commands for display
                cmd_preview = command if len(command) <= 80 else command[:77] + "..."
                print(f"{prefix}🔧 Running: {cmd_preview}")
            elif block.name == "Read":
                file_path = block.input.get('file_path', 'N/A')
                print(f"{prefix}📖 Reading: {file_path}")
            elif block.name == "Write":
                file_path = block.input.get('file_path', 'N/A')
                print(f"{prefix}✏️  Writing: {file_path}")
        elif isinstance(block, ToolResultBlock):
            # Tool execution result
            if hasattr(block, 'content') and block.content:
                result_text = str(block.content)[:100].replace('\n', ' ')
                print(f"{prefix}   ✓ Result: {result_text}...")


def handle_result_message(message, prefix: str = "") -> tuple[bool, str]:
    """
    Handle a ResultMessage and determine success/failure.
    
    Args:
        message: The ResultMessage from the SDK
        prefix: Optional prefix for output lines
        
    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    if hasattr(message, 'subtype'):
        if message.subtype == 'success':
            return True, None
        elif message.subtype == 'error':
            error_msg = str(getattr(message, 'result', 'Unknown error'))
            return False, error_msg
    
    # Default to success if no subtype
    return True, None

