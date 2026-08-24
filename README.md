<!-- title: Self-Improving Skill Agent -->

# Self-Improving Skill Agent

A Claude Managed Agents recreation of [`self-improving-agent-skills`](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/self-improving-agent-skills): a single agent, given bash and file tools inside its own sandbox, iterates on a Claude Agent Skill's `SKILL.md` against a deterministic eval suite until it clears a target pass rate or exhausts its round budget. Every skill tested here started at a known baseline and ended with a measured, verifiable result: real API calls, real costs, real diffs.

## Credit

Concept and problem framing (skill folders per the agentskills.io spec, an Executor/Analyst/Mutator improvement loop, keep-only-if-improved scoring) are from [`awesome-llm-apps/agent_skills/self-improving-agent-skills`](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/self-improving-agent-skills) by [Shubham Saboo](https://github.com/Shubhamsaboo), licensed Apache-2.0. This is an independent reimplementation on a different stack (Claude Managed Agents instead of Google ADK, Gemini, and FastAPI); no code from the original is reused here.

## Architecture

The original project ran three separate agents (Executor, Analyst, Mutator) coordinated by hand-written orchestration code. This version collapses that into two pieces, both native to the [Managed Agents](https://platform.claude.com) platform:

- **One agent, not three.** A single Managed Agent's system prompt walks the same three jobs (run the eval, diagnose the failure pattern, apply one targeted edit) in sequence, sharing one context and one working copy of the skill file. A multiagent roster is the right tool for fan-out work; this is a tight sequential loop over shared file state, which a single agent with sandbox tools handles more reliably.
- **The Outcomes API replaces the hand-rolled round loop.** A `user.define_outcome` event plus a rubric gives the "keep iterating until an independent grader is satisfied" behavior the original project built by hand. The agent's own system prompt still drives the inner mutate/test/keep-or-revert mechanics; the rubric checks the *result* (target pass rate met, one change per round, no test tampering, no regressions).
- **Deterministic, regex-based grading, not an LLM judge.** Every rule checks something explicit and gradeable (a required section header, a word-count ceiling, a required OWASP finding) rather than asking a model to rate quality. That keeps the eval free to run, reproducible, and immune to grader drift between rounds.

## Repository layout

```
agent.yaml                    Managed Agent config: model, system prompt, sandbox tools
rubric.md                     Grading rubric for the Outcomes API
eval/run_eval.py              Generic eval harness, shared across every skill
scripts/setup.py              One-time: creates the environment, vault, and agent
scripts/launch_session.py     Per-run: uploads a skill's eval set, starts a session
skills/<name>/SKILL.md            Baseline snapshot of the skill under test
skills/<name>/eval/cases.json     Test scenarios for that skill
skills/<name>/eval/rules.py       Deterministic grading rules for that skill
skills/<name>/eval/results/       Local test output and real session artifacts
```

`eval/run_eval.py` is skill-agnostic: it loads `rules.py` dynamically from whichever skill's directory it's pointed at, so the same harness runs every skill in `skills/` unchanged.

## Setup

```bash
pip install anthropic pyyaml
```

The self-improvement loop needs a real, long-lived API key, not a short-lived CLI session token: the CMA agent's own sandbox has to call `api.anthropic.com` mid-session through a vault credential, and a vault credential holds a static secret, not something that expires in hours. Create a key in the [Console](https://platform.claude.com/settings/keys), then either export it or drop it into a local `.env` file (gitignored):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

```bash
python scripts/setup.py     # once: creates the environment, vault, and agent
python scripts/launch_session.py --skill rational-tone --target-pass-rate 0.9
```

`setup.py` refuses to run twice, so `agent.yaml` changes after the first run go through `agents.update()` instead of creating a second orphaned agent.

## Results

Six skills were run through the full live loop: `--model claude-haiku-4-5` for the eval harness (writing a commit message or a due-diligence finding is instruction-following, not judgment, so testing on a cheap, literal model is both cheaper and a better test of whether the instructions are actually explicit), `claude-sonnet-5` at medium effort for the improving agent itself.

| Skill | Baseline | Final | Rounds | Cost |
|---|---|---|---|---|
| commit-message-writer | 38% | 100% | 2 | $0.51 |
| gameplan | 86% | 100% | 1 | $0.31 |
| rational-tone | 50% | 100% (single run) / 83% (10-run average) | 8 | $2.08 |
| spec | 100% | 100% (no edit needed) | 0 | $0.28 |
| prd-threads | 100% | 100% (no edit needed) | 0 | $0.32 |
| owasp-review | 100% | 100% (no edit needed) | 0 | $0.27 |
| **Total** | | | | **$3.77** |

Three of the six already scored 100% at baseline. In every one of those cases the agent measured that, verified it wasn't a lucky single sample by re-running the eval two or three times, and correctly declined to make a speculative edit rather than manufacturing a change to look productive. That refusal is graded: the rubric explicitly checks that no edit was applied without a diagnosed failure to justify it.

### What the improvement loop actually found

- **commit-message-writer** had no guidance at all on commit bodies or breaking-change markup. Two rounds added an explicit rule and worked example for each.
- **gameplan** was truncating its own output: large plans hit the eval's token cap before ever reaching the `## Risks` section. The agent diagnosed this as a verbosity problem, not a missing-instruction problem, and added a "keep it concise" constraint so the closing sections always survive.
- **rational-tone** had a non-obvious bug: its own "self-check before delivering" section was leaking into the graded output, and that checklist commentary (colon-heavy, by design) was what tripped the very colon-budget rule it was meant to help enforce. The agent traced this to the actual root cause by reading raw model output, not just the failure labels, then rewrote the ambiguous section instead of patching around the symptom.
- The **rational-tone** run also surfaced a real property of the eval itself: no fixed sampling temperature, so the same final skill scored anywhere from 50% to 100% across ten repeated runs (83% average). Rather than reporting the best single number, the agent ran the stability check unprompted and logged the honest range.

## Cost

The first version of this defaulted to `claude-opus-5` everywhere at high effort, an 8-round ceiling, and a 4-pass outcome grader: roughly $5 to $12 per session for a task this mechanical. Measured cost with the tuned defaults above landed at $0.27 to $2.08 per skill, all in the table above. Three changes did most of the work:

| Change | Why it's safe |
|---|---|
| Eval harness on Haiku instead of Opus | Testing on a cheap, literal model surfaces instruction gaps a smarter model would silently paper over |
| Improving agent on Sonnet at medium effort instead of Opus at high | The task (read a JSON failure report, pick one of four listed mutation strategies, make one edit) is fully scoped by the system prompt, not open-ended reasoning |
| Outcome grader capped at 2 iterations instead of 4 | Keeps one real retry (the grader can send the agent back once if it disagrees) at roughly half the cost of the original cap |

A `budget` field on every session (`--budget-usd`, default $2) is a hard platform-enforced spend ceiling regardless of how a run goes.

### A bug the cost tuning surfaced

`rubric.md` said the round-exhaustion clause kicks in after 8 rounds; `agent.yaml`'s own system prompt capped the agent at 4. The rational-tone run hit that mismatch directly: the agent correctly stopped at round 4, the independent grader read the rubric literally, saw only 4 of the stated 8 rounds attempted, and returned `needs_revision`. Fixing the actual bug (syncing the round cap across `agent.yaml`, `rubric.md`, and `launch_session.py`'s default) mattered more than tuning the grader's retry count.

## License

MIT. See [LICENSE](LICENSE). The original project this is inspired by is licensed Apache-2.0; see [Credit](#credit) above.
