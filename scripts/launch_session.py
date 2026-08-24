#!/usr/bin/env python3
"""Per-run: upload the skill + eval, start a session, define the outcome, stream it.

Run scripts/setup.py once first. This script is the "every run" half: it
never creates the agent/environment/vault, only reads their IDs from ids.json.

This is a rough, single-purpose event loop, not the reconnect-safe client
described in shared/managed-agents-client-patterns.md. It's fine for a
one-shot foreground run; for anything unattended (a dropped connection should
not orphan the session), build on that pattern instead. Because every tool in
agent.yaml uses the default always_allow permission policy, there are no
tool_confirmation round-trips to handle here: if you add always_ask to any
tool, this loop needs extending.

Usage:
    python scripts/launch_session.py --skill spec --target-pass-rate 0.9 --budget-usd 2
"""

import argparse
import json
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
IDS_FILE = ROOT / "ids.json"
SKILLS_DIR = ROOT / "skills"


def upload(client, path: Path):
    with open(path, "rb") as f:
        return client.beta.files.upload(file=f)


def main():
    available = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.exists() else []

    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, choices=available or None,
                         help=f"Which skill under skills/ to run the loop on. Available: {available}")
    parser.add_argument("--target-pass-rate", type=float, default=0.9)
    parser.add_argument("--max-rounds", type=int, default=8,
                         help="Told to the agent in the outcome description; must match agent.yaml's own "
                              "stated cap AND rubric.md's criterion 1 exhaustion threshold: a mismatch "
                              "here is exactly what made the rational-tone run cost $2 instead of $0.30: "
                              "the agent stopped at its (lower) prompt cap, the grader read the (higher) "
                              "rubric number literally, called it incomplete, and the agent burned extra "
                              "rounds reconciling the two. All three must agree.")
    parser.add_argument("--outcome-max-iterations", type=int, default=2,
                         help="How many grade cycles the Outcomes grader gets. 2 keeps a real retry: "
                              "if the grader disagrees with the agent's self-assessment on the first "
                              "pass, it can send the agent back for one more attempt before settling. "
                              "1 would drop to a single grade-and-report pass with no retry (cheapest, "
                              "but the agent's internal loop is then unassisted). Each increment above "
                              "this costs roughly one more grader pass.")
    parser.add_argument("--budget-usd", type=float, default=2.0,
                         help="Hard dollar cap on this session's spend (list-price rates). This is a "
                              "safety ceiling, not the expected cost (see README's cost estimate).")
    args = parser.parse_args()
    skill_dir = SKILLS_DIR / args.skill

    ids = json.loads(IDS_FILE.read_text())
    client = anthropic.Anthropic()

    print(f"Uploading skill + eval files for '{args.skill}'...")
    skill_file = upload(client, skill_dir / "SKILL.md")
    cases_file = upload(client, skill_dir / "eval" / "cases.json")
    rules_file = upload(client, skill_dir / "eval" / "rules.py")
    run_eval_file = upload(client, ROOT / "eval" / "run_eval.py")  # shared, skill-agnostic harness

    rubric_text = (ROOT / "rubric.md").read_text()

    description = (
        f"Improve the Agent Skill mounted at /workspace/skill/SKILL.md so it "
        f"scores at least {args.target_pass_rate:.0%} pass rate on the eval "
        f"suite at /workspace/eval/cases.json (run via "
        f"/workspace/eval/run_eval.py), using at most {args.max_rounds} rounds "
        f"of one-targeted-edit-per-round mutation. Log every round to "
        f"/workspace/work/changelog.md and copy final deliverables to "
        f"/mnt/session/outputs/ before finishing."
    )

    print("Creating session...")
    session = client.beta.sessions.create(
        agent={"type": "agent", "id": ids["agent_id"], "version": ids["agent_version"]},
        environment_id=ids["environment_id"],
        vault_ids=[ids["vault_id"]],
        title=f"Skill self-improvement: {args.skill}",
        budget={
            "type": "limit",
            "max_list_cost": {"amount": str(int(args.budget_usd * 100)), "currency": "USD"},
        },
        resources=[
            {"type": "file", "file_id": skill_file.id, "mount_path": "/workspace/skill/SKILL.md"},
            {"type": "file", "file_id": cases_file.id, "mount_path": "/workspace/eval/cases.json"},
            {"type": "file", "file_id": rules_file.id, "mount_path": "/workspace/eval/rules.py"},
            {"type": "file", "file_id": run_eval_file.id, "mount_path": "/workspace/eval/run_eval.py"},
        ],
        initial_events=[
            {
                "type": "user.define_outcome",
                "description": description,
                "rubric": {"type": "text", "content": rubric_text},
                "max_iterations": args.outcome_max_iterations,
            }
        ],
    )
    print(f"session_id = {session.id} (status: {session.status})")
    print(f"Watch live: https://platform.claude.com/workspaces/default/sessions/{session.id}")
    print("(replace 'default' with your workspace ID if this key isn't on the org's default workspace)\n")

    with client.beta.sessions.events.stream(session_id=session.id) as stream:
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if block.type == "text":
                        print(block.text, end="", flush=True)
            elif event.type in ("agent.tool_use", "agent.mcp_tool_use"):
                print(f"\n[tool: {getattr(event, 'name', event.type)}]")
            elif event.type == "span.outcome_evaluation_end":
                print(f"\n[outcome iteration {event.iteration}: {event.result}] {event.explanation}")
            elif event.type == "session.error":
                print(f"\n[session.error] {event.error}")
            elif event.type == "session.status_idle":
                print("\n--- idle ---")
                break
            elif event.type == "session.status_terminated":
                print("\n--- terminated ---")
                break

    out_dir = skill_dir / "eval" / "results" / "session_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading output files to {out_dir} (may need a retry if empty, brief indexing lag)...")
    # files.list(scope_id=session.id) returns BOTH the uploaded input resources
    # (e.g. the original SKILL.md mounted read-only at session start) and the
    # agent's /mnt/session/outputs/ deliverables, and an input and an output
    # can share the same filename (SKILL.md in, SKILL.md out). Downloading
    # naively by filename let whichever came later in listing order silently
    # clobber the other on disk, twice, in opposite directions, across two
    # live sessions, before this was caught. Keep only the newest file per
    # filename: inputs are uploaded before the session starts, outputs are
    # written during/after, so latest created_at is reliably the real output.
    latest_by_name = {}
    for f in client.beta.files.list(scope_id=session.id, betas=["managed-agents-2026-04-01"]):
        existing = latest_by_name.get(f.filename)
        if existing is None or f.created_at > existing.created_at:
            latest_by_name[f.filename] = f
    for f in latest_by_name.values():
        dest = out_dir / f.filename
        dest.write_bytes(client.beta.files.download(f.id).read())
        print(f"  saved {f.filename} ({f.size_bytes} bytes)")

    final = client.beta.sessions.retrieve(session.id)
    cost = final.usage.list_cost
    print(f"\nMeasured session cost: ${int(cost.amount) / 100:.2f} {cost.currency} "
          f"({final.usage.input_tokens} input + {final.usage.output_tokens} output tokens, "
          f"list rates). Note: eval-harness calls the agent makes from inside its sandbox via "
          f"the vaulted key are billed separately and are NOT included in this figure.")


if __name__ == "__main__":
    main()
