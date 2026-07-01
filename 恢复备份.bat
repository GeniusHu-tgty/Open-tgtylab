@echo off
chcp 65001 >nul 2>&1
title open-tgtylab Restore
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tgtylab-files\deploy.ps1" -Restore
pause
