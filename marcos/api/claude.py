"""
Claude API integration for Marcos.

Handles all communication with the Claude API, maintaining
conversation history and applying the Marcos system prompt.
Now with tool execution capability.
"""

from typing import Optional
import anthropic

from ..config import CLAUDE_API_KEY, CLAUDE_MODEL


# Tool definitions for Marcos
TOOLS = [
    {
        "name": "bash",
        "description": "Execute a bash command and return the output. Use for file operations, git commands, system tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file at the given path. Creates the file if it doesn't exist, overwrites if it does.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "git",
        "description": "Execute a git command. Use for commits, pushes, pulls, status checks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": "Git arguments (e.g., 'status', 'add .', 'commit -m \"message\"', 'push')"
                }
            },
            "required": ["args"]
        }
    }
]


class ClaudeClient:
    """
    Client for Claude API interactions with tool execution.

    Handles:
    - System prompt from MARCOS_SOUL.md
    - Conversation history per session
    - Tool execution loop
    - Structured analysis requests
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or CLAUDE_API_KEY
        self.model = model or CLAUDE_MODEL

        if not self.api_key:
            raise ValueError(
                "No API key provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key to ClaudeClient."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def chat(self, system_prompt: str, user_message: str,
             history: Optional[list[dict]] = None,
             max_tokens: int = 4096) -> str:
        """
        Send a chat message to Claude with tool execution capability.

        Args:
            system_prompt: The Marcos soul / system prompt
            user_message: The user's message
            history: Previous conversation history
            max_tokens: Maximum response tokens

        Returns:
            Claude's final response text after all tool executions complete
        """
        from ..engine.tools import execute_tool

        # Build initial messages
        current_messages = []
        if history:
            current_messages.extend(history)
        current_messages.append({"role": "user", "content": user_message})

        collected_text = []

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=current_messages,
                tools=TOOLS
            )

            # Separate tool use and text blocks
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]

            # If no tool use, we're done - return the text
            if not tool_use_blocks:
                final_text = "".join(b.text for b in text_blocks)
                collected_text.append(final_text)
                return "\n".join(collected_text)

            # Print any text before tool execution (Claude's narration)
            for block in text_blocks:
                if block.text.strip():
                    print(block.text)
                    collected_text.append(block.text)

            # Execute tools and collect results
            tool_results = []
            for tool_block in tool_use_blocks:
                print(f"\n[Executing: {tool_block.name}]")
                result = execute_tool(tool_block.name, tool_block.input)

                # Truncate long results for display
                display_result = result[:500] + '...' if len(result) > 500 else result
                print(f"[Result: {display_result}]")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result
                })

            # Add assistant response and tool results to conversation
            current_messages.append({"role": "assistant", "content": response.content})
            current_messages.append({"role": "user", "content": tool_results})

            # Check stop reason - if end_turn, we might be done even with tools
            if response.stop_reason == "end_turn" and not tool_use_blocks:
                break

    def analyze(self, system_prompt: str, user_message: str,
                history: Optional[list[dict]] = None,
                max_tokens: int = 4096) -> str:
        """
        Request a system analysis from Claude.

        This is essentially the same as chat but exists as a separate
        method for semantic clarity and potential future customization.
        """
        return self.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            history=history,
            max_tokens=max_tokens,
        )

    def stream_chat(self, system_prompt: str, user_message: str,
                    history: Optional[list[dict]] = None,
                    max_tokens: int = 4096):
        """
        Stream a chat response from Claude.

        Yields text chunks as they arrive.
        Note: Streaming does not support tool use - use chat() for tools.
        """
        messages = []

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def test_connection(self) -> bool:
        """Test that the API connection works."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                system="You are a helpful assistant.",
                messages=[{"role": "user", "content": "Say 'connected' and nothing else."}],
            )
            return "connected" in response.content[0].text.lower()
        except Exception:
            return False
