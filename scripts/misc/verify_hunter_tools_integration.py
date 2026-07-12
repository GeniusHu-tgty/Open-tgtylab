#!/usr/bin/env python3
"""Validate the single hunter_tools registration and OpenTgtyLab workspace bridge."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HUNTER = Path.home() / ".agents" / "skills" / "hunter" / "mcp_server.py"


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8-sig"))


def check_registration() -> list[str]:
    errors: list[str] = []
    mcp_json = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8-sig"))
    json_servers = mcp_json.get("mcpServers", {})
    codex_servers = load_toml(ROOT / ".codex" / "config.toml").get("mcp_servers", {})
    for source, servers in ((".mcp.json", json_servers), (".codex/config.toml", codex_servers)):
        if "hunter" in servers:
            errors.append(f"{source}: legacy hunter registration is forbidden")
        if "hunter_tools" not in servers:
            errors.append(f"{source}: hunter_tools registration is missing")
    return errors


def main() -> int:
    errors = check_registration()
    entrypoint = Path(os.environ.get("HUNTER_TOOLS_ENTRYPOINT", DEFAULT_HUNTER)).expanduser().resolve()
    if not entrypoint.is_file():
        errors.append(f"Hunter entrypoint missing: {entrypoint}")
    else:
        os.environ.setdefault("OPEN_TGTYLAB_ROOT", str(ROOT))
        sys.path.insert(0, str(entrypoint.parent))
        spec = importlib.util.spec_from_file_location("hunter_tools_integration_check", entrypoint)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        health = module._workspace.health()
        if not health.get("data", {}).get("available"):
            errors.append(f"Workspace adapter unavailable: {health}")
        tools = {name for name, value in vars(module).items() if name.startswith("hunter_") and callable(value)}
        required = {"hunter_workspace_health", "hunter_case_open", "hunter_project_kb_search", "hunter_evidence_save", "hunter_report_publish"}
        missing = sorted(required - tools)
        if missing:
            errors.append(f"Missing workspace MCP tools: {missing}")
    result = {"status": "error" if errors else "ok", "workspace": str(ROOT), "hunter_entrypoint": str(entrypoint), "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
