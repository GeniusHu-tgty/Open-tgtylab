import json
import sys

import pytest

from scripts.misc import hunter_tools_manager
from scripts.misc.hunter_tools_manager import (
    HunterToolsManager,
    remove_toml_server_block,
    result_failed,
)


def test_remove_legacy_hunter_without_removing_hunter_tools():
    text = (
        '[mcp_servers.hunter_tools]\ncommand="python"\n\n'
        '[mcp_servers.hunter]\ncommand="python"\n\n'
        "[features]\nx=true\n"
    )
    out = remove_toml_server_block(text, "hunter")
    assert "[mcp_servers.hunter_tools]" in out
    assert "[mcp_servers.hunter]" not in out
    assert "[features]" in out


def test_configure_project_is_dynamic_and_idempotent(tmp_path):
    root = tmp_path / "Open-tgtylab"
    root.mkdir()
    (root / ".codex").mkdir()
    (root / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"hunter": {"command": "old"}}}),
        encoding="utf-8",
    )
    (root / ".codex" / "config.toml").write_text(
        '[mcp_servers.hunter]\ncommand="old"\n',
        encoding="utf-8",
    )
    hunter = tmp_path / "hunter"
    hunter.mkdir()
    (hunter / "mcp_server.py").write_text("", encoding="utf-8")
    manager = HunterToolsManager(root=root, hunter_dir=hunter, python="python")
    first = manager.configure_project()
    second = manager.configure_project()
    data = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
    assert "hunter" not in data["mcpServers"]
    assert "hunter_tools" in data["mcpServers"]
    assert (
        data["mcpServers"]["hunter_tools"]["env"]["OPEN_TGTYLAB_ROOT"]
        == str(root.resolve())
    )
    toml = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "[mcp_servers.hunter]" not in toml
    assert toml.count("[mcp_servers.hunter_tools]") == 1
    assert first["changed"] is True
    assert second["changed"] is False


def test_status_reports_contract_and_entrypoint(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    (root / "cases").mkdir()
    (root / "kb").mkdir()
    hunter = tmp_path / "hunter"
    hunter.mkdir()
    (hunter / "mcp_server.py").write_text("", encoding="utf-8")
    (hunter / "integration-contract.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "server_name": "hunter_tools",
            }
        ),
        encoding="utf-8",
    )
    status = HunterToolsManager(
        root=root,
        hunter_dir=hunter,
        python="python",
    ).status()
    assert status["entrypoint_exists"] is True
    assert status["contract"]["server_name"] == "hunter_tools"


@pytest.mark.parametrize(
    "result",
    [
        {"status": "error"},
        {"status": "ok", "verify": {"status": "error"}},
        {"status": {"entrypoint_exists": False}, "verify": {"status": "ok"}},
    ],
)
def test_result_failed_propagates_nested_failures(result):
    assert result_failed(result) is True


@pytest.mark.parametrize("action", ["doctor", "update"])
def test_main_returns_nonzero_when_nested_verification_fails(
    monkeypatch,
    tmp_path,
    action,
):
    class FakeManager:
        def __init__(self, *args, **kwargs):
            pass

        def install_or_update(self):
            return {"status": "ok", "action": "updated"}

        def configure_project(self):
            return {"status": "ok"}

        def configure_global_codex(self):
            return {"status": "ok"}

        def status(self):
            return {"entrypoint_exists": True}

        def verify(self):
            return {"status": "error", "returncode": 1}

    monkeypatch.setattr(
        hunter_tools_manager,
        "HunterToolsManager",
        FakeManager,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hunter_tools_manager.py",
            action,
            "--root",
            str(tmp_path),
        ],
    )

    assert hunter_tools_manager.main() == 1
