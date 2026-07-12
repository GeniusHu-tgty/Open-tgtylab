# Hunter / Open-tgtylab 多 Agent 路径清单

更新时间：2026-07-12

## 正式 Git 仓库

- Hunter（正式工作树 / 已推送 main）：`C:\Users\Administrator\.agents\skills\hunter`
- Open-tgtylab（正式 Git 工作树 / 已推送 main）：`D:\Open-tgtylab-repo`
- Open-tgtylab（本机运行工作区、cases/KB/exports）：`D:\Open-tgtylab`

## 核心实现

- Hunter MCP 入口：`C:\Users\Administrator\.agents\skills\hunter\mcp_server.py`
- Hunter Workflow Kernel：`C:\Users\Administrator\.agents\skills\hunter\core\workflow`
- Hunter 集成契约：`C:\Users\Administrator\.agents\skills\hunter\integration-contract.json`
- Hunter Skill：`C:\Users\Administrator\.agents\skills\hunter\SKILL.md`
- Hunter 测试：`C:\Users\Administrator\.agents\skills\hunter\tests`

- Workflow State v2 Schema：`D:\Open-tgtylab-repo\schemas\workflow-state-v2.schema.json`
- Workflow Event v1 Schema：`D:\Open-tgtylab-repo\schemas\workflow-event-v1.schema.json`
- Workflow State/Event 工具：`D:\Open-tgtylab-repo\scripts\misc\workflow_state.py`
- 多客户端 Session Checkpoint：`D:\Open-tgtylab-repo\scripts\misc\session_checkpoint.py`
- Hunter 生命周期管理器：`D:\Open-tgtylab-repo\scripts\misc\hunter_tools_manager.py`
- 集成验证器：`D:\Open-tgtylab-repo\scripts\misc\verify_hunter_tools_integration.py`
- 统一工作流文档：`D:\Open-tgtylab-repo\docs\hunter-unified-workflow.md`

## 本机运行与配置

- Codex 全局配置：`C:\Users\Administrator\.codex\config.toml`
- Codex 全局目录：`C:\Users\Administrator\.codex`
- 全局 Agent Skills：`C:\Users\Administrator\.agents\skills`
- Open-tgtylab 项目 Codex 配置：`D:\Open-tgtylab\.codex\config.toml`
- Open-tgtylab 项目 MCP 配置：`D:\Open-tgtylab\.mcp.json`
- Open-tgtylab 项目 Skills：`D:\Open-tgtylab\.codex\skills`
- 当前 Hunter Case：`D:\Open-tgtylab\cases\hunter-skill\state.json`
- 当前架构设计笔记：`D:\Open-tgtylab\notes\hunter-unified-ctf-reverse-pentest-workflow.md`

## Open-tgtylab 数据目录

- Cases：`D:\Open-tgtylab\cases`
- Knowledge Base：`D:\Open-tgtylab\kb`
- Samples：`D:\Open-tgtylab\samples`
- Evidence：`D:\Open-tgtylab\exports\evidence`
- Notes：`D:\Open-tgtylab\exports\notes`
- Reports：`D:\Open-tgtylab\exports\reports`
- Checkpoints：`D:\Open-tgtylab\exports\checkpoints`

## 参考研究仓库

- codex-session-patcher：`D:\external-research\codex-session-patcher`
- ReiPenFlow：`D:\external-research\ReiPenFlow`
- reverse-flow-skill 只读副本：`C:\Users\Administrator\AppData\Local\Temp\hunter-readonly-research\reverse-flow-skill`

## GitHub

- Hunter：`https://github.com/GeniusHu-tgty/Hunter`
- Open-tgtylab：`https://github.com/GeniusHu-tgty/Open-tgtylab`

其他 Agent 开始任务时应优先读取：

1. `D:\Open-tgtylab\AGENTS.md`
2. `D:\Open-tgtylab\cases\<slug>\state.json`
3. `C:\Users\Administrator\.agents\skills\hunter\SKILL.md`
4. `D:\Open-tgtylab-repo\docs\hunter-unified-workflow.md`
