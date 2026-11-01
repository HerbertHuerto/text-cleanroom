# Text Cleanroom

A small agent skill for reviewable text cleanup and controlled prose rewriting.
It is **not a watermark remover or AI-text detector**.

## What ships

- An agent workflow with inspect, conservative cleanup and requested rewrite modes.
- A read-only Python helper for Unicode inspection, numeric/URL token comparisons,
  explicit protected phrases and a bounded unified diff.
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
Inspection flags are not deletion instructions. The checker does not parse
Markdown, identify every factual invariant, or establish semantic equivalence.
Equal counts can hide swapped associations, changed units or inverted meaning.
Read the diff and verify facts in context. Reports can include sensitive input.

No check here demonstrates absence of a statistical watermark. No proprietary
watermark detector is included. A rewrite is a new candidate, not a certificate
of human authorship or undetectability. Originals are not changed by the helper.

## Publishing

Publish only the skill folder, not this whole repository. ClawHub requires MIT-0.
Use the authenticated personal account after confirming `clawhub whoami`:

```sh
clawhub login
clawhub whoami
clawhub skill publish ./skills/text-cleanroom --slug text-cleanroom --name 'Text Cleanroom' --version 0.1.0 --categories creative,knowledge --topics text,markdown,editing
```

ClawHub publication is separate from pushing this repository to GitHub. A pending
registry release is not an installable release until its security checks pass.
See the [official publishing guide](https://github.com/openclaw/clawhub/blob/main/docs/publishing.md).

License: MIT-0. See [LICENSE](skills/text-cleanroom/LICENSE).
