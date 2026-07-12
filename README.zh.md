<div align="center">

# 🐙 open-tgtylab

> 一键部署的安全研究工具包

150+ MCP 工具 · 208 篇知识库 · 15 条自动化流水线 · 9 个逆向工具自动下载

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-red.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20WSL-blue.svg)]()
[![MCP Tools](https://img.shields.io/badge/MCP_Tools-150+-9cf.svg)]()
[![Knowledge Base](https://img.shields.io/badge/KB-208%20Articles-brightgreen.svg)]()
[![Pipelines](https://img.shields.io/badge/CTF_Pipelines-15-orange.svg)]()

</div>

---

> [English version](README.md)

## 特性

- 🔧 150+ MCP 自动化工具（PE 逆向 / Android / CTF / 加密 / 调试）
- 📚 208 篇技术知识库（Web / APK / PE / 密码学 / 游戏安全）
- 🔄 15 条 CTF 流水线（全链路 / 24h 无人值守 / 攻击路由 / 专项攻击）
- 🛠 9 个逆向工具自动下载（Ghidra / Cutter / x64dbg / DiE / PE-bear / Procmon / nmap / apktool / jadx）
- 🖥 全平台支持（Windows / macOS / Linux / WSL）
- 💾 自动备份现有配置
- ✅ 一键部署，自动检测所有配置目录

## 快速开始

### Windows

双击 `启动.bat` 一键部署。

### macOS

```bash
chmod +x tgtylab-files/install.sh
./tgtylab-files/install.sh
```

### Linux

```bash
chmod +x tgtylab-files/linux-install.sh
./tgtylab-files/linux-install.sh
```

### 使用

部署完成后，**用 AI 工具打开 `Open-tgtylab` 目录**：

- **Claude Code**：`cd Open-tgtylab` 后启动会话
- **Codex App**：直接打开 `Open-tgtylab` 文件夹
- **Hermes / OpenCode**：自动配置，重启生效

> ⚠️ 必须在 `Open-tgtylab` 目录内使用，不要在其他目录打开。M 工具和知识库的路径都是相对于项目根目录的。

## 路由

```
信号 → kb_router(board=) → kb_read_file → 技术文档 → MCP 工具映射 → 执行
```

| 信号类型 | Board | KB 分类/文件 | MCP 工具族 |
|---------|-------|-------------|-----------|
| HTTP/Web/API/CVE/Cloud | `ctf-website` | 26/118 | `http_probe` `run_ctf_tool` `kb_router` |
| APK/DEX/SO/Frida/Java | `apk-reverse` | 8/20 | `android_app_baseline` `android_crypto_unpack_recipe` `android_frida_*` |
| PE/x64/x86/malware/driver | `pe-reverse` | 9/22 | `triage_pe` `ghidra_headless_analyze` `make_x64dbg_breakpoint_script` `sample_full_workup` |
| Crypto/Protocol/Cheat/IoT/Radio | `general` | 5/17 | `die_scan` `ghidra_*` `rizin_*` `python_re_tool_*` |

## 知识库

```
kb/
├── ctf-website/techniques/   26 类 118 篇 — Web 安全全覆盖
├── apk-reverse/techniques/    8 类  20 篇 — APK/DEX 逆向
├── pe-reverse/techniques/     9 类  22 篇 — PE 二进制分析
├── general/techniques/        5 类  17 篇 — 密码学/协议/内核/游戏安全
└── windows/techniques/        1 类   2 篇 — Windows 安全
```

## 目录约定

```
samples/      → 原始样本 + _quarantine/ + unpacked/
exports/      → 工具输出
patches/      → Patch 产物
notes/        → 分析笔记
reports/      → 最终报告
scripts/      → 自动化脚本
kb/           → 知识库
tools/        → 工具链
cases/        → 轻量索引
```

## 系统要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| **操作系统** | Windows 10/11 / macOS 12+ / Linux | WSL 自动检测 |
| **Python** | 3.11+ | MCP 工具运行环境 |
| **Git** | 任意版本 | clone 项目 |
| **PowerShell** | 5.1+（Windows） | 部署脚本 |
| **uv** | 任意版本 | Python 包管理器（自动安装） |

| AI 工具 | 状态 |
|---------|------|
| Claude Code | ✅ 完整支持 |
| Codex App | ✅ 完整支持 |
| Hermes | ✅ 完整支持 |
| OpenCode | ✅ 完整支持 |

| 兼容性 | 状态 |
|--------|------|
| Windows 11 / 10 / 8 / 7 | ✅ |
| WSL (Ubuntu/Debian) | ✅ 自动检测 |
| macOS 12+ | ✅ |
| Linux (Ubuntu/Debian/Arch) | ✅ |
| 中文路径 | ✅ |
| 空格路径 | ✅ |
| 非管理员 | ✅ |

## 其他操作

| 操作 | Windows | macOS / Linux |
|------|---------|---------------|
| 卸载 | 双击 `卸载.bat` | `./tgtylab-files/uninstall.sh` |
| 验证 | 双击 `验证.bat` | 检查 `~/.claude/CLAUDE.md` 是否存在 |
| 恢复 | 双击 `恢复备份.bat` | 手动复制 `~/.claude/backups/tgtylab-*` |

## 备份位置

部署前自动备份到：`~/.claude/backups/tgtylab-*`

恢复备份：把备份目录里的文件复制回 `~/.claude/` 即可。

## 文件结构

```
open-tgtylab/
├── 启动.bat                       Windows 一键部署
├── 启动.command                   macOS 一键部署
├── 卸载.bat / 验证.bat / 恢复备份.bat
├── tgtylab-files/
│   ├── deploy.ps1                 Windows 部署引擎
│   ├── install_tools.ps1          逆向工具下载器
│   ├── install.sh / linux-install.sh / uninstall.sh
│   └── config-bundle/
│       ├── CLAUDE.md              研究协议（562 示例）
│       └── system-prompt.md       系统提示词
├── tools/
│   ├── ctf-website/               CTF 工具 + 字典 + payload
│   ├── skills/mcp/                MCP Server（150+ 工具）
│   ├── common/                    Ghidra（自动下载）
│   ├── windows/                   x64dbg/DiE/PE-bear/Procmon（自动下载）
│   └── android/                   apktool/jadx（自动下载）
├── kb/                            知识库（208 篇）
├── .claude/                       Claude Code 配置 + 流水线 + skills
├── .codex/                        Codex 配置
├── AGENTS.md                      Agent 操作协议
├── AI-USAGE.md                    任务路由
├── codex-files/                   Codex 配置模板
├── hermes-files/                  Hermes 配置
└── opencode-files/                OpenCode 配置
```

## 兼容性

| 系统 | 状态 |
|------|------|
| Windows 11 | ✅ |
| Windows 10 | ✅ |
| macOS 12+ | ✅ |
| Linux (Ubuntu/Debian/Arch) | ✅ |
| 中文路径 | ✅ |
| 空格路径 | ✅ |

## 许可

GPL-3.0-only. 详见 [LICENSE](LICENSE)。

## 免责声明

本项目仅供学习交流和授权安全研究使用。使用者应确保在合法授权范围内使用本项目，使用本项目造成的任何后果由使用者自行承担。

详见 [DISCLAIMER.md](DISCLAIMER.md)。

## Hunter MCP 协同

OpenTgtyLab 通过唯一完整 MCP 名称 `hunter_tools` 接入独立的 [Hunter](https://github.com/GeniusHu-tgty/Hunter) 仓库，共享 case state、项目知识库、evidence、notes 与 reports，同时保持和 `reverse_lab_tools` 的职责边界。

详见 `docs/hunter-tools-integration.md`，验证命令：

```bash
python scripts/misc/verify_hunter_tools_integration.py
```
