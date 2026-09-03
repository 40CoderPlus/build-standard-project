# build-standard-project

面向 VibeCoding 的 Codex 工程 Skill：保留必要质量底线，同时避免把普通修复和优化升级成复杂工程流程。

V1.9 的核心原则：

- 普通 Bug、优化、UI 调整和重构默认走 Routine 快路径；
- Routine 只要求最小完整改动、最终 diff 走查和最相关单元测试；
- 只有明确的初始化、标准化或重建请求才走完整 Init；
- 技术与部署方案根据产品特性选择，默认推荐最小充分方案；
- Redis、队列、微服务、Kubernetes、多地域等复杂组件必须由用户明确选择；
- 额外流程和验证必须有实际风险依据，效率本身也是质量的一部分。
- 基础质量只保留常规格式、Lint、类型、测试、契约、迁移和构建，不生成指纹、Git diff 哈希、需求台账校验、Agent 文案校验或机器可读 AI Review 证明。
- 需求变更、优化和 Bug 使用一份简短的 `docs/changes.md` 记录；源码变更必须带直接相关测试，Bug 必须带回归测试，并由 CI 做轻量检查。
- 旧项目安装新 Skill 不等于项目规则已迁移；1.1—1.6 项目提供显式迁移检查，避免遗留 `quality:full`、覆盖率、指纹和 AI Review 继续拖慢小改动。
- 用户明确要求时，可按创建日期、固定类型词表和真实主题统一当前项目的对话标题；该模式只修改标题元数据。

## 工作模式

- **Routine（默认）**：Bug、优化、UI 修改、局部重构。
- **Init / Adopt**：仅在用户明确要求初始化、标准化、接入或重建时执行完整流程。
- **Audit**：只报告优先级明确的问题，不主动修改。
- **Release**：发布或高风险变更按受影响边界增加验证，不重复 Init。

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

真正的 Skill 位于 `skills/build-standard-project/`。仓库根目录只保存安装和开源说明。

## 安装到 Codex 与其他 Agent

### 使用 Codex Skill Installer

Windows PowerShell：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo 40CoderPlus/build-standard-project `
  --path skills/build-standard-project `
  --ref main
```

macOS / Linux：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo 40CoderPlus/build-standard-project \
  --path skills/build-standard-project \
  --ref main
```

官方 Codex Installer 只安装到 Codex 目录，并且在目标目录已存在时会停止。需要同时供 Claude、其他兼容 Agent 使用，或升级已有安装时，使用下面的仓库安装脚本。

### 克隆并安装或升级

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

安装脚本会在升级前分别备份旧版本，并同时安装到：

- Codex：`${CODEX_HOME:-~/.codex}/skills/build-standard-project`
- Claude Code：`${CLAUDE_CONFIG_DIR:-~/.claude}/skills/build-standard-project`
- 其他兼容 Agent：`${AGENTS_HOME:-~/.agents}/skills/build-standard-project`

Windows 下默认对应 `%USERPROFILE%\.codex\skills`、`%USERPROFILE%\.claude\skills` 和 `%USERPROFILE%\.agents\skills`。重新启动相应 Agent 或开启新任务后生效。

## 使用方式

普通任务直接描述需求即可；Skill 被调用后默认就是 Routine，无需反复强调“不执行 Init”。如需显式调用：

```text
使用 $build-standard-project 修复这个 Bug。
```

初始化或标准化项目时明确说明：

```text
使用 $build-standard-project 初始化这个项目。先根据产品特性提供最小充分方案和一个有理由的升级方案，由我选择后再生成。
```

审计但不修改：

```text
使用 $build-standard-project 审计当前仓库，只报告问题和证据。
```

统一当前项目的对话标题（TYPE 默认使用英文代码）：

这是“手动触发、自动执行”的能力：Skill 不会在后台定时运行，也不会在每次新建对话后自行改名；用户需要在当前任务中提出一次整理请求。触发后 Agent 会自动批量处理，无需逐个手工修改。

```text
使用 $build-standard-project 统一当前项目的对话标题，只改标题，不改项目名或其他状态。
```

标题规则为 `MMDD｜TYPE｜Topic`。日期严格取对话的 `createdAt` 并转换到 `Asia/Shanghai`；主题不明确时保留原名，不猜测。若明确要求中文 TYPE，则本次统一使用“功能 / 设计 / 修复 / 优化 / 发布 / 探索 / 文档 / 研究”。

Codex 在提供项目对话列表、创建时间和标题修改能力时可直接完成批量改名。Claude Code 或其他兼容 Agent 可以加载同一 Skill，但能否实际改名取决于宿主是否提供等价的会话管理能力。

如果希望已有工程长期采用 Routine 规则，可将 Skill 生成的精简规则合并进工程根目录 `AGENTS.md`。

## 技术与部署选择

Skill 不再假定所有项目使用同一套架构。Init 时会根据产品规模、团队、流量、数据、合规、预算和运维能力给出选择：

1. 最小充分方案；
2. 一个确有产品理由的升级方案；
3. 只有需求已经证明必要时才提供复杂方案。

用户确认前不会引入复杂基础设施。说明主要成本、限制和风险后，由用户决定产品、架构与运维取舍。

无论选择哪种架构，初始化都会直接建立不可关闭的工程基础：commit 格式与暂存文件格式/Lint 门禁、唯一变更记录、直接相关测试、Bug 回归测试，以及与技术栈匹配的 CI/发布命令。这些基础不作为可选架构问题反复询问。

## 质量策略

Routine 的固定底线：

1. 检查相关代码和约束；
2. 在唯一的变更记录中写清需求变更、优化或 Bug；
3. 完成最小完整改动，并补直接相关测试；
4. Bug 用能复现原问题的回归测试锁住；
5. 走查最终 diff，运行最相关的测试；
6. 只重跑失败或被后续修改影响的检查。

本地 Routine 必须优先运行单个受影响测试文件，例如：

```bash
pnpm test -- path/to/affected.test.ts
```

普通小改动不运行 `quality`、`quality:full`、覆盖率、E2E、视觉、部署或独立 Review。`quality:fast` 是 CI 或确实需要整套单元测试反馈时的后备命令。

每次 commit 前只检查相关暂存文件的格式与 Lint，并校验 Conventional Commit 信息。类型检查、测试、构建和 E2E 仍按改动风险执行，不塞进 commit 钩子。

安全、隐私、资金、权限、不可逆数据、迁移、公共契约、共享基础设施和发布边界按实际风险增加验证。普通任务只保留一份简短变更记录和直接相关测试，不要求平行需求台账、独立 Reviewer、Review 文件、全量 E2E、视觉测试或部署证据；高风险或发布审查直接记录在现有任务、PR 或 Issue 中。

## 给其他 AI Agent 使用

没有原生 Skill 发现能力的 Agent，可以先读取：

```text
skills/build-standard-project/SKILL.md
```

然后只读取该文件针对当前模式明确引用的 references。不要为 Routine 加载完整 Init 或 Release 流程。

## 生成项目

用户完成 Init 选择后，底层生成命令为：

```bash
python skills/build-standard-project/scripts/scaffold_project.py \
  --config path/to/project-profile.json \
  --output path/to/project
```

生成器只支持其明确声明的架构与部署模式；其他选择应使用针对该方案的实现，而不是强行套用复杂模板。

### 升级 1.1—1.6 生成的旧项目

安装或升级 Skill 只更新 Codex 的 Skill 目录，不会自动重写已有项目里的 `AGENTS.md`、`package.json` 和 CI。先只检查迁移计划：

```bash
python skills/build-standard-project/scripts/migrate_legacy_project.py \
  --project path/to/existing-project
```

确认识别的是旧版生成规则后，再显式应用：

```bash
python skills/build-standard-project/scripts/migrate_legacy_project.py \
  --project path/to/existing-project \
  --apply
```

迁移器只处理已知的 1.1—1.6 生成模板；遇到自定义 `AGENTS.md` 会停止，不会覆盖项目规则。
应用迁移后运行一次 `pnpm prepare`，即可启用仓库内的 commit 基础质量钩子。

仓库自身的轻量回归测试：

```bash
python -m unittest discover -s tests -v
```

## 更新

```bash
git pull --ff-only
```

然后重新运行 `install.ps1` 或 `install.sh`。旧安装会自动备份。

## 当前版本

`1.9.0`

本版本的需求与验证记录见 [CHANGELOG.md](CHANGELOG.md)。

## License

MIT
