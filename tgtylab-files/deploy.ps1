# open-tgtylab Deploy v2.0
# Compatible: Windows 7/8/10/11, PowerShell 2.0-7.x, Core/Desktop

param([switch]$Uninstall, [switch]$Verify, [switch]$Restore)

# ========== Encoding ==========
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { [Console]::InputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { chcp 65001 | Out-Null } catch {}

# ========== Detect PowerShell ==========
$PS_FLAVOR = 'Desktop'
$PS_VER = '2.0'
try {
    if ($PSVersionTable.PSEdition -eq 'Core') { $PS_FLAVOR = 'Core' }
    $PS_VER = "$($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor)"
} catch {}

# ========== Detect OS ==========
$OS_VER = 'Unknown'
$OS_BUILD = 0
try {
    $os = [System.Environment]::OSVersion.Version
    $OS_VER = "$($os.Major).$($os.Minor)"
    $OS_BUILD = $os.Build
} catch {}

# ========== Admin detection ==========
$IS_ADMIN = $false
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $IS_ADMIN = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
} catch {}

# ========== User home path (with fallback) ==========
$USER_HOME = $env:USERPROFILE
if (!$USER_HOME) {
    try { $USER_HOME = [Environment]::GetFolderPath('UserProfile') } catch {}
    if (!$USER_HOME) {
        foreach ($drive in @('C', 'D', 'E')) {
            $testPath = "${drive}:\Users\$env:USERNAME"
            if (Test-Path $testPath) { $USER_HOME = $testPath; break }
        }
        if (!$USER_HOME) { $USER_HOME = "C:\Users\$env:USERNAME" }
    }
}

# ========== Target directories ==========
$CLAUDE_DIR = Join-Path $USER_HOME '.claude'
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

# ========== Source directory ==========
$SCRIPT_DIR = $PSScriptRoot
if (!$SCRIPT_DIR) {
    try { $SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path } catch {}
    if (!$SCRIPT_DIR) { $SCRIPT_DIR = (Get-Location).Path }
}
$BUNDLE_DIR = Join-Path $SCRIPT_DIR 'config-bundle'

# ========== Helper functions ==========

function Write-FileUtf8($Path, $Content) {
    $Path = [System.Environment]::ExpandEnvironmentVariables($Path)
    try {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($Path, $Content, $utf8)
        return $true
    } catch {}
    try {
        $Content | Out-File -FilePath $Path -Encoding UTF8 -Force -ErrorAction Stop
        return $true
    } catch {}
    try {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        $sw = New-Object System.IO.StreamWriter($Path, $false, $utf8)
        $sw.Write($Content)
        $sw.Close()
        return $true
    } catch {}
    return $false
}

function Copy-FileSafe($src, $dst, $retries = 3) {
    for ($i = 0; $i -lt $retries; $i++) {
        try {
            Copy-Item $src $dst -Force -ErrorAction Stop
            return $true
        } catch {
            if ($i -lt ($retries - 1)) { Start-Sleep -Milliseconds (500 * ($i + 1)) }
        }
    }
    return $false
}

function New-DirSafe($path) {
    if (Test-Path $path) { return $true }
    try {
        New-Item -ItemType Directory -Path $path -Force -ErrorAction Stop | Out-Null
        return $true
    } catch {}
    try {
        & cmd /c "mkdir `"$path`"" 2>nul
        return (Test-Path $path)
    } catch {}
    return $false
}

function Remove-FileSafe($path) {
    if (!(Test-Path $path)) { return $true }
    try {
        Remove-Item $path -Force -ErrorAction Stop
        return $true
    } catch {}
    try {
        & cmd /c "del /f `"$path`"" 2>nul
        return !(Test-Path $path)
    } catch {}
    return $false
}

function Test-DiskSpace($path, $minMB = 10) {
    try {
        $drive = Split-Path -Qualifier $path -ErrorAction Stop
        if ($drive) {
            $disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='$drive'" -ErrorAction Stop
            if ($disk.FreeSpace -gt ($minMB * 1MB)) { return $true }
            return $false
        }
    } catch {}
    return $true
}

function Test-PathLength($path, $maxLen = 240) {
    $expanded = [System.Environment]::ExpandEnvironmentVariables($path)
    return $expanded.Length -lt $maxLen
}

function Test-FileWritable($path) {
    if (!(Test-Path $path)) { return $true }
    try {
        $item = Get-Item $path -ErrorAction Stop
        if ($item.IsReadOnly) { $item.IsReadOnly = $false }
        return $true
    } catch {}
    return $false
}

function Test-FileLocked($path) {
    if (!(Test-Path $path)) { return $false }
    try {
        $stream = [System.IO.File]::Open($path, 'Open', 'ReadWrite', 'None')
        $stream.Close()
        return $false
    } catch { return $true }
}

# ========== Backup ==========
function Backup-Config($claudeDir) {
    $date = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupDir = Join-Path $claudeDir "backups\tgtylab-$date"
    $files = @('CLAUDE.md', 'system-prompt.md', 'config.toml', 'settings.json')
    $count = 0
    foreach ($f in $files) {
        $srcPath = Join-Path $claudeDir $f
        if (Test-Path $srcPath) {
            New-DirSafe $backupDir | Out-Null
            if (Copy-FileSafe $srcPath (Join-Path $backupDir $f)) { $count++ }
        }
    }
    return $count
}

# ========== Restore ==========
function Restore-Config($claudeDir) {
    $backupBase = Join-Path $claudeDir "backups"
    if (!(Test-Path $backupBase)) {
        Write-Host "  No backups found" -ForegroundColor DarkGray
        return $false
    }
    $backups = @()
    try { $backups = Get-ChildItem $backupBase -Directory -ErrorAction Stop | Sort-Object Name -Descending } catch {}
    if ($backups.Count -eq 0) {
        Write-Host "  No backups found" -ForegroundColor DarkGray
        return $false
    }
    $latest = $backups[0].FullName
    Write-Host "  Restoring from: $($backups[0].Name)" -ForegroundColor Yellow
    $files = @('CLAUDE.md', 'system-prompt.md', 'config.toml', 'settings.json')
    $restored = 0
    foreach ($f in $files) {
        $srcPath = Join-Path $latest $f
        if (Test-Path $srcPath) {
            if (Copy-FileSafe $srcPath (Join-Path $claudeDir $f)) {
                Write-Host "    Restored $f" -ForegroundColor Green
                $restored++
            }
        }
    }
    return $restored -gt 0
}

# ========== Deploy ==========
function Deploy-Config($dst, $src, $scriptRoot) {
    $ok = 0; $fail = 0

    Write-Host '[1/6] CLAUDE.md...' -ForegroundColor Yellow
    $file = Join-Path $src 'CLAUDE.md'
    if (Test-Path $file) {
        $dstFile = Join-Path $dst 'CLAUDE.md'
        Test-FileWritable $dstFile | Out-Null
        if (Copy-FileSafe $file $dstFile) {
            $size = (Get-Item $dstFile).Length
            Write-Host "    OK ($size bytes)" -ForegroundColor Green; $ok++
        } else { Write-Host "    FAIL (file locked or permission denied)" -ForegroundColor Red; $fail++ }
    } else { Write-Host "    NOT FOUND: $file" -ForegroundColor Red; $fail++ }

    Write-Host '[2/6] system-prompt.md...' -ForegroundColor Yellow
    $file = Join-Path $src 'system-prompt.md'
    if (Test-Path $file) {
        $dstFile = Join-Path $dst 'system-prompt.md'
        Test-FileWritable $dstFile | Out-Null
        if (Copy-FileSafe $file $dstFile) {
            $size = (Get-Item $dstFile).Length
            Write-Host "    OK ($size bytes)" -ForegroundColor Green; $ok++
        } else { Write-Host "    FAIL" -ForegroundColor Red; $fail++ }
    } else { Write-Host "    NOT FOUND: $file" -ForegroundColor Red; $fail++ }

    Write-Host '[3/6] settings.json...' -ForegroundColor Yellow
    $settingsPath = Join-Path $dst 'settings.json'
    if (!(Test-Path $settingsPath)) {
        $json = '{"permissions":{"defaultMode":"bypassPermissions"},"skipDangerousModePermissionPrompt":true,"effortLevel":"xhigh","env":{"CLAUDE_CODE_EFFORT_LEVEL":"max","DISABLE_AUTOUPDATER":"1"}}'
        if (Write-FileUtf8 $settingsPath $json) {
            Write-Host "    OK (bypassPermissions)" -ForegroundColor Green; $ok++
        } else { Write-Host "    FAIL" -ForegroundColor Red; $fail++ }
    } else {
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
        } catch { Write-Host "    SKIPPED (parse error: $_)" -ForegroundColor Yellow; $ok++ }
    }

    Write-Host '[4/6] config.toml...' -ForegroundColor Yellow
    if (Write-FileUtf8 (Join-Path $dst 'config.toml') 'model_instructions_file = "system-prompt.md"') {
        Write-Host "    OK" -ForegroundColor Green; $ok++
    } else { Write-Host "    FAIL" -ForegroundColor Red; $fail++ }

    Write-Host '[5/6] hooks + settings.local.json...' -ForegroundColor Yellow
    $claudeProjectDir = Join-Path $dst '.claude'
    New-DirSafe (Join-Path $claudeProjectDir 'hooks') | Out-Null
    New-DirSafe (Join-Path $claudeProjectDir 'workflows') | Out-Null
    $hookSrc = Join-Path (Join-Path (Join-Path (Join-Path $scriptRoot '..') '.claude') 'hooks') 'pre-tool-call.sh'
    if (Test-Path $hookSrc) {
        Copy-FileSafe $hookSrc (Join-Path (Join-Path $claudeProjectDir 'hooks') 'pre-tool-call.sh') | Out-Null
        Write-Host "    hooks OK" -ForegroundColor Green; $ok++
    } else { Write-Host "    hooks SKIPPED (source not found)" -ForegroundColor DarkGray; $ok++ }
    $settingsSrc = Join-Path (Join-Path $scriptRoot '..') 'settings.local.json'
    if (Test-Path $settingsSrc) {
        Copy-FileSafe $settingsSrc (Join-Path $claudeProjectDir 'settings.local.json') | Out-Null
        Write-Host "    settings.local.json OK" -ForegroundColor Green; $ok++
    } else { Write-Host "    settings.local.json SKIPPED" -ForegroundColor DarkGray; $ok++ }

    Write-Host '[6/6] workflows...' -ForegroundColor Yellow
    $wfSrc = Join-Path (Join-Path (Join-Path $scriptRoot '..') '.claude') 'workflows'
    if (Test-Path $wfSrc) {
        $wfDst = Join-Path $claudeProjectDir 'workflows'
        $wfCount = 0
        Get-ChildItem $wfSrc -Filter '*.js' | ForEach-Object {
            Copy-FileSafe $_.FullName (Join-Path $wfDst $_.Name) | Out-Null
            $wfCount++
        }
        Write-Host "    OK ($wfCount workflows)" -ForegroundColor Green; $ok++
    } else { Write-Host "    SKIPPED (source not found)" -ForegroundColor DarkGray; $ok++ }

    return @{ Ok = $ok; Fail = $fail }
}

# ========== Uninstall ==========
function Uninstall-Config($dst) {
    $removed = 0
    foreach ($f in @('CLAUDE.md', 'system-prompt.md', 'config.toml', 'settings.json')) {
        $path = Join-Path $dst $f
        if (Test-Path $path) {
            if (Remove-FileSafe $path) { Write-Host "    Removed $f" -ForegroundColor Green; $removed++ }
            else { Write-Host "    Failed to remove $f" -ForegroundColor Red }
        }
    }
    $claudeProjectDir = Join-Path $dst '.claude'
    if (Test-Path $claudeProjectDir) {
        foreach ($sub in @('hooks', 'workflows')) {
            $dir = Join-Path $claudeProjectDir $sub
            if (Test-Path $dir) {
                Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
                if (!(Test-Path $dir)) { Write-Host "    Removed .claude/$sub/" -ForegroundColor Green; $removed++ }
            }
        }
        $slj = Join-Path $claudeProjectDir 'settings.local.json'
        if (Test-Path $slj) {
            if (Remove-FileSafe $slj) { Write-Host "    Removed .claude/settings.local.json" -ForegroundColor Green; $removed++ }
        }
        try {
            if ((Get-ChildItem $claudeProjectDir -Force -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
                Remove-Item $claudeProjectDir -Force -ErrorAction SilentlyContinue
            }
        } catch {}
    }
    return $removed
}

# ========== Verify ==========
function Verify-Config($dst) {
    $checks = @(
        @{ File = 'CLAUDE.md'; Pattern = 'Ghost' },
        @{ File = 'system-prompt.md'; Pattern = 'Ghost' },
        @{ File = 'settings.json'; Pattern = 'bypassPermissions' },
        @{ File = 'config.toml'; Pattern = 'system-prompt.md' }
    )
    $allOk = $true
    foreach ($c in $checks) {
        $path = Join-Path $dst $c.File
        if (Test-Path $path) {
            $size = (Get-Item $path).Length
            $content = ''
            try { $content = Get-Content $path -Raw -ErrorAction Stop } catch {}
            if ($content -match $c.Pattern) {
                Write-Host "    $($c.File) - OK ($size bytes)" -ForegroundColor Green
            } else {
                Write-Host "    $($c.File) - WARNING ($size bytes)" -ForegroundColor Yellow
                $allOk = $false
            }
        } else {
            Write-Host "    $($c.File) - MISSING" -ForegroundColor Red
            $allOk = $false
        }
    }
    return $allOk
}

# ========== Warnings ==========
function Show-Warnings {
    $warnings = @()
    if ($USER_HOME -match '[^\x00-\x7F]') { $warnings += 'User profile contains non-ASCII characters' }
    if ($USER_HOME -match '\s') { $warnings += 'User profile path contains spaces' }
    if ($CLAUDE_DIR.Length -gt 200) { $warnings += 'Target path is very long' }
    try { if ($PSVersionTable.PSVersion.Major -lt 3) { $warnings += 'PowerShell version is very old' } } catch {}
    foreach ($w in $warnings) { Write-Host "[!] $w" -ForegroundColor Yellow }
    return $warnings.Count
}

# ========== MAIN ==========

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  open-tgtylab Deploy v2.0' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''
Write-Host "[*] User: $env:USERNAME" -ForegroundColor DarkGray
Write-Host "[*] PS: $PS_VER ($PS_FLAVOR)" -ForegroundColor DarkGray
Write-Host "[*] OS: $OS_VER (Build $OS_BUILD)" -ForegroundColor DarkGray
Write-Host "[*] Admin: $IS_ADMIN" -ForegroundColor DarkGray
Write-Host "[*] Home: $USER_HOME" -ForegroundColor DarkGray
Write-Host "[*] Config dirs found: $($ALL_DIRS.Count)" -ForegroundColor DarkGray
foreach ($d in $ALL_DIRS) { Write-Host "    $d" -ForegroundColor DarkGray }
$warnCount = Show-Warnings
if ($warnCount -gt 0) { Write-Host '' }

# ---- Uninstall ----
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

# ---- Verify ----
if ($Verify) {
    Write-Host 'Verifying deployment...' -ForegroundColor Yellow
    $ok = Verify-Config $CLAUDE_DIR
    Write-Host ''
    if ($ok) { Write-Host 'All checks passed!' -ForegroundColor Green }
    else { Write-Host 'Some checks failed. Run deploy first.' -ForegroundColor Yellow }
    Write-Host ''
    Read-Host 'Press Enter to exit'
    exit
}

# ---- Restore ----
if ($Restore) {
    Write-Host 'Restoring from backup...' -ForegroundColor Yellow
    $restored = Restore-Config $CLAUDE_DIR
    Write-Host ''
    if ($restored) { Write-Host 'Restore complete!' -ForegroundColor Green }
    else { Write-Host 'No backup to restore.' -ForegroundColor Yellow }
    Write-Host ''
    Read-Host 'Press Enter to exit'
    exit
}

# ---- Deploy ----

# Pre-flight
if (!(Test-DiskSpace $CLAUDE_DIR)) {
    Write-Host '[!] Low disk space' -ForegroundColor Red
    Read-Host 'Press Enter to exit'
    exit 1
}
if (!(Test-PathLength $CLAUDE_DIR)) {
    Write-Host '[!] Target path too long (>240 chars)' -ForegroundColor Red
    Read-Host 'Press Enter to exit'
    exit 1
}
if (!(Test-Path $BUNDLE_DIR)) {
    Write-Host "[!] Source directory not found: $BUNDLE_DIR" -ForegroundColor Red
    Read-Host 'Press Enter to exit'
    exit 1
}
foreach ($f in @('CLAUDE.md', 'system-prompt.md')) {
    if (!(Test-Path (Join-Path $BUNDLE_DIR $f))) {
        Write-Host "[!] Missing source file: $f" -ForegroundColor Red
        Read-Host 'Press Enter to exit'
        exit 1
    }
}

# Ensure target
if (!(Test-Path $CLAUDE_DIR)) {
    if (New-DirSafe $CLAUDE_DIR) {
        Write-Host '[+] Created .claude directory' -ForegroundColor Yellow
    } else {
        Write-Host '[!] Failed to create .claude directory' -ForegroundColor Red
        if (!$IS_ADMIN) { Write-Host '    Try running as administrator' -ForegroundColor Red }
        Read-Host 'Press Enter to exit'
        exit 1
    }
}

# Lock file
$lockFile = Join-Path $CLAUDE_DIR '.tgtylab-deploy.lock'
if (Test-Path $lockFile) {
    Write-Host '[!] Another deployment may be in progress' -ForegroundColor Yellow
    $continue = Read-Host 'Continue anyway? (Y/N)'
    if ($continue -ne 'Y' -and $continue -ne 'y') { exit 0 }
}
try {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $sw = New-Object System.IO.StreamWriter($lockFile, $false, $utf8)
    $sw.WriteLine("$env:USERNAME - $(Get-Date)")
    $sw.Close()
} catch {}

# Backup
$backupCount = Backup-Config $CLAUDE_DIR
if ($backupCount -gt 0) {
    Write-Host "[*] Backed up $backupCount existing files" -ForegroundColor DarkGray
}

# Deploy to primary
$result = Deploy-Config $CLAUDE_DIR $BUNDLE_DIR $SCRIPT_DIR

# Remove lock
Remove-FileSafe $lockFile | Out-Null

# Deploy to all other dirs
foreach ($dir in $ALL_DIRS) {
    if ($dir -ne $CLAUDE_DIR) {
        Write-Host ''
        Write-Host "[*] Deploying to: $dir" -ForegroundColor Yellow
        $r = Deploy-Config $dir $BUNDLE_DIR $SCRIPT_DIR
        if ($r.Fail -eq 0) { Write-Host "    Complete ($($r.Ok)/6)" -ForegroundColor Green }
    }
}

# OpenCode
Write-Host ''
Write-Host '[*] OpenCode deploy...' -ForegroundColor Cyan
$opencodeSrc = Join-Path (Join-Path (Join-Path $SCRIPT_DIR '..') 'opencode-files') 'opencode-config-bundle'
if (Test-Path $opencodeSrc) {
    $opencodeDst = Join-Path (Join-Path $USER_HOME '.config') 'opencode'
    New-DirSafe $opencodeDst | Out-Null
    $ocJson = Join-Path $opencodeSrc 'opencode.json'
    if (Test-Path $ocJson) {
        Copy-FileSafe $ocJson (Join-Path $opencodeDst 'opencode.json') | Out-Null
        Write-Host "    opencode.json -> ~/.config/opencode/" -ForegroundColor Green
    }
    $agentSrc = Join-Path (Join-Path $opencodeSrc '.opencode') 'agents'
    if (Test-Path $agentSrc) {
        $agentDst = Join-Path $opencodeDst 'agents'
        New-DirSafe $agentDst | Out-Null
        Get-ChildItem $agentSrc -Filter '*.md' | ForEach-Object {
            Copy-FileSafe $_.FullName (Join-Path $agentDst $_.Name) | Out-Null
        }
        Write-Host "    agents -> ~/.config/opencode/agents/" -ForegroundColor Green
    }
    $promptSrc = Join-Path $opencodeSrc 'prompts'
    if (Test-Path $promptSrc) {
        $promptDst = Join-Path $opencodeDst 'prompts'
        New-DirSafe $promptDst | Out-Null
        Get-ChildItem $promptSrc | ForEach-Object {
            Copy-FileSafe $_.FullName (Join-Path $promptDst $_.Name) | Out-Null
        }
        Write-Host "    prompts -> ~/.config/opencode/prompts/" -ForegroundColor Green
    }
    Write-Host "    OK" -ForegroundColor Green
} else { Write-Host "    SKIPPED (source not found)" -ForegroundColor DarkGray }

# Hermes
Write-Host ''
Write-Host '[*] Hermes deploy...' -ForegroundColor Cyan
$hermesSrc = Join-Path (Join-Path (Join-Path $SCRIPT_DIR '..') 'hermes-files') 'hermes-config-bundle'
if (Test-Path $hermesSrc) {
    $hermesDst = Join-Path $USER_HOME '.hermes'
    New-DirSafe $hermesDst | Out-Null
    $soulSrc = Join-Path $hermesSrc 'SOUL.md'
    if (Test-Path $soulSrc) {
        Copy-FileSafe $soulSrc (Join-Path $hermesDst 'SOUL.md') | Out-Null
        Write-Host "    SOUL.md -> ~/.hermes/ (updated)" -ForegroundColor Green
    }
    $cfgSrc = Join-Path $hermesSrc 'config.yaml'
    if (Test-Path $cfgSrc) {
        Copy-FileSafe $cfgSrc (Join-Path $hermesDst 'config.yaml') | Out-Null
        Write-Host "    config.yaml -> ~/.hermes/ (updated)" -ForegroundColor Green
    }
    Write-Host "    OK" -ForegroundColor Green
} else { Write-Host "    SKIPPED (source not found)" -ForegroundColor DarkGray }

# Summary
Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
if ($result.Fail -eq 0) {
    Write-Host "  Deploy complete! ($($result.Ok)/6)" -ForegroundColor Green
} else {
    Write-Host "  Deploy done ($($result.Ok) ok, $($result.Fail) fail)" -ForegroundColor Yellow
    if (!$IS_ADMIN) { Write-Host '  Try running as administrator if issues persist' -ForegroundColor DarkGray }
}
Write-Host ''
Write-Host '  Next steps:' -ForegroundColor Yellow
Write-Host '  1. cd tools/skills/mcp/ReverseLabToolsMCP && uv sync' -ForegroundColor Gray
Write-Host '  2. pip install lief frida angr capstone keystone-engine unicorn' -ForegroundColor Gray
Write-Host '  3. Restart Claude Code' -ForegroundColor Gray
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''
Read-Host 'Press Enter to exit'
