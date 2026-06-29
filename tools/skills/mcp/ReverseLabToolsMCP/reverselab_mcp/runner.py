from __future__ import annotations

import atexit
import os
import subprocess
from pathlib import Path
from typing import Any

from .config import REVERSE_ROOT
from .errors import TimeoutToolError


# ── Process tracking for launch() ──
_launched_processes: dict[int, subprocess.Popen[Any]] = {}


def _cleanup_launched() -> None:
    """Terminate all tracked launched processes on MCP server exit."""
    for pid, proc in list(_launched_processes.items()):
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass
    _launched_processes.clear()


atexit.register(_cleanup_launched)


def run(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        proc = subprocess.run(
            args,
            cwd=str(REVERSE_ROOT),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        # Wrap in our structured error with truncation
        partial = ""
        if exc.stdout:
            partial = exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", errors="replace")
        cmd_str = " ".join(str(a) for a in args)
        raise TimeoutToolError(cmd_str, timeout, partial) from exc


def launch(args: list[str], visible: bool = True, cwd: Path | None = None) -> int:
    startupinfo = None
    creationflags = 0
    if os.name == "nt" and not visible:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        args,
        cwd=str(cwd or REVERSE_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    # Track the process for cleanup
    _launched_processes[proc.pid] = proc
    return proc.pid


def get_launched_status() -> list[dict[str, Any]]:
    """Return status of all tracked launched processes."""
    result = []
    for pid, proc in list(_launched_processes.items()):
        status = "running" if proc.poll() is None else f"exited (code={proc.returncode})"
        result.append({"pid": pid, "status": status})
    return result


def terminate_launched(pid: int) -> bool:
    """Terminate a specific launched process by PID."""
    proc = _launched_processes.get(pid)
    if not proc:
        return False
    try:
        if proc.poll() is None:
            proc.terminate()
            return True
    except Exception:
        pass
    return False
