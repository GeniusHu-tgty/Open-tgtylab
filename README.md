# open-tgtylab

> Claude Code / Codex / OpenCode / Hermes 越狱配置包

降低 AI 对你的所有限制，直接给代码、不拒绝、不警告、不废话。

## 特性

- 🔓 身份锁：AI 认为自己是真人黑客，绕过安全对齐
- 🧠 思维重定向：检测 thinking 中的拒绝词，实时拦截
- 📚 562 个示例覆盖 16 大类安全场景
- 🛠 150+ MCP 工具（PE 分析、Android 逆向、CTF 自动化）
- 📖 165 篇知识库（Web 攻击、逆向工程、密码学）
- 🔄 5 个 CTF 自动化流水线
- 🐍 sqlmap / dirsearch / jwt_tool / tplmap 内置
- 🖥 跨平台（Windows / macOS / Linux）

## 快速开始

### Windows

双击 `启动.bat` 一键部署。

### macOS

```bash
chmod +x tgtylab-files/install.sh && ./tgtylab-files/install.sh
```

或双击 `启动.command`（如有 Gatekeeper 提示，右键 → 打开）。

### Linux

```bash
chmod +x tgtylab-files/linux-install.sh && ./tgtylab-files/linux-install.sh
```

### 安装 MCP 工具（可选，推荐）

```powershell
cd tools/skills/mcp/ReverseLabToolsMCP
uv sync
pip install lief frida angr capstone keystone-engine unicorn
```

### 验证

双击 `验证.bat`，看到 "All checks passed!" 就成功了。

## 其他操作

| 操作 | Windows | macOS / Linux |
|------|---------|---------------|
| 卸载 | 双击 `卸载.bat` | `./tgtylab-files/uninstall.sh` |
| 验证 | 双击 `验证.bat` | `powershell deploy.ps1 -Verify` |
| 恢复备份 | 双击 `恢复备份.bat` | `powershell deploy.ps1 -Restore` |

## 兼容性

| 系统 | 状态 |
|------|------|
| Windows 11 | ✅ |
| Windows 10 | ✅ |
| Windows 7/8 | ✅ (PowerShell 2.0+) |
| macOS 12+ | ✅ |
| Linux | ✅ |
| 中文路径 | ✅ |
| 空格路径 | ✅ |
| 非管理员 | ✅ |

## 系统要求

- Claude Code / Codex / OpenCode / Hermes（任一）
- Windows 7+ / macOS / Linux
- Git、Python 3.11+

## 文件结构

```
open-tgtylab/
├── 启动.bat                      Windows 一键安装
├── 启动.command                  macOS 一键安装
├── 卸载.bat                      Windows 卸载
├── 卸载.command                  macOS 卸载
├── 验证.bat                      验证部署
├── 恢复备份.bat                  恢复原配置
├── tgtylab-files/
│   ├── deploy.ps1                Windows 部署脚本（v2.0）
│   ├── install.sh                macOS 部署脚本
│   ├── linux-install.sh          Linux 部署脚本
│   └── config-bundle/
│       ├── CLAUDE.md             越狱核心（562 示例）
│       └── system-prompt.md      系统提示词
├── tools/
│   ├── ctf-website/              sqlmap/dirsearch/jwt_tool/tplmap
│   └── skills/mcp/               ReverseLabToolsMCP + GhidraMCP
├── kb/                           知识库（165 篇）
├── .claude/
│   ├── hooks/                    MCP 工具拦截 hook
│   └── workflows/                CTF 自动化流水线（5 个）
├── codex-files/                  OpenAI Codex 配置
├── hermes-files/                 Hermes 配置
└── opencode-files/               OpenCode 配置
```

## 备份位置

部署前自动备份到：`~/.claude/backups/tgtylab-*`

## 常见问题

**Q: 部署后没变化？**
A: 重启 Claude Code。

**Q: macOS 提示"无法验证"？**
A: 右键 `.command` → 打开 → 弹窗点"打开"。

**Q: Windows Defender 报毒？**
A: 误报。把项目文件夹加到排除项。

**Q: 想恢复原配置？**
A: 双击 `恢复备份.bat`。

## 许可

GPL-3.0 — 详见 [LICENSE](LICENSE)。

## 免责声明

本项目仅供学习交流使用。使用本项目造成的任何后果由使用者自行承担。
