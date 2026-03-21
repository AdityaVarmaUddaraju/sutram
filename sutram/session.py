"""Conversation session management."""

import logging

logger = logging.getLogger(__name__)

class Session:
    def __init__(self, system_prompt: str | None = None):
        self.messages: list[dict] = []
        if system_prompt:
            self.add_system_message(system_prompt)
            logger.debug("Session created with system prompt")

    def add_message(self, role: str, content: str, **kwargs) -> None:
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        logger.debug(f"Added {role} message ({len(content)} chars)")

    def add_system_message(self, content: str) -> None:
        self.add_message("system", content)

    def add_user_message(self, content: str) -> None:
        self.add_message("user", content)

    def add_assistant_message(self, content: str | None = None, tool_calls: list[dict] | None = None) -> None:
        msg = {"role": "assistant"}
        if content: msg["content"] = content
        if tool_calls: msg["tool_calls"] = tool_calls
        self.messages.append(msg)
        logger.debug(f"Added assistant message")

    def add_tool_message(self, tool_call_id: str, content: str, name: str | None = None) -> None:
        msg = {"role": "tool", "tool_call_id": tool_call_id, "content": content}
        if name: msg["name"] = name
        self.messages.append(msg)
        logger.debug(f"Added tool message: {name or tool_call_id}")

    def get_messages(self) -> list[dict]:
        return self.messages.copy()

    def __repr__(self) -> str:
        return f"Session({len(self.messages)} messages)"
