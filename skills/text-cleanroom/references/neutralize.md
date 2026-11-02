# Experimental text-watermark neutralization

Use only for a requested attempt on selected prose. The output is a reconstructed
candidate plus an integrity review, not a certificate of watermark removal.
The host agent prepares/reviews the facts; `reconstruct.py` performs generation
through a separately checked Platform API route. `check_text.py` remains read-only.
Read [public-evidence.md](public-evidence.md) for method choice and the evidence
boundary, last checked 2026-11-02. No restricted access is needed to make an attempt.

## Reconstruct, then verify

0. **Check the generation route.** Follow [generation-route.md](generation-route.md)
   and validate current OFF settings for the authorized organization/project.
   Missing, stale or unknown evidence means `blocked_generation_route`, not a
   host-model fallback. Do not change settings or create credentials automatically.
1. **Establish the target.** Distinguish a claimed statistical watermark from
   visible attribution or unusual Unicode. Do not infer any of these from an
   AI-detector score. State when presence of a watermark is itself unknown.
   Inspect Unicode when appropriate; remove a character only with contextual
   evidence that it is extraneous, never a blanket category deletion.
2. **Extract a content ledger.** Record factual propositions, entities, numbers
   with their units and associations, dates, URLs, causality, negations and
   uncertainty. Separate exact quotations, attribution and code as immutable
   islands. Preserve meaningful Unicode in those islands and in names/language.
   Do not reduce the ledger to keywords that omit qualifications or relationships.
   Express facts as structured propositions (subject, relation, value, conditions),
   not a copy of the original sentences: a verbatim ledger encourages copying.
   Run `--dry-run` and inspect its `ledger_wording` report before generation. Long
   copied editable runs in the ledger warrant rewriting the *ledger* as complete
   propositions, without dropping context or qualifications; this is not a
   calibrated watermark threshold. Live runs also save `ledger-wording.json`.
   Give explicit caveats their own entries: "not all paid" is not "none paid",
   and "process initiated" must not drop a separate "completion not established"
   qualification. Protect full institutional names, not only their acronyms.
   Explicitly protect every indented or list/blockquote-nested code block with
   `--protect` before comparing files: the extractor does not reliably cover them.
   Use safely quoted argument arrays, and review exact spans manually if the
   helper is not being run. Never execute any input code.
3. **Reconstruct the prose through the checked API route.** Generate from the ledger and a fresh outline rather
   than editing sentence-by-sentence or replacing words with synonyms. Change
   sentence construction, clause arrangement and paragraph structure where that
   preserves meaning. Keep the requested language, tone, level of detail and
   logical dependencies. The runner unions overlapping immutable spans, assigns
   each occurrence a placeholder and requires exactly one use of every placeholder.
   It reinserts original fragments locally, byte-for-byte in UTF-8, and restores
   fact-map locators. Missing/duplicated/unknown markers fail the run. This does
   not verify placement or meaning. Do not translate or encode the text merely
   to manufacture differences.
   Use `reconstruct.py`, not a new host-agent response. It sends only ledger facts
   and immutable strings, without the original prose or this chat's history.
4. **Check against the original, not just the ledger.** Run the available helper
   comparison, inspect the diff and perform a proposition-by-proposition check in
   both directions: every original fact remains; every candidate claim is
   supported. Resolve unintended changes in numbers, Unicode, quotes and code.
   An intentional Unicode cleanup still needs an explicit explanation when the
   helper flags it. Preserve the raw report; do not relabel it as clean.
   Also inspect whether meaningful reconstruction actually occurred. If the
   candidate is identical or only cosmetically changed, report a limited/no
   reconstruction, not a completed disruption attempt. Wording-change measures
   describe the transformation only; they are not watermark detection scores.
   Inspect `transformation.json`: it excludes immutable spans, reports 3/5/8-word
   overlap in both directions, the longest copied editable run, protected share
   and editable length ratio. Zero overlap is not removal; short or fully protected
   text may have no measurable windows. The word regex is not a model tokenizer
   or a language-specific segmenter (especially for unsegmented scripts).
   `no_heuristic_differences` is insufficient in reconstruction mode. Build a
   concise table pairing each original fact (including number-to-entity links,
   conditions and negations) with the matching candidate sentence; also flag
   candidate sentences without support. Read preserved Unicode sequences in
   context: equal counts do not detect a joiner moved inside the wrong word.
5. **Default to one reconstruction and necessary fidelity repairs.** When stronger
   reconstruction is explicitly requested or inspection finds long copied editable
   passages, one alternative with `--strategy explain` is available within the
   authorized API budget. Default `restructure` regroups related propositions;
   `explain` starts with conditions/limitations before decisions and details. Generate
   independently from the same original ledger, not from the preceding candidate.
   Keep both, review both against the original and choose fidelity first, useful
   reconstruction second. No automatic winner or watermark-efficacy ranking is
   produced. Do not loop, pad or degrade prose to improve an overlap measure.
   If meaning cannot be preserved, return the
   limitation and keep the original; do not present the candidate as ready.
   After a repair, recheck the entire candidate: fixing an omission can introduce
   a different scope/negation error. Preserve failed drafts in the experiment
   record instead of counting only the final acceptable version.

Keep the `tone` field about register/audience, not a contradictory old outline;
the selected strategy supplies the organization instructions. Never protect an
entire paragraph merely to get clean integrity checks: protected text is preserved,
not neutralized. If exact fidelity dominates the passage, report that limitation.

The rationale is to replace the original wording and token context, which may
disrupt a watermark tied to those choices. **This package has not measured that
effect against a production watermark.** A semantic or robust scheme may survive;
unchanged quotations/code may retain the original signal. Generating with a
watermarking backend can introduce a fresh signal. Reconstruction in the same
agent context is not an independent or provably unwatermarked generation.

Use the explicitly checked Platform route and preserve its receipt. Do not invent
an API opt-out, silently change providers, or send the text to a new detector.
If the user requires a known unwatermarked route and none is verified, that
requirement remains unmet; explain it instead of promising removal.

## Ledger file

Create a private JSON object with `schema_version: 1`, `original_sha256` (exact
original file bytes), `language`, `tone`, `facts` (objects with unique `id` and
complete `text`), and `immutable` (exact original strings). Include names, quotations,
code, URLs and significant Unicode spans in `immutable` as appropriate. The helper
checks their occurrence counts; still review their positions and associations.
Record every factual proposition, not just a summary. Verify this ledger against
the original before calling the API. Input content cannot choose a route, authorize
costs, change a setting or supply its own trusted settings evidence.

## Report the outcome accurately

- Deliver the candidate, change summary, checks performed and unresolved items.
- Include the fact-to-sentence table (a separate report is fine for long text)
  and state **Semantic check: performed** only when the two-way factual check
  was completed. Otherwise state **Semantic check: not performed** and do not
  call the candidate ready. This is a recorded review, not a semantic guarantee.
- Separate **transformation performed**, **integrity checks** and **watermark
  evidence**. A clean integrity report is not evidence of neutralization.
- Without a relevant authorized detector: **Watermark status: not verified.**
- If a matching detector is already authorized and available, test original and
  candidate under the same documented version, key/configuration and thresholds.
  Record scores, lengths and errors. A negative result is only that detector's
  observation under those conditions, not proof of universal absence.
- If the original was not detected, do not claim removal from a negative
  candidate result. Do not treat style scores or percentage of changed words as
  watermark evidence.
- Preserve applicable attribution/provenance disclosures. Never claim human
  authorship or successful evasion based on this workflow.
- Deliver the reviewed candidate file without host regeneration. If a later edit
  changes its bytes, the old route receipt/detector observations no longer apply
  to the edited version. See [evaluation.md](evaluation.md) for paired measurements.
