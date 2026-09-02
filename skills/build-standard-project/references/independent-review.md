# Independent review

Use an independent review only for release work, a materially affected high-risk boundary, or an explicit user or policy request. Routine fixes and initialization scaffolds use the implementing agent's final-diff review plus relevant tests.

High-risk boundaries include authorization, privacy, money, irreversible data, migrations, public contracts, shared infrastructure, deployment, and product-AI governance.

## Review method

Prefer a separate reviewer or fresh context. Give it the requirement or intended behavior, the raw final diff, affected contracts or migrations, and the checks actually run. Do not steer it toward a desired verdict.

Ask the reviewer to focus on the affected risks rather than exhaustively scoring every engineering category. Findings should state severity, concrete file/line evidence, impact, and a recommended action.

- `blocker`: unsafe, destructive, unauthorized, corrupting, or fundamentally off-spec.
- `high`: likely security/privacy failure, data loss, broken contract, or missing critical recovery.
- `medium`: meaningful bounded defect or test gap.
- `low`: optional improvement.

Resolve blocker/high findings before the relevant release or high-risk change is accepted. Rerun only checks invalidated by the fix.

## Evidence

Record the review in the existing task, pull request, or issue. A short Markdown summary is enough: reviewer/context, reviewed diff or files, checks considered, findings, resolutions, and verdict.

Do not create custom proof, schema, or validator machinery unless an external compliance policy explicitly requires it. Such machinery adds ceremony without proving reviewer independence.

Never fabricate reviewer identity, commands, findings, or test evidence.
