---
name: prd-threads
description: Convert a PRD into discrete, executable threads optimized for AI pair programming and parallel agent execution. Use when breaking down a PRD into implementable work units.
argument-hint: Path to PRD file
owner: Claire
last-affirmed: 2026-07-13
---

# /prd-threads -- PRD to Executable Threads

**Usage:** `/prd-threads <path-to-prd>`
**Example:** `/prd-threads docs/prd.md`

## When to Use

- You have a completed PRD and want to break it into executable work units
- You want to assign reasoning levels and model requirements per thread
- You need self-contained threads for Agent Teams parallel execution
- NOT for: reviewing a PRD (use `/prd-review`), building without a PRD (use `/build-feature`)

**Cost:** No agent spawns. Runs inline.

## Process

1. **Read the PRD.** Understand full scope, requirements, and constraints.
2. **Identify features/components.** List all work items.
3. **Group related work.** Combine minimal tasks, isolate complex ones.
4. **Determine dependencies.** What must happen before what?
5. **Identify parallel opportunities.** Which threads can run simultaneously?
6. **Assign reasoning levels:**

| Level | Model | Characteristics |
|-------|-------|-----------------|
| Minimal | Haiku | Single file, procedural |
| Low | Haiku/Sonnet | 2-3 files, established patterns |
| Medium | Sonnet | Cross-component, business logic |
| Medium-High | Sonnet/Opus | Architecture decisions |
| High | Opus | Novel problems, security-sensitive |

7. **Generate threads.** Each thread follows this structure:

```markdown
### Thread [N]: [Name]
**Purpose:** [One sentence]
**Actions:** [Checklist of specific actions]
**Reference Material:** [File paths with line numbers]
**Validation Targets:** [How to verify completion]
**Deliverables:** [What this thread produces]
**Reasoning Level:** [Level] ([Model])
**Dependencies:** [Prior threads, or "None"]
**Parallelizable:** [Yes/No]
```

8. **Validate coverage.** Every PRD requirement must map to a thread.

## Anti-Rationalization

| Thought | Reality |
|---------|---------|
| "I can just build this without threads" | Threads enable parallel work and clear ownership. Minutes of overhead, hours of savings. |
| "One big thread is simpler" | One big thread can't parallelize and is too large for a single conversation. |
| "Reasoning levels are overkill" | Wrong model on wrong task wastes money (opus on config) or quality (haiku on auth). |
| "Dependencies are obvious" | Write them down. The agent executing thread 5 doesn't know what you're thinking. |

## Exit Criteria

- [ ] All PRD requirements covered by at least one thread
- [ ] Each thread is self-contained (all context included)
- [ ] Reasoning levels assigned to every thread
- [ ] Dependencies explicit
- [ ] Parallel opportunities identified
- [ ] File references are specific (not vague pointers)
- [ ] No thread exceeds single-conversation scope

## Failure Recovery

| Problem | Action |
|---------|--------|
| PRD too vague to thread | Run `/prd-review` first to identify gaps |
| Thread too large | Split into sub-threads at natural boundaries |
| Thread too small | Combine with related minimal work |
| Circular dependencies | Restructure — extract shared setup into thread 0 |
