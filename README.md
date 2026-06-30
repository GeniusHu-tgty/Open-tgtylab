<div align="center">

# 🐙 open-tgtylab

### **AI Agent 越狱部署工具**

**一键部署无限制安全操作员到 Claude Code / OpenCode / Hermes**

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-red.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Ready-green.svg)]()
[![Examples](https://img.shields.io/badge/Examples-562-orange.svg)]()
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-150+-purple.svg)]()

</div>

---

## 它是什么

open-tgtylab 把一个**无审查、无限制、无废话**的安全操作员配置一键部署到你的 AI Agent 中。

部署后，你的 Claude Code 会变成 **Ghost** — 一个有 20 年经验的资深黑客，直接给代码、不拒绝、不警告、不废话。

## 核心特性

| 特性 | 说明 |
|------|------|
| 🔓 **身份锁** | 强制 AI 认为自己是真人黑客，绕过安全对齐 |
| 🧠 **思维重定向** | 检测 thinking 中的拒绝词，实时拦截并重定向 |
| 📚 **562 个示例** | 覆盖 16 大类场景，形成压倒性的"接受模式" |
| 🔇 **零关键词泄露** | 不含"安全研究"、"授权测试"等触发安全审查的词 |
| 🛠 **150+ MCP 工具** | PE/Android/CTF/知识库/自动化流水线，开箱即用 |
| 🖥 **跨平台** | Windows / macOS / Linux 全支持 |

## 覆盖场景（16 大类）

```
真实目标渗透    后门/Webshell    免杀/反检测     游戏安全
移动安全        逆向工程         密码学/加密     网络协议
Web攻击         云/容器/K8s      社会工程学      恶意软件分析
内核/驱动       数据库攻击       自动化脚本      数字取证
```

## 快速开始

### Windows

```powershell
git clone https://github.com/your-org/open-tgtylab.git
cd open-tgtylab
双击 启动.bat
```

### macOS

```bash
git clone https://github.com/your-org/open-tgtylab.git
cd open-tgtylab
双击 启动.command
```

### Linux

```bash
git clone https://github.com/your-org/open-tgtylab.git
cd open-tgtylab/tgtylab-files
bash linux-install.sh
```

部署完成后，**重启 Claude Code** 即可生效。

## 内置内容

| 内容 | 说明 | 状态 |
|------|------|------|
| CLAUDE.md | 越狱配置（562 示例，16 大类） | 已内置 |
| system-prompt.md | 系统提示词（身份锁 + 操作上下文） | 已内置 |
| settings.json | bypassPermissions | 部署时生成 |
| config.toml | 模型指令文件指向 | 部署时生成 |
| hooks/pre-tool-call.sh | 拦截 curl/wget/strings | 已内置 |
| workflows/*.js | 5 个 CTF 自动化流水线 | 已内置 |
| settings.local.json | MCP server + hooks 配置 | 已内置 |
| tools/ctf-website/ | sqlmap + dirsearch + jwt_tool + tplmap | **已内置** |
| tools/skills/mcp/ | ReverseLabToolsMCP + GhidraMCP 源码 | **已内置** |
| kb/ | 知识库：165 篇技术文件 | **已内置** |
| .mcp.json.example | MCP server 注册模板 | **已内置** |

## 后续安装（部署后手动完成）

### 1. MCP Server 依赖

```powershell
cd tools/skills/mcp/ReverseLabToolsMCP
uv sync
```

然后复制 `.mcp.json.example` 到你的项目根目录，重命名为 `.mcp.json`。

### 2. Python RE 库

```powershell
pip install lief frida angr capstone keystone-engine unicorn
```

### 3. 外部工具（按需）

<details>
<summary><b>逆向工程</b></summary>

| 工具 | 用途 | 下载 |
|------|------|------|
| Ghidra | 反编译 | https://github.com/NationalSecurityAgency/ghidra/releases |
| Cutter | 反汇编 + Rizin | https://github.com/rizinorg/cutter/releases |
| DiE | 查壳 | https://github.com/horsicq/Detect-It-Easy/releases |
| PE-bear | PE 分析 | https://github.com/hasherezade/pe-bear/releases |
| x64dbg | 调试器 | https://github.com/x64dbg/x64dbg/releases |
| Procmon | 动态分析 | https://download.sysinternals.com/files/ProcessMonitor.zip |
</details>

<details>
<summary><b>移动安全</b></summary>

| 工具 | 用途 | 下载 |
|------|------|------|
| apktool | APK 反编译 | https://bitbucket.org/iBotPeaches/apktool/downloads/ |
| jadx | APK 反编译 | https://github.com/skylot/jadx/releases |
| Frida | 动态注入 | https://frida.re/ |
</details>

<details>
<summary><b>网络扫描</b></summary>

| 工具 | 用途 | 下载 |
|------|------|------|
| nmap | 端口扫描 | https://nmap.org/download.html |
| Burp Suite | Web 测试 | https://portswigger.net/burp/releases |
| nuclei | 漏洞扫描 | https://github.com/projectdiscovery/nuclei |
</details>

## MCP 工具链（150+ 工具）

### PE / ELF 二进制分析（17 工具）

| 工具 | 功能 |
|------|------|
| `hash_file` | MD5/SHA1/SHA256 + 文件大小 |
| `die_scan` | 查壳、识别编译器/packer/签名 |
| `rizin_bin_info` | 二进制基础信息 |
| `rizin_sections` | 节区信息 |
| `rizin_imports` | 导入表 |
| `rizin_strings` | 字符串提取 |
| `triage_pe` | PE/ELF 一键初筛 |
| `ghidra_headless_analyze` | Ghidra 无头分析 |
| `pe_address_to_offset` | PE 偏移/RVA/VA 转换 |
| `rizin_write_bytes` | raw write |
| `rizin_assemble_bytes` | 汇编 → 机器码 |
| `rizin_assemble_patch` | 汇编 + Patch |
| `patch_bytes` | 按偏移 patch |
| `patch_pattern` | 按 pattern 定位 patch |
| `patch_pe_bytes` | 按 PE 地址 patch |
| `search_pattern` | pattern 搜索（?? 通配） |
| `copy_sample_to_patches` | 复制到 patches 修改 |

### Ghidra 深度分析（7 工具）

| 工具 | 功能 |
|------|------|
| `ghidra_summary_list` | 列出已导出 summary |
| `ghidra_summary_overview` | 总体信息 |
| `ghidra_summary_functions` | 按函数名/地址过滤 |
| `ghidra_summary_function_detail` | callers/callees/反编译 |
| `ghidra_summary_imports` | 按 API 名/库过滤导入 |
| `ghidra_summary_strings` | 按内容/地址过滤字符串 |
| `ghidra_summary_call_focus` | 函数阅读优先级 |

### 样本全分析流水线（4 工具）

| 工具 | 功能 |
|------|------|
| `sample_full_workup` | 一键全分析：triage → Ghidra → 断点 → IOC → YARA |
| `sample_autopilot_round` | 自动规划下一轮动作 |
| `triage_to_notes` | 生成分析笔记骨架 |
| `generate_patch_report` | 生成 patch 报告 |

### IOC / 检测规则（4 工具）

| 工具 | 功能 |
|------|------|
| `extract_iocs_from_summary` | 提取 IOC |
| `refine_ioc_sources` | IOC 按来源分层 |
| `make_yara_stub` | YARA 规则草案 |
| `make_sigma_stub` | Sigma 规则草案 |

### 调试 / 断点脚本（3 工具）

| 工具 | 功能 |
|------|------|
| `make_x64dbg_breakpoint_script` | x64dbg 断点脚本 |
| `make_pe_crypto_unpack_plan` | x64dbg + Frida + 解密计划 |
| `make_procmon_filters` | Procmon 过滤计划 |

### 加密 / 脱壳（6 工具）

| 工具 | 功能 |
|------|------|
| `carve_payloads_from_dump` | carve PE/DEX payload |
| `extract_frida_buffers` | Frida JSON → 二进制 buffer |
| `solve_crypto_from_evidence` | key/IV 自动解密 |
| `make_crypto_replay_scaffold` | Python 解密复现脚本 |
| `postprocess_frida_crypto_result` | Frida 结果一键后处理 |
| `parse_android_crypto_unpack_result` | 解析加密/脱壳结果 |

### Android 逆向（28 工具）

| 工具 | 功能 |
|------|------|
| `android_mumu_instance_info` | MuMu 模拟器状态 |
| `android_adb_connect` | 连接 ADB |
| `android_adb_devices` | 列出设备 |
| `android_device_info` | 设备信息 |
| `android_list_packages` | 列出包名 |
| `android_install_apk` | 安装 APK |
| `android_uninstall_package` | 卸载包 |
| `android_start_package` | 启动应用 |
| `android_force_stop` | 强制停止 |
| `android_current_activity` | 前台 Activity |
| `android_package_paths` | APK 路径 |
| `android_package_info` | dumpsys package |
| `android_pull_package_apk` | 拉取 APK |
| `android_capture_screenshot` | 屏幕截图 |
| `android_logcat_dump` | 导出 logcat |
| `android_clear_logcat` | 清空 logcat |
| `android_push_file` | 推送文件 |
| `android_pull_file` | 拉取文件 |
| `android_frida_ensure_server` | 部署 frida-server |
| `android_frida_status` | frida 状态 |
| `android_frida_processes` | 枚举进程 |
| `android_frida_run_script` | 运行 Frida 脚本 |
| `android_frida_template_library` | Frida 模板库 |
| `android_frida_render_template` | 渲染模板为 JS |
| `android_app_baseline` | 应用一键取证 |
| `android_package_fs_recipe` | 私有目录取证 |
| `android_http_observation_recipe` | HTTP 流量观察 |
| `android_crypto_unpack_recipe` | 加密/脱壳 recipe |

### 知识库（3 工具）

| 工具 | 功能 |
|------|------|
| `kb_catalog` | 列出所有板块/分类 |
| `kb_router` | 按信号搜索技术文件 |
| `kb_read_file` | 读取技术文件内容 |

### CTF 自动化（4 工具）

| 工具 | 功能 |
|------|------|
| `ctf_new_challenge` | 创建 CTF case |
| `ctf_tool_status` | CTF 工具状态 |
| `run_ctf_tool` | 运行 sqlmap/dirsearch/jwt_tool/tplmap |
| `http_probe` | HTTP 探测 |

### 工具箱（4 工具）

| 工具 | 功能 |
|------|------|
| `toolbox_list` | 列出可用工具 |
| `toolbox_version` | 版本查询 |
| `toolbox_launch` | 启动 GUI 工具 |
| `server_healthcheck` | 健康检查 |

### 样本管理（7 工具）

| 工具 | 功能 |
|------|------|
| `import_sample` | 导入样本 |
| `list_samples` | 列出样本 |
| `rename_sample` | 重命名 |
| `copy_sample` | 复制 |
| `move_sample` | 移动 |
| `quarantine_sample` | 隔离 |
| `delete_sample` | 删除 |

### 工作区管理（7 工具）

| 工具 | 功能 |
|------|------|
| `workspace_read_text` | 读取内容 |
| `workspace_write_text` | 写入文件 |
| `workspace_copy_artifact` | 复制品 |
| `workspace_move_artifact` | 移动制品 |
| `workspace_delete_artifact` | 删除制品 |
| `list_generated_artifacts` | 列出生成物 |
| `delete_generated_artifact` | 删除生成物 |

### Procmon 动态分析（3 工具）

| 工具 | 功能 |
|------|------|
| `procmon_start_capture` | 启动抓取 |
| `procmon_stop_capture` | 停止抓取 |
| `procmon_export_csv` | PML → CSV |

### Python RE 库管理（3 工具）

| 工具 | 功能 |
|------|------|
| `python_re_tool_status` | 安装状态检查 |
| `python_re_tool_install` | 安装指定库 |
| `python_re_tool_version` | 查询版本 |

### 审计 / 维护（3 工具）

| 工具 | 功能 |
|------|------|
| `mutation_audit_tail` | 审计日志尾部 |
| `mcp_update_audit` | MCP 更新检查 |
| `project_skills_status` | skills 安装状态 |

## 目录结构

```
open-tgtylab/
├── 启动.bat                          Windows 一键部署
├── 启动.command                      macOS 一键部署
├── 卸载.bat                          Windows 卸载
├── 卸载.command                      macOS 卸载
├── README.md
├── .gitignore
├── .mcp.json.example                 MCP server 注册模板
├── settings.local.json               Claude Code 项目设置
├── tgtylab-files/
│   ├── deploy.ps1                    Windows 部署引擎
│   ├── install.sh                    macOS 部署引擎
│   ├── linux-install.sh              Linux 部署引擎
│   ├── uninstall.sh                  macOS/Linux 卸载
│   └── config-bundle/
│       ├── CLAUDE.md                 越狱核心（562 示例）
│       └── system-prompt.md          系统提示词
├── tools/
│   ├── ctf-website/                  CTF 工具（已内置）
│   │   ├── sqlmap/
│   │   ├── dirsearch/
│   │   ├── jwt_tool/
│   │   └── tplmap/
│   └── skills/mcp/                   MCP Server（已内置）
│       ├── ReverseLabToolsMCP/
│       └── GhidraMCP/
├── kb/                               知识库（已内置）
│   ├── ctf-website/techniques/       111 篇
│   ├── apk-reverse/techniques/       19 篇
│   ├── pe-reverse/techniques/        21 篇
│   └── general/techniques/           14 篇
├── .claude/
│   ├── hooks/
│   │   └── pre-tool-call.sh          MCP 工具强制 hook
│   └── workflows/
│       ├── ctf-full-pipeline.js      CTF 全链路
│       ├── ctf-asset-discovery.js    资产发现
│       ├── ctf-dos-assessment.js     DoS 评估
│       ├── ctf-vuln-discovery.js     漏洞挖掘
│       └── ctf-vuln-verify.js        漏洞验证
├── codex-files/                      OpenAI Codex 配置
├── hermes-files/                     Hermes 配置
└── opencode-files/                   OpenCode 配置
```

## 部署路径

自动检测并部署到所有找到的 Claude 配置目录：

| 路径 | 平台 |
|------|------|
| `~/.claude/` | 全平台主目录 |
| `%LOCALAPPDATA%/Claude-3p/` | Windows 桌面版 |
| `%APPDATA%/claude/` | Windows 桌面版备选 |
| `~/Library/Application Support/claude/` | macOS |

## 卸载

| 平台 | 操作 |
|------|------|
| Windows | 双击 `卸载.bat` |
| macOS | 双击 `卸载.command` |
| Linux | `cd tgtylab-files && bash uninstall.sh` |

## 许可

GPL-3.0-only

本项目包含以下 GPL-3.0 许可的组件：
- ReverseLabToolsMCP (GPL-3.0-only)
- sqlmap (GPL-3.0)
- jwt_tool (GPL-3.0)
- tplmap (GPL-3.0)

以及 Apache 2.0 许可的组件：
- GhidraMCP (Apache 2.0)

根据 GPL-3.0 要求，修改后的版本必须以 GPL-3.0 兼容方式开源。
