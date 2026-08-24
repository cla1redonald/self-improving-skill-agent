---
name: rational-tone
description: "Supplies the decision rules the Rational Partners writing guide leaves unstated, so the same brief produces the same shape of copy every time. Use when drafting or editing any RP client-facing prose, including DD report sections, assessment findings, board updates and executive summaries. Sits on top of the firm guide rather than replacing it."
metadata:
  owner: Claire
  last-affirmed: "2026-08-16"
---

# Rational Partners tone: the missing decision rules

The firm guide is the source of truth for voice, tone and vocabulary. Follow it.
This skill does not restate it and does not overrule it.

What it adds is the part the guide leaves open. Six of its rules state a
preference without stating a threshold, so two competent drafts can both claim
to follow them while looking different. One further rule is clear but is the
one most often missed. This file closes those seven gaps and nothing else.

Everything here is self-contained on purpose. It must work where the guide
cannot be fetched, which includes phone and any surface without the Insights
connector. Keep it that way: no tool calls, no file references, no shell.

Graded runs that produced these rules are recorded in
`~/.claude/reference/rational-tone-evals/`, deliberately outside this folder so
they do not ride along when the skill is packaged.

## 1. Evidence before interpretation

The most-missed rule in the guide, by a distance. In testing it was followed in
fewer than half of drafts, while every other clear rule held.

Within a finding, the observable fact comes first and the reading of it comes
second. Not in a later sentence: first.

Wrong:

> Test coverage is inadequate for a platform at this stage. Coverage sits at
> 31% with no gate in CI.

Right:

> Test coverage sits at 31%, with no coverage gate in continuous integration.
> That is below the 40 to 60% typically seen in production systems of this
> complexity, and it means a regression can reach production unchallenged.

The test: delete the first sentence of each finding. If what remains is only
interpretation, the fact came first and the order was right. If what remains is
still the facts, the finding led with the view and the order was wrong.

## 2. Sentence length

Mean at or below 22 words. No single sentence over 40.

**Check the tail, not just the mean.** On a real 8,500-word report the mean came
in at 20.4, inside the limit, while seventeen sentences ran over 40 and the
longest hit 54. The mean hid all of it.

**Split to a full stop.** The tempting fix for an over-long sentence is to break
it at an existing colon or semicolon, which satisfies this rule while leaving
the tic in place. See rule 8.

The guide says "prefer shorter" and gives no number, which is why length drifts.
These figures are calibrated to drafts the guide already produces well, so they
are not a new constraint, only the existing one made checkable.

## 3. Concerns-to-strengths balance

Count substantive sentences, not words, and not paragraphs. Concerns should be
55 to 65% of them.

Sentences that are scene-setting, transitional, or purely descriptive of
architecture count as neither. If the count falls outside the band, the fix is
to add or remove a finding, never to pad an existing one.

## 4. Section openings

Within one section, use one opening pattern throughout.

Across sections, do not use the same pattern in two consecutive sections. The
patterns are the four the guide names: company name plus verb, "The" plus entity
noun, "There is / are", and a transitional phrase.

This is what "vary the approach" means operationally. Varying within a section
reads as inconsistency; varying between sections reads as range.

## 5. Descriptive or evaluative opening

Not a free choice. Decide by what the section is for.

- **Descriptive** when the section reports a state of affairs the reader does
  not yet know. Architecture, tooling, team structure.
- **Evaluative** when the section renders the judgement the reader is paying
  for. Risk, capability, readiness.

If a section does both, open descriptive and turn evaluative at the pivot.

## 6. Choosing among the guide's characteristic phrases

Never reuse an opening phrase within one document. The guide offers roughly
forty and gives no selection rule, so the failure mode is reaching for the same
three all report. Track what you have used and pick an unused one.

**Track home-grown formulae too, not only the guide's list.** In practice the
guide's forty phrases were not the problem: an invented shape was. One report
carried nine paragraph openers of the form "One [noun] ...", none of which
appear anywhere in the guide, so a check scoped to the guide's list saw nothing
wrong. Any opening formula you have coined yourself, used more than twice in a
document, is a tell. Count the shapes you are repeating, not just the phrases
the guide happens to name.

## 7. Assigning severity

The guide maps severity to language but never says how to assign severity in
the first place. Assign it from evidence, using the first row that matches:

| Severity | Assign when |
|---|---|
| Critical | Customer data, funds or availability are exposed now, with no compensating control |
| Significant | A single point of failure with no mitigation underway, or a control that exists on paper and has never been exercised |
| Moderate | A real gap, but a workaround exists or mitigation is in progress |
| Mild | Below benchmark, and not load-bearing at the company's current scale |
| Observation | Recorded for completeness; no action implied |

Then use the guide's language ladder for the severity you assigned. Assign
first, phrase second. Doing it the other way round is how the same finding ends
up as "there may be value in" in one draft and "we strongly recommend" in the
next.

## 8. The substitution budget

A ban on a mark does not remove the habit behind it, it relocates it. The em
dash is banned, so the load moves to the colon, and nothing in the guide bounds
that. On a real report, 20% of sentences carried a mid-sentence hinge colon
before this rule existed. That is the em-dash tell wearing a different hat, and
it passed every other check in this file.

**Hinge colons: at or below 10% of sentences.** A hinge colon is one where what
follows is a full clause elaborating the claim before it. "Coverage is the
weak point: no gate exists in CI and nothing blocks a regression."

Count only hinge colons. These do not count, and must be excluded before you
work out the percentage, or the number you report will not be the number this
rule is about:

- list introducers ("The gaps are:")
- labels and lead-ins ("Observed:", "Enablers:")
- definitional appositions, where a noun phrase rather than a clause follows
- branch labels, and deliberate question-restatement inside worked examples

**Semicolon sentences: at or below 10%.** Same reasoning, simpler count: any
sentence containing a semicolon. Splitting an over-long sentence into a
semicolon chain moves the problem rather than fixing it.

**Short documents round down to zero.** A single finding is typically 3-5
sentences. One hinge colon in a 4-sentence finding is 25% of it, one in a
5-sentence finding is 20% — both already blow the 10% budget on their own. Do
the arithmetic before you use one: if the piece you are writing has fewer than
ten sentences total, one hinge colon (or one semicolon sentence) is already
over budget, so the working target for anything that short is zero of each,
not "one is probably fine." Reserve hinge colons and semicolon sentences for
documents long enough to have room for one, and default to a full stop or a
comma instead whenever you're drafting something short.

When a hinge colon is genuinely doing work, keep it. When it is standing in for
a full stop, a comma apposition, or a "because" or "so", it is a lazy hinge and
the rewrite is one of those three.

## Self-check before delivering

This check is internal working, not part of the deliverable. Run it silently,
in your head or in a scratch area you discard, and fix the draft accordingly.
**The final message you send back must contain only the requested prose (the
findings, the report section, the update) and nothing else.** Never print the
checklist, the counts, the rule names, or a "Self-check" heading in the
response. A response that includes both the finding and a self-check writeup
is two documents, not one, and the second one is graded by the same rules as
the first: a stray colon or long sentence in your own commentary breaks the
budget just as one in the finding does. If you catch yourself writing "Mean
sentence length:" or "Hinge colons:" in the output, delete that whole
section before sending.

Before delivering, silently confirm:

1. Mean sentence length, the longest sentence, and how many run over 40 words.
   The mean can sit inside the limit while the tail breaks it.
2. Substantive sentence count, and the concerns percentage.
3. The opening pattern used per section, in order.
4. Any opening phrase used more than once, and any home-grown opening formula
   used more than twice.
5. Hinge-colon percentage, with list introducers, labels and appositions
   excluded from the count.
6. Semicolon-sentence percentage.
7. For each finding: does the first sentence state a fact rather than a view?
8. For each recommendation: which severity row it matched, and why.

Fix anything that falls outside the rules before delivering. Do not act on a
number you have not actually counted, and do not show your counting.
