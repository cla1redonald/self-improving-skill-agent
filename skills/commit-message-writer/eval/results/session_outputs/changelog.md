# Changelog

## Round 0 (baseline)
- No edits. Ran eval against original SKILL.md as-is.
- Pass rate: 3/8 (38%)
- Failures observed:
  - `requires_body_multi_file`: 4 cases (multi_file_refactor, breaking_api_change,
    new_feature_multi_file, sweeping_rename_temptation) — skill produced
    header-only messages even when multiple files changed.
  - `mentions_breaking_change`: 1 case (breaking_api_change) — no `!` marker or
    `BREAKING CHANGE:` footer.
  - `header_length_72`: 1 case (dependency_bump) — header exceeded 72 chars.

## Round 1
- Mutation strategy: add an explicit constraint + concrete example (missing
  rule, not ambiguity — the original SKILL.md never mentioned commit bodies
  at all).
- Rule(s) targeted: `requires_body_multi_file`, `body_line_length_100`.
- Change: added instruction step 5 requiring a body (blank line + explanation)
  whenever the change touches more than one file, capped body lines at 100
  chars, and included a worked example of a multi-file commit message.
- Before pass rate: 3/8 (38%)
- After pass rate: 7/8 (88%)
- Rationale: the dominant failure pattern (4/8 cases) was the total absence
  of body-writing guidance in the skill; adding the rule + example directly
  addresses the gap the model had no way to infer on its own.
- Side effect: `header_length_72` failure on dependency_bump also disappeared
  (model produced a shorter header on this run).
- Outcome: **kept**.

## Round 2
- Mutation strategy: add an explicit constraint + concrete example (missing
  rule — the skill had no guidance at all on how to signal a breaking
  change; the model tried to convey it in prose, which the deterministic
  `mentions_breaking_change` rule can't detect).
- Rule(s) targeted: `mentions_breaking_change`.
- Change: added instruction step 6 requiring both a `!` after the type/scope
  in the header AND a `BREAKING CHANGE:` footer line in the body whenever a
  change breaks backward compatibility, with a worked example, and explicitly
  called out that a plain-language note is insufficient.
- Before pass rate: 7/8 (88%)
- After pass rate: 8/8 (100%)
- Rationale: the sole remaining failure (breaking_api_change) was caused by
  the model describing the break in natural language instead of using the
  two structural markers the grader checks for; spelling out the exact
  required markup closed the gap.
- Outcome: **kept**.

## Verification run
- Re-ran the eval once more against the final SKILL.md to check for
  non-determinism across LLM calls.
- Result: 8/8 (100%) again — see `round_2_verify.json`.
- Final skill meets and exceeds the 90% target; stopping after round 2 of
  the allotted 4.
