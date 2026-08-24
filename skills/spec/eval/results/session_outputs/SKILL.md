---
name: spec
description: Capture requirements, constraints, and success criteria for a feature. Lighter than a full PRD.
argument-hint: Feature description
owner: Claire
last-affirmed: 2026-07-13
---

# /spec -- Feature Specification

**Usage:** `/spec <feature-description>`
**Example:** `/spec "Add dark mode toggle to settings page"`

## When to Use

- You know what you want to build and need it written down
- You want to capture requirements before jumping to code
- You're about to run `/gameplan` or `/build-feature` and want structured input
- NOT for: full product discovery (use `/orchestrate` with @strategist)

**Cost:** No agent spawns. Runs inline.

## Process

1. **Parse the feature description.** Slugify it (e.g., "Add dark mode toggle" -> `dark-mode-toggle`).
2. **Ask up to 3 clarifying questions** — only if critical information is missing. Prefer inferring from context.
3. **Read the codebase.** Check existing patterns, related features, relevant files.
4. **Write the spec** to `docs/specs/<slug>.md`:

```markdown
# Spec: [Feature Name]

## What
[What is being built — concrete, not abstract]

## Why
[Why it matters — user need, business goal, or technical requirement]

## Success Criteria
- [ ] [Checkable condition — specific enough to verify]
- [ ] [Another checkable condition]

## Constraints
[Technical or business constraints that shape the solution]

## Out of Scope
[Explicitly excluded — prevents scope creep]
```

5. **Present the spec** to the user for review.
6. **Commit** the spec file.

## Anti-Rationalization

| Thought | Reality |
|---------|---------|
| "I already know what to build, I don't need a spec" | Writing it down reveals gaps. The spec takes 2 minutes. |
| "Success criteria are obvious" | If obvious, they're easy to write. Write them. |
| "Out of Scope isn't needed for something small" | Small features grow. Explicit boundaries prevent creep. |
| "I'll just start coding and figure it out" | Figuring it out while coding means rewriting. Figure it out first. |

## Exit Criteria

- [ ] Spec file exists at `docs/specs/<slug>.md`
- [ ] All sections filled (What, Why, Success Criteria, Constraints, Out of Scope)
- [ ] Success criteria are checkable (not vague)
- [ ] User has reviewed and approved
- [ ] Spec committed to git

## Failure Recovery

| Problem | Action |
|---------|--------|
| Can't determine requirements | Ask up to 3 clarifying questions, then proceed with assumptions documented |
| Feature overlaps existing code | Note overlap in Constraints, reference existing files |
| Scope too large for one spec | Split into multiple specs, note dependencies |
