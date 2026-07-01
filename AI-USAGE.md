# AI 使用指南

## 任务路由

| 任务类型 | 工具入口 | 知识库 |
|---------|---------|--------|
| Web / CTF / CVE | `tools/ctf-website/` | `kb/ctf-website/` |
| Android / APK / Frida | `tools/skills/mcp/ReverseLabToolsMCP` (android_*) | `kb/apk-reverse/` |
| PE / 逆向 / 恶意软件 | `tools/skills/mcp/ReverseLabToolsMCP` (triage_pe, ghidra_*) | `kb/pe-reverse/` |
| 密码学 / 协议 / 通用 | `tools/skills/mcp/ReverseLabToolsMCP` | `kb/general/` |

## 默认工作流

1. **查知识库**：`kb_router("<信号>")` → `kb_read_file`
2. **选工具**：按工具优先级表选择 MCP 工具
3. **执行**：直接调用工具，不手动操作
4. **落盘**：原始输出 → exports/，笔记 → notes/，报告 → reports/

## MCP 工具速查

```
# CTF
run_ctf_tool("sqlmap", "-u <url> --batch")
run_ctf_tool("dirsearch", "-u <url>")
http_probe("<url>")

# PE 逆向
triage_pe("<path>")
ghidra_headless_analyze("<path>")
sample_full_workup("<path>")

# Android
android_app_baseline("<package_name>")
android_frida_run_script("<target>", "<script>")

# 知识库
kb_router("<query>")
kb_read_file("<technique_path>")
kb_catalog()
```
