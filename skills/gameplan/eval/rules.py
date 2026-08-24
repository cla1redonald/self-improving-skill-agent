"""Deterministic structural checks for the /gameplan skill's output.

Grades against the skill's own template and Exit Criteria: a stated
complexity level, numbered steps that reference concrete files, a
dependencies section, and risks with mitigations. Doesn't check the
file-write/git-commit side effects, same scoping note as the /spec eval.
"""

import re

COMPLEXITY_ORDER = ["Low", "Medium", "Medium-High", "High"]
COMPLEXITY_RE = re.compile(r"\*\*Complexity:\*\*\s*\*{0,2}(Low|Medium-High|Medium|High)\*{0,2}", re.IGNORECASE)
FILE_TOKEN_RE = re.compile(
    r"[A-Za-z0-9_\-./]+\.(py|ts|tsx|js|jsx|json|md|yaml|yml|css|scss|sql|go|rb|java|rs)\b"
    r"|(?:^|[\s`(])[A-Za-z0-9_\-]+/[A-Za-z0-9_\-./]+"
)


def _extract_complexity(message: str):
    match = COMPLEXITY_RE.search(message)
    if not match:
        return None
    # Normalize casing since the regex is case-insensitive.
    raw = match.group(1)
    for level in COMPLEXITY_ORDER:
        if level.lower() == raw.lower():
            return level
    return None


def check_has_complexity(message, case):
    level = _extract_complexity(message)
    ok = level is not None
    return ok, "" if ok else "no '**Complexity:** Low|Medium|Medium-High|High' line found"


def _extract_section(message: str, heading: str):
    # Prefix-tolerant on the heading line itself ("## Steps (Sequential...)"
    # is a reasonable elaboration, not a template violation): only the
    # section body is what gets checked for structure.
    pattern = re.compile(rf"^##\s*{re.escape(heading)}\b[^\n]*\n(.*?)(?:^##\s|\Z)",
                          re.MULTILINE | re.DOTALL | re.IGNORECASE)
    match = pattern.search(message)
    return match.group(1) if match else None


# The template specifies a numbered list ("1. [Step ...]"), but a "#### Step 1.1"
# / "#### Phase 2" sub-header scheme conveys the same thing: ordered, concrete,
# individually addressable steps, just via headers instead of list markers.
STEP_ITEM_RE = re.compile(
    r"^\s*(?:\d+\.\s+\S|#{2,5}\s*(?:Step|Phase)\s*\d|#{2,5}\s*\d+[.)]\s+\S)",
    re.MULTILINE | re.IGNORECASE,
)


def check_has_numbered_steps(message, case):
    body = _extract_section(message, "Steps")
    if body is None:
        return False, "no '## Steps' section found"
    steps = STEP_ITEM_RE.findall(body)
    ok = len(steps) >= 2
    return ok, "" if ok else f"'## Steps' section has {len(steps)} identifiable step(s) (numbered or Step/Phase headers), expected at least 2"


def check_steps_reference_files(message, case):
    hits = FILE_TOKEN_RE.findall(message)
    ok = len(hits) >= 1
    return ok, "" if ok else "no step mentions a concrete file path or filename"


def check_has_dependencies_section(message, case):
    ok = bool(re.search(r"^##\s*Dependencies\b", message, re.MULTILINE | re.IGNORECASE))
    return ok, "" if ok else "no '## Dependencies' section found"


def check_has_risks_with_mitigation(message, case):
    body = _extract_section(message, "Risks")
    if body is None:
        return False, "no '## Risks' section found"
    body = body.strip()
    ok = len(body) > 0 and body.lower() not in ("none", "n/a", "-")
    return ok, "" if ok else "'## Risks' section is present but empty or a placeholder"


def check_flags_high_complexity_appropriately(message, case):
    level = _extract_complexity(message)
    if level is None:
        return False, "cannot check complexity threshold: no complexity line found"
    expected_min = case.get("expected_min_complexity")
    if expected_min not in COMPLEXITY_ORDER:
        return True, ""
    ok = COMPLEXITY_ORDER.index(level) >= COMPLEXITY_ORDER.index(expected_min)
    return ok, "" if ok else f"assessed complexity {level!r} is below the expected floor {expected_min!r} for a change this large"


RULES = {
    "has_complexity": check_has_complexity,
    "has_numbered_steps": check_has_numbered_steps,
    "steps_reference_files": check_steps_reference_files,
    "has_dependencies_section": check_has_dependencies_section,
    "has_risks_with_mitigation": check_has_risks_with_mitigation,
    "flags_high_complexity_appropriately": check_flags_high_complexity_appropriately,
}
