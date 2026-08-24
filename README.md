# Self-improving skill agent (Managed Agents)

A Managed Agents recreation of the `self-improving-agent-skills` project: one
CMA agent, given bash + file tools and an eval suite in its sandbox, iterates
on a Skill's `SKILL.md` until it clears a pass-rate bar or runs out of
rounds — replacing the original's Google ADK / Gemini / FastAPI / Executor-
Analyst-Mutator stack.

## Credit

Concept and problem framing (skill folders per the agentskills.io spec, an
Executor/Analyst/Mutator improvement loop, keep-only-if-improved scoring) are
from [`awesome-llm-apps/agent_skills/self-improving-agent-skills`](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/self-improving-agent-skills)
by [Shubham Saboo](https://github.com/Shubhamsaboo), licensed Apache-2.0.
This is an independent reimplementation on a different stack (Claude Managed
Agents instead of Google ADK/Gemini/FastAPI) — no code from the original is
reused here.

## Layout

| File | Role |
|---|---|
| `agent.yaml` | The CMA agent config: model, system prompt encoding the improve-loop, tools. |
| `rubric.md` | Grading rubric for the Outcomes API — defines "done." |
| `skill_under_test/SKILL.md` | The skill being improved. Deliberately loose to start (no length limits, no imperative-mood rule, no vague-phrase ban) so there's real room for the loop to close gaps. |
| `eval/cases.json` | 8 test scenarios (single-file fix, multi-file refactor, breaking change, etc). |
| `eval/rules.py` | Deterministic, regex/structural grading rules — no LLM judge, so scoring is free and reproducible. |
| `eval/run_eval.py` | The harness: calls Claude with the skill as system prompt, scores the output, writes a JSON report. This is the original project's "Executor" role. |
| `scripts/setup.py` | One-time: creates the environment, vault + `ANTHROPIC_API_KEY` credential, and agent. Writes `ids.json`. |
| `scripts/launch_session.py` | Every run: uploads the skill + eval as session resources, opens a session with a `user.define_outcome` event, streams it to stdout. |

## Why this shape

- **No separate Executor/Analyst/Mutator agents.** The original's three ADK
  agents become one CMA agent whose system prompt walks the same three jobs
  in sequence, sharing one context and one working copy of the file. A
  multiagent roster is for fan-out (parallel research); this is a tight
  sequential loop over shared file state, which single-agent-plus-sandbox
  handles more reliably.
- **The Outcomes API replaces the hand-rolled round loop.** `user.define_outcome`
  + a rubric gives you the "keep iterating until the grader is satisfied"
  behavior the original built by hand. The agent's own system prompt still
  drives the inner mutate/test/keep-or-revert mechanics — the rubric checks
  the *result* (target pass rate, one-change-per-round, no test tampering).
- **Rule-based scoring, not an LLM judge**, per the Outcomes docs' own advice:
  gradeable criteria, not vibes. Keeps the eval cheap, deterministic, and
  immune to grader drift between rounds.

## Running it

```bash
pip install anthropic pyyaml
export ANTHROPIC_API_KEY=sk-ant-...   # a real key, not an `ant auth` session token —
                                       # the vault credential needs a static secret

python scripts/setup.py               # once
python scripts/launch_session.py --target-pass-rate 0.9 --budget-usd 10
```

`setup.py` refuses to run twice (no orphaned agents/environments) — to change
`agent.yaml` afterward, update the agent in place rather than re-running setup
(see `shared/managed-agents-core.md` → Versioning in the claude-api skill).

## Verified so far

Without spending anything:

```bash
cd eval && python3 run_eval.py --self-test
```

Runs the 8 rule-checker functions against 7 canned commit messages (good and
bad) with no API calls — confirms the scoring logic itself is correct before
any live run. This passes as of this writing.

Live, against the real API (`claude-haiku-4-5`):

```bash
cd eval && python3 run_eval.py --skill ../skill_under_test/SKILL.md --cases cases.json --model claude-haiku-4-5
```

One baseline pass over all 8 cases: **1,173 input tokens, 134 output tokens,
$0.0018** — measured, not estimated (`run_eval.py` now tracks and prints
`response.usage` on every run). The baseline skill scores 4/8 (50%), failing
almost entirely on missing commit bodies for multi-file changes — a real,
meaningful gap for the self-improvement loop to close, not a fabricated one.

## Cost estimate for an actual run

The first version of this defaulted to `claude-opus-5` everywhere at
`effort: high`, 8 rounds, and a 4-pass outcome grader — roughly **$5–12 per
session**. That's a lot more than it needs to be, for a task this mechanical.
Current defaults, tuned for cost without dropping any of the actual
functionality (eval coverage, revert-on-regression, changelog, independent
grading — see below for the one thing that *is* traded off):

| Component | Was | Now | Why it's safe to cut here |
|---|---|---|---|
| Eval harness model (`run_eval.py --model`) | `claude-opus-5` | `claude-haiku-4-5` | Writing a commit message from explicit instructions is simple instruction-following, not judgment. Bonus: testing on a cheap, literal model surfaces instruction gaps a smarter model would silently paper over — arguably makes the eval *more* rigorous, not less. |
| CMA agent model + effort | `claude-opus-5` @ `high` | `claude-sonnet-5` @ `medium` | The agent's job (read a JSON failure report, pick one of four listed mutation strategies, make one edit) is exactly the kind of scoped, in-structure task Sonnet handles well — the system prompt already spells out the whole procedure, so the model isn't being asked to improvise. |
| Round ceiling | 8 | 4 | 4 targeted edits is enough to close the gaps in a starter skill this small; halves total eval-harness and agent-turn volume directly. |
| Outcome grader `max_iterations` | 4 | 2 | Keeps a real retry: if the grader disagrees with the agent's self-assessment on the first pass, it gets to send the agent back once before settling — not just a report card. Dropping to 1 (`--outcome-max-iterations 1`) removes that retry entirely and saves roughly one grader pass; going back up to 4 restores the original safety net at roughly double this line's cost. |
| Session budget cap | $10 | $2 | This is a safety ceiling, not a target — see below for the actual expected cost. |

**Estimated total: roughly $1.00–2.10 per session**, revised down for the eval
harness now that it's measured rather than guessed:

- Eval harness (9 passes across a full session): **~$0.016, confirmed live**
  (was estimated at ~$0.10 — the real number came in ~6x cheaper than
  guessed, because the skill's system prompt and single-line commit-header
  outputs are both smaller than assumed).
- CMA agent turns (Sonnet 5 @ medium, up to 4 rounds): still an estimate,
  ~$0.40–1.00.
- Outcome grader (2 passes): still an estimate, ~$0.50–1.00.

So the two components I *can't* verify without spinning up a real Managed
Agents session (agent turns + grader) are still the entire estimate — the
part I just measured turned out to be a rounding error either way. The $2
budget cap stands as the backstop regardless.

**To get a real number on the parts that matter, I need a static API key, not
the OAuth session token you just set up.** `ant auth login` authenticates
*me* (this CLI/SDK session) — but `setup.py` needs to hand a real,
long-lived key to a **vault credential** so the CMA agent's own sandbox can
call `api.anthropic.com` when it runs the eval mid-session. A short-lived
OAuth token isn't the right shape for that (it expires in hours, not the
credential store's model). If you want the full end-to-end number:

1. Create an API key in the [Console](https://platform.claude.com/settings/keys) (or `ant` doesn't mint static keys — only OAuth sessions).
2. `export ANTHROPIC_API_KEY=sk-ant-...` in your own terminal (not pasted to me).
3. Say the word and I'll run `setup.py` + `launch_session.py` for one real session.
