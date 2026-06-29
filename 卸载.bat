@echo off
chcp 65001 >nul 2>&1
title open-tgtylab Uninstall

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%tgtylab-files\deploy.ps1"

if not exist "%PS_SCRIPT%" (
    echo.
    echo [!] deploy.ps1 not found
    echo.
    pause
    exit /b 1
)

echo.
echo This will remove open-tgtylab configuration from all Claude directories.
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Uninstall

if %errorlevel% neq 0 (
    echo.
    echo [!] Uninstall may have issues.
    echo.
    pause
)
