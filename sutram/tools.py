"""Tool utilities for converting Python functions to LLM tool schemas."""

import inspect
import logging
from typing import get_type_hints

from .config import ToolConfig

logger = logging.getLogger(__name__)

PYTHON_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
}


def _get_json_type(py_type: type) -> str:
    json_type = PYTHON_TYPE_MAP.get(py_type)
    if json_type is None:
        raise TypeError(f"Unsupported type: {py_type}. Supported: {list(PYTHON_TYPE_MAP.keys())}")
    return json_type


def tool(func):
    """Decorator that attaches an OpenAI-compatible tool schema to a function.

    Usage:
        @tool
        def get_weather(location: str, units: str = "celsius"):
            '''Get the current weather for a location'''
            ...

        get_weather.schema  # -> {"type": "function", "function": {...}}
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    description = inspect.getdoc(func) or ""

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "self":
            continue
        py_type = hints.get(name)
        if py_type is None:
            raise TypeError(f"Parameter '{name}' in '{func.__name__}' must have a type annotation")

        prop = {"type": _get_json_type(py_type)}

        if param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            required.append(name)

        properties[name] = prop

    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }

    func.schema = schema
    logger.debug(f"Registered tool: {func.__name__}")
    return func


def make_tool_config(*funcs, tool_choice: str | dict | None = None) -> ToolConfig:
    """Create a ToolConfig from @tool-decorated functions.

    Usage:
        tc = make_tool_config(get_weather, search_books)
        result = provider.call_llm("...", tool_config=tc)
    """
    tools = []
    for f in funcs:
        if not hasattr(f, "schema"):
            raise ValueError(f"Function '{f.__name__}' is not decorated with @tool")
        tools.append(f.schema)
    return ToolConfig(tools=tools, tool_choice=tool_choice)
