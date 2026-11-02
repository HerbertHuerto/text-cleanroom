# v0.4 functional smoke on public-source prose

Seven real API calls on 2026-11-02, using the same three public-source originals
as [the earlier pilot](../2026-11-02/README.md). They concern historical Italian
elections, a WHO mpox statement and European flood-recovery funding. These are
AI-generated briefings of public material, not human-written negative controls.

The isolated lab project and organization were observed OFF at 00:05 UTC; those
settings were not changed for these runs. Model: `gpt-6-sol`, fixed official API
endpoint, exact project echo checked, no provider fallback. Private identifiers,
credentials and full receipts are not published. Public hashes bind originals,
ledgers and candidates; `results.json` contains token usage and observation basis.

## What was run

1. Six first drafts: `restructure` and the initial `explain` outline for each case.
2. Both Spanish drafts duplicated the protected acronym FSUE outside its frozen
   placeholder. The integrity check correctly reported `requires_review`.
3. The generation instructions were clarified to prohibit raw fragment repetition;
   `explain` was made explicitly conditions-first. One Spanish repair was generated
   from the original ledger, not from the prior draft. It passes the integrity checks.
4. The final runner also reports ledger copying and hashes its instruction/payload
   inputs. Prompt revisions are retained in `prompts.json`; they were reconstructed
   from the source edits, not contemporaneously captured in the first six receipts.

All seven candidates remain here, including the two flagged drafts. Two prompt
revisions and one selected repair mean this is **not a controlled ranking of
strategies**. No claim that v0.4 removes more watermark than v0.3 is supported.

| Case / draft | Integrity result | Longest copied editable run, words |
| --- | --- | ---: |
| Elections / restructure | No heuristic differences | 19 |
| Elections / initial explain | No heuristic differences | 15 |
| Health / restructure | No heuristic differences | 16 |
| Health / initial explain | No heuristic differences | 11 |
| Floods / restructure | Review: FSUE count 1 → 2 | 9 |
| Floods / initial explain | Review: FSUE count 1 → 2 | 10 |
| Floods / revised explain repair | No heuristic differences | 8 |

The `*-wording.json` reports were replayed with the final diagnostic code. They
exclude protected islands and show both overlap directions, copied ranges and
length changes. Counts are regex words, not model tokens. **None is a detector
score, and smaller numbers do not prove removal or preserved meaning.** The
protected share deliberately retains unchanged material, possibly including signal.

## Review and reproduction

[review.md](review.md) records an agent's two-way factual review against the
originals, including number/entity links, negations and historical framing. It
is not independent human approval. Exact fragment counts and wording diagnostics
cannot replace it; the case involving swapped prices from the earlier review
remains a counterexample to purely numeric validation.

Reproduce the offline diagnostics without credentials, from the repository root:

```sh
python3 skills/text-cleanroom/scripts/transformation.py examples/2026-11-02/floods-es/original.md examples/2026-11-02-v0.4/floods-es-explain-repair.md --ledger examples/2026-11-02-v0.4/floods-es-ledger.json
python3 -m unittest discover -s tests -v
```

Live reproduction requires a separately authorized OFF route, fresh settings
evidence and API budget; generation is stochastic and prompt revisions matter.
No new detector, key access application or third-party contact was used.

**Production detector calls: 0. Known-detected originals: 0. Production watermark
removal rate: not measured.** Seven calls consumed 6,804 input and 9,058 output
tokens (including reasoning); unit tests are separate from those live calls.
