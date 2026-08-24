# build-standard-project

面向 VibeCoding 的 Codex 工程 Skill：保留必要质量底线，同时避免把普通修复和优化升级成复杂工程流程。

V1.6 的核心原则：

- 普通 Bug、优化、UI 调整和重构默认走 Routine 快路径；
- Routine 只要求最小完整改动、最终 diff 走查和最相关单元测试；
- 只有明确的初始化、标准化或重建请求才走完整 Init；
- 技术与部署方案根据产品特性选择，默认推荐最小充分方案；
- Redis、队列、微服务、Kubernetes、多地域等复杂组件必须由用户明确选择；
- 额外流程和验证必须有实际风险依据，效率本身也是质量的一部分。

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

## 安装到 Codex

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

官方 Installer 在目标目录已存在时会停止。升级已有安装时使用仓库安装脚本。

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

安装脚本会在升级前备份旧版本，并安装到 `$CODEX_HOME/skills/build-standard-project`。重新启动 Codex 或开启新任务后生效。

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

如果希望已有工程长期采用 Routine 规则，可将 Skill 生成的精简规则合并进工程根目录 `AGENTS.md`。

## 技术与部署选择

Skill 不再假定所有项目使用同一套架构。Init 时会根据产品规模、团队、流量、数据、合规、预算和运维能力给出选择：

1. 最小充分方案；
2. 一个确有产品理由的升级方案；
3. 只有需求已经证明必要时才提供复杂方案。

用户确认前不会引入复杂基础设施。说明主要成本、限制和风险后，由用户决定产品、架构与运维取舍。

## 质量策略

Routine 的固定底线：

1. 检查相关代码和约束；
2. 完成最小完整改动；
3. 走查最终 diff；
4. 运行最相关的单元测试；
5. 只重跑失败或被后续修改影响的检查。

安全、隐私、资金、权限、不可逆数据、迁移、公共契约、共享基础设施和发布边界按实际风险增加验证。普通任务默认不要求 REQ/OPT、独立 Reviewer、AI Review 报告、全量 E2E、视觉测试或部署证据。

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

## 更新

```bash
git pull --ff-only
```

然后重新运行 `install.ps1` 或 `install.sh`。旧安装会自动备份。

## 当前版本

`1.6.0`

## License

MIT
