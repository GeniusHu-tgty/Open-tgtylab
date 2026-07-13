import json
from pathlib import Path

from scripts.misc.verify_hunter_tools_integration import verify_integration


VERSION_FIELDS = {
    "contract_version": "1.0",
    "workspace_schema_version": "1.0",
    "adaptive_engine_version": "1.0",
    "workflow_kernel_version": "2.0",
    "stealth_http_version": "1.0",
    "attack_session_version": "1.0",
    "reverse_pipeline_version": "1.0",
    "memory_system_version": "1.0",
    "unified_orchestrator_version": "1.0",
}


def _write_fixture(
    tmp_path: Path,
    *,
    configured_entrypoint: str | None = None,
    configured_workspace: str = "${workspaceFolder}",
    registered_tools: tuple[str, ...] = ("hunter_required",),
    required_tools: tuple[str, ...] = ("hunter_required",),
    server_name: str = "hunter_tools",
    minimum_tool_count: int = 1,
) -> tuple[Path, Path]:
    root = tmp_path / "Open-tgtylab"
    hunter = tmp_path / "hunter"
    root.mkdir()
    hunter.mkdir()
    (root / ".codex").mkdir()
    entrypoint = hunter / "mcp_server.py"
    configured_entrypoint = configured_entrypoint or str(entrypoint)

    registry_items = ", ".join(
        f"{name!r}: object()" for name in registered_tools
    )
    entrypoint.write_text(
        "\n".join(
            [
                "import os",
                "from pathlib import Path",
                "class ToolManager:",
                f"    _tools = {{{registry_items}}}",
                "class MCP:",
                "    name = 'hunter_tools'",
                "    _tool_manager = ToolManager()",
                "mcp = MCP()",
                "def hunter_required():",
                "    return None",
                "class Workspace:",
                "    root = Path(os.environ['OPEN_TGTYLAB_ROOT']).resolve()",
                "    def health(self):",
                "        return {'status': 'ok', 'data': {'root': str(self.root), 'checks': {'root': True, 'kb': True}}}",
                "_workspace = Workspace()",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    contract = {
        **VERSION_FIELDS,
        "server_name": server_name,
        "minimum_tool_count": minimum_tool_count,
        "required_tools": list(required_tools),
    }
    (hunter / "integration-contract.json").write_text(
        json.dumps(contract),
        encoding="utf-8",
    )
    (root / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "hunter_tools": {
                        "command": "python",
                        "args": [configured_entrypoint],
                        "env": {
                            "OPEN_TGTYLAB_ROOT": configured_workspace,
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (root / ".codex" / "config.toml").write_text(
        "\n".join(
            [
                "[mcp_servers.hunter_tools]",
                'command = "python"',
                f"args = [{json.dumps(configured_entrypoint)}]",
                "",
                "[mcp_servers.hunter_tools.env]",
                f"OPEN_TGTYLAB_ROOT = {json.dumps(configured_workspace)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root, entrypoint


def test_verifier_rejects_contract_required_tool_missing_from_registry(
    tmp_path,
):
    root, entrypoint = _write_fixture(
        tmp_path,
        registered_tools=("hunter_other",),
        required_tools=("hunter_required",),
    )

    result = verify_integration(root, entrypoint)

    assert result["status"] == "error"
    assert result["missing_tools"] == ["hunter_required"]


def test_verifier_uses_fastmcp_registry_not_module_callables(tmp_path):
    root, entrypoint = _write_fixture(
        tmp_path,
        registered_tools=(),
        required_tools=("hunter_required",),
    )

    result = verify_integration(root, entrypoint)

    assert result["status"] == "error"
    assert result["registered_tool_count"] == 0
    assert "hunter_required" in result["missing_tools"]


def test_verifier_rejects_configured_entrypoint_mismatch(tmp_path):
    root, entrypoint = _write_fixture(
        tmp_path,
        configured_entrypoint="${HOME}/wrong/mcp_server.py",
    )

    result = verify_integration(root, entrypoint)

    assert result["status"] == "error"
    assert any(
        "entrypoint mismatch" in error for error in result["errors"]
    )


def test_verifier_rejects_configured_workspace_mismatch(tmp_path):
    root, entrypoint = _write_fixture(
        tmp_path,
        configured_workspace=str(tmp_path / "wrong-workspace"),
    )

    result = verify_integration(root, entrypoint)

    assert result["status"] == "error"
    assert any(
        "workspace mismatch" in error for error in result["errors"]
    )


def test_verifier_overrides_stale_workspace_environment(
    tmp_path,
    monkeypatch,
):
    root, entrypoint = _write_fixture(tmp_path)
    monkeypatch.setenv("OPEN_TGTYLAB_ROOT", str(tmp_path / "stale"))

    result = verify_integration(root, entrypoint)

    assert result["status"] == "ok"
    assert Path(result["workspace_health_root"]) == root.resolve()


def test_ci_runs_full_hunter_integration_verification():
    workflow = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "hunter-tools-integration.yml"
    ).read_text(encoding="utf-8")
    invocations = [
        line.strip()
        for line in workflow.splitlines()
        if "verify_hunter_tools_integration.py" in line
    ]

    assert any("--config-only" not in line for line in invocations)


def test_ci_prepares_hunter_checkout_and_runtime_dependencies():
    workflow = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "hunter-tools-integration.yml"
    ).read_text(encoding="utf-8")

    assert "GeniusHu-tgty/Hunter.git" in workflow
    assert ".agents/skills/hunter" in workflow
    assert '"mcp[cli]"' in workflow
    assert "PyYAML" in workflow
    assert "cryptography" in workflow


def test_committed_project_configs_resolve_to_this_checkout():
    root = Path(__file__).parents[1].resolve()
    entrypoint = (
        Path.home()
        / ".agents"
        / "skills"
        / "hunter"
        / "mcp_server.py"
    )

    result = verify_integration(root, entrypoint, config_only=True)

    assert result["status"] == "ok", result["errors"]


def test_readme_uses_current_hunter_tool_count():
    readme = (
        Path(__file__).parents[1] / "README.md"
    ).read_text(encoding="utf-8")

    assert "current integration exposes 111 Hunter tools" in readme
    assert "current integration exposes 94 Hunter tools" not in readme
