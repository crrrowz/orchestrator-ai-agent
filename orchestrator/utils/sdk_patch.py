"""Resilient OpenHands SDK patch for robust JSON tool argument parsing.

Protects against small/free LLMs (e.g. GLM, DeepSeek, Qwen) emitting unescaped newlines,
trailing quotes, or control characters that would otherwise fail with 'unparseable JSON'.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def resilient_parse_tool_call_arguments(raw_arguments: str) -> dict[str, Any]:
    """Parse tool call arguments with multiple fallback recovery layers."""
    if not raw_arguments:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments

    # Layer 1: Standard json.loads with strict=False (allows unescaped control chars/tabs)
    try:
        parsed = json.loads(raw_arguments, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Layer 2: OpenHands built-in control char sanitization
    try:
        from openhands.sdk.agent.utils import sanitize_json_control_chars

        sanitized = sanitize_json_control_chars(raw_arguments)
        parsed = json.loads(sanitized, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Layer 3: Replace unescaped raw newlines inside string literals
    try:
        # Match literal newlines that are not escaped and replace with \n
        cleaned = (
            raw_arguments.replace("\r\n", "\\n")
            .replace("\n", "\\n")
            .replace("\r", "\\n")
        )
        parsed = json.loads(cleaned, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Layer 4: Fallback regex extraction for known tool parameters
    extracted: dict[str, Any] = {}
    try:
        # Match operation
        m_op = re.search(r'"(?:operation|op)":\s*"([^"]+)"', raw_arguments)
        if m_op:
            extracted["operation"] = m_op.group(1)

        # Match path/target_file/file
        m_path = re.search(r'"(?:path|file|target_file)":\s*"([^"]+)"', raw_arguments)
        if m_path:
            extracted["path"] = m_path.group(1)

        # Match command/cmd
        m_cmd = re.search(r'"(?:command|cmd)":\s*"([^"]+)"', raw_arguments)
        if m_cmd:
            extracted["command"] = m_cmd.group(1)

        # Match content / text / message (greedy up to next JSON key or closing brace)
        m_content = re.search(
            r'"(?:content|message|text|thought)":\s*"(.*?)(?:"\s*,\s*"[a-zA-Z_]+":|"\s*\}\s*$)',
            raw_arguments,
            re.DOTALL,
        )
        if m_content:
            raw_val = m_content.group(1)
            # Unescape any escaped characters
            raw_val = (
                raw_val.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
            )
            extracted["content"] = raw_val

        # Match line_number / start_line / end_line
        for num_field in ["line_number", "start_line", "end_line", "timeout_seconds"]:
            m_num = re.search(rf'"{num_field}":\s*(\d+)', raw_arguments)
            if m_num:
                extracted[num_field] = int(m_num.group(1))

        if extracted:
            return extracted
    except Exception as e:
        logger.debug(f"Regex extraction failed: {e}")

    logger.warning("All JSON parsing layers failed for tool arguments.")
    return {}


def apply_sdk_patches() -> None:
    """Patch openhands.sdk.agent to use resilient tool argument parsing."""
    try:
        import openhands.sdk.agent.utils as agent_utils
        import openhands.sdk.agent.agent as agent_module

        agent_utils.parse_tool_call_arguments = resilient_parse_tool_call_arguments
        if hasattr(agent_module, "parse_tool_call_arguments"):
            agent_module.parse_tool_call_arguments = resilient_parse_tool_call_arguments
    except Exception as e:
        logger.debug(f"Could not patch openhands SDK: {e}")
