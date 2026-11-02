# Public evidence and method choice

Last checked: **2026-11-02**. These are public sources, not access to the deployed
secret key or an authorized production detector. Recheck before asserting a later
state. Do not request restricted access or contact authors as part of this skill.

## What supports the attempt

| Source | Finding and scope | Consequence here |
| --- | --- | --- |
| [OpenAI announcement](https://openai.com/index/eu-text-provenance/) | Editing can weaken detection; performance varies with length/domain. API marking is opt-in, unlike eligible EU ChatGPT/Codex rollout. | Reconstruct substantially through a checked OFF route, but never promise success. |
| [OpenAI technical report](https://cdn.openai.com/pdf/e9508624-d767-41b6-a26d-e34ca798ada6/textgrain-entropy-calibrated-watermarking-for-language-model-text.pdf) | textGrain couples token choices to keyed randomness derived from preceding context. Matching key/configuration are needed for its detector. | Changing wording and local context is a plausible intervention, not a measured production result. |
| [DIPPER, NeurIPS 2023](https://arxiv.org/abs/2303.13408) | Paragraph-level paraphrasing with lexical/content-order diversity weakens several evaluated detectors. Retrieval remains a separate defense. This predates textGrain. | Change clause construction and organization, not only synonyms. No claim of defeating every form of attribution/detection. |
| [SIRA, ICML 2025](https://proceedings.mlr.press/v267/cheng25c.html) | Targets tokens using self-information from an attack model; experiments cover seven watermark methods, not deployed textGrain. | Interesting benchmark comparator, not an implemented feature: this skill does not compute token self-information or reproduce those results. |
| [Smoothing Attack, EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.264/) | Studies confidence-related weaknesses across ten watermarks and open models. | Requires its own model/configuration and fidelity evaluation. Do not simulate confidence with a word-frequency heuristic. |
| [OpenAI provenance help](https://help.openai.com/en/articles/8912793-provenance-signals-in-openai-generated-content) | textGrain does not insert hidden characters. A project ON toggle does not grant detector access. | Unicode cleanup is a different operation. Do not search for a watermark in zero-width characters or API credentials. |

## Approaches not silently added

- **Full reconstruction with OFF settings:** the implemented attempt. Can lose
  meaning; exact fragments and original-vs-candidate review remain mandatory.
- **A second independent, conditions-first outline:** available as `--strategy explain`, compared
  with default `restructure`, only within an authorized generation budget. It is
  not established to outperform the default. Never choose a worse factual result
  to maximize wording differences.
- **Back-translation:** an optional research comparator, not the default or an
  automatic chain. It can change meanings and reintroduce a generation watermark.
- **Short-fragment assembly/encoding:** [no-textgrain's published results](https://github.com/HexCine/no-textgrain/blob/016055347f04c8446045417e0cd8cf438324544a/verification/2026-10-05/results.json)
  explicitly leave watermark effectiveness untested. Successful joining of pieces
  is not evidence of removal. We do not ship that as a verified workaround.
- **Known-key reimplementations:** [textgrain-eval](https://github.com/omarht27/textgrain-eval)
  is a reference experiment with its own setup. Its key is not OpenAI's deployed
  secret. Use `reference_known_key` in paired evaluation, never `production_authorized`.
- **Generic AI-detector scores, hidden-character deletion, padding, deliberate
  typos or stripping attribution:** not evidence or valid success criteria.

## Why inspect unchanged passages

An unmodified quotation or code island can retain its original signal. Exact
preservation intentionally takes priority. `transformation.py` excludes protected
spans when measuring editable wording and reports their share separately. It shows
3/5/8-word window overlap and the longest retained editable word run. Both original
retention and candidate copying fractions are reported, so padding cannot conceal
full retention of the original. These are **not tokenizer-context lengths** and
there is **no validated threshold that means removal**. Cosmetic-only changes or
long copied editable passages justify inspecting the transformation; low overlap
does not justify approving it. Do not alter exact islands to improve a metric.

The algorithms, placeholders and tests in this package improve execution and
review. They are not an implementation of textGrain, SIRA, DIPPER or a detector.
Local placeholder reinsertion preserves bytes; no watermark effect is attributed
to the placeholders themselves. More sophistication is not a substitute for data.

## Public-data evaluation protocol

1. Record source URLs, model/version, date, language, settings observation and
   exact original/candidate hashes. Keep public-source generated briefings distinct
   from verbatim human-authored controls. Do not treat an ON setting as a positive
   detector label or an OFF setting as a human-authored negative control.
2. Use complete factual ledgers. Keep original length and information, including
   caveats; do not shorten below a detector's useful range to manufacture a win.
   For research, stratify by language, domain and length using the actual model
   tokenizer where available. Word counts are only descriptive.
3. Record the first candidate, repairs, failures and all planned alternatives.
   Select for fidelity first, then useful reconstruction; do not cherry-pick a
   success rate from final drafts. A repeated pass on a previous candidate risks
   accumulating semantic errors; start alternatives from the original ledger.
4. Use `transformation.json` plus full integrity/diff and two-way semantic review.
   Report discarded facts, changed associations/negations and repair counts, not
   just generic similarity. Do not auto-approve from model-generated fact maps.
5. Only a matching known-key detector can support a **reference-scheme** result.
   Use paired scores and matching calibration/thresholds, record untreated,
   already-negative and too-short controls, and apply [evaluation.md](evaluation.md).
   None of that establishes an OpenAI production result without a matching detector.

The public three-language pilot in the repository contains live generation and
semantic failures/repairs, but no production detection. Tests with mocked API
responses or injected scores verify software behavior only. State those limits
alongside the results, not only in a footnote.
