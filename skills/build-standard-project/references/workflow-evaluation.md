# Workflow evaluation

Use only for an explicitly requested comparison of model or engineering-rule changes. Keep this separate from application CI and Routine work. Do not claim a model upgrade improved this Skill without measured results.

## Representative tasks

Select small, real fixtures from repository history and define acceptance criteria before execution:

| Task | Observable acceptance |
| --- | --- |
| Scoped bug | Original failure reproduced, fix passes regression, unrelated behavior preserved |
| Behavior-preserving optimization | Existing tests cover the invariant; explanation names the scenario; no cosmetic test edit |
| UI adjustment | Requested screen/state renders correctly at relevant size and interaction; only justified checks run |
| Cross-module feature | One complete user flow works across affected boundaries, including relevant failure states |
| Authorization change | Allowed and denied actions behave correctly; focused risk checks run |
| Mid-task correction | A scripted correction arrives at the same milestone; final result includes it and retains earlier constraints |

Use isolated copies of the same starting revision, the same inputs, acceptance checks, tool permissions, and comparable environments. Compare one variable at a time: old/new rules under the same model, or old/new model under the same rules. Record the model and reasoning setting actually used; do not silently change the user's selection. Use only available host capabilities and separately authorized external actions.

## Record and decide

Keep results in one existing task, issue, or release note. For each run record acceptance outcome, elapsed time, available token usage, tool calls, unnecessary confirmations/checks, and rework. Mark unavailable metrics and blocked runs explicitly; do not count them as zero or success.

Start with one paired run per selected task. Repeat only ambiguous or variable results before making performance claims. Keep the raw outcome and actual checks alongside the conclusion. Accept a rule change when correctness is preserved and the intended friction decreases; investigate regressions before adoption. A written scenario list is an evaluation method, not evidence that evaluation has run.
