"""Unified response models for LLM providers."""

import json
import html as html_lib
from typing import Any

from pydantic import BaseModel


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function_name: str
    function_arguments: str  # JSON string, like the raw API returns


class LLMResponse(BaseModel):
    content: str | None = None
    reasoning: str | None = None
    tool_calls: list[ToolCall] = []
    finish_reason: str | None = None
    usage: Usage = Usage()
    raw: dict = {}
    parsed: Any = None

    model_config = {"arbitrary_types_allowed": True}

    def _repr_html_(self) -> str:
        parts = ['<div style="font-family: monospace; font-size: 13px; line-height: 1.6;">']

        # Content
        content_display = html_lib.escape(self.content) if self.content else "<em>None</em>"
        parts.append(f'<div><strong>Content:</strong> {content_display}</div>')

        # Reasoning (collapsible)
        if self.reasoning:
            reasoning_display = html_lib.escape(self.reasoning)
            parts.append(
                f'<details><summary><strong>Reasoning</strong></summary>'
                f'<pre style="background: #fffbe6; padding: 8px; border-radius: 4px; '
                f'white-space: pre-wrap; max-height: 300px; overflow: auto;">{reasoning_display}</pre></details>'
            )

        # Finish reason
        parts.append(f'<div><strong>Finish Reason:</strong> {html_lib.escape(self.finish_reason or "None")}</div>')

        # Usage
        u = self.usage
        parts.append(
            f'<div><strong>Usage:</strong> '
            f'{u.prompt_tokens} prompt + {u.completion_tokens} completion = {u.total_tokens} total</div>'
        )

        # Tool calls (collapsible)
        if self.tool_calls:
            tc_html = "<br>".join(
                f'&nbsp;&nbsp;{html_lib.escape(tc.function_name)}({html_lib.escape(tc.function_arguments)})'
                for tc in self.tool_calls
            )
            parts.append(
                f'<details><summary><strong>Tool Calls ({len(self.tool_calls)})</strong></summary>'
                f'{tc_html}</details>'
            )

        # Parsed (collapsible)
        if self.parsed is not None:
            parsed_display = html_lib.escape(repr(self.parsed))
            parts.append(
                f'<details><summary><strong>Parsed</strong></summary>'
                f'<pre style="background: #e6f7ff; padding: 8px; border-radius: 4px; '
                f'white-space: pre-wrap; max-height: 300px; overflow: auto;">{parsed_display}</pre></details>'
            )

        # Raw (collapsible)
        if self.raw:
            raw_json = html_lib.escape(json.dumps(self.raw, indent=2))
            parts.append(
                f'<details><summary><strong>Raw Response</strong></summary>'
                f'<pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; '
                f'max-height: 300px; overflow: auto;">{raw_json}</pre></details>'
            )

        parts.append('</div>')
        return "\n".join(parts)
