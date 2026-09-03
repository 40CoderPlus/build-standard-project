# Conversation title normalization

Use this route only when the user explicitly asks to rename or normalize conversation, task, or thread titles in the current project. It is a metadata-only operation, not a repository change.

## Scope and safety

- Resolve the exact current project from the calling conversation's project context, then include only conversations assigned to that project.
- Read titles, summaries, timestamps, and conversation content only as needed to determine accurate names.
- Change only each conversation's title field. Never change the project name, conversation content, project assignment, order, pin state, archive state, or any other metadata.
- If the host cannot list the current project's conversations, expose `createdAt`, or update a title without other side effects, report that limitation and make no changes.

## Title format

Use `MMDD｜TYPE｜Topic`, with the full-width separator `｜` (U+FF5C) and no surrounding spaces.

- Derive `MMDD` from the conversation's `createdAt` converted to `Asia/Shanghai`. Never use `updatedAt`. If `createdAt` is missing or invalid, keep the original title.
- Use exactly one TYPE vocabulary across the entire run. Default to the English code; use Chinese labels only when the user explicitly requests Chinese:

  | English | Chinese | Meaning |
  | --- | --- | --- |
  | `FEA` | `功能` | feature |
  | `DES` | `设计` | design |
  | `FIX` | `修复` | bug fix |
  | `OPT` | `优化` | optimization |
  | `REL` | `发布` | release |
  | `EXP` | `探索` | exploration |
  | `DOC` | `文档` | docs |
  | `RES` | `研究` | research |

- Make Topic a short, specific summary of what the conversation is actually about. Do not repeat the project name.
- Prefer the conversation's primary language for Topic unless the user requests another language.
- If either TYPE or Topic cannot be determined from the available evidence, keep the complete original title. Do not guess or partially rename it.

## Execution

1. Gather the current project's conversations and their `createdAt` values. Read ambiguous conversations only as far as needed to classify them.
2. Choose English or Chinese TYPE labels once for the run; English is the default.
3. Build the proposed old-to-new title mapping. Leave already-correct titles and uncertain conversations unchanged.
4. Apply title-only updates with the host's narrowest conversation-management tool.
5. Report the changed mapping and any titles kept because required metadata or topic evidence was unavailable.

Examples using the default English codes:

- `0903｜OPT｜批次文字显示`
- `0902｜REL｜生产包 CID 验证`
- `0901｜FIX｜TTS 加载卡住`
