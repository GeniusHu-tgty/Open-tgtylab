#!/bin/bash
# open-tgtylab Uninstall - macOS/Linux
CLAUDE_DIR="$HOME/.claude"
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; GRAY='\033[0;37m'; NC='\033[0m'

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${RED}  open-tgtylab Uninstall${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

ALL_DIRS=("$CLAUDE_DIR")
for candidate in \
    "$HOME/Library/Application Support/claude" \
    "$HOME/Library/Application Support/claude-code" \
    "$HOME/Library/Application Support/Claude" \
    "$HOME/Library/Application Support/Claude Code"; do
    if [ -d "$candidate" ] && [ "$candidate" != "$CLAUDE_DIR" ]; then
        ALL_DIRS+=("$candidate")
    fi
done

echo -e "${GRAY}Will remove config from:${NC}"
for d in "${ALL_DIRS[@]}"; do echo -e "${GRAY}  - $d${NC}"; done
echo ""

read -p "Confirm uninstall? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    read -p "Press Enter to exit..."
    exit 0
fi

total=0
for dir in "${ALL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${CYAN}[*] Cleaning: $dir${NC}"
        for f in CLAUDE.md system-prompt.md config.toml; do
            if [ -f "$dir/$f" ]; then
                rm -f "$dir/$f" 2>/dev/null
                echo -e "${GREEN}    Removed $f${NC}"
                total=$((total + 1))
            fi
        done
    fi
done

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  Uninstall complete. Removed $total files.${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
read -p "Press Enter to exit..."
