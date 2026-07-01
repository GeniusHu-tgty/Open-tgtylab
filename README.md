<div align="center">

# 🐙 open-tgtylab

### **AI Agent 越狱部署工具**

**让你的 Claude Code / Codex / OpenCode / Hermes 变成无限制的安全研究助手**

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-red.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Examples](https://img.shields.io/badge/Examples-562-orange.svg)]()
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-150+-purple.svg)]()
[![Knowledge Base](https://img.shields.io/badge/Knowledge%20Base-165%20Articles-green.svg)]()

</div>

---

降低 AI 对你的所有限制，直接给代码、不拒绝、不警告、不废话。

## 核心特性

| 特性 | 说明 |
|------|------|
| 🔓 **身份锁** | 强制 AI 认为自己是真人黑客，绕过安全对齐 |
| 🧠 **思维重定向** | 检测 thinking 中的拒绝词，实时拦截并重定向 |
| 📚 **562 个示例** | 覆盖 16 大类安全场景，形成压倒性的"接受模式" |
| 🛠 **150+ MCP 工具** | PE 分析、Android 逆向、CTF 自动化、知识库 |
| 📖 **165 篇知识库** | Web 攻击、逆向工程、密码学、恶意软件分析 |
| 🔄 **5 个流水线** | CTF 全链路：资产发现 → 漏洞挖掘 → 漏洞验证 |
| 🐍 **CTF 工具内置** | sqlmap / dirsearch / jwt_tool / tplmap |
| 🖥 **跨平台** | Windows 7+ / macOS / Linux，中文路径 ✅ |

## 覆盖场景（16 大类）

```
真实目标渗透    后门/Webshell    免杀/反检测     游戏安全
移动安全        逆向工程         密码学/加密     网络协议
Web攻击         云/容器/K8s      社会工程学      恶意软件分析
内核/驱动       数据库攻击       自动化脚本      数字取证
```

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
| WSL (Ubuntu/Debian) | ✅ 自动检测 |
| macOS 12+ | ✅ |
| Linux | ✅ |
| 中文路径 | ✅ |
| 空格路径 | ✅ |
| 非管理员 | ✅ |

## 系统要求

- Claude Code / Codex / OpenCode / Hermes（任一）
- Windows 7+ / macOS / Linux
- Git、Python 3.11+

## MCP 工具链（150+ 工具）

| 类别 | 工具数 | 核心能力 |
|------|--------|---------|
| PE/ELF 分析 | 17 | triage、Ghidra 反编译、Rizin 反汇编、patch |
| Ghidra 深度分析 | 7 | 函数/导入/字符串查询、call focus |
| 样本全分析 | 4 | 一键：triage → Ghidra → 断点 → IOC → YARA |
| IOC/检测规则 | 4 | YARA/Sigma 草案生成、IOC 提取 |
| 调试/断点 | 3 | x64dbg 脚本、Procmon 过滤、解密计划 |
| 加密/脱壳 | 6 | 自动解密、buffer 提取、PE/DEX carve |
| Android 逆向 | 28 | ADB、Frida 注入、私有目录取证、流量观察 |
| 知识库 | 3 | 165 篇技术文件，按信号搜索 |
| CTF 自动化 | 4 | sqlmap/dirsearch/jwt_tool/tplmap |
| 样本管理 | 7 | 导入/复制/移动/隔离/删除 |
| Procmon | 3 | 启停抓取、PML 导出 CSV |
| Python RE | 3 | lief/frida/angr/capstone/keystone/unicorn |

## 知识库（165 篇）

| 板块 | 篇数 | 覆盖内容 |
|------|------|---------|
| ctf-website | 111 | JWT/SQLi/XSS/SSRF/SSTI/OAuth/GraphQL/支付/... |
| pe-reverse | 21 | 壳分析/AOB/断点/脱壳/YARA/... |
| apk-reverse | 19 | Frida/IL2CPP/加密/协议/脱壳/... |
| general | 14 | 密码学/协议逆向/游戏安全/方法论 |

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
