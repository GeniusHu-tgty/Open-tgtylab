@echo off
chcp 65001 >nul 2>&1
title open-tgtylab Deploy

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%tgtylab-files\deploy.ps1"

if not exist "%PS_SCRIPT%" (
    echo.
    echo [!] deploy.ps1 not found
    echo     Expected: %PS_SCRIPT%
    echo.
    pause
    exit /b 1
)

where powershell.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [!] PowerShell not found. Install PowerShell 5.1+
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   open-tgtylab - AI Agent 越狱部署工具
echo ============================================================
echo.
echo [INFO] This tool deploys CLAUDE.md, system-prompt.md,
echo        settings, hooks, and workflows to your Claude config.
echo.
echo [INFO] After deployment, you still need to install:
echo        1. MCP Server:
echo           git clone <your-repo-url>
echo           cd open-reverselab/tools/skills/mcp/ReverseLabToolsMCP
echo           uv sync
echo.
echo        2. Python RE libs:
echo           pip install lief frida angr capstone keystone-engine unicorn
echo.
echo        3. External tools (optional):
echo           Ghidra, Cutter, DiE, PE-bear, x64dbg, Procmon
echo           See README.md for download links.
echo.
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"

if %errorlevel% neq 0 (
    echo.
    echo [!] Deploy may have issues. Try running as administrator.
    echo.
    pause
)
