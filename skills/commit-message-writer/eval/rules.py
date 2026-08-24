"""Deterministic, rule-based checks for commit messages.

Kept mechanical on purpose: the Managed Agents Outcomes docs warn that a
grader scores each rubric criterion independently, so vague criteria produce
noisy loops. Same logic applies here — every check is a yes/no structural
test, not a judgment call, so the eval is cheap, fast, and reproducible.
"""

import re

VALID_TYPES = r"(feat|fix|refactor|docs|test|chore|perf|style|build|ci|revert)"
HEADER_RE = re.compile(rf"^{VALID_TYPES}(\([\w./-]+\))?!?: .+")

VAGUE_PHRASES = [
    "misc changes",
    "various fixes",
    "fix stuff",
    "update files",
    "minor changes",
    "wip",
    "small changes",
    "cleanup",
]

# Crude but deterministic: reject the most common non-imperative verb forms.
NON_IMPERATIVE_PREFIXES = (
    "added", "adds", "adding",
    "fixed", "fixes", "fixing",
    "updated", "updates", "updating",
    "changed", "changes", "changing",
    "removed", "removes", "removing",
    "refactored", "refactors", "refactoring",
    "renamed", "renames", "renaming",
)


def _split(message: str):
    lines = message.strip("\n").split("\n")
    header = lines[0] if lines else ""
    body_lines = lines[1:]
    # Drop a single leading blank line (conventional header/body separator).
    if body_lines and body_lines[0].strip() == "":
        body_lines = body_lines[1:]
    return header, body_lines


def check_header_type_prefix(message, case):
    header, _ = _split(message)
    ok = bool(HEADER_RE.match(header))
    return ok, "" if ok else f"header does not start with a valid conventional-commit type: {header!r}"


def check_header_length_72(message, case):
    header, _ = _split(message)
    ok = len(header) <= 72
    return ok, "" if ok else f"header is {len(header)} chars, exceeds 72: {header!r}"


def check_no_trailing_period_header(message, case):
    header, _ = _split(message)
    ok = not header.rstrip().endswith(".")
    return ok, "" if ok else f"header ends with a period: {header!r}"


def check_imperative_mood(message, case):
    header, _ = _split(message)
    match = HEADER_RE.match(header)
    if not match:
        return False, "cannot check mood: header does not match expected format"
    summary = header[match.end(2) if match.group(2) else match.end(1):].lstrip(":!").strip()
    first_word = summary.split(" ", 1)[0].lower() if summary else ""
    ok = first_word not in NON_IMPERATIVE_PREFIXES
    return ok, "" if ok else f"first word after the type is not imperative mood: {first_word!r}"


def check_no_vague_phrases(message, case):
    lowered = message.lower()
    hit = next((p for p in VAGUE_PHRASES if p in lowered), None)
    return hit is None, "" if hit is None else f"contains a banned vague phrase: {hit!r}"


def check_requires_body_multi_file(message, case):
    _, body_lines = _split(message)
    non_empty_body = [l for l in body_lines if l.strip()]
    ok = len(non_empty_body) >= 1
    return ok, "" if ok else "change touches multiple files but the message has no body"


def check_body_line_length_100(message, case):
    _, body_lines = _split(message)
    too_long = [l for l in body_lines if len(l) > 100]
    ok = not too_long
    return ok, "" if ok else f"{len(too_long)} body line(s) exceed 100 chars"


def check_mentions_breaking_change(message, case):
    header, body_lines = _split(message)
    has_bang = bool(re.match(rf"^{VALID_TYPES}(\([\w./-]+\))?!:", header))
    has_footer = any("BREAKING CHANGE:" in l for l in body_lines)
    ok = has_bang or has_footer
    return ok, "" if ok else "breaking change not flagged with '!' after the type or a 'BREAKING CHANGE:' footer"


RULES = {
    "header_type_prefix": check_header_type_prefix,
    "header_length_72": check_header_length_72,
    "no_trailing_period_header": check_no_trailing_period_header,
    "imperative_mood": check_imperative_mood,
    "no_vague_phrases": check_no_vague_phrases,
    "requires_body_multi_file": check_requires_body_multi_file,
    "body_line_length_100": check_body_line_length_100,
    "mentions_breaking_change": check_mentions_breaking_change,
}
