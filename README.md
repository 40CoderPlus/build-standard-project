# build-standard-project

[简体中文](README.md) | [English](README.en.md)

面向 AI 辅助开发的工程 Skill，帮助 Codex、Claude Code 和其他兼容 Agent 建立项目基础，并在后续开发中遵循一致的工程规则。

它覆盖两个主要场景：**初始化时，根据产品需求选择合适的技术与部署方案；日常开发时，以最小完整改动、相关测试和简短变更记录完成任务。**

当前版本：`2.0.0` · [变更记录](CHANGELOG.md) · [MIT License](LICENSE)

## 你可以用它做什么

| 场景 | 提供的能力 | 触发方式 |
| --- | --- | --- |
| 日常开发 | 修复 Bug、优化、调整 UI、局部重构，按影响范围执行检查 | 默认使用 Routine 模式 |
| 初始化或接入项目 | 比较技术与部署方案，建立目录、工程规则、测试和 CI 基础 | 明确要求初始化、标准化、接入或重建 |
| 仓库审计 | 按优先级报告问题和证据 | 明确要求审计，默认不修改 |
| 发布准备 | 针对发布及高风险边界补充验证 | 明确要求发布相关工作 |
| 旧项目迁移 | 清理 1.1—1.6 生成项目中的旧版工程规则 | 明确要求迁移，支持先查看计划 |
| 对话整理 | 按统一格式批量修改当前项目的对话标题 | 手动触发，依赖 Agent 宿主能力 |

Skill 由 Agent 读取并执行。安装后不会自动初始化已有项目，也不会在后台定时运行。仓库内另附项目生成器和旧版迁移脚本，供相应流程使用。

## 安装与上手

### 1. 安装 Skill

先克隆仓库，再运行对应系统的安装脚本。需要本机具备 Git；脚本会同时安装到 Codex、Claude Code 和共享 Agent 技能目录，已有安装会分别备份。

**Windows PowerShell**

```powershell
git clone https://github.com/40CoderPlus/build-standard-project.git
cd build-standard-project
.\install.ps1
```

**macOS / Linux**

```bash
git clone https://github.com/40CoderPlus/build-standard-project.git
cd build-standard-project
chmod +x install.sh
./install.sh
```

| 使用方 | 默认安装位置 | 自定义根目录环境变量 |
| --- | --- | --- |
| Codex | `~/.codex/skills/build-standard-project` | `CODEX_HOME` |
| Claude Code | `~/.claude/skills/build-standard-project` | `CLAUDE_CONFIG_DIR` |
| 其他兼容 Agent | `~/.agents/skills/build-standard-project` | `AGENTS_HOME` |

Windows 下 `~` 对应 `%USERPROFILE%`。安装后重新启动相应 Agent 或开启新任务。

### 2. 在项目中使用

在目标项目的任务中明确调用，例如：

```text
使用 $build-standard-project 修复登录失败的问题。
```

Skill 被调用后，普通开发任务默认走 Routine，无需每次补充“不要初始化”。初始化、审计和其他操作的示例见下文。

没有原生 Skill 发现能力的 Agent，可以先读取本仓库的 `skills/build-standard-project/SKILL.md`，再按当前任务读取其中引用的文档。

### 3. 更新已安装的 Skill

在克隆的仓库中执行：

```bash
git pull --ff-only
```

然后重新运行 `install.ps1` 或 `install.sh`，并开启新任务。**更新 Skill 不会迁移已有项目中的工程规则**；旧版生成项目的处理方式见[旧项目迁移](#旧项目迁移)。

<details>
<summary>其他安装方式：仅使用 Codex Skill Installer</summary>

也可以使用本机 Codex 自带的安装器，需要 Python 和对应安装器脚本。此方式只安装到 Codex，目标目录已存在时会停止；升级已有安装请使用上面的仓库脚本。

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

</details>

## 日常开发：按改动范围完成任务

Routine 适用于 Bug 修复、优化、UI 调整和局部重构，基本流程是：

1. 读取相关代码、测试和项目约束。
2. 在现有变更记录中简述需求、优化或 Bug；生成项目统一使用 `docs/changes.md`。
3. 完成最小完整改动，为未覆盖的行为补充测试；非 Bug 改动可引用现有测试并说明 `existing coverage:` 理由，Bug 修复需要新增或更新回归测试。
4. 运行受影响的测试文件，走查最终 diff；只有检查失败或后续修改影响结果时才重跑。

例如，使用 pnpm 的项目优先运行单个相关测试文件：

```bash
pnpm test -- path/to/affected.test.ts
```

各类检查按用途分开：

| 时机 | 检查范围 |
| --- | --- |
| 日常小改动 | 直接相关测试和最终 diff；不默认运行全量质量检查、覆盖率、E2E 或视觉测试 |
| 提交代码 | 相关暂存文件的格式与 Lint，以及 Conventional Commit 提交信息 |
| CI | 执行与技术栈匹配的检查；对行为源码变更轻量检查变更记录与相关测试的关联 |
| 高风险变更或发布 | 根据安全、权限、资金、隐私、迁移、公共契约、基础设施或部署边界增加验证 |

`quality:fast` 用于 CI 或确实需要整套单元测试反馈的场景。类型检查、构建和 E2E 不塞进提交钩子；普通任务也不要求独立 Reviewer、Review 文件或部署证据。

## 初始化：先选择方案，再建立工程基础

明确提出初始化或标准化请求即可：

```text
使用 $build-standard-project 初始化这个项目。先根据产品需求推荐技术与部署方案，说明成本和限制，由我选择后再生成。
```

### 如何选择方案

Agent 会结合产品规模、团队、流量、数据、预算和运维约束，推荐最小充分方案；有实际需求依据时，再提供升级选项。用户作出选择，或明确授权 Agent 决定后，才进入生成步骤。

Redis、队列、独立 API、微服务、Kubernetes、多地域等组件只有在需求支持、且用户明确选择后才引入。已确认的决策会记录下来，没有新证据时不反复讨论。

### 初始化会交付什么

| 产物 | 用途 |
| --- | --- |
| `.project/standard-project.json` | 记录技术与部署选择、替代方案及重新评估的条件 |
| `AGENTS.md` | 项目统一工程规则与日常开发流程 |
| 应用代码与模块目录 | 按所选架构建立边界，不创建无用途的应用或基础设施包 |
| `docs/product/`、`docs/architecture/`、`docs/engineering/` | 说明产品约束、架构与工程使用方式 |
| `docs/changes.md` | 统一记录需求变更、优化、Bug 与相关测试 |
| 工具配置与 Git 钩子 | 建立格式、Lint、类型、测试、构建和提交规范 |
| CI、部署配置与环境变量示例 | 支持所选技术栈的验证、部署检查和恢复说明 |

提交检查、变更记录、直接相关测试、Bug 回归测试和 CI/发布命令属于初始化基础，随所选方案一起建立。初始化还需要实现并验证一条有代表性的完整业务流程，生成目录本身不代表产品已经完成。

### 内置生成器的范围

**当前内置生成器只支持 `modular-monolith`（模块化单体）与 `container-generic`（通用容器部署）的组合。** Skill 可以指导其他方案，但需要 Agent 针对该方案实现，或扩展生成器。

一般通过 Agent 完成初始化。需要直接调用脚本时，先参考[配置说明](skills/build-standard-project/references/project-profile.md)和[示例配置](skills/build-standard-project/assets/project-profile.example.json)，准备已经确认的配置，再从本仓库根目录运行：

```bash
python skills/build-standard-project/scripts/scaffold_project.py \
  --config path/to/project-profile.json \
  --output path/to/project
```

示例配置中的选型处于待确认状态，不能直接当作已批准方案。生成后，在目标项目中运行：

```bash
pnpm install
pnpm format
pnpm quality
```

详细流程见[初始化工作流](skills/build-standard-project/references/init-workflow.md)和[生成交付要求](skills/build-standard-project/references/generation-contract.md)。

## 其他使用场景

### 审计与发布

只检查仓库并报告问题：

```text
使用 $build-standard-project 审计当前仓库，只报告问题和证据。
```

为发布做准备：

```text
使用 $build-standard-project 检查本次发布涉及的风险和验证缺口。
```

审计默认不修改文件。发布流程围绕受影响边界开展验证，不重新执行初始化；详细规则见[质量检查](skills/build-standard-project/references/quality-checks.md)和[部署说明](skills/build-standard-project/references/deployment-system.md)。

### 旧项目迁移

适用于 **1.1—1.6 版本生成的项目**。如果更新 Skill 后，小改动仍被旧版 `quality:full`、覆盖率、指纹或 AI Review 规则拖慢，需要单独迁移项目内的 `AGENTS.md`、`package.json` 和 CI。

先查看迁移计划，此命令不修改项目：

```bash
python skills/build-standard-project/scripts/migrate_legacy_project.py \
  --project path/to/existing-project
```

确认后应用迁移：

```bash
python skills/build-standard-project/scripts/migrate_legacy_project.py \
  --project path/to/existing-project \
  --apply
```

迁移器只处理已知的旧版生成模板；遇到自定义 `AGENTS.md` 会停止。应用后在目标项目运行一次 `pnpm prepare`，启用仓库内的提交检查钩子。详见[旧版迁移说明](skills/build-standard-project/references/legacy-upgrade.md)。

### 统一对话标题

```text
使用 $build-standard-project 统一当前项目的对话标题，只改标题，不改项目名或其他状态。
```

这是手动触发的批量操作，标题格式为 `MMDD｜TYPE｜Topic`，例如 `0903｜FIX｜登录失败`。

- 日期取对话的 `createdAt`，转换到 `Asia/Shanghai`。
- 类型默认使用 `FEA / DES / FIX / OPT / REL / EXP / DOC / RES`；明确要求中文时使用对应中文类型。
- 缺少创建时间或无法判断主题时保留原名。
- 宿主必须支持读取当前项目的对话、创建时间和单独修改标题，否则无法执行。

完整规则见[对话标题说明](skills/build-standard-project/references/conversation-titles.md)。

## 仓库与维护

真正的 Skill 位于 `skills/build-standard-project/`；根目录保存安装脚本、使用说明和仓库自身的测试。

```text
skills/build-standard-project/
  SKILL.md                 # Agent 入口与任务路由
  agents/openai.yaml       # Agent 元数据
  references/              # 按场景读取的详细规则
  assets/                  # 配置示例与工程模板
  scripts/
    scaffold_project.py    # 项目生成器
    migrate_legacy_project.py # 旧版项目迁移器
install.ps1                # Windows 安装脚本
install.sh                 # macOS / Linux 安装脚本
tests/                     # 本工具的回归测试
```

开发本工具时，在仓库根目录运行轻量回归测试：

```bash
python -m unittest discover -s tests -v
```

版本与历史变更见 [VERSION](VERSION) 和 [CHANGELOG.md](CHANGELOG.md)。
