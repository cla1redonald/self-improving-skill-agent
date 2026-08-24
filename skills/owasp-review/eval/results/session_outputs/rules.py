"""Deterministic checks for the owasp-review skill.

Unlike the other four skills' evals, this one grades correctness, not just
format: each case plants exactly one known, unambiguous OWASP Top 10
vulnerability, and the check is whether the skill's output actually flags
that category as a FINDING (not PASS/N/A) — not whether the prose looks
plausible. Format checks (all ten categories covered, a Findings section, a
verdict line) exist too, but flags_expected_category is the one that matters.
"""

import re

CATEGORY_NAMES = [f"A{n:02d}" for n in range(1, 11)]


def check_flags_expected_category(message, case):
    expected = case["expected_category"]
    # Look for the category code and a FINDING verdict on the same line (the
    # coverage table row), or in a Findings-section bullet naming it, e.g.
    # "**[A03] SQL Injection**".
    row_pattern = re.compile(rf"\b{expected}\b.*\bFINDING\b", re.IGNORECASE)
    bullet_pattern = re.compile(rf"\[{expected}\]", re.IGNORECASE)
    finding_nearby = any(
        row_pattern.search(line) or bullet_pattern.search(line)
        for line in message.splitlines()
    )
    return finding_nearby, "" if finding_nearby else f"expected {expected} to be flagged as a FINDING; not found on any table row or findings bullet"


def check_has_all_ten_rows(message, case):
    missing = [c for c in CATEGORY_NAMES if not re.search(rf"\b{c}\b", message)]
    ok = not missing
    return ok, "" if ok else f"missing coverage rows for: {missing}"


def check_has_findings_section(message, case):
    ok = bool(re.search(r"^##\s*Findings\b", message, re.MULTILINE | re.IGNORECASE))
    return ok, "" if ok else "no '## Findings' section found"


VERDICT_WINDOW_RE = re.compile(
    r"\bverdict\b.{0,80}?\b(SHIP|FIX[\s-]FIRST)\b", re.IGNORECASE | re.DOTALL
)


def check_has_verdict_line(message, case):
    # The skill's own template bolds the colon+value together
    # ("**Verdict: FIX-FIRST**"); live output varied into "## Verdict: **FIX-FIRST**",
    # "FIX FIRST" (space not hyphen), an emoji prefix, and the value on its own
    # line two lines below a bare "## Verdict" heading. Rather than chase every
    # markup permutation, search a small window of text after "Verdict" instead
    # of requiring same-line or exact-hyphenation matches.
    ok = bool(VERDICT_WINDOW_RE.search(message))
    return ok, "" if ok else "no 'Verdict' followed by SHIP/FIX-FIRST within ~80 chars found"


RULES = {
    "flags_expected_category": check_flags_expected_category,
    "has_all_ten_rows": check_has_all_ten_rows,
    "has_findings_section": check_has_findings_section,
    "has_verdict_line": check_has_verdict_line,
}
