#!/usr/bin/env python3
"""Validate the complete Hunter MCP contract and OpenTgtyLab bridge."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tomllib
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HUNTER = Path.home() / ".agents" / "skills" / "hunter" / "mcp_server.py"
REQUIRED_VERSION_FIELDS = {
    "contract_version",
    "workspace_schema_version",
    "adaptive_engine_version",
    "workflow_kernel_version",
    "stealth_http_version",
    "attack_session_version",
    "reverse_pipeline_version",
    "memory_system_version",
    "unified_orchestrator_version",
}


def load_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8-sig"))


def _expand_path(value: str, workspace: Path) -> Path:
    expanded = str(value)
    replacements = {
        "${HOME}": str(Path.home()),
        "${workspaceFolder}": str(workspace),
    }
    for marker, replacement in replacements.items():
        expanded = expanded.replace(marker, replacement)
    expanded = os.path.expandvars(expanded)
    path = Path(expanded).expanduser()
    if not path.is_absolute():
        path = workspace / path
    return path.resolve()


def _configured_servers(
    workspace: Path,
) -> list[tuple[str, Mapping[str, Any]]]:
    mcp_path = workspace / ".mcp.json"
    codex_path = workspace / ".codex" / "config.toml"
    sources: list[tuple[str, Mapping[str, Any]]] = []
    if mcp_path.is_file():
        data = json.loads(mcp_path.read_text(encoding="utf-8-sig"))
        sources.append((".mcp.json", data.get("mcpServers", {})))
    else:
        sources.append((".mcp.json", {}))
    if codex_path.is_file():
        sources.append(
            (
                ".codex/config.toml",
                load_toml(codex_path).get("mcp_servers", {}),
            )
        )
    else:
        sources.append((".codex/config.toml", {}))
    return sources


def check_registration(
    workspace: Path,
    entrypoint: Path,
) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    inspected: list[dict[str, Any]] = []
    for source, servers in _configured_servers(workspace):
        if "hunter" in servers:
            errors.append(
                f"{source}: legacy hunter registration is forbidden"
            )
        registration = servers.get("hunter_tools")
        if not isinstance(registration, Mapping):
            errors.append(f"{source}: hunter_tools registration is missing")
            inspected.append({"source": source, "present": False})
            continue

        args = registration.get("args", [])
        configured_entrypoint = args[-1] if isinstance(args, list) and args else ""
        resolved_entrypoint = (
            _expand_path(configured_entrypoint, workspace)
            if configured_entrypoint
            else None
        )
        if resolved_entrypoint != entrypoint:
            errors.append(
                f"{source}: hunter_tools entrypoint mismatch: "
                f"{resolved_entrypoint or '<missing>'} != {entrypoint}"
            )

        env = registration.get("env", {})
        configured_workspace = (
            env.get("OPEN_TGTYLAB_ROOT")
            if isinstance(env, Mapping)
            else None
        )
        resolved_workspace = (
            _expand_path(configured_workspace, workspace)
            if configured_workspace
            else None
        )
        if resolved_workspace != workspace:
            errors.append(
                f"{source}: hunter_tools workspace mismatch: "
                f"{resolved_workspace or '<missing>'} != {workspace}"
            )
        inspected.append(
            {
                "source": source,
                "present": True,
                "entrypoint": (
                    str(resolved_entrypoint)
                    if resolved_entrypoint
                    else None
                ),
                "workspace": (
                    str(resolved_workspace)
                    if resolved_workspace
                    else None
                ),
            }
        )
    return errors, inspected


def _load_contract(entrypoint: Path) -> dict[str, Any]:
    contract_path = entrypoint.parent / "integration-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
    required = {
        "server_name",
        "minimum_tool_count",
        "required_tools",
        *REQUIRED_VERSION_FIELDS,
    }
    missing_fields = sorted(required - set(contract))
    if missing_fields:
        raise ValueError(
            f"Contract missing fields: {', '.join(missing_fields)}"
        )
    if contract["server_name"] != "hunter_tools":
        raise ValueError("Contract server_name must be hunter_tools")
    minimum = contract["minimum_tool_count"]
    if not isinstance(minimum, int) or minimum < 1:
        raise ValueError(
            "Contract minimum_tool_count must be a positive integer"
        )
    required_tools = contract["required_tools"]
    if (
        not isinstance(required_tools, list)
        or not all(isinstance(item, str) and item for item in required_tools)
    ):
        raise ValueError("Contract required_tools must be a string list")
    invalid_versions = sorted(
        field
        for field in REQUIRED_VERSION_FIELDS
        if not isinstance(contract.get(field), str) or not contract[field]
    )
    if invalid_versions:
        raise ValueError(
            f"Contract version fields must be non-empty strings: "
            f"{', '.join(invalid_versions)}"
        )
    return contract


def _load_hunter_module(entrypoint: Path, workspace: Path):
    module_name = f"hunter_tools_integration_check_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, entrypoint)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Hunter entrypoint: {entrypoint}")
    module = importlib.util.module_from_spec(spec)
    old_workspace = os.environ.get("OPEN_TGTYLAB_ROOT")
    os.environ["OPEN_TGTYLAB_ROOT"] = str(workspace)
    sys.path.insert(0, str(entrypoint.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(str(entrypoint.parent))
        except ValueError:
            pass
        if old_workspace is None:
            os.environ.pop("OPEN_TGTYLAB_ROOT", None)
        else:
            os.environ["OPEN_TGTYLAB_ROOT"] = old_workspace
    return module


def _registered_tools(module: Any) -> list[str]:
    mcp = getattr(module, "mcp", None)
    manager = getattr(mcp, "_tool_manager", None)
    tools = getattr(manager, "_tools", None)
    if not isinstance(tools, Mapping):
        raise ValueError(
            "Hunter FastMCP registry mcp._tool_manager._tools is unavailable"
        )
    return sorted(str(name) for name in tools)


def verify_integration(
    workspace: str | Path = ROOT,
    entrypoint: str | Path = DEFAULT_HUNTER,
    *,
    config_only: bool = False,
) -> dict[str, Any]:
    workspace_path = Path(workspace).expanduser().resolve()
    entrypoint_path = Path(entrypoint).expanduser().resolve()
    errors, registrations = check_registration(
        workspace_path,
        entrypoint_path,
    )
    result: dict[str, Any] = {
        "status": "ok",
        "workspace": str(workspace_path),
        "hunter_entrypoint": str(entrypoint_path),
        "server_name": None,
        "registered_tool_count": 0,
        "minimum_tool_count": None,
        "missing_tools": [],
        "workspace_health_root": None,
        "registrations": registrations,
        "errors": errors,
    }
    if config_only:
        result["status"] = "error" if errors else "ok"
        return result

    if not entrypoint_path.is_file():
        errors.append(f"Hunter entrypoint missing: {entrypoint_path}")
        result["status"] = "error"
        return result

    try:
        contract = _load_contract(entrypoint_path)
        module = _load_hunter_module(entrypoint_path, workspace_path)
        registered = _registered_tools(module)
        mcp_name = getattr(getattr(module, "mcp", None), "name", None)
        if mcp_name != contract["server_name"]:
            errors.append(
                f"FastMCP server name mismatch: "
                f"{mcp_name!r} != {contract['server_name']!r}"
            )
        missing_tools = sorted(
            set(contract["required_tools"]) - set(registered)
        )
        if missing_tools:
            errors.append(
                f"FastMCP registry missing required tools: {missing_tools}"
            )
        if len(registered) < contract["minimum_tool_count"]:
            errors.append(
                "FastMCP registered tool count below contract minimum: "
                f"{len(registered)} < {contract['minimum_tool_count']}"
            )

        workspace_adapter = getattr(module, "_workspace", None)
        if workspace_adapter is None or not callable(
            getattr(workspace_adapter, "health", None)
        ):
            errors.append("Hunter workspace adapter is unavailable")
        else:
            health = workspace_adapter.health()
            health_data = (
                health.get("data", {})
                if isinstance(health, Mapping)
                else {}
            )
            health_root_raw = health_data.get("root")
            health_root = (
                Path(health_root_raw).expanduser().resolve()
                if health_root_raw
                else None
            )
            checks = health_data.get("checks", {})
            if (
                health_root != workspace_path
                or not isinstance(checks, Mapping)
                or not checks.get("root")
                or not checks.get("kb")
            ):
                errors.append(
                    f"Workspace adapter root/health mismatch: {health}"
                )
            result["workspace_health_root"] = (
                str(health_root) if health_root else None
            )

        result.update(
            {
                "server_name": mcp_name,
                "registered_tool_count": len(registered),
                "minimum_tool_count": contract["minimum_tool_count"],
                "missing_tools": missing_tools,
                "contract_versions": {
                    field: contract[field]
                    for field in sorted(REQUIRED_VERSION_FIELDS)
                },
            }
        )
    except Exception as exc:
        errors.append(f"Hunter integration load failed: {exc}")

    result["status"] = "error" if errors else "ok"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-only", action="store_true")
    args = parser.parse_args()
    entrypoint = Path(
        os.environ.get("HUNTER_TOOLS_ENTRYPOINT", DEFAULT_HUNTER)
    )
    result = verify_integration(
        ROOT,
        entrypoint,
        config_only=args.config_only,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
