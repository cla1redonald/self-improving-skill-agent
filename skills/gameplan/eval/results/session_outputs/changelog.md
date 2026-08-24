# Changelog — /gameplan SKILL.md self-improvement loop

## Round 0 (baseline, no edits)
- **Pass rate:** 6/7 (86%)
- **Command:** `python3 run_eval.py --skill /workspace/work/SKILL.md --cases /workspace/eval/cases.json --model claude-haiku-4-5 --out /workspace/eval_results/round_0.json`
- **Failure:** `auth_rework_high` failed rule `has_risks_with_mitigation` ("no '## Risks' section found").
  Inspection of the raw output showed the model produced a very long, heavily
  padded 24-step plan — each step carrying its own What/Why/Dependencies/Details
  sub-bullets — and hit the harness's `max_tokens=4000` cap partway through the
  `## Dependencies` section, before ever reaching `## Risks`. The plan content
  itself was fine; the failure was a token-budget/verbosity problem specific to
  large (High/Medium-High complexity) plans.

## Round 1
- **Mutation strategy:** Add an explicit constraint the instructions currently
  omitted — a "Keep It Concise" rule enforcing that `## Dependencies` and
  `## Risks` are mandatory regardless of plan size, that each step should be
  1-2 lines (no per-step Dependencies/Details/Why sub-bullet pattern), that
  large plans should use phase headers with terse one-line steps rather than
  padding, and that if the model notices it's running long it should compress
  remaining content and go straight to Dependencies/Risks rather than omitting
  them.
- **Rule(s) targeted:** `has_risks_with_mitigation` (and indirectly
  `has_dependencies_section`) on `auth_rework_high` / High-complexity cases.
- **Diagnosis:** Pattern, not one-off — any sufficiently large plan risked the
  same truncation-before-Risks failure, since the template itself didn't cap
  per-step verbosity or explicitly prioritize which sections must survive if
  output space runs short.
- **Before pass rate:** 6/7 (86%) — round_1_before.md is the round-0 SKILL.md.
- **After pass rate:** 7/7 (100%) — `python3 run_eval.py --skill /workspace/work/SKILL.md --cases /workspace/eval/cases.json --model claude-haiku-4-5 --out /workspace/eval_results/round_1_after.json`
- **Outcome:** **kept.** All 7 cases pass, including `auth_rework_high`
  (no failures reported), and no previously-passing case regressed. Target
  (≥90%) met after a single targeted edit; stopping the loop here per the
  "stop when target is met" rule.
