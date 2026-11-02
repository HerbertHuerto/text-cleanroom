# Paired evaluation, without inventing detector evidence

`scripts/evaluate_pairs.py` summarizes already collected detector observations.
It does not call a detector, guess a secret key, use AI-style scores, or establish
the authenticity of imported scores. Do not fill a manifest with invented values
to demonstrate effectiveness. Unit-test fixtures are not experimental results.

For an authorized detector, preserve the same detector version, key/configuration,
tokenizer, decision threshold and direction for original and candidate. Use a
non-secret configuration ID, never publish a secret detector key. Store the texts
unchanged and bind their SHA-256 hashes to the score export. Include every planned
case, including failures; never report only successful rewrites. Run a known
positive and known negative control and establish the threshold independently of
the texts being evaluated. Follow the detector's access and usage conditions.

The manifest is a JSON object with `schema_version: 1`, `detector`, and `pairs`:

- `detector`: `name`, `version`, `scope` (`reference_known_key` or
  `production_authorized`), `configuration_id`, finite `threshold`, `positive_when`
  (`at_least` or `at_most`), and positive integer `minimum_tokens`.
- Each pair: unique `id`; `original`/`candidate` UTF-8 text file paths relative to
  the manifest; `original_sha256`/`candidate_sha256`; finite
  `original_score`/`candidate_score`; positive integer
  `original_tokens`/`candidate_tokens` counted using that detector's tokenizer.

```sh
python3 /path/to/text-cleanroom/scripts/evaluate_pairs.py measurements.json
```

The report distinguishes unchanged detection, detected-to-not-detected, undetected
baselines and insufficient length. Only eligible detected baselines enter the
transition denominator. A low score on an already negative original is not removal
evidence. Scores and counts are supplied observations, not independently verified.
A transition under a reference watermark says nothing conclusive about production
textGrain. Even an authorized production detector's negative is not universal absence.
Keep fidelity review and watermark measurements as separate columns in any report.

## Optional controlled ON/OFF experiment

With explicit authorization, an isolated test project can enable the provider's
watermark while the reconstruction project remains OFF. Do not change the user's
working organization/default project for an experiment. The flag is scoped to
organization/project and models, not a secret key provided to the customer.

Use the same pinned model, prompts and generation settings in both conditions;
record settings observations and routing for each. Randomize/interleave order and
collect multiple independent samples per prompt, with held-out prompts for any
statistical classifier. Stratify by length, language and domain, preserve all
outcomes, and compare original/reconstructed text alongside positive/negative
controls. Do not claim a handful of samples or vocabulary differences identify
the production secret or produce an official detector. Without authorized detector
access, this measures distributional differences, not certified watermark removal.

Current production evidence: **not measured by this package**. OpenAI's text
detector access is separately approved; enabling generation watermarking does not
grant access. [Official guidance](https://developers.openai.com/api/docs/guides/content-provenance)
