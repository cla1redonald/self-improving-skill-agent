---
name: owasp-review
description: Security audit mapped explicitly to the OWASP Top 10 (2021) and the relevant OWASP ASVS v4 chapters. Use when the user asks for an OWASP review, an ASVS check, a security audit against a recognised standard, or wants category-by-category security coverage of an API/auth boundary/web app. Produces a per-category pass/finding table with severity, evidence (file:line), and fixes.
owner: Claire
last-affirmed: 2026-07-13
---

# OWASP-Mapped Security Review

Audit the target code against the **OWASP Top 10 (2021)** and, where the surface
warrants depth (auth, sessions, crypto, input handling), the matching **OWASP ASVS
v4** chapters. Output a category-by-category table, not a freeform list: the point
of an OWASP review is provable *coverage*, so every category gets an explicit verdict
even when the verdict is "not applicable" or "pass".

## Scope

Default target: the diff/branch under discussion, or files the user names. If nothing
is specified, audit the auth/API boundary first (highest blast radius), then data
handling and input surfaces. Read the actual code: never infer a verdict from naming.

## The Top 10 (2021): every one gets a verdict

For each: state **PASS / FINDING / N/A**, and for findings give severity
(Critical/High/Medium/Low), `file:line` evidence, the concrete attack, and the fix.

1. **A01 Broken Access Control**: authz on every endpoint; horizontal/vertical
   privilege escalation; IDOR (can a user reach another user's rows?); function-level
   access (admin paths); missing deny-by-default; forced browsing; CORS as an
   access-control bypass. *Trace at least one concrete low-privilege→high-privilege
   path end to end.*
2. **A02 Cryptographic Failures**: secrets at rest (hashed vs plaintext tokens/
   passwords); TLS assumptions; weak/again-used algorithms; PKCE/JWT correctness;
   randomness source (CSPRNG vs Math.random); constant-time comparison where a
   timing oracle is reachable.
3. **A03 Injection**: SQL/NoSQL (parameterised vs string-built); command injection;
   XSS (output encoding in every HTML/attribute/JS/URL context); template injection;
   header/CRLF injection; ORM/`.rpc()` arg construction.
4. **A04 Insecure Design**: missing rate limits on auth/expensive ops; missing
   single-use/expiry on codes & tokens; trust boundaries; the threat model the design
   *assumes* (e.g. "single user") stated and checked; abuse cases.
5. **A05 Security Misconfiguration**: verbose errors/stack traces to clients; default
   creds; CORS `*`-with-credentials or over-broad origin reflection; missing security
   headers (CSP, frame-ancestors/X-Frame-Options, HSTS where relevant); RLS enabled +
   policy-correct; unnecessary methods/endpoints exposed.
6. **A06 Vulnerable & Outdated Components**: known-vuln deps (note, don't block on a
   full SCA unless asked); pinned/maintained; risky transitive patterns.
7. **A07 Identification & Authentication Failures**: credential brute-force
   protection; session/token lifecycle (expiry, rotation, revocation, single-use);
   token storage; predictable identifiers; auth bypass via fall-through; user
   enumeration on login/reset.
8. **A08 Software & Data Integrity Failures**: unsigned/untrusted update or
   deserialization paths; CI/build trust; integrity of confirm/replay flows
   (can a stored action be replayed or substituted?).
9. **A09 Security Logging & Monitoring Failures**: are auth failures/abuse
   observable? AND the inverse (just as important): are **secrets leaking into logs**, specifically
   passwords, tokens, codes, keys? Grep the log lines.
10. **A10 SSRF**: any server-side fetch built from user-controlled input; URL
    allow-listing; the in-process/self-fetch pattern (is the host/path attacker-
    influenced?).

## ASVS deep-dive (when the surface justifies it)

If the target is an auth/session/crypto/input boundary, add a focused ASVS v4 pass on
the relevant chapters and cite control numbers where useful:
- **V2 Authentication** (passwords, MFA, lifecycle, brute-force)
- **V3 Session Management** (token binding, rotation, expiry, revocation)
- **V4 Access Control**
- **V5 Validation, Sanitization & Encoding** (the XSS/injection contexts)
- **V7 Cryptography** (storage, randomness, algorithms)
- **V8/V9 Data Protection & Comms**

Pick the chapters that fit; don't pad with irrelevant ones.

## Method

1. **Map the surface first**: list the endpoints/entry points and the trust
   boundaries before judging anything. An OWASP review without an attack-surface map
   is theatre.
2. **Read, then verify by tracing**: for the access-control and auth categories,
   trace a real request path (low-privilege principal → protected action) and say
   exactly where it's stopped, or that it isn't.
3. **Grep for the cheap-but-deadly**: secrets in logs (A09), `Math.random` in a
   security context (A02), `dangerouslySetInnerHTML`/unescaped interpolation (A03),
   `origin: '*'` + `credentials` (A05), string-built SQL (A03).
4. **State the assumed threat model** and check the code actually matches it
   (e.g. "single-user personal app" changes what counts as exploitable: say so, but
   still flag anything that breaks under a *plausible* future like multi-user).
5. **Be exploit-oriented.** A finding needs a concrete attack and a `file:line`, or
   it's a recommendation, not a finding. Don't inflate severity; don't bury a real one.

## Output format

```
# OWASP Review: <target>

**Attack surface:** <endpoints / entry points / trust boundaries, 3-6 lines>
**Assumed threat model:** <one line, and whether the code matches it>

## Top 10 coverage
| # | Category | Verdict | Notes |
|---|----------|---------|-------|
| A01 | Broken Access Control | PASS / FINDING(sev) / N/A | one-line |
| ... | ... | ... | ... |

## Findings (by severity)
### CRITICAL / HIGH / MEDIUM / LOW
- **[Axx] <title>**, `file:line`, attack, fix

## ASVS deep-dive (<chapters audited>)
- <control area>: PASS / FINDING: evidence

## Recommendations (non-blocking)
- ...

**Verdict: SHIP / FIX-FIRST** (+ minimal blocker list if FIX-FIRST)
```

Keep clean categories to one line. Spend the words on real findings and the traced
paths. If a prior plain security review exists, cross-check that its fixes still hold
rather than re-deriving from scratch.
