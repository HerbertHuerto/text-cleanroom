# Text Cleanroom

A small agent skill for experimental text-watermark neutralization attempts,
reviewable cleanup and controlled prose rewriting. **It is not a watermark
detector and does not guarantee removal.** No production-watermark effectiveness
has been measured for this workflow.

## What ships

- Inspect, conservative cleanup, rewrite and experimental neutralize modes.
- Neutralize reconstructs prose from a content ledger and a fresh outline, then
  checks the candidate against the original. It is an attempt, not just a checker.
- A read-only Python helper for Unicode inspection, numeric/URL token comparisons,
  Unicode count changes, recognized code spans/fences, protected phrases and a diff.
- No dependencies outside Python's standard library; Python 3.10+ required.
- No server, hooks, telemetry, provider integration or automatic repository scanning.

The helper makes no network requests. Rewriting is performed by your host agent
using its existing model, so model access and any normal provider charges still
apply. This is not a promise of offline AI processing.

## Use

The installable folder is [`skills/text-cleanroom`](skills/text-cleanroom).
Place it in your agent's skills directory, then ask, for example:

> Use text-cleanroom to inspect this Markdown for unusual Unicode. Do not edit it.

> Rewrite this paragraph more clearly. Preserve quotations, names, prices,
> uncertainty and code; show the changes.

> Use text-cleanroom to attempt watermark neutralization on this passage.
> Reconstruct from the facts, preserve meaning and exact quotations/code,
> then report integrity checks separately from watermark evidence.

For local checks without an agent:

```sh
python3 skills/text-cleanroom/scripts/check_text.py inspect original.md
python3 skills/text-cleanroom/scripts/check_text.py compare original.md candidate.md --protect 'Jane Doe'
python3 -m unittest discover -s tests -v
```

On Windows use `python` if that is your Python 3 command. UTF-8 `.txt`, `.md`, and
`.markdown` files up to 1 MiB are supported. No document conversion is performed.

## Limits that matter

Unicode joiners and similar characters may be essential to language or emoji.
Inspection flags are not deletion instructions. Variation selectors, nonstandard
spaces and selected blank characters are listed, but no exhaustive hidden-data
detector is claimed. The checker recognizes top-level fences and inline code,
not all Markdown (indented or nested code needs manual/explicit protection).
It cannot identify every factual invariant or establish semantic equivalence.
Equal counts can hide moved joiners, swapped code/associations or inverted meaning.
Read the diff and verify facts in context. Reports can include sensitive input.
URL punctuation/case differences can cause false positives. Require valid JSON
with an expected `status`: an interpreter failure is not a successful check.

No check here demonstrates absence of a statistical watermark. No proprietary
watermark detector is included. A rewrite is a new candidate, not a certificate
of human authorship or undetectability. Originals are not changed by the helper.
The generating backend may add a new watermark, and preserved text can retain
an old one. See the [neutralization workflow](skills/text-cleanroom/references/neutralize.md)
for the actual method and reporting limits.

## Publishing

Publish only the skill folder, not this whole repository. ClawHub requires MIT-0.
Use the authenticated personal account after confirming `clawhub whoami`:

```sh
clawhub login
clawhub whoami
clawhub skill publish ./skills/text-cleanroom --slug text-cleanroom --name 'Text Cleanroom' --version 0.2.0 --categories creative,knowledge --topics text,markdown,editing
```

ClawHub publication is separate from pushing this repository to GitHub. A pending
registry release is not an installable release until its security checks pass.
See the [official publishing guide](https://github.com/openclaw/clawhub/blob/main/docs/publishing.md).

License: MIT-0. See [LICENSE](skills/text-cleanroom/LICENSE).
