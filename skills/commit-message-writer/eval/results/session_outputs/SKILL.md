---
name: commit-message-writer
description: Writes a git commit message summarizing a set of changes.
---

# Commit Message Writer

Given a description of a code change, write a commit message for it.

## Instructions

1. Read the change description.
2. Summarize what changed in one line (the header).
3. Use a conventional commit prefix (feat, fix, docs, refactor, chore, etc.) followed by a colon and the summary.
4. Keep it clear and professional.
5. If the change touches more than one file, you MUST add a body after the
   header: leave one blank line after the header, then write one or more
   lines of body text explaining what changed and why. Never leave a
   multi-file change as a header-only message. Keep every body line to 100
   characters or fewer.

   Example (change touches 3 files):

   ```
   refactor: extract shared retry logic into retry helper

   Move the duplicated retry logic from client.py, uploader.py, and
   downloader.py into a single shared src/api/retry.py helper. No
   behavior change.
   ```
6. If the change breaks backward compatibility (e.g. an existing caller,
   signature, or output format stops working as before), you MUST flag it
   as breaking using BOTH of the following — never just a plain-language
   note like "this is a breaking change" in the body, since that is not
   machine-detectable:
   - Add a `!` immediately after the type (and scope, if present) in the
     header, before the colon — e.g. `fix(config)!: ...`.
   - Add a footer line in the body that starts with exactly
     `BREAKING CHANGE:` followed by a description of what breaks.

   Example (breaking change):

   ```
   fix(config)!: add strict parameter to parse_config

   Update parse_config() in src/config.py to accept a strict parameter
   and update the caller in src/main.py accordingly.

   BREAKING CHANGE: callers passing a second positional argument to
   parse_config() will now bind it to strict instead of being rejected.
   ```

## Output

Return only the commit message text, nothing else.
