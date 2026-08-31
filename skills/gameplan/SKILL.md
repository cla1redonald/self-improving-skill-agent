---
name: gameplan
description: Produce an implementation plan from a spec or description. Files to modify, order of operations, dependencies, risks.
argument-hint: Feature description or path to spec
owner: Claire
last-affirmed: 2026-07-13
---

# /gameplan -- Implementation Plan

**Usage:** `/gameplan <feature-description-or-spec-path>`
**Example:** `/gameplan "Add dark mode toggle"` or `/gameplan docs/specs/dark-mode-toggle.md`

## When to Use

- You have a spec or clear idea and want a plan before building
- You want to understand complexity and file changes before committing
- You're about to run `/build-feature` and want it to have a plan to follow
- NOT for: exploring what to build (use `/spec` first), full product planning (use `/orchestrate`)

**Cost:** No agent spawns. Runs inline.

## Process

1. **Check for existing spec.** Look for `docs/specs/<slug>.md`. If found, read it.
2. **Read the codebase.** Understand structure, patterns, test setup, relevant files.
3. **Assess complexity:**

| Level | Characteristics |
|-------|-----------------|
| Low | 1-3 files, established patterns |
| Medium | 4-8 files, some new patterns |
| Medium-High | 8-15 files, architecture decisions |
| High | 15+ files, novel problems, security-sensitive |

4. **Write the gameplan** to `docs/gameplans/<slug>.md`:

```markdown
# Gameplan: [Feature Name]

**Spec:** [path to spec, or "none: working from description"]
**Complexity:** Low | Medium | Medium-High | High
**Estimated files:** N

## Steps
1. [Step: what to do, which files to create/modify, why]
2. [Step: note dependencies on previous steps]
...

## Dependencies
[Which steps depend on which: informs parallel execution]

## Risks
[What could go wrong and how to mitigate]
```

5. **Present the gameplan** to the user for review.
6. **Commit** the gameplan file.

## Keep It Concise (especially High complexity)

The `## Dependencies` and `## Risks` sections are **mandatory in every
gameplan, no matter how many steps it has.** A gameplan that gets truncated
before it reaches Risks is an incomplete gameplan: never let step-level
detail crowd out these closing sections.

- Each step should be **1-2 lines**: what to do, the file(s) touched, and why.
  Do not add separate "Dependencies" / "Details" / "Why" sub-bullets under
  every individual step: that information belongs in the `## Dependencies`
  section, not repeated per step.
- For High or Medium-High complexity plans with many steps, group them under
  phase headers (`### Phase 1: ...`) but keep each step to one line. A 20-step
  High-complexity plan should still be shorter overall than a padded 8-step
  Medium plan.
- If you notice you're running long partway through, immediately compress:
  shorten remaining step descriptions to a single line each, and go
  straight to `## Dependencies` and `## Risks` next. Always finish with all
  four template sections present (Steps, Dependencies, Risks): a shorter
  Risks section beats a missing one every time.

## Anti-Rationalization

| Thought | Reality |
|---------|---------|
| "The feature is simple, I don't need a plan" | Simple features have simple plans. Write it in 2 minutes. |
| "Planning is overhead, let me just build" | Building without a plan means discovering the plan while debugging. |
| "I know which files to change" | Write them down. The next agent doesn't know what you're thinking. |
| "Risks section is pessimistic" | Risks section is realistic. Name them now or discover them at midnight. |
| "I'll assess complexity as I go" | Complexity drives resource decisions. Assess it upfront. |

## Exit Criteria

- [ ] Gameplan file exists at `docs/gameplans/<slug>.md`
- [ ] Complexity assessed
- [ ] All steps have concrete file paths
- [ ] Dependencies documented
- [ ] Risks identified with mitigations
- [ ] User has reviewed and approved
- [ ] Gameplan committed to git

## Failure Recovery

| Problem | Action |
|---------|--------|
| No spec and description is vague | Run `/spec` first, then come back |
| Complexity is High | Flag to user: may need decomposition |
| Can't determine file structure | Read ARCHITECTURE.md or explore codebase more |
| All steps are sequential | Look for parallel opportunities |
