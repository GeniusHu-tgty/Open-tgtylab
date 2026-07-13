#!/usr/bin/env python3
"""Install, update, configure, and diagnose the complete hunter_tools MCP."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

HUNTER_REPO = "https://github.com/GeniusHu-tgty/Hunter.git"
DEFAULT_HUNTER_DIR = Path.home() / ".agents" / "skills" / "hunter"


def result_failed(result: Mapping[str, Any]) -> bool:
    status = result.get("status")
    if status == "error":
        return True
    if isinstance(status, Mapping) and status.get("entrypoint_exists") is False:
        return True
    verify = result.get("verify")
    if isinstance(verify, Mapping) and verify.get("status") == "error":
        return True
    for key in ("project", "global", "project_config", "global_config"):
        nested = result.get(key)
        if isinstance(nested, Mapping) and nested.get("status") == "error":
            return True
    return False


def remove_toml_server_block(text: str, name: str) -> str:
    pattern = re.compile(rf"(?ms)^\[mcp_servers\.{re.escape(name)}\]\s*\n.*?(?=^\[(?!mcp_servers\.{re.escape(name)}\.env\])|\Z)")
    return pattern.sub("", text).strip() + ("\n" if text else "")


def _toml_quote(value: str) -> str:
    return json.dumps(value.replace("\\", "/"), ensure_ascii=False)


class HunterToolsManager:
    def __init__(self, root: Path, hunter_dir: Path = DEFAULT_HUNTER_DIR, python: str | None = None):
        self.root = Path(root).expanduser().resolve()
        self.hunter_dir = Path(hunter_dir).expanduser().resolve()
        self.python = str(Path(python).resolve()) if python and Path(python).exists() else (python or sys.executable)
        self.entrypoint = self.hunter_dir / "mcp_server.py"

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], text=True, capture_output=True, check=False)

    def install_or_update(self, ref: str = "main") -> dict[str, Any]:
        if (self.hunter_dir / ".git").is_dir():
            fetch = self._git("-C", str(self.hunter_dir), "fetch", "origin", ref)
            if fetch.returncode:
                return {"status": "error", "action": "fetch", "stderr": fetch.stderr.strip()}
            checkout = self._git("-C", str(self.hunter_dir), "checkout", "main")
            pull = self._git("-C", str(self.hunter_dir), "merge", "--ff-only", f"origin/{ref}")
            if checkout.returncode or pull.returncode:
                return {"status": "error", "action": "update", "stderr": (checkout.stderr + pull.stderr).strip()}
            action = "updated"
        elif self.hunter_dir.exists() and any(self.hunter_dir.iterdir()):
            return {"status": "error", "action": "install", "stderr": f"Destination is not an empty Git repository: {self.hunter_dir}"}
        else:
            self.hunter_dir.parent.mkdir(parents=True, exist_ok=True)
            clone = self._git("clone", "--branch", ref, "--single-branch", HUNTER_REPO, str(self.hunter_dir))
            if clone.returncode:
                return {"status": "error", "action": "clone", "stderr": clone.stderr.strip()}
            action = "installed"
        return {"status": "ok", "action": action, "hunter_dir": str(self.hunter_dir), "entrypoint": str(self.entrypoint)}

    def configure_project(self) -> dict[str, Any]:
        changed = False
        mcp_path = self.root / ".mcp.json"
        data = json.loads(mcp_path.read_text(encoding="utf-8-sig")) if mcp_path.exists() else {"mcpServers": {}}
        servers = data.setdefault("mcpServers", {})
        if "hunter" in servers:
            del servers["hunter"]; changed = True
        desired = {"command": self.python, "args": [str(self.entrypoint)], "env": {"OPEN_TGTYLAB_ROOT": str(self.root)}}
        if servers.get("hunter_tools") != desired:
            servers["hunter_tools"] = desired; changed = True
        rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if not mcp_path.exists() or mcp_path.read_text(encoding="utf-8-sig") != rendered:
            mcp_path.write_text(rendered, encoding="utf-8"); changed = True

        codex_path = self.root / ".codex" / "config.toml"; codex_path.parent.mkdir(parents=True, exist_ok=True)
        original = codex_path.read_text(encoding="utf-8-sig") if codex_path.exists() else ""
        cleaned = remove_toml_server_block(remove_toml_server_block(original, "hunter"), "hunter_tools").rstrip()
        block = (
            "[mcp_servers.hunter_tools]\n"
            f"command = {_toml_quote(self.python)}\n"
            f"args = [{_toml_quote(str(self.entrypoint))}]\n"
            "startup_timeout_sec = 30\n\n"
            "[mcp_servers.hunter_tools.env]\n"
            f"OPEN_TGTYLAB_ROOT = {_toml_quote(str(self.root))}\n"
        )
        updated = (cleaned + "\n\n" + block).lstrip()
        if original != updated:
            codex_path.write_text(updated, encoding="utf-8"); changed = True
        return {"status": "ok", "changed": changed, "mcp_json": str(mcp_path), "codex_config": str(codex_path)}

    def configure_global_codex(self, path: Path | None = None) -> dict[str, Any]:
        path = (path or (Path.home() / ".codex" / "config.toml")).resolve(); path.parent.mkdir(parents=True, exist_ok=True)
        original = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        cleaned = remove_toml_server_block(remove_toml_server_block(original, "hunter"), "hunter_tools").rstrip()
        block = "\n\n[mcp_servers.hunter_tools]\ntype = \"stdio\"\n" + f"command = {_toml_quote(self.python)}\nargs = [{_toml_quote(str(self.entrypoint))}]\nstartup_timeout_sec = 30\n\n[mcp_servers.hunter_tools.env]\nOPEN_TGTYLAB_ROOT = {_toml_quote(str(self.root))}\n"
        updated = cleaned + block
        changed = original != updated
        if changed: path.write_text(updated, encoding="utf-8")
        return {"status":"ok","changed":changed,"path":str(path),"restart_required":changed}

    def status(self) -> dict[str, Any]:
        contract_path = self.hunter_dir / "integration-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8-sig")) if contract_path.is_file() else None
        commit = None
        if (self.hunter_dir / ".git").is_dir():
            proc=self._git("-C",str(self.hunter_dir),"rev-parse","HEAD"); commit=proc.stdout.strip() if proc.returncode==0 else None
        return {"workspace":str(self.root),"workspace_exists":self.root.is_dir(),"hunter_dir":str(self.hunter_dir),"entrypoint_exists":self.entrypoint.is_file(),"contract":contract,"commit":commit,"python":self.python}

    def verify(self) -> dict[str, Any]:
        script=self.root/"scripts"/"misc"/"verify_hunter_tools_integration.py"
        proc=subprocess.run([self.python,str(script)],text=True,capture_output=True,env={**os.environ,"OPEN_TGTYLAB_ROOT":str(self.root),"HUNTER_TOOLS_ENTRYPOINT":str(self.entrypoint)})
        return {"status":"ok" if proc.returncode==0 else "error","returncode":proc.returncode,"stdout":proc.stdout,"stderr":proc.stderr}


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("action",choices=["install","update","configure","doctor","status"])
    parser.add_argument("--root",default=str(Path(__file__).resolve().parents[2])); parser.add_argument("--hunter-dir",default=str(DEFAULT_HUNTER_DIR)); parser.add_argument("--python",default=sys.executable); parser.add_argument("--global-codex",action="store_true")
    args=parser.parse_args(); manager=HunterToolsManager(Path(args.root),Path(args.hunter_dir),args.python)
    if args.action in {"install","update"}:
        result=manager.install_or_update();
        if result.get("status")=="ok": result["project_config"]=manager.configure_project(); result["global_config"]=manager.configure_global_codex() if args.global_codex else None; result["verify"]=manager.verify()
    elif args.action=="configure": result={"project":manager.configure_project(),"global":manager.configure_global_codex() if args.global_codex else None}
    elif args.action=="doctor": result={"status":manager.status(),"verify":manager.verify()}
    else: result=manager.status()
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 1 if result_failed(result) else 0

if __name__=="__main__": raise SystemExit(main())
