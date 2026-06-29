from __future__ import annotations

import os
import sys
from pathlib import Path


SERVER_NAME = "reverse_lab_tools"

# ── Project root discovery ──
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REVERSE_ROOT = next(
    (
        parent
        for parent in [PACKAGE_ROOT, *PACKAGE_ROOT.parents]
        if (parent / "AGENTS.md").exists() and (parent / ".mcp.json").exists()
    ),
    PACKAGE_ROOT.parents[4],
)

# ── Directory shortcuts ──
TOOLS_DIR = REVERSE_ROOT / "tools"
TOOLS_COMMON_DIR = TOOLS_DIR / "common"
TOOLS_WINDOWS_DIR = TOOLS_DIR / "windows"
TOOLS_ANDROID_DIR = TOOLS_DIR / "android"

EXPORTS_DIR = REVERSE_ROOT / "exports" / "windows" / "triage"
EXPORTS_ROOT = REVERSE_ROOT / "exports"
AUDIT_DIR = REVERSE_ROOT / "exports" / "misc" / "audit"
AUDIT_LOG = AUDIT_DIR / "reverse_lab_tools_audit.jsonl"
GHIDRA_EXPORTS_DIR = REVERSE_ROOT / "exports" / "windows" / "ghidra"
GHIDRA_PROJECTS_DIR = REVERSE_ROOT / "projects" / "windows" / "ghidra-headless"
GHIDRA_SCRIPT_DIR = REVERSE_ROOT / "scripts" / "_shared" / "ghidra"
PATCHES_DIR = REVERSE_ROOT / "patches"
PROJECTS_DIR = REVERSE_ROOT / "projects"
REPORTS_DIR = REVERSE_ROOT / "reports"
SAMPLES_DIR = REVERSE_ROOT / "samples"
SAMPLE_QUARANTINE_DIR = SAMPLES_DIR / "_quarantine"
PROCMON_EXPORTS_DIR = REVERSE_ROOT / "exports" / "windows" / "procmon"
IOC_EXPORTS_DIR = REVERSE_ROOT / "exports" / "windows" / "iocs"
YARA_EXPORTS_DIR = REVERSE_ROOT / "exports" / "windows" / "yara"
SIGMA_EXPORTS_DIR = REVERSE_ROOT / "exports" / "windows" / "sigma"
ANDROID_EXPORTS_DIR = REVERSE_ROOT / "exports" / "android"
DEBUG_SCRIPTS_DIR = REVERSE_ROOT / "scripts" / "windows" / "debug"
PROCMON_FILTERS_DIR = REVERSE_ROOT / "scripts" / "windows" / "procmon"
SCRIPTS_DIR = REVERSE_ROOT / "scripts"
NOTES_DIR = REVERSE_ROOT / "notes"


# ── Tool autodiscovery ──
def _find_glob(dir_path: Path, pattern: str, name: str) -> Path:
    """Find first match for glob pattern, raise if not found."""
    candidates = sorted(dir_path.glob(pattern))
    if not candidates:
        raise FileNotFoundError(
            f"{name} not found at {dir_path / pattern}. "
            f"Run: .\\scripts\\misc\\install_tools.ps1"
        )
    return candidates[0]


def _find_exe(base: Path, names: list[str], label: str) -> Path:
    """Find executable by trying multiple possible names."""
    for name in names:
        candidate = base / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"{label} not found in {base}. Tried: {names}. "
        f"Run: .\\scripts\\misc\\install_tools.ps1"
    )


# Ghidra (version-flexible)
try:
    GHIDRA_ROOT = _find_glob(TOOLS_COMMON_DIR, "ghidra_*/ghidra_*_PUBLIC", "Ghidra")
    GHIDRA_HEADLESS_BAT = GHIDRA_ROOT / "support" / "analyzeHeadless.bat"
except FileNotFoundError:
    GHIDRA_ROOT = TOOLS_COMMON_DIR / "ghidra_placeholder"
    GHIDRA_HEADLESS_BAT = GHIDRA_ROOT / "support" / "analyzeHeadless.bat"

# Cutter / Rizin (version-flexible)
try:
    CUTTER_ROOT = _find_glob(TOOLS_WINDOWS_DIR / "Cutter", "Cutter-*/Cutter-*", "Cutter")
except FileNotFoundError:
    CUTTER_ROOT = TOOLS_WINDOWS_DIR / "Cutter" / "Cutter-placeholder"
try:
    RZ_BIN_EXE = _find_exe(CUTTER_ROOT, ["rz-bin.exe", "rizin.exe"], "rz-bin")
    RZ_HASH_EXE = _find_exe(CUTTER_ROOT, ["rz-hash.exe"], "rz-hash")
except FileNotFoundError:
    # Optional external tools must not prevent the MCP server from starting.
    # Individual tools report the actionable install error when invoked.
    RZ_BIN_EXE = CUTTER_ROOT / "rz-bin.exe"
    RZ_HASH_EXE = CUTTER_ROOT / "rz-hash.exe"

# DiE (version-flexible)
try:
    DIE_ROOT = _find_glob(TOOLS_WINDOWS_DIR / "die", "die*/", "DiE")
except FileNotFoundError:
    DIE_ROOT = TOOLS_WINDOWS_DIR / "die" / "die"
try:
    DIEC_EXE = _find_exe(DIE_ROOT, ["diec.exe"], "diec")
except FileNotFoundError:
    DIEC_EXE = DIE_ROOT / "diec.exe"

# PE-bear (version-flexible)
try:
    PE_BEAR_EXE = _find_glob(
        TOOLS_WINDOWS_DIR / "PE-bear", "PE-bear*.exe", "PE-bear"
    )
except FileNotFoundError:
    PE_BEAR_EXE = TOOLS_WINDOWS_DIR / "PE-bear" / "PE-bear.exe"

# Procmon
PROCMON_ROOT = TOOLS_WINDOWS_DIR / "ProcessMonitor"

# x64dbg (version-flexible)
try:
    X64DBG_ROOT = _find_glob(TOOLS_WINDOWS_DIR, "snapshot_*/release", "x64dbg")
except FileNotFoundError:
    X64DBG_ROOT = TOOLS_WINDOWS_DIR / "x64dbg"

# Android
ANDROID_SDK_PLATFORM_TOOLS = Path(
    os.environ.get("ANDROID_SDK_PLATFORM_TOOLS", r"C:\Program Files (x86)\Android\android-sdk\platform-tools")
)
ADB_EXE = ANDROID_SDK_PLATFORM_TOOLS / "adb.exe"
MUMU_DEFAULT_SERIAL = os.environ.get("MUMU_SERIAL", "127.0.0.1:16384")
MUMU_CLI_EXE = REVERSE_ROOT.parents[0] / "MuMuPlayer" / "nx_main" / "mumu-cli.exe"

# ── Host Python discovery ──
import shutil
import subprocess as _sp

def _is_venv_python(p: Path) -> bool:
    """Check if a Python executable is inside a virtual environment."""
    # venv puts pyvenv.cfg next to the python executable
    if (p.parent / "pyvenv.cfg").exists():
        return True
    # uv venv also creates pyvenv.cfg
    if p.parent.name.lower() in ("scripts", "bin") and (p.parent.parent / "pyvenv.cfg").exists():
        return True
    return False

def _discover_host_python() -> tuple[Path, str]:
    """Find the system (non-venv) Python executable.
    Returns (path, source) where source describes how it was found.
    """
    # 1. Explicit env var takes priority
    env_path = os.environ.get("REVERSELAB_HOST_PYTHON")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p, "env:REVERSELAB_HOST_PYTHON"

    # 2. Try `where.exe python` to find system PATH Python
    where = shutil.which("where")
    if where:
        try:
            result = _sp.run(["where.exe", "python"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.strip().splitlines():
                candidate = Path(line.strip())
                if candidate.exists() and candidate.suffix.lower() == ".exe" and not _is_venv_python(candidate):
                    return candidate, "where.exe (system PATH)"
        except Exception:
            pass

    # 3. Try common LOCALAPPDATA locations (any version)
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        python_base = Path(localappdata) / "Programs" / "Python"
        if python_base.exists():
            # Prefer newest version first
            for d in sorted(python_base.iterdir(), reverse=True):
                candidate = d / "python.exe"
                if candidate.exists() and not _is_venv_python(candidate):
                    return candidate, f"LOCALAPPDATA ({d.name})"

    # 4. Check Program Files
    for pf in [os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")]:
        if not pf:
            continue
        python_base = Path(pf)
        for d in sorted(python_base.iterdir(), reverse=True):
            if d.name.lower().startswith("python"):
                candidate = d / "python.exe"
                if candidate.exists() and not _is_venv_python(candidate):
                    return candidate, f"Program Files ({d.name})"

    # 5. Last resort: sys.executable (may be venv) — with warning
    return Path(sys.executable).resolve(), "sys.executable (FALLBACK — may be venv)"

_host_python, _host_python_source = _discover_host_python()
HOST_PYTHON_EXE = _host_python

# Emit warning if fallback is venv
if _is_venv_python(HOST_PYTHON_EXE):
    import warnings as _warnings
    _warnings.warn(
        f"HOST_PYTHON_EXE resolved to venv Python: {HOST_PYTHON_EXE}. "
        f"Set REVERSELAB_HOST_PYTHON env var to your system Python path, "
        f"or install Python 3.11+ to the default location.",
        stacklevel=2,
    )

HOST_PYTHON_SOURCE = _host_python_source

# ── Security: allow-listed roots ──
ALLOWED_ROOTS = [
    REVERSE_ROOT,
]

GENERATED_ROOTS = [
    REVERSE_ROOT / "exports",
    PATCHES_DIR,
    PROJECTS_DIR,
    REPORTS_DIR,
]
