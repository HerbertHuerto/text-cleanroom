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
- An opt-in reconstruction runner pinned to an OpenAI Platform project/API key,
  exact model and recently observed OFF settings; no host-model/provider fallback.
- A local paired-observation evaluator, not a watermark detector.
- Exact local reinsertion of immutable fragments using occurrence-specific placeholders.
- Two explicit reconstruction outlines, plus copied-passage diagnostics excluding
  protected material; no automatic selection by an unvalidated watermark proxy.
- No dependencies outside Python's standard library; Python 3.10+ required.
- No server, hooks, telemetry or automatic repository scanning.

The integrity helper and paired evaluator make no network requests. Ordinary
rewriting uses your host agent. Experimental neutralization uses an explicitly
authorized paid Platform API request, after route checks; the host prepares and
reviews the facts. It does not hide your original from the host agent. No API key
is bundled, discovered automatically or stored by the skill. This is not offline AI.

## Use

The installable folder is [`skills/text-cleanroom`](skills/text-cleanroom).
Place it in your agent's skills directory, then ask, for example:

> Use text-cleanroom to inspect this Markdown for unusual Unicode. Do not edit it.

> Rewrite this paragraph more clearly. Preserve quotations, names, prices,
> uncertainty and code; show the changes.

> Use text-cleanroom to attempt watermark neutralization on this passage.
> Reconstruct from the facts, preserve meaning and exact quotations/code,
> then report integrity checks separately from watermark evidence.

Neutralization now requires [a checked generation route](skills/text-cleanroom/references/generation-route.md).
Without one it stops with `blocked_generation_route` instead of regenerating with
an unknown host backend. The settings record is **operator-observed evidence, not
a provider attestation**; it expires after 24 hours. This version supports project
API keys and the official OpenAI endpoint only. No new keys/settings are created.

For local checks without an agent:

```sh
python3 skills/text-cleanroom/scripts/check_text.py inspect original.md
python3 skills/text-cleanroom/scripts/check_text.py compare original.md candidate.md --protect 'Jane Doe'
python3 skills/text-cleanroom/scripts/transformation.py original.md candidate.md --ledger ledger.json
python3 -m unittest discover -s tests -v
```

For explicit generation, prepare an original, factual ledger and private route
record as described in the route guide, then invoke `scripts/reconstruct.py`.
Generation supports selected passages up to 4 KiB UTF-8, 24 facts and an 8 KiB
ledger payload; oversized inputs are rejected before a paid request. The 1 MiB
limit above applies only to the read-only inspection/comparison helpers.
Deliver its reviewed `candidate.md` file unchanged: host regeneration would lose
the route evidence. A generated fact map still requires independent semantic review.
The default `--strategy restructure` regroups related facts; optional `--strategy explain`
provides a conditions-first alternative within an authorized API budget. Each command
is one request, never an automatic loop. Frozen-fragment placeholders improve byte
preservation, not watermark removal; their values remain visible to the generator.

`transformation.json` reports 3/5/8-word overlap, longest copied editable passage,
protected share and length ratio. It has no removal threshold, is not a tokenizer
or semantic check, and never says a low-overlap candidate is safe to deliver.
Preflight also checks wording retained in the factual ledger: copying source
sentences into the ledger defeats the purpose of reconstructing from propositions.
The [public evidence review](skills/text-cleanroom/references/public-evidence.md)
explains the implemented method, alternatives and limits as of **2026-11-02**.
The [v0.4 live functional smoke](examples/2026-11-02-v0.4/README.md) retains seven
real generations, including two flagged first drafts and their repair. It measures
execution/fidelity and wording changes, **not production-watermark removal**.

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

The controlled runner reduces accidental re-marking risk by binding generation
to recently observed OFF settings. It cannot independently query/attest those
settings or guarantee provider behavior. **No production textGrain effectiveness
has been measured.** [Paired evaluation](skills/text-cleanroom/references/evaluation.md)
binds supplied detector scores to text hashes and keeps reference/production
observations separate. Tests with synthetic scores are not effectiveness evidence.

### Live pilot, 2 November 2026

[Thirty ON/OFF-setting generations and three real-source reconstruction trials](examples/2026-11-02/README.md)
cover elections, public health and flood recovery in Italian, English and Spanish.
The report includes failed drafts, fidelity repairs and final fact checks.
It validates route execution and illustrates remaining semantic risks, **not
production textGrain removal**.

## Publishing

Publish only the skill folder, not this whole repository. ClawHub requires MIT-0.
Use the authenticated personal account after confirming `clawhub whoami`:

```sh
clawhub login
clawhub whoami
clawhub skill publish ./skills/text-cleanroom --slug text-cleanroom --name 'Text Cleanroom' --version 0.4.0 --categories creative,knowledge --topics text,markdown,editing
```

ClawHub publication is separate from pushing this repository to GitHub. A pending
registry release is not an installable release until its security checks pass.
See the [official publishing guide](https://github.com/openclaw/clawhub/blob/main/docs/publishing.md).

License: MIT-0. See [LICENSE](skills/text-cleanroom/LICENSE).
