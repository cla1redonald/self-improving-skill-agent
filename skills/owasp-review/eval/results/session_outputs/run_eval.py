#!/usr/bin/env python3
"""Generic eval harness — works for any skill under skills/<name>/.

Runs a SKILL.md (used as the system prompt) against every case in that
skill's cases.json, scores each output with that skill's own rules.py, and
writes a JSON report. This plays the "Executor" role from the original
self-improving-agent-skills project, minus the framework: any Claude API
call + a JSON report is all that role ever needed to be.

rules.py is loaded dynamically from the cases.json's own directory (or
--rules explicitly) rather than a static `import rules` — a static import
resolves against the *script's* directory, not the caller's cwd, which broke
as soon as a second skill's rules.py needed to sit next to a different
cases.json. This way the same run_eval.py works for every skill unchanged.

Usage:
    python run_eval.py --skill /workspace/work/SKILL.md --cases /workspace/eval/cases.json --out round_0.json
    python run_eval.py --self-test        # sanity-checks the commit-message-writer's rules.py, no API calls
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

STRIP_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


def load_rules(rules_path: Path):
    spec = importlib.util.spec_from_file_location("rules", rules_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RULES


def load_skill_instructions(skill_path: str) -> str:
    text = Path(skill_path).read_text()
    return STRIP_FRONTMATTER_RE.sub("", text, count=1).strip()


def extract_text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text").strip()


def score_message(message: str, case: dict, rules: dict) -> dict:
    results = {}
    for rule_name in case["rules"]:
        check_fn = rules[rule_name]
        passed, detail = check_fn(message, case)
        results[rule_name] = {"passed": passed, "detail": detail}
    case_passed = all(r["passed"] for r in results.values())
    return {"passed": case_passed, "rules": results}


# $ / 1M tokens, list rates. Extend as needed; unlisted models just skip cost estimation.
PRICING = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int):
    if model not in PRICING:
        return None
    in_rate, out_rate = PRICING[model]
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate


def run_eval(skill_path: str, cases_path: str, model: str, rules_path: Path, max_tokens: int) -> dict:
    import anthropic  # deferred import so --self-test never needs the SDK installed

    client = anthropic.Anthropic()
    skill_instructions = load_skill_instructions(skill_path)
    cases = json.loads(Path(cases_path).read_text())
    rules = load_rules(rules_path)

    case_results = []
    total_input_tokens = 0
    total_output_tokens = 0
    for case in cases:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=skill_instructions,
            messages=[{"role": "user", "content": case["input"]}],
        )
        message = extract_text(response)
        scored = score_message(message, case, rules)
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens
        case_results.append({
            "id": case["id"],
            "input": case["input"],
            "output": message,
            "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
            **scored,
        })

    passed = sum(1 for c in case_results if c["passed"])
    cost = estimate_cost(model, total_input_tokens, total_output_tokens)
    return {
        "skill_path": skill_path,
        "model": model,
        "pass_rate": passed / len(case_results) if case_results else 0.0,
        "passed": passed,
        "total": len(case_results),
        "usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "estimated_cost_usd": cost,
        },
        "cases": case_results,
    }


def print_summary(report: dict) -> None:
    print(f"\n{report['passed']}/{report['total']} cases passed "
          f"({report['pass_rate']:.0%}) — {report['skill_path']}\n")
    usage = report["usage"]
    cost_str = f"${usage['estimated_cost_usd']:.4f}" if usage["estimated_cost_usd"] is not None else "n/a (unlisted model)"
    print(f"  usage: {usage['input_tokens']} input tokens, {usage['output_tokens']} output tokens, "
          f"est. cost {cost_str} ({report['model']}, list rates)\n")
    for case in report["cases"]:
        mark = "PASS" if case["passed"] else "FAIL"
        print(f"  [{mark}] {case['id']}")
        if not case["passed"]:
            for rule_name, result in case["rules"].items():
                if not result["passed"]:
                    print(f"         - {rule_name}: {result['detail']}")


# --- self-test: exercises rules.py against canned messages, no API calls ---

SELF_TEST_CASES = [
    {
        "message": "fix: correct typo in login error message",
        "case": {"rules": ["header_type_prefix", "header_length_72", "no_trailing_period_header",
                            "imperative_mood", "no_vague_phrases"]},
        "expect_pass": True,
    },
    {
        "message": "Fixed the login bug.",
        "case": {"rules": ["header_type_prefix"]},
        "expect_pass": False,  # no valid type prefix
    },
    {
        "message": "fix: fixed the login bug",
        "case": {"rules": ["imperative_mood"]},
        "expect_pass": False,  # "fixed" is not imperative
    },
    {
        "message": "fix: misc changes to login",
        "case": {"rules": ["no_vague_phrases"]},
        "expect_pass": False,
    },
    {
        "message": "refactor: extract shared retry helper\n\nMoves duplicated retry logic from three call sites into retry.py.",
        "case": {"rules": ["requires_body_multi_file", "body_line_length_100"]},
        "expect_pass": True,
    },
    {
        "message": "refactor: extract shared retry helper",
        "case": {"rules": ["requires_body_multi_file"]},
        "expect_pass": False,  # no body at all
    },
    {
        "message": "fix(config)!: change parse_config signature\n\nBREAKING CHANGE: second positional argument removed.",
        "case": {"rules": ["mentions_breaking_change"]},
        "expect_pass": True,
    },
]


# Fixed regardless of cwd: self-test checks the harness's scoring MECHANISM against
# the one rule set it was originally validated against, not whichever skill you're
# currently pointed at.
SELF_TEST_RULES_PATH = Path(__file__).resolve().parent.parent / "skills" / "commit-message-writer" / "eval" / "rules.py"


def run_self_test() -> bool:
    rules = load_rules(SELF_TEST_RULES_PATH)
    all_ok = True
    for i, spec in enumerate(SELF_TEST_CASES):
        result = score_message(spec["message"], spec["case"], rules)
        ok = result["passed"] == spec["expect_pass"]
        all_ok = all_ok and ok
        mark = "ok" if ok else "MISMATCH"
        print(f"[{mark}] case {i}: expected passed={spec['expect_pass']}, got {result['passed']}")
        if not ok:
            print(f"         detail: {result['rules']}")
    print(f"\nself-test {'PASSED' if all_ok else 'FAILED'} ({len(SELF_TEST_CASES)} canned cases, no API calls)")
    return all_ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", help="Path to the SKILL.md under test")
    parser.add_argument("--cases", default="cases.json", help="Path to cases.json")
    parser.add_argument("--rules", help="Path to rules.py. Defaults to rules.py next to --cases.")
    parser.add_argument("--model", default="claude-haiku-4-5",
                         help="Model the skill-under-test runs on. Cheap on purpose: "
                              "most of these skills are instruction-following text generation, "
                              "and testing on a literal, less-inferring model surfaces "
                              "instruction gaps a smarter model would paper over.")
    parser.add_argument("--max-tokens", type=int, default=4000,
                         help="4000 covers a thorough gameplan for a large migration without "
                              "truncating mid-word (measured: a 'High' complexity case hit exactly "
                              "1500/1500 tokens and cut off mid-sentence at the old default). "
                              "commit-message-writer barely uses a fraction of this — cheap on "
                              "Haiku either way. Raise further for very large PRDs.")
    parser.add_argument("--out", help="Where to write the JSON report")
    parser.add_argument("--self-test", action="store_true",
                         help="Check the commit-message-writer's rules.py against canned messages; makes no API calls")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(0 if run_self_test() else 1)

    if not args.skill:
        parser.error("--skill is required unless --self-test is set")

    rules_path = Path(args.rules) if args.rules else Path(args.cases).resolve().parent / "rules.py"
    report = run_eval(args.skill, args.cases, args.model, rules_path, args.max_tokens)
    print_summary(report)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
