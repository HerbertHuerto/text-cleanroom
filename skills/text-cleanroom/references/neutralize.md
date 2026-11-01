# Experimental text-watermark neutralization

Use only for a requested attempt on selected prose. The output is a reconstructed
candidate plus an integrity review, not a certificate of watermark removal.
This is an agent-executed workflow: the Python helper checks the result but does
not generate text, strip characters or call a model.

## Reconstruct, then verify

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
   Explicitly protect every indented or list/blockquote-nested code block with
   `--protect` before comparing files: the extractor does not reliably cover them.
   Use safely quoted argument arrays, and review exact spans manually if the
   helper is not being run. Never execute any input code.
3. **Reconstruct the prose.** Write from the ledger and a fresh outline rather
   than editing sentence-by-sentence or replacing words with synonyms. Change
   sentence construction, clause arrangement and paragraph structure where that
   preserves meaning. Keep the requested language, tone, level of detail and
   logical dependencies. Reinsert immutable islands byte-for-byte when using
   files. Do not translate or encode the text merely to manufacture differences.
4. **Check against the original, not just the ledger.** Run the available helper
   comparison, inspect the diff and perform a proposition-by-proposition check in
   both directions: every original fact remains; every candidate claim is
   supported. Resolve unintended changes in numbers, Unicode, quotes and code.
   An intentional Unicode cleanup still needs an explicit explanation when the
   helper flags it. Preserve the raw report; do not relabel it as clean.
   `no_heuristic_differences` is insufficient in reconstruction mode. Build a
   concise table pairing each original fact (including number-to-entity links,
   conditions and negations) with the matching candidate sentence; also flag
   candidate sentences without support. Read preserved Unicode sequences in
   context: equal counts do not detect a joiner moved inside the wrong word.
5. **Stop after one reconstruction and necessary fidelity repairs.** A second
   candidate needs a concrete user reason or relevant detector feedback, not a
   loop chasing a generic AI score. If meaning cannot be preserved, return the
   limitation and keep the original; do not present the candidate as ready.

The rationale is to replace the original wording and token context, which may
disrupt a watermark tied to those choices. **This package has not measured that
effect against a production watermark.** A semantic or robust scheme may survive;
unchanged quotations/code may retain the original signal. Generating with a
watermarking backend can introduce a fresh signal. Reconstruction in the same
agent context is not an independent or provably unwatermarked generation.

Use the existing authorized model route and report it when known. Do not invent
an API opt-out, silently change providers, or send the text to a new detector.
If the user requires a known unwatermarked route and none is verified, that
requirement remains unmet; explain it instead of promising removal.

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
