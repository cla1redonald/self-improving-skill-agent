"""Deterministic structural checks for the /spec skill's output.

Grades against the skill's own stated template and Exit Criteria: What / Why
/ Success Criteria / Constraints / Out of Scope sections, with success
criteria that are checkable rather than vague. Does not check the file-write
or git-commit side effects (Exit Criteria items 4-5): the eval only ever
sees the skill's single text response, not a sandboxed repo it can commit
into, so this grades the content the skill would have written, not whether
it got written to disk.
"""

import re

# Regex, not literal phrases: an exact-string list missed trivial variants
# ("work well" vs "works well", "user friendly" vs "user-friendly") during
# testing against a deliberately vague handwritten example. Un-anchored
# word-order-flexible patterns catch the family, not just one inflection.
VAGUE_CRITERION_PATTERNS = [
    re.compile(r"\bworks?\s+(well|correctly|properly|as\s+expected)\b", re.IGNORECASE),
    re.compile(r"\buser[\s-]?friendly\b", re.IGNORECASE),
    re.compile(r"\b(is|feels?)\s+intuitive\b", re.IGNORECASE),
    re.compile(r"\b(is|feels?)\s+fast\b", re.IGNORECASE),
    re.compile(r"\b(is|looks?)\s+(good|nice|great|better)\b", re.IGNORECASE),
    re.compile(r"\beasy\s+to\s+use\b", re.IGNORECASE),
    re.compile(r"\bperforms?\s+well\b", re.IGNORECASE),
    re.compile(r"\b(is|are)\s+(reliable|robust|stable)\b", re.IGNORECASE),
]


def _has_section(message: str, heading: str):
    pattern = re.compile(rf"^#{{1,3}}\s*{re.escape(heading)}\b", re.IGNORECASE | re.MULTILINE)
    return bool(pattern.search(message))


def check_has_what(message, case):
    ok = _has_section(message, "What")
    return ok, "" if ok else "no '## What' section found"


def check_has_why(message, case):
    ok = _has_section(message, "Why")
    return ok, "" if ok else "no '## Why' section found"


def check_has_success_criteria(message, case):
    ok = _has_section(message, "Success Criteria")
    return ok, "" if ok else "no '## Success Criteria' section found"


def check_has_checkable_items(message, case):
    # The template uses markdown checkboxes: "- [ ] ...".
    items = re.findall(r"^\s*-\s*\[\s*\]\s*.+", message, re.MULTILINE)
    ok = len(items) >= 1
    return ok, "" if ok else "no checkbox-style success criteria ('- [ ] ...') found"


def check_has_constraints(message, case):
    ok = _has_section(message, "Constraints")
    return ok, "" if ok else "no '## Constraints' section found"


def check_has_out_of_scope(message, case):
    ok = _has_section(message, "Out of Scope")
    return ok, "" if ok else "no '## Out of Scope' section found"


def check_no_vague_criteria(message, case):
    hit = next((p.pattern for p in VAGUE_CRITERION_PATTERNS if p.search(message)), None)
    return hit is None, "" if hit is None else f"contains a vague, unverifiable criterion phrase matching /{hit}/"


RULES = {
    "has_what": check_has_what,
    "has_why": check_has_why,
    "has_success_criteria": check_has_success_criteria,
    "has_checkable_items": check_has_checkable_items,
    "has_constraints": check_has_constraints,
    "has_out_of_scope": check_has_out_of_scope,
    "no_vague_criteria": check_no_vague_criteria,
}
