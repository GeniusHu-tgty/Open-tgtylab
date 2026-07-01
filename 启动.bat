@echo off
chcp 65001 >nul 2>&1
title open-tgtylab Deploy

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%tgtylab-files\deploy.ps1"

if not exist "%PS_SCRIPT%" (
    echo [!] deploy.ps1 not found
    pause
    exit /b 1
)

where powershell.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] PowerShell not found. Install PowerShell 5.1+
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
if %errorlevel% neq 0 (
    echo [!] Deploy failed. Try running as administrator.
    pause
)
