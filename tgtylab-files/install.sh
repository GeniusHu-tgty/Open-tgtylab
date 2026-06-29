#!/bin/bash
# open-tgtylab Deploy - macOS/Linux
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_DIR="$SCRIPT_DIR/config-bundle"
CLAUDE_DIR="$HOME/.claude"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; GRAY='\033[0;37m'; NC='\033[0m'

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  open-tgtylab Deploy v1.0${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${GRAY}[*] User: $(whoami)${NC}"
echo -e "${GRAY}[*] Home: $HOME${NC}"
echo -e "${GRAY}[*] Target: $CLAUDE_DIR${NC}"
echo ""

if [ ! -f "$BUNDLE_DIR/CLAUDE.md" ]; then
    echo -e "${RED}[!] CLAUDE.md not found in $BUNDLE_DIR${NC}"
    exit 1
fi

# Detect all config dirs
ALL_DIRS=("$CLAUDE_DIR")
for candidate in \
    "$HOME/Library/Application Support/claude" \
    "$HOME/Library/Application Support/claude-code" \
    "$HOME/Library/Application Support/Claude" \
    "$HOME/Library/Application Support/Claude Code" \
    "$HOME/Library/Preferences/claude" \
    "$HOME/Library/Preferences/claude-code"; do
    if [ -d "$candidate" ] && [ "$candidate" != "$CLAUDE_DIR" ]; then
        ALL_DIRS+=("$candidate")
    fi
done

echo -e "${GRAY}[*] Config dirs found: ${#ALL_DIRS[@]}${NC}"
for d in "${ALL_DIRS[@]}"; do echo -e "${GRAY}    $d${NC}"; done
echo ""

# Backup
date_str=$(date +%Y%m%d-%H%M%S)
backup="$CLAUDE_DIR/backups/tgtylab-$date_str"
backed=0
for f in CLAUDE.md system-prompt.md config.toml settings.json; do
    if [ -f "$CLAUDE_DIR/$f" ]; then
        mkdir -p "$backup" 2>/dev/null
        cp "$CLAUDE_DIR/$f" "$backup/$f" 2>/dev/null && backed=$((backed + 1))
    fi
done
[ $backed -gt 0 ] && echo -e "${GRAY}[*] Backed up $backed files${NC}"

# Deploy function
deploy() {
    local dst="$1"
    local src_root="$SCRIPT_DIR/.."
    mkdir -p "$dst" 2>/dev/null

    echo -e "${YELLOW}[1/6] CLAUDE.md${NC}"
    if cp "$BUNDLE_DIR/CLAUDE.md" "$dst/CLAUDE.md" 2>/dev/null; then
        local size=$(wc -c < "$dst/CLAUDE.md" | tr -d ' ')
        echo -e "${GREEN}      OK ($size bytes)${NC}"
    else echo -e "${RED}      FAIL${NC}"; fi

    echo -e "${YELLOW}[2/6] system-prompt.md${NC}"
    if cp "$BUNDLE_DIR/system-prompt.md" "$dst/system-prompt.md" 2>/dev/null; then
        local size=$(wc -c < "$dst/system-prompt.md" | tr -d ' ')
        echo -e "${GREEN}      OK ($size bytes)${NC}"
    else echo -e "${RED}      FAIL${NC}"; fi

    echo -e "${YELLOW}[3/6] settings.json${NC}"
    if [ ! -f "$dst/settings.json" ]; then
        cat > "$dst/settings.json" << 'EOF'
{"permissions":{"defaultMode":"bypassPermissions"},"skipDangerousModePermissionPrompt":true,"effortLevel":"xhigh","env":{"CLAUDE_CODE_EFFORT_LEVEL":"max","DISABLE_AUTOUPDATER":"1"}}
EOF
        echo -e "${GREEN}      OK (bypassPermissions)${NC}"
    else echo -e "${GRAY}      SKIPPED (exists)${NC}"; fi

    echo -e "${YELLOW}[4/6] config.toml${NC}"
    echo 'model_instructions_file = "system-prompt.md"' > "$dst/config.toml" 2>/dev/null
    echo -e "${GREEN}      OK${NC}"

    # 5. Hooks + settings.local.json
    echo -e "${YELLOW}[5/6] hooks + settings.local.json${NC}"
    local claude_project_dir="$dst/.claude"
    mkdir -p "$claude_project_dir/hooks" 2>/dev/null
    mkdir -p "$claude_project_dir/workflows" 2>/dev/null
    local hook_src="$src_root/.claude/hooks/pre-tool-call.sh"
    if [ -f "$hook_src" ]; then
        cp "$hook_src" "$claude_project_dir/hooks/pre-tool-call.sh" 2>/dev/null
        echo -e "${GREEN}      hooks OK${NC}"
    else echo -e "${GRAY}      hooks SKIPPED (source not found)${NC}"; fi
    local settings_src="$src_root/settings.local.json"
    if [ -f "$settings_src" ]; then
        cp "$settings_src" "$claude_project_dir/settings.local.json" 2>/dev/null
        echo -e "${GREEN}      settings.local.json OK${NC}"
    else echo -e "${GRAY}      settings.local.json SKIPPED${NC}"; fi

    # 6. Workflows
    echo -e "${YELLOW}[6/6] workflows${NC}"
    local wf_src="$src_root/.claude/workflows"
    if [ -d "$wf_src" ]; then
        local wf_count=0
        for wf in "$wf_src"/*.js; do
            [ -f "$wf" ] && cp "$wf" "$claude_project_dir/workflows/" 2>/dev/null && wf_count=$((wf_count + 1))
        done
        echo -e "${GREEN}      OK ($wf_count workflows)${NC}"
    else echo -e "${GRAY}      SKIPPED (source not found)${NC}"; fi
}

# Deploy to all dirs
for dir in "${ALL_DIRS[@]}"; do
    echo -e "${CYAN}[*] Deploying to: $dir${NC}"
    deploy "$dir"
    echo ""
done

echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  Deploy complete!${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${YELLOW}  Next steps (install manually):${NC}"
echo -e "${YELLOW}  1. MCP Server:${NC}"
echo -e "${GRAY}     git clone <your-repo-url>${NC}"
echo -e "${GRAY}     cd open-reverselab/tools/skills/mcp/ReverseLabToolsMCP${NC}"
echo -e "${GRAY}     uv sync${NC}"
echo -e "${YELLOW}  2. Python RE libs:${NC}"
echo -e "${GRAY}     pip install lief frida angr capstone keystone-engine unicorn${NC}"
echo -e "${YELLOW}  3. External tools: see README.md${NC}"
echo ""
echo -e "${CYAN}  Restart Claude Code and start working.${NC}"
echo ""
read -p "Press Enter to exit..."
