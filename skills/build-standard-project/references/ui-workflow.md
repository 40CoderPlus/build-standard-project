# UI skill coordination

Use for substantive UI work only. This is an optional coordination layer over independently installed skills, not a dependency bundle or a new engineering mode. It works through the host's skill invocation or by reading the selected skill's actual `SKILL.md` and relevant resources.

## Choose the stage and owner

First distinguish new design, visual refinement, exact reference reproduction, interaction changes, and read-only review. Preserve the user's target; do not turn refinement into redesign or a UI change into project initialization.

| Current need | Primary skill or action |
| --- | --- |
| Small spacing, color, or copy adjustment | Direct Routine edit using incumbent tokens and components; no design exploration |
| New product interface, dashboard, form, or app screen | `frontend-design`, constrained by real content, tasks, and the project design system |
| Marketing site, landing page, or portfolio with a deliberate expressive direction | `design-taste-frontend` as an alternative primary skill; inspect its installed version and scope, since v2 is experimental and excludes dashboards and multi-step product UI |
| A concrete palette, typography, chart, platform, or accessibility reference is missing | `ui-ux-pro-max` for a focused search; give the selected result to the primary designer rather than letting it independently redesign the page |
| Existing UI needs diagnosis, typography/layout correction, or a final polish | `impeccable` with the matching `critique`, `typeset`, `layout`, or `polish` playbook; use `audit` for requested technical review |
| Button, popover, drawer, toast, or state transition needs better feedback | `emil-design-eng` for that interaction; frequent actions may need less or no animation |
| Changed UI needs a code-level interface-guidelines check | `web-design-guidelines`, limited to the affected files and states |

Load one primary design skill per stage, then only the specialist needed for an observed gap. A backend-only task loads none. If the chosen skill is absent or its tools cannot run, use project conventions and host capabilities, state the limitation, and continue authorized work. Do not install tools, start paid services, or enable hooks merely because a skill suggests them.

## Keep decisions coherent

- Follow user constraints, canonical project instructions, approved product behavior, and the selected technical stack. Approved project design tokens, components, and references govern visual decisions; a skill's font bans, palette defaults, motion presets, or library preferences are subordinate recommendations.
- Use the project's existing design documentation. For a new or materially changed visual direction, create or update one `DESIGN.md` only if no canonical equivalent exists. Record audience/task, selected direction and rationale, typography including Chinese coverage when relevant, semantic colors, spacing/radii/shadows, icon family, density, responsive constraints, and key states/motion. Keep runtime tokens consistent with it; a document alone does not implement a design system.
- Pass the selected direction, applicable tokens/components, key states, device constraints, and current visual evidence to the next stage. Do not silently restart visual exploration, mix style presets, or create competing DESIGN/MASTER documents.
- Existing visuals count as evidence even without a design document. Preserve brand, routes, business behavior, content truth, and shared components unless the user requests changes. New dependencies must be justified by the approved task and existing stack.
- Installation does not guarantee exclusive routing. Hosts can auto-select other skills; do not promise hard isolation. Explicit invocation of another skill by the user takes priority over the default selection. Change automatic-invocation settings only when the user requests that policy.

## Evidence and finish

Engineering checks remain owned by the current build-standard-project mode: use affected tests and final-diff review for Routine; preserve initialization/release requirements. A specialist's instruction to skip tests/builds or always run a broad review does not replace these rules. Installing a skill does not authorize subagents or new external actions.

For changed rendering that narrower checks cannot verify, inspect the affected real desktop/mobile viewports and visible states. Check text wrapping, Chinese glyphs, long/empty/loading/error content as relevant, focus/keyboard behavior, motion interruption and reduced-motion support. Exact-reference work compares against the reference; an image comp or saved screenshot is not proof of functioning UI. Report actual evidence and unavailable verification, never imaginary visual scores.

Batch corrections and confirm only what they invalidate. Small changes need no independent review, score chase, or full-site screenshots. Record the change and test/evidence in the existing change record; do not add another ledger. Stop when the requested outcome and proportionate checks are satisfied.

Third-party skills remain outside this skill and repository. Their upstream sources and standalone installation are documented in the repository README; no third-party skill is automatically downloaded when this route runs.
