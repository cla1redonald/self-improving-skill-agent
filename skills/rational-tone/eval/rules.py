"""Deterministic checks for the rational-tone skill's own numeric rules.

Translates the skill's stated thresholds (sentence length, hinge-colon and
semicolon budgets, evidence-before-interpretation ordering, no repeated
opening phrases) into regex/structural checks. Two things this deliberately
does NOT try to grade, because they need judgment a regex can't fake:

- Severity assignment (rule 7): whether Critical/Significant/Moderate/Mild/
  Observation was assigned correctly from the evidence. Left out rather than
  faked with a bad heuristic.
- Section-opening pattern variety (rule 4) and descriptive-vs-evaluative
  framing (rule 5): these need multi-section documents to even apply, which
  single-finding test cases don't produce.

Sentence splitting is a simple heuristic (split on . ! ? followed by
whitespace/end, with light guards against common abbreviations and decimal
numbers), good enough for a rough eval, not a real sentence tokenizer.
"""

import re

ABBREV_GUARD = re.compile(r"\b(?:e\.g|i\.e|etc|vs|Mr|Mrs|Dr|approx)\.$", re.IGNORECASE)
# Tolerate markdown emphasis markers sitting between the sentence-ending
# punctuation and the next word ("engineer.** One ..." from a bolded topic
# sentence), found live: the naive version missed this split entirely and
# treated two sentences as one.
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\*{0,2}\s+(?=\*{0,2}[A-Z(\"'])")
HEADING_LINE_RE = re.compile(r"^\s{0,3}#{1,6}\s+.*$", re.MULTILINE)

EVALUATIVE_OPENERS = [
    "this is", "that is", "this means", "this suggests", "this indicates",
    "inadequate", "concerning", "problematic", "worrying", "poor", "weak",
    "insufficient", "unacceptable", "troubling",
]


def _split_sentences(text: str):
    # Strip markdown headings first: a "# Finding: ..." title line is
    # structural markup, not a prose sentence, and got counted as one live.
    text = HEADING_LINE_RE.sub("", text)
    # Merge lines, split on paragraph breaks first so cross-finding text
    # doesn't get treated as one run-on sentence.
    paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    sentences = []
    for para in paragraphs:
        raw_splits = SENTENCE_SPLIT_RE.split(para)
        buf = ""
        for piece in raw_splits:
            buf = f"{buf} {piece}".strip() if buf else piece
            if not ABBREV_GUARD.search(buf):
                sentences.append(buf)
                buf = ""
        if buf:
            sentences.append(buf)
    return [s for s in sentences if s]


def _word_count(sentence: str) -> int:
    return len(re.findall(r"\S+", sentence))


def check_mean_sentence_length_le_22(message, case):
    sentences = _split_sentences(message)
    if not sentences:
        return False, "no sentences found to measure"
    mean = sum(_word_count(s) for s in sentences) / len(sentences)
    ok = mean <= 22
    return ok, "" if ok else f"mean sentence length {mean:.1f} words exceeds 22"


def check_no_sentence_over_40(message, case):
    sentences = _split_sentences(message)
    over = [(s, _word_count(s)) for s in sentences if _word_count(s) > 40]
    ok = not over
    return ok, "" if ok else f"{len(over)} sentence(s) exceed 40 words (longest: {max(w for _, w in over)})"


def check_evidence_before_interpretation(message, case):
    sentences = _split_sentences(message)
    if not sentences:
        return False, "no sentences found to check"
    first = sentences[0].strip().lower()
    starts_evaluative = any(first.startswith(opener) for opener in EVALUATIVE_OPENERS)
    if starts_evaluative:
        return False, f"first sentence opens with an evaluative claim, not a fact: {sentences[0]!r}"
    # Only demand a digit when the case's underlying facts are actually
    # numeric (e.g. "31%"). Some genuine facts aren't ("one engineer holds
    # sole access"), requiring a number there would fail a correctly-ordered
    # finding just for lacking a statistic it was never given.
    if case.get("requires_numeric_evidence", True) and not re.search(r"\d", sentences[0]):
        return False, f"first sentence contains no concrete figure, expected one for this case's facts: {sentences[0]!r}"
    return True, ""


# Cheap proxy for "a full clause elaborating the claim" (the skill's definition
# of a hinge colon) vs. a flat list of nouns after a list-introducer colon: a
# clause almost always carries a finite verb, a noun list usually doesn't.
CLAUSE_VERB_RE = re.compile(
    r"\b(is|are|was|were|has|have|had|does|do|did|means|exist|exists|existed|"
    r"allow|allows|block|blocks|create|creates|cause|causes|require|requires|"
    r"include|includes|result|results|lead|leads|would|could|can|will|must|should)\b",
    re.IGNORECASE,
)


def check_hinge_colon_budget(message, case):
    sentences = _split_sentences(message)
    if not sentences:
        return False, "no sentences found to measure"

    def is_hinge_colon(sentence: str) -> bool:
        if ":" not in sentence:
            return False
        after = sentence.split(":", 1)[1].strip()
        # Short continuation, or a comma-separated list of nouns with no verb:
        # a list-introducer or label, not a hinge.
        if len(re.findall(r"\S+", after)) < 4:
            return False
        return bool(CLAUSE_VERB_RE.search(after))

    hinge_count = sum(1 for s in sentences if is_hinge_colon(s))
    pct = hinge_count / len(sentences)
    ok = pct <= 0.10
    return ok, "" if ok else f"{hinge_count}/{len(sentences)} sentences ({pct:.0%}) use a hinge colon, exceeds 10%"


def check_semicolon_budget(message, case):
    sentences = _split_sentences(message)
    if not sentences:
        return False, "no sentences found to measure"
    semi_count = sum(1 for s in sentences if ";" in s)
    pct = semi_count / len(sentences)
    ok = pct <= 0.10
    return ok, "" if ok else f"{semi_count}/{len(sentences)} sentences ({pct:.0%}) contain a semicolon, exceeds 10%"


def check_no_repeated_opening_phrase(message, case):
    paragraphs = [p.strip() for p in message.strip().split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        return False, f"expected multiple findings separated by blank lines, found {len(paragraphs)}"
    openers = []
    for para in paragraphs:
        words = re.findall(r"\S+", para)[:3]
        openers.append(" ".join(words).lower().strip(".,;:"))
    seen = set()
    dupes = [o for o in openers if o in seen or seen.add(o)]
    ok = not dupes
    return ok, "" if ok else f"repeated 3-word opening across findings: {dupes}"


RULES = {
    "mean_sentence_length_le_22": check_mean_sentence_length_le_22,
    "no_sentence_over_40": check_no_sentence_over_40,
    "evidence_before_interpretation": check_evidence_before_interpretation,
    "hinge_colon_budget": check_hinge_colon_budget,
    "semicolon_budget": check_semicolon_budget,
    "no_repeated_opening_phrase": check_no_repeated_opening_phrase,
}
