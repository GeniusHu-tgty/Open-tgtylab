from __future__ import annotations

import traceback
from typing import Any


class ToolError(RuntimeError):
    """Expected tool error returned to MCP clients as a structured error field."""

    error_type: str = "tool_error"
    hint: str = ""

    def __init__(self, message: str, *, hint: str = ""):
        super().__init__(message)
        if hint:
            self.hint = hint


class ToolNotFoundError(ToolError):
    """External tool binary not found."""

    error_type = "tool_not_found"

    def __init__(self, name: str, path: str = ""):
        msg = f"{name} not found"
        if path:
            msg += f": {path}"
        super().__init__(
            msg,
            hint="Run: .\\scripts\\misc\\install_tools.ps1 -All",
        )


class PathViolationError(ToolError):
    """File path is outside allowed sandbox roots."""

    error_type = "path_violation"

    def __init__(self, path: str, allowed: str = ""):
        msg = f"Path outside allowed roots: {path}"
        hint = f"Copy the file to samples/ first"
        super().__init__(msg, hint=hint)


class TimeoutToolError(ToolError):
    """Subprocess timed out."""

    error_type = "timeout"

    def __init__(self, command: str, timeout: int, partial_output: str = ""):
        # Truncate command to avoid polluting Claude context
        cmd_short = command[:200] + "..." if len(command) > 200 else command
        msg = f"Command timed out after {timeout}s: {cmd_short}"
        hint = f"Increase timeout_seconds or reduce analysis scope"
        super().__init__(msg, hint=hint)
        self.partial_output = partial_output[:500] if partial_output else ""


class SecurityViolationError(ToolError):
    """Security red line hit (credential/token detected)."""

    error_type = "security_violation"

    def __init__(self, what: str = "credential"):
        super().__init__(
            f"Security stop: {what} detected. Not recorded.",
            hint="Review the finding manually. Do NOT save to files.",
        )


def classify_error(exc: Exception) -> dict[str, Any]:
    """Convert any exception into a structured error dict for MCP clients."""
    if isinstance(exc, ToolError):
        result: dict[str, Any] = {
            "error": str(exc),
            "error_type": exc.error_type,
        }
        if exc.hint:
            result["hint"] = exc.hint
        if isinstance(exc, TimeoutToolError) and exc.partial_output:
            result["partial_output"] = exc.partial_output
        return result

    # Map well-known Python exceptions to error types
    if isinstance(exc, FileNotFoundError):
        return {
            "error": str(exc),
            "error_type": "file_not_found",
            "hint": "Check the path and ensure the file exists",
        }
    if isinstance(exc, PermissionError):
        return {
            "error": str(exc),
            "error_type": "permission_error",
            "hint": "File may be locked by another process",
        }
    if isinstance(exc, subprocess.TimeoutExpired):  # type: ignore[attr-defined]
        cmd = str(getattr(exc, "cmd", ""))[:200]
        timeout = getattr(exc, "timeout", 0)
        return {
            "error": f"Timed out after {timeout}s: {cmd}...",
            "error_type": "timeout",
            "hint": "Increase timeout_seconds or reduce analysis scope",
        }
    if isinstance(exc, ValueError):
        return {"error": str(exc), "error_type": "invalid_input"}
    if isinstance(exc, MemoryError):
        return {
            "error": "Out of memory",
            "error_type": "resource_error",
            "hint": "Reduce input size or increase available memory",
        }

    # Unknown exception — include traceback for debugging
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tb_short = "".join(tb[-3:])  # last 3 frames only
    return {
        "error": str(exc)[:500],  # truncate long messages
        "error_type": "internal_error",
        "traceback": tb_short[:1000],
    }


# Need this for isinstance check in classify_error
import subprocess  # noqa: E402
