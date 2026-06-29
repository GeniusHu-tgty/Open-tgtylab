#!/bin/bash
# open-tgtylab Mac 一键部署
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
xattr -cr "$SCRIPT_DIR" 2>/dev/null
chmod +x "$SCRIPT_DIR"/*.command 2>/dev/null
chmod +x "$SCRIPT_DIR"/tgtylab-files/*.sh 2>/dev/null
bash "$SCRIPT_DIR/tgtylab-files/install.sh"
