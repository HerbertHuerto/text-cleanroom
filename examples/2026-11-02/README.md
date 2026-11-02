# Live pilot — 2 November 2026

**This is a route/integrity pilot, not evidence that textGrain was removed.**
We generated 30 public-source briefings under observed ON/OFF project settings,
then reconstructed three ON-setting plain-prose outputs through the OFF route.
No production watermark detector was available or called. The removal rate is
**unknown**, not zero and not 100%.

## Why these real-world cases?

The EU's [Recital 133](https://ai-act-service-desk.ec.europa.eu/en/ai-act/recital-133)
identifies information integrity, misinformation/manipulation at scale, fraud,
impersonation and deception as reasons for machine-readable provenance.
[Article 50](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50)
distinguishes providers' marking obligations from disclosure for public-interest
text, with specific exceptions including human review/editorial responsibility.
The following are representative public-interest tasks, **not proven incidents
that caused the law**, nor a claim that these official source texts contain a watermark.

| Case | Official factual source | Sensitive distinctions tested |
| --- | --- | --- |
| [Italian elections](elections-it/review.md) | [European Parliament, 2024 Italy voting guide](https://elections.europa.eu/it/how-to-vote/it/) | Historical dates; same-list preferences and sex condition; not compulsory; threshold versus voting age. |
| [English public health](health-en/review.md) | [WHO, mpox declaration, 14 August 2024](https://www.who.int/news/item/14-08-2024-who-director-general-declares-mpox-outbreak-a-public-health-emergency-of-international-concern) | Possible spread, not certainty; required versus released funds; process started, not completed. |
| [Spanish flood recovery](floods-es/review.md) | [European Commission in Spain, 3 October 2025](https://spain.representation.ec.europa.eu/noticias-eventos/noticias-0/casi-1-600-millones-de-euros-de-fondos-de-la-ue-ayudaran-espana-recuperarse-de-las-devastadoras-2025-10-03_es) | Proposed versus approved versus paid; advance subtraction; up to 95% of eligible costs, not all losses. |

We authored factual ledgers from these sources. The test texts are new AI-generated
briefings grounded in real material, **not verbatim official articles or verified
human-negative controls**. All are historical; they are not current voting or
medical instructions, or a current aid-payment report.

## Method and observed results

- One isolated project and a dedicated restricted API key; the working organization
  and Default project were not changed. The lab ended OFF.
- `gpt-6-sol` selected in the model-specific watermark settings and returned by
  every call. Exact project response headers matched the requested project.
- Structured-output arm: 4 independent samples per case per condition (24 total).
  Plain-prose arm: 1 sample per case per condition (6 total).
- Prompts/settings were identical across conditions within each arm/case. The
  experiment used OFF-before / ON / OFF-after blocks and shuffled the case order
  within structured blocks. This was **not a randomized, fully counterbalanced
  trial**; time, deployment, propagation and sampling confounds remain.
- ON and OFF mean saved settings observed in the authenticated UI, **not
  provider-attested labels or detected watermark presence/absence**. We did not
  establish marking coverage for each output format or individual sample.
- All 30 calls completed. No explicit watermark detector result appeared in the
  response bodies examined. Its absence is not evidence of no watermark.

| Case | OFF samples / word range | ON samples / word range |
| --- | --- | --- |
| Elections | 5 / 140–156 | 5 / 145–163 |
| Public health | 5 / 155–171 | 5 / 152–178 |
| Flood recovery | 5 / 179–190 | 5 / 179–193 |

These ranges combine the two output formats for an inventory only, **not a
statistical effect estimate**. Thirty samples on three prompts cannot identify
the production watermark, recover its secret, or validate a classifier. No
classifier was fitted. Short and constrained passages also limit detectability.

The 30 calls used 17,526 input and 32,731 output tokens (including reasoning).
Reconstruction/repair calls are additional and recorded in the selected receipts.
Original raw responses/settings observations are retained privately; this export
contains hashes, usage and the selected text pairs without account identifiers.

## Three reconstruction trials, including failures

The original for each trial was predetermined: its first plain-prose ON-setting
sample. We did not choose a favorable output after seeing reconstruction results.
The controlled runner used OFF settings, a factual ledger, a fresh outline and
exact protected spans. Sami then compared the full original and candidate in both
directions; this is **agent review, not independent human validation**.

| Case | Calls, including repairs | Final review | Original word 5-grams retained |
| --- | --- | --- | --- |
| Elections | 1 | No material factual discrepancy identified | 10.88% |
| Public health | 2 | Completion caveat restored | 58.55% |
| Flood recovery | 3 | Full name and not-all-paid qualification restored | 33.33% |

The last column is the fraction of unique original lowercased Unicode-word
5-grams still present in the final candidate, using Python `re.findall(r'\w+',
text.lower())`. It describes wording overlap only: **not watermark strength,
removal percentage, or human authorship**. Immutable content deliberately remains.
The election reconstruction also became shorter (149 → 102 whitespace-delimited
words); apparent detector changes would need length-aware controls.

Every first draft passed the numeric/Unicode/protected-string heuristics. Two
still required review repairs. The first flood repair introduced a new ambiguous
negation, caught by checking the entire revision again. Failed drafts and review
tables are published beside the final candidates, not erased from the record.
Historical framing in the final election/flood texts is conveyed through dated
past-tense context; the original explicit archive disclaimers are not verbatim.

Lessons incorporated in the workflow: give caveats their own ledger entries,
protect full names rather than acronyms alone, recheck the whole text after every
repair, and never treat `no_heuristic_differences` as semantic approval.

## What this resolves — and does not

The skill now performs an explicit paid API reconstruction with checked OFF
settings instead of silently letting an unknown host model add another signal.
It binds the route and candidate bytes, and retains integrity/semantic evidence.

It **does not demonstrate production-watermark neutralization**. OpenAI describes
[substantial editing as capable of weakening detection](https://openai.com/index/eu-text-provenance/),
but [text verification requires separate approved access](https://developers.openai.com/api/docs/guides/content-provenance).
Turning generation ON does not grant a verifier or reveal the secret watermark
key. There are no positive/negative detector controls or production scores in
this pilot. Do not invent them from the ON/OFF labels.

See [pilot.json](pilot.json), [samples.jsonl](samples.jsonl), and
[source-facts.json](source-facts.json). Generated fact-map locators in the sanitized
receipts are not the manual review; the linked `review.md` files record that step.
