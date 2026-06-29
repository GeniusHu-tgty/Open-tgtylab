#!/bin/bash
# ============================================================
# PRE-ACTION GATE HOOK — open-tgtylab强制协议 §1
# ============================================================
# 拦截 curl/wget/Python-requests/路径枚举 等违规操作。
#
# 参数来源（优先级高到低）：
# 1. CLAUDE_TOOL_INPUT env var （标准模式）
# 2. stdin pipe （部分环境）
# 3. $* 参数
#
# Windows/MinGW 已知问题：CLAUDE_TOOL_INPUT 为空
# stdin 方式有效（echo "curl ..." | bash hook.sh）
# ============================================================

# 收集命令文本
CMD="${CLAUDE_TOOL_INPUT}"
[ -z "$CMD" ] && CMD=$(cat /dev/stdin 2>/dev/null)
[ -z "$CMD" ] && CMD="$*"
[ -z "$CMD" ] && echo "[HOOK] ⚠ Windows/MinGW: 无法获取命令内容（env var 为空），跳过拦截" && exit 0

# === §1.1 禁止 curl/wget HTTP 请求 ===
if echo "$CMD" | grep -qiE 'curl\s+.*https?://'; then
    echo "[HOOK BLOCKED] §1.1 BANNED: curl for HTTP. Use http_probe() or Burp MCP instead."
    exit 1
fi
if echo "$CMD" | grep -qiE 'wget\s+.*https?://'; then
    echo "[HOOK BLOCKED] §1.1 BANNED: wget for HTTP. Use http_probe() or Burp MCP instead."
    exit 1
fi

# === §1.2 禁止 Python requests/http.client ===
if echo "$CMD" | grep -qE '(python|python3).*import.*requests|import.*http\.client|urllib\.request'; then
    echo "[HOOK BLOCKED] §1.2 BANNED: Python requests/http.client for HTTP. Use http_probe() or Burp MCP instead."
    exit 1
fi

# === §1.3 禁止 for/while 循环枚举 URL 路径 ===
if echo "$CMD" | grep -qE '(for (p|path|dir|endpoint|page|uri|prefix).*\bcurl\b|while.*read.*curl)'; then
    echo "[HOOK BLOCKED] §1.3 BANNED: Bash loop URL enumeration. Use dirsearch (run_ctf_tool) instead."
    exit 1
fi

# === §1.4 禁止 MinGW 下的 grep -P ===
if echo "$CMD" | grep -qE '(^|[|;&\s])\s*grep\s+.*\b-P\b'; then
    echo "[HOOK BLOCKED] §1.4 BANNED: grep -P on MinGW (known crash). Use grep -E instead."
    exit 1
fi

# === §1.5 禁止 strings/file/hash 替代 MCP 工具 ===
BASE_CMD=$(echo "$CMD" | grep -oE '^\s*\w+' | head -1)
case "$BASE_CMD" in
    strings)
        echo "[HOOK BLOCKED] §1.5 BANNED: strings command. Use rizin_strings() MCP instead."
        exit 1
        ;;
    file)
        echo "[HOOK BLOCKED] §1.5 BANNED: file command. Use rizin_bin_info() / triage_pe() instead."
        exit 1
        ;;
    md5sum|sha1sum|sha256sum)
        echo "[HOOK BLOCKED] §1.5 BANNED: hash command. Use hash_file() MCP instead."
        exit 1
        ;;
esac

exit 0
