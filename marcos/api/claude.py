"""
Claude API integration for Marcos.

Handles all communication with the Claude API, maintaining
conversation history and applying the Marcos system prompt.
"""

from typing import Optional
import anthropic

from ..config import CLAUDE_API_KEY, CLAUDE_MODEL


class ClaudeClient:
    """
    Client for Claude API interactions.

    Handles:
    - System prompt from MARCOS_SOUL.md
    - Conversation history per session
    - Structured analysis requests
    - General chat
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
        Send a chat message to Claude.

        Args:
            system_prompt: The Marcos soul / system prompt
            user_message: The user's message
            history: Previous conversation history
            max_tokens: Maximum response tokens

        Returns:
            Claude's response text
        """
        messages = []

        # Add conversation history
        if history:
            messages.extend(history)

        # Add current message
        messages.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )

        return response.content[0].text

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
