"""
Agent Runtime —工具集 (Tools)

内置工具，供 Agent Executor 调用：
- code_analyzer: 代码分析
- text_formatter: 文本整理
- web_searcher: 搜索
- calculator: 计算
- file_reader: 文件读取
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """A tool that an Agent can invoke"""
    name: str
    description: str
    parameters: dict  # JSON Schema for parameters
    func: Callable

    def to_openai_spec(self) -> dict:
        """Convert to OpenAI function-calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# ============================================================
# Built-in Tools
# ============================================================

def tool_code_analyzer(code: str, language: str = "auto") -> str:
    """
    Analyze code quality and suggest improvements.

    Args:
        code: Source code to analyze
        language: Programming language (auto-detect if "auto")
    """
    # Heuristic analysis (v0.1: basic metrics)
    lines = code.strip().split("\n")
    total_lines = len(lines)
    comment_lines = sum(1 for l in lines if l.strip().startswith(("#", "//", "--")))
    blank_lines = sum(1 for l in lines if not l.strip())
    code_lines = total_lines - comment_lines - blank_lines

    # Complexity heuristic
    complexity = "LOW"
    if total_lines > 100:
        complexity = "MEDIUM"
    if total_lines > 500:
        complexity = "HIGH"

    result_parts = [
        f"Code Analysis Report",
        f"- Total lines: {total_lines}",
        f"- Code lines: {code_lines}",
        f"- Comment lines: {comment_lines}",
        f"- Blank lines: {blank_lines}",
        f"- Estimated complexity: {complexity}",
        f"- Comment ratio: {comment_lines / max(total_lines, 1) * 100:.1f}%",
    ]

    if comment_lines / max(code_lines, 1) < 0.1:
        result_parts.append("- WARNING: Low comment ratio. Consider adding documentation.")

    if total_lines > 200:
        result_parts.append("- SUGGESTION: Consider splitting into smaller modules.")

    return "\n".join(result_parts)


def tool_text_formatter(text: str, format_type: str = "markdown") -> str:
    """
    Format text according to specified format.

    Args:
        text: Raw text to format
        format_type: Target format (markdown, plain, json)
    """
    if format_type == "markdown":
        # Basic markdown clean-up
        text = text.strip()
        text = "\n\n".join(p.strip() for p in text.split("\n\n") if p.strip())
        return text
    elif format_type == "plain":
        # Strip markdown
        import re
        text = re.sub(r"[*_~`#]", "", text)
        return text.strip()
    elif format_type == "json":
        import json
        return json.dumps({"content": text.strip()}, ensure_ascii=False)
    return text


def tool_calculator(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate
    """
    import math
    import re

    # Safety: only allow numbers, operators, and math function names
    allowed = re.compile(r'^[\d\s+\-*/().%^,A-Za-z_]+$')
    if not allowed.match(expression):
        return f"Error: expression contains disallowed characters."

    # Whitelist-safe eval with math namespace
    safe_ns = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow,
        "pi": math.pi, "e": math.e,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "floor": math.floor, "ceil": math.ceil,
    }

    try:
        result = eval(expression, {"__builtins__": {}}, safe_ns)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"


def tool_searcher(query: str) -> str:
    """
    Search placeholder — returns guidance for external search.

    Args:
        query: Search query
    """
    return (
        f"Search query: \"{query}\"\n"
        f"[v0.1] External search is not yet integrated. "
        f"Suggested action: use web search tools to research this topic, "
        f"then synthesize findings into a knowledge entry."
    )


# ============================================================
# Tool Registry
# ============================================================

def build_tool_registry() -> dict[str, Tool]:
    """Build the default tool registry"""
    tools = [
        Tool(
            name="code_analyzer",
            description="Analyze source code quality and suggest improvements",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to analyze"},
                    "language": {"type": "string", "default": "auto", "description": "Programming language"},
                },
                "required": ["code"],
            },
            func=tool_code_analyzer,
        ),
        Tool(
            name="text_formatter",
            description="Format text into markdown, plain text, or JSON",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to format"},
                    "format_type": {"type": "string", "enum": ["markdown", "plain", "json"], "default": "markdown"},
                },
                "required": ["text"],
            },
            func=tool_text_formatter,
        ),
        Tool(
            name="calculator",
            description="Safely evaluate mathematical expressions",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression, e.g. '2 + 3 * 4'"},
                },
                "required": ["expression"],
            },
            func=tool_calculator,
        ),
        Tool(
            name="searcher",
            description="Search for information (placeholder for web search integration)",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
            func=tool_searcher,
        ),
    ]
    return {t.name: t for t in tools}
