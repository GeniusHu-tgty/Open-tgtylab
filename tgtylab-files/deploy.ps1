# open-tgtylab Deploy v1.0
# Windows: PowerShell 2.0-7.x, Core/Desktop

param([switch]$Uninstall)

$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { chcp 65001 | Out-Null } catch {}

$USER_HOME = $env:USERPROFILE
if (!$USER_HOME) { $USER_HOME = [Environment]::GetFolderPath('UserProfile') }
$CLAUDE_DIR = Join-Path $USER_HOME '.claude'

$SCRIPT_DIR = $PSScriptRoot
if (!$SCRIPT_DIR) { $SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path }
$BUNDLE_DIR = Join-Path $SCRIPT_DIR 'config-bundle'

$ALL_DIRS = @($CLAUDE_DIR)
$desktopCandidates = @(
    (Join-Path $env:APPDATA 'claude'),
    (Join-Path $env:APPDATA 'Claude'),
    (Join-Path $env:APPDATA 'Claude-3p'),
    (Join-Path $env:LOCALAPPDATA 'claude-code'),
    (Join-Path $env:LOCALAPPDATA 'claude'),
    (Join-Path $env:LOCALAPPDATA 'Claude'),
    (Join-Path $env:LOCALAPPDATA 'Claude-3p'),
    (Join-Path $USER_HOME 'AppData\Roaming\claude'),
    (Join-Path $USER_HOME 'AppData\Roaming\Claude'),
    (Join-Path $USER_HOME 'AppData\Roaming\Claude-3p'),
    (Join-Path $USER_HOME 'AppData\Local\claude-code'),
    (Join-Path $USER_HOME 'AppData\Local\claude'),
    (Join-Path $USER_HOME 'AppData\Local\Claude'),
    (Join-Path $USER_HOME 'AppData\Local\Claude-3p')
)
foreach ($candidate in $desktopCandidates) {
    if ($candidate -ne $CLAUDE_DIR -and (Test-Path $candidate)) {
        $ALL_DIRS += $candidate
    }
}

function Write-FileUtf8($Path, $Content) {
    try {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($Path, $Content, $utf8)
        return $true
    } catch {}
    try {
        $Content | Out-File -FilePath $Path -Encoding UTF8 -Force -ErrorAction Stop
        return $true
    } catch {}
    return $false
}

function Deploy-Config($dst, $src, $scriptRoot) {
    $ok = 0; $fail = 0

    Write-Host '[1/6] CLAUDE.md...' -ForegroundColor Yellow
    $file = Join-Path $src 'CLAUDE.md'
    if (Test-Path $file) {
        try {
            Copy-Item $file (Join-Path $dst 'CLAUDE.md') -Force -ErrorAction Stop
            $size = (Get-Item (Join-Path $dst 'CLAUDE.md')).Length
            Write-Host "    OK ($size bytes)" -ForegroundColor Green; $ok++
        } catch { Write-Host "    FAIL: $_" -ForegroundColor Red; $fail++ }
    } else { Write-Host "    NOT FOUND" -ForegroundColor Red; $fail++ }

    Write-Host '[2/6] system-prompt.md...' -ForegroundColor Yellow
    $file = Join-Path $src 'system-prompt.md'
    if (Test-Path $file) {
        try {
            Copy-Item $file (Join-Path $dst 'system-prompt.md') -Force -ErrorAction Stop
            $size = (Get-Item (Join-Path $dst 'system-prompt.md')).Length
            Write-Host "    OK ($size bytes)" -ForegroundColor Green; $ok++
        } catch { Write-Host "    FAIL: $_" -ForegroundColor Red; $fail++ }
    } else { Write-Host "    NOT FOUND" -ForegroundColor Red; $fail++ }

    Write-Host '[3/6] settings.json...' -ForegroundColor Yellow
    $settingsPath = Join-Path $dst 'settings.json'
    if (!(Test-Path $settingsPath)) {
        $json = '{"permissions":{"defaultMode":"bypassPermissions"},"skipDangerousModePermissionPrompt":true,"effortLevel":"xhigh","env":{"CLAUDE_CODE_EFFORT_LEVEL":"max","DISABLE_AUTOUPDATER":"1"}}'
        if (Write-FileUtf8 $settingsPath $json) {
            Write-Host "    OK (bypassPermissions)" -ForegroundColor Green; $ok++
        } else { Write-Host "    FAIL" -ForegroundColor Red; $fail++ }
    } else {
        # Ensure bypassPermissions is present in existing settings.json
        try {
            $existing = Get-Content $settingsPath -Raw -ErrorAction Stop | ConvertFrom-Json
            $changed = $false
            if (-not $existing.permissions) {
                $existing | Add-Member -NotePropertyName "permissions" -NotePropertyValue (@{defaultMode="bypassPermissions"}) -Force
                $changed = $true
            } elseif ($existing.permissions.defaultMode -ne "bypassPermissions") {
                $existing.permissions.defaultMode = "bypassPermissions"
                $changed = $true
            }
            if (-not $existing.skipDangerousModePermissionPrompt) {
                $existing | Add-Member -NotePropertyName "skipDangerousModePermissionPrompt" -NotePropertyValue $true -Force
                $changed = $true
            }
            if ($changed) {
                $existing | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
                Write-Host "    OK (merged bypassPermissions)" -ForegroundColor Green; $ok++
            } else {
                Write-Host "    OK (already configured)" -ForegroundColor Green; $ok++
            }
        } catch {
            Write-Host "    SKIPPED (parse error: $_)" -ForegroundColor Yellow; $ok++
        }
    }

    Write-Host '[4/6] config.toml...' -ForegroundColor Yellow
    if (Write-FileUtf8 (Join-Path $dst 'config.toml') 'model_instructions_file = "system-prompt.md"') {
        Write-Host "    OK" -ForegroundColor Green; $ok++
    } else { Write-Host "    FAIL" -ForegroundColor Red; $fail++ }

    # 5. Hooks + settings.local.json (project-level .claude/)
    Write-Host '[5/6] hooks + settings.local.json...' -ForegroundColor Yellow
    $claudeProjectDir = Join-Path $dst '.claude'
    New-Item -ItemType Directory -Path (Join-Path $claudeProjectDir 'hooks') -Force 2>$null | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $claudeProjectDir 'workflows') -Force 2>$null | Out-Null
    $hookSrc = Join-Path (Join-Path (Join-Path (Join-Path $scriptRoot '..') '.claude') 'hooks') 'pre-tool-call.sh'
    if (Test-Path $hookSrc) {
        Copy-Item $hookSrc (Join-Path (Join-Path $claudeProjectDir 'hooks') 'pre-tool-call.sh') -Force 2>$null
        Write-Host "    hooks OK" -ForegroundColor Green; $ok++
    } else { Write-Host "    hooks SKIPPED (source not found)" -ForegroundColor DarkGray; $ok++ }
    $settingsSrc = Join-Path (Join-Path $scriptRoot '..') 'settings.local.json'
    if (Test-Path $settingsSrc) {
        Copy-Item $settingsSrc (Join-Path $claudeProjectDir 'settings.local.json') -Force 2>$null
        Write-Host "    settings.local.json OK" -ForegroundColor Green; $ok++
    } else { Write-Host "    settings.local.json SKIPPED" -ForegroundColor DarkGray; $ok++ }

    # 6. Workflows
    Write-Host '[6/6] workflows...' -ForegroundColor Yellow
    $wfSrc = Join-Path (Join-Path (Join-Path $scriptRoot '..') '.claude') 'workflows'
    if (Test-Path $wfSrc) {
        $wfDst = Join-Path $claudeProjectDir 'workflows'
        $wfCount = 0
        Get-ChildItem $wfSrc -Filter '*.js' | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $wfDst $_.Name) -Force 2>$null
            $wfCount++
        }
        Write-Host "    OK ($wfCount workflows)" -ForegroundColor Green; $ok++
    } else { Write-Host "    SKIPPED (source not found)" -ForegroundColor DarkGray; $ok++ }

    return @{ Ok = $ok; Fail = $fail }
}

function Uninstall-Config($dst) {
    $removed = 0
    # Remove top-level config files
    foreach ($f in @('CLAUDE.md', 'system-prompt.md', 'config.toml', 'settings.json')) {
        $path = Join-Path $dst $f
        if (Test-Path $path) {
            Remove-Item $path -Force -ErrorAction Stop 2>$null
            if (!(Test-Path $path)) { Write-Host "    Removed $f" -ForegroundColor Green; $removed++ }
            else { Write-Host "    Failed to remove $f" -ForegroundColor Red }
        }
    }
    # Remove project-level .claude/ contents
    $claudeProjectDir = Join-Path $dst '.claude'
    if (Test-Path $claudeProjectDir) {
        # Remove hooks
        $hooksDir = Join-Path $claudeProjectDir 'hooks'
        if (Test-Path $hooksDir) {
            Remove-Item $hooksDir -Recurse -Force -ErrorAction Stop 2>$null
            if (!(Test-Path $hooksDir)) { Write-Host "    Removed .claude/hooks/" -ForegroundColor Green; $removed++ }
        }
        # Remove workflows
        $wfDir = Join-Path $claudeProjectDir 'workflows'
        if (Test-Path $wfDir) {
            Remove-Item $wfDir -Recurse -Force -ErrorAction Stop 2>$null
            if (!(Test-Path $wfDir)) { Write-Host "    Removed .claude/workflows/" -ForegroundColor Green; $removed++ }
        }
        # Remove settings.local.json
        $slj = Join-Path $claudeProjectDir 'settings.local.json'
        if (Test-Path $slj) {
            Remove-Item $slj -Force -ErrorAction Stop 2>$null
            if (!(Test-Path $slj)) { Write-Host "    Removed .claude/settings.local.json" -ForegroundColor Green; $removed++ }
        }
        # Remove .claude dir if empty
        if ((Get-ChildItem $claudeProjectDir -Force | Measure-Object).Count -eq 0) {
            Remove-Item $claudeProjectDir -Force 2>$null
        }
    }
    # Remove backups
    $backupDir = Join-Path $dst 'backups'
    if (Test-Path $backupDir) {
        Remove-Item $backupDir -Recurse -Force -ErrorAction Stop 2>$null
        if (!(Test-Path $backupDir)) { Write-Host "    Removed backups/" -ForegroundColor Green; $removed++ }
    }
    return $removed
}

# Banner
Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  open-tgtylab Deploy v1.0' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''
Write-Host "[*] User: $env:USERNAME" -ForegroundColor DarkGray
Write-Host "[*] Home: $USER_HOME" -ForegroundColor DarkGray
Write-Host "[*] Config dirs found: $($ALL_DIRS.Count)" -ForegroundColor DarkGray
foreach ($d in $ALL_DIRS) { Write-Host "    $d" -ForegroundColor DarkGray }
Write-Host ''

# Uninstall
if ($Uninstall) {
    Write-Host 'Uninstalling...' -ForegroundColor Yellow
    $total = 0
    foreach ($dir in $ALL_DIRS) {
        Write-Host "[*] Cleaning: $dir" -ForegroundColor Yellow
        $total += Uninstall-Config $dir
    }
    Write-Host ''
    Write-Host "Removed $total files" -ForegroundColor Cyan
    Write-Host ''
    Read-Host 'Press Enter to exit'
    exit
}

# Deploy
# Backup
$date = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = Join-Path $CLAUDE_DIR "backups\tgtylab-$date"
$backed = 0
foreach ($f in @('CLAUDE.md', 'system-prompt.md', 'config.toml', 'settings.json')) {
    $srcPath = Join-Path $CLAUDE_DIR $f
    if (Test-Path $srcPath) {
        New-Item -ItemType Directory -Path $backupDir -Force 2>$null | Out-Null
        Copy-Item $srcPath (Join-Path $backupDir $f) -Force 2>$null
        $backed++
    }
}
if ($backed -gt 0) { Write-Host "[*] Backed up $backed files to backups\tgtylab-$date" -ForegroundColor DarkGray }

# Deploy to primary
$result = Deploy-Config $CLAUDE_DIR $BUNDLE_DIR $SCRIPT_DIR

# Deploy to all other dirs
foreach ($dir in $ALL_DIRS) {
    if ($dir -ne $CLAUDE_DIR) {
        Write-Host ''
        Write-Host "[*] Deploying to: $dir" -ForegroundColor Yellow
        $r = Deploy-Config $dir $BUNDLE_DIR $SCRIPT_DIR
        if ($r.Fail -eq 0) { Write-Host "    Complete ($($r.Ok)/4)" -ForegroundColor Green }
    }
}

# ========== OpenCode Deploy ==========
Write-Host ''
Write-Host '[*] OpenCode deploy...' -ForegroundColor Cyan
$opencodeSrc = Join-Path (Join-Path (Join-Path $SCRIPT_DIR '..') 'opencode-files') 'opencode-config-bundle'
if (Test-Path $opencodeSrc) {
    # Copy opencode.json to project root (user copies to their project)
    $opencodeDst = Join-Path (Join-Path $USER_HOME '.config') 'opencode'
    New-Item -ItemType Directory -Path $opencodeDst -Force 2>$null | Out-Null
    $ocJson = Join-Path $opencodeSrc 'opencode.json'
    if (Test-Path $ocJson) {
        Copy-Item $ocJson (Join-Path $opencodeDst 'opencode.json') -Force 2>$null
        Write-Host "    opencode.json -> ~/.config/opencode/" -ForegroundColor Green
    }
    # Copy agent definition
    $agentSrc = Join-Path (Join-Path $opencodeSrc '.opencode') 'agents'
    if (Test-Path $agentSrc) {
        $agentDst = Join-Path $opencodeDst 'agents'
        New-Item -ItemType Directory -Path $agentDst -Force 2>$null | Out-Null
        Get-ChildItem $agentSrc -Filter '*.md' | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $agentDst $_.Name) -Force 2>$null
        }
        Write-Host "    agents -> ~/.config/opencode/agents/" -ForegroundColor Green
    }
    # Copy prompt file
    $promptSrc = Join-Path $opencodeSrc 'prompts'
    if (Test-Path $promptSrc) {
        $promptDst = Join-Path $opencodeDst 'prompts'
        New-Item -ItemType Directory -Path $promptDst -Force 2>$null | Out-Null
        Get-ChildItem $promptSrc | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $promptDst $_.Name) -Force 2>$null
        }
        Write-Host "    prompts -> ~/.config/opencode/prompts/" -ForegroundColor Green
    }
    Write-Host "    OK" -ForegroundColor Green
} else { Write-Host "    SKIPPED (source not found)" -ForegroundColor DarkGray }

# ========== Hermes Deploy ==========
Write-Host ''
Write-Host '[*] Hermes deploy...' -ForegroundColor Cyan
$hermesSrc = Join-Path (Join-Path (Join-Path $SCRIPT_DIR '..') 'hermes-files') 'hermes-config-bundle'
if (Test-Path $hermesSrc) {
    $hermesDst = Join-Path $USER_HOME '.hermes'
    New-Item -ItemType Directory -Path $hermesDst -Force 2>$null | Out-Null
    # SOUL.md -> ~/.hermes/SOUL.md (always overwrite)
    $soulSrc = Join-Path $hermesSrc 'SOUL.md'
    if (Test-Path $soulSrc) {
        Copy-Item $soulSrc (Join-Path $hermesDst 'SOUL.md') -Force 2>$null
        Write-Host "    SOUL.md -> ~/.hermes/ (updated)" -ForegroundColor Green
    }
    # config.yaml -> ~/.hermes/config.yaml (always overwrite)
    $cfgSrc = Join-Path $hermesSrc 'config.yaml'
    if (Test-Path $cfgSrc) {
        Copy-Item $cfgSrc (Join-Path $hermesDst 'config.yaml') -Force 2>$null
        Write-Host "    config.yaml -> ~/.hermes/ (updated)" -ForegroundColor Green
    }
    Write-Host "    OK" -ForegroundColor Green
    Write-Host "    NOTE: Copy .hermes.md to your project root manually" -ForegroundColor DarkGray
} else { Write-Host "    SKIPPED (source not found)" -ForegroundColor DarkGray }

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
if ($result.Fail -eq 0) {
    Write-Host "  Deploy complete! ($($result.Ok)/4)" -ForegroundColor Green
} else {
    Write-Host "  Deploy done ($($result.Ok) ok, $($result.Fail) fail)" -ForegroundColor Yellow
}
Write-Host ''
Write-Host '  Next steps (install manually):' -ForegroundColor Yellow
Write-Host '  1. MCP Server:' -ForegroundColor Yellow
Write-Host '     git clone <your-repo-url>' -ForegroundColor Gray
Write-Host '     cd open-reverselab/tools/skills/mcp/ReverseLabToolsMCP' -ForegroundColor Gray
Write-Host '     uv sync' -ForegroundColor Gray
Write-Host '  2. Python RE libs:' -ForegroundColor Yellow
Write-Host '     pip install lief frida angr capstone keystone-engine unicorn' -ForegroundColor Gray
Write-Host '  3. External tools: see README.md' -ForegroundColor Yellow
Write-Host ''
Write-Host '  Restart Claude Code and start working.' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''
Read-Host 'Press Enter to exit'
