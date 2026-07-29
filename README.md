# build-standard-project

面向纯 AI VibeCoding 的标准工程 Skill。它将已确认的产品设计、PRD、原型或架构说明转换为可开发、可测试、可审查、可部署和可恢复的全栈项目。

V1.1 的核心原则：

- 人工 Review 默认可选，不作为普通 VibeCoding 的阻塞条件；
- 独立 AI Review 强制执行；
- Blocker / High 未解决时禁止验收和发布；
- 新需求、优化、废弃和删除必须先落入 REQ/OPT 需求账本；
- 所有 Agent 共享根 `AGENTS.md`，避免不同模型各自解释规则；
- AI Review 报告绑定需求、验收标准、base/head、完整 Git diff、当前文件与删除文件。

## 适用范围

- 从产品设计或 PRD 创建标准项目；
- 为现有项目补齐工程规则、AI 规则、质量门禁和部署能力；
- 审计项目是否满足标准；
- 升级既有标准项目；
- 让 Codex、Claude Code、Gemini CLI、Cursor、GitHub Copilot 或其他编码 Agent 采用同一工程治理体系。

默认技术基线为 pnpm Workspace、Turborepo、Next.js、React、TypeScript、NestJS、PostgreSQL 和 Prisma。Worker、Redis、队列、后台应用等仅在产品需求满足触发条件时启用。

## 仓库结构

```text
skills/build-standard-project/
  SKILL.md
  agents/openai.yaml
  assets/
  references/
  scripts/scaffold_project.py
install.ps1
install.sh
```

真正的 Skill 位于 `skills/build-standard-project/`。仓库根目录只保存面向使用者的安装和开源说明，避免把 README、许可证等内容加载进 Agent Skill 上下文。

## 安装到 Codex

### 方法一：使用 Codex 官方 Skill Installer

Windows PowerShell：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo 40CoderPlus/build-standard-project `
  --path skills/build-standard-project
```

macOS / Linux：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo 40CoderPlus/build-standard-project \
  --path skills/build-standard-project
```

官方 Installer 在目标目录已存在时会停止，不会覆盖当前版本。升级已有安装时使用下面的仓库安装脚本。

### 方法二：克隆并安装或升级

Windows PowerShell：

```powershell
git clone https://github.com/40CoderPlus/build-standard-project.git
cd build-standard-project
.\install.ps1
```

macOS / Linux：

```bash
git clone https://github.com/40CoderPlus/build-standard-project.git
cd build-standard-project
chmod +x install.sh
./install.sh
```

安装脚本会：

1. 验证源目录存在 `SKILL.md`；
2. 使用 `$CODEX_HOME`，未设置时使用 `~/.codex`；
3. 升级前把旧版本移动为带时间戳的备份；
4. 将 Skill 安装到 `$CODEX_HOME/skills/build-standard-project`。

安装后从下一次 Codex 对话开始可用。

## 在 Codex 中使用

创建新项目：

```text
使用 $build-standard-project，根据已经确认的 PRD、产品设计和原型，
生成标准全栈项目。人工 Review 非阻塞，但必须完成独立 AI Review。
```

改造现有项目：

```text
使用 $build-standard-project 的 Adopt 模式，
在保留现有代码和用户改动的前提下补齐需求追踪、AGENTS.md、
质量门禁、CI、AI Review、容器部署和恢复流程。
```

只做审计：

```text
使用 $build-standard-project 的 Audit 模式检查当前仓库，
只输出缺口、风险和证据，不修改文件。
```

升级旧标准：

```text
使用 $build-standard-project 的 Refresh 模式升级当前工程标准，
先记录决策和迁移计划，再实施并完成独立 AI Review。
```

## 给其他 AI Agent 使用

Codex 会原生发现 `SKILL.md`。其他 Agent 若没有 Skill 自动发现机制，可以把仓库克隆到任意只读位置，并在任务开头使用：

```text
请先完整读取：
1. skills/build-standard-project/SKILL.md
2. 该文件针对本任务要求读取的 references

严格执行 Required workflow 和 Non-negotiable behavior。
生成项目后，以项目根 AGENTS.md 为唯一工程规则源。
所有新增、优化、废弃和删除必须先登记 REQ/OPT；
修改完成后必须通过自动化质量门禁和独立 AI Review。
人工 Review 可选，不作为默认阻塞条件。
```

也可以直接采用：

`skills/build-standard-project/references/bootstrap-prompt.md`

作为通用 System Prompt 或项目初始化 Prompt。

生成后的项目会提供以下 Agent 适配器：

| Agent | 规则入口 |
| --- | --- |
| Codex | `AGENTS.md` |
| Claude Code | `CLAUDE.md` → `AGENTS.md` |
| Gemini CLI | `GEMINI.md` → `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` → `AGENTS.md` |
| Cursor | `.cursor/rules/project.mdc` → `AGENTS.md` |
| 其他 Agent | 显式读取根 `AGENTS.md` |

## 生成项目

Agent 完成产品交接和项目 Profile 后，底层生成命令为：

```bash
python skills/build-standard-project/scripts/scaffold_project.py \
  --config path/to/project-profile.json \
  --output path/to/project
```

首次初始化：

```bash
pnpm install
pnpm format
pnpm quality
```

注意：生成的是生产级工程基础，不代表产品功能已经实现。产品功能必须继续按照“REQ/OPT → AC → 实现 → 测试 → AI Review → 发布证据”逐个垂直切片交付。

## 质量和 Review

普通 PR 使用 `pnpm quality`。AI 交付和发布使用 `pnpm quality:full`。

完整门禁可包含：

- format、lint、typecheck、真实 coverage；
- unit、integration、contract、migration drift；
- build、E2E、Firefox/WebKit、Accessibility、visual snapshot；
- secret scan、SAST、SBOM、dependency audit；
- requirement traceability；
- 强制 AI Review；
- deployment preflight、health、smoke 和 recovery。

AI Review 不能由实现 Agent 在同一推理过程内自我批准。优先使用独立 Agent；不可用时使用全新上下文。报告必须写入 `artifacts/ai-review/`，且旧报告不能批准修改后的代码。

## 更新

```bash
git pull --ff-only
```

然后重新运行 `install.ps1` 或 `install.sh`。旧安装会自动备份。

## 当前版本

`1.1.0`

第三轮独立 AI Review 结果：0 Blocker、0 High。

## License

MIT
