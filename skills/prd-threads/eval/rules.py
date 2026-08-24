"""Deterministic structural checks for the /prd-threads skill's output.

Grades against the skill's own thread template (Purpose / Reasoning Level /
Dependencies / Parallelizable) and its coverage requirement (every PRD
requirement maps to at least one thread), using keyword presence as a cheap
proxy for "this requirement was actually addressed" rather than semantic
matching.
"""

import re

# Heading LEVEL (## vs ###) is cosmetic: a downstream parallel-agent consumer
# cares about getting a distinct block with the required fields, not the exact
# hash count. Numbering starting at 0 vs 1 is likewise not checked here.
THREAD_HEADING_RE = re.compile(r"^#{2,3}\s*Thread\s*\d+", re.MULTILINE)
REASONING_LEVELS = ["Minimal", "Low", "Medium-High", "Medium", "High"]


def _split_threads(message: str):
    starts = [m.start() for m in THREAD_HEADING_RE.finditer(message)]
    if not starts:
        return []
    starts.append(len(message))
    return [message[starts[i]:starts[i + 1]] for i in range(len(starts) - 1)]


def check_has_multiple_threads(message, case):
    threads = _split_threads(message)
    ok = len(threads) >= 1
    return ok, "" if ok else "no '### Thread N: ...' blocks found"


def check_each_thread_has_purpose(message, case):
    threads = _split_threads(message)
    if not threads:
        return False, "no threads found to check"
    missing = [i for i, t in enumerate(threads) if not re.search(r"\*\*Purpose:\*\*", t)]
    ok = not missing
    return ok, "" if ok else f"thread(s) at position(s) {missing} missing a '**Purpose:**' field"


def check_each_thread_has_reasoning_level(message, case):
    threads = _split_threads(message)
    if not threads:
        return False, "no threads found to check"
    pattern = re.compile(r"\*\*Reasoning Level:\*\*\s*(" + "|".join(REASONING_LEVELS) + r")", re.IGNORECASE)
    missing = [i for i, t in enumerate(threads) if not pattern.search(t)]
    ok = not missing
    return ok, "" if ok else f"thread(s) at position(s) {missing} missing a valid '**Reasoning Level:**' field"


def check_each_thread_has_dependencies_field(message, case):
    threads = _split_threads(message)
    if not threads:
        return False, "no threads found to check"
    missing = [i for i, t in enumerate(threads) if not re.search(r"\*\*Dependencies:\*\*", t)]
    ok = not missing
    return ok, "" if ok else f"thread(s) at position(s) {missing} missing a '**Dependencies:**' field"


def check_each_thread_has_parallelizable_field(message, case):
    threads = _split_threads(message)
    if not threads:
        return False, "no threads found to check"
    missing = [i for i, t in enumerate(threads) if not re.search(r"\*\*Parallelizable:\*\*", t)]
    ok = not missing
    return ok, "" if ok else f"thread(s) at position(s) {missing} missing a '**Parallelizable:**' field"


def check_covers_requirement_keywords(message, case):
    lowered = message.lower()
    keywords = case.get("requirement_keywords", [])
    missing = [k for k in keywords if k.lower() not in lowered]
    ok = not missing
    return ok, "" if ok else f"requirement keyword(s) not referenced in any thread: {missing}"


def check_has_a_real_dependency(message, case):
    threads = _split_threads(message)
    pattern = re.compile(r"\*\*Dependencies:\*\*\s*(.+)")
    deps = [pattern.search(t).group(1).strip() for t in threads if pattern.search(t)]
    real = [d for d in deps if d.lower() not in ("none", "n/a", "-", "")]
    ok = len(real) >= 1
    return ok, "" if ok else "this PRD describes a dependency chain, but no thread names a real Dependencies value (all are 'None')"


RULES = {
    "has_multiple_threads": check_has_multiple_threads,
    "each_thread_has_purpose": check_each_thread_has_purpose,
    "each_thread_has_reasoning_level": check_each_thread_has_reasoning_level,
    "each_thread_has_dependencies_field": check_each_thread_has_dependencies_field,
    "each_thread_has_parallelizable_field": check_each_thread_has_parallelizable_field,
    "covers_requirement_keywords": check_covers_requirement_keywords,
    "has_a_real_dependency": check_has_a_real_dependency,
}
