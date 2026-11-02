# Explicit Platform generation route

Neutralization must not silently reconstruct with the host model: that route may
introduce a fresh watermark. This version supports one opt-in route: a project
API key sent directly to `https://api.openai.com/v1/responses`. Ordinary editorial
rewrite can still use the host, but is not the controlled neutralization workflow.

## Verify settings, then bind the request

Use only an already authorized API account. Switching to paid API generation is
not implied by installing this skill: confirm the route if the user has not
authorized it. Never create keys, change watermark settings or change providers
merely to make a run succeed. A ChatGPT/Codex subscription is not an API key.

In the authenticated Platform UI, verify the organization identity, project ID,
organization Text provenance OFF and project OFF or inheriting that OFF default.
Record this outside the skill/source repository. Do not infer OFF from defaults,
an absent response field, the endpoint hostname or the model's own answer.

Example **settings-evidence.json** (replace identifiers and timestamp with the
actual observation; do not manufacture a fresh timestamp for an old check):

```json
{
  "schema_version": 1,
  "organization": "org-REPLACE",
  "project": "proj_REPLACE",
  "observed_at": "2026-11-02T09:00:00+00:00",
  "observer": "person or agent that inspected the authenticated settings",
  "organization_watermarking": false,
  "project_watermarking": "inherit",
  "organization_settings_url": "https://platform.openai.com/settings/organization/data-controls/text-provenance",
  "project_settings_url": "https://platform.openai.com/settings/proj_REPLACE/text-provenance"
}
```

Example **route.json** alongside that evidence:

```json
{
  "schema_version": 1,
  "provider": "openai_platform",
  "model": "REPLACE_WITH_EXACT_SUPPORTED_MODEL_ID",
  "organization": "org-REPLACE",
  "project": "proj_REPLACE",
  "credential_env": "OPENAI_API_KEY",
  "evidence_file": "settings-evidence.json",
  "evidence_sha256": "REPLACE_WITH_SHA256_OF_EVIDENCE_FILE_BYTES"
}
```

The credential must be a project API key supplied through the environment; do not
put it in the route, ledger, shell command, report or repository. The helper does
not discover credentials or read the host agent's authentication files. It does
not support custom proxies/endpoints, OAuth, other providers or model fallback.

The helper checks scope consistency, the evidence hash and an observation age of
at most 24 hours. It sends organization/project headers, requires an exact project
ID echo, rejects a contradictory canonical organization ID, and requires the
returned model ID to match exactly. The organization response header can contain
a legacy name instead of an `org-` ID; it is then recorded as not independently
mapped, not compared as if it were an ID. A model alias
that resolves to a different ID is rejected; pin the returned documented snapshot
after checking it, not by disabling the guard. A missing project echo fails closed.

**Trust boundary:** the evidence is an operator observation, not a provider-signed
attestation or a live settings query. A hash binds a record; it does not prove its
truth. Settings could change after observation. No documented per-request
`watermark=false` control is sent, and `store:false` controls storage, not marking.
Report `settings_basis: operator_observed_off_not_provider_attestation` and keep
`watermark_status: not_verified` even when generation succeeds.

## Execute without returning to host generation

Prepare the ledger described in [neutralize.md](neutralize.md), then run:

```sh
python3 /path/to/text-cleanroom/scripts/reconstruct.py original.md --ledger ledger.json --route route.json --out new-run --dry-run
python3 /path/to/text-cleanroom/scripts/reconstruct.py original.md --ledger ledger.json --route route.json --out new-run
# Optional independent alternative, only within the authorized generation budget:
python3 /path/to/text-cleanroom/scripts/reconstruct.py original.md --ledger ledger.json --route route.json --out alternative-run --strategy explain
```

Preflight validates files/settings without a network call; it does not test the
credential. Generation is limited to **4 KiB UTF-8 originals, 24 facts and 8 KiB
of serialized ledger payload**; larger inputs fail preflight. Select a coherent
short passage rather than silently truncating a document. The response allowance
is 16,384 tokens, including model reasoning and the fact map: the selected model
must support that allowance. This is headroom, not a guarantee against refusal or
excessive reasoning; incomplete responses still fail closed.
Actual execution is one paid API request, without automatic retry.
The output directory must not exist. On POSIX it is created as 0700, with files
0600; on Windows choose a private parent directory with appropriate ACLs.
Only the ledger and protected strings are sent, not the full original or agent
history. Those can still contain sensitive information. Network errors fail closed.

Outputs: `candidate.md`, `receipt.json`, `integrity.json`, `fact-map.json`,
`transformation.json`, `ledger-wording.json`. Preflight includes ledger-copying
diagnostics so copied source sentences can be identified before a paid request.
Immutable fragments are shown to the API with placeholders
for context, not hidden from the provider; the runner requires each placeholder
once and restores the fragment locally. Marker errors fail, not silently repair.
Exit 0 = preflight only; exit 1 = candidate generated, **review still required**;
exit 2 = failed. Read the JSON status, not the exit code alone. `failure.json`
means the run failed; never deliver partial files as ready. A flagged integrity
report is preserved, not relabeled clean. The fact map is model-generated locator
data, not a second reviewer or proof of meaning preservation.

After independent comparison with the original, deliver **the candidate file's
exact bytes**, through an attachment/file-copy channel. Do not ask the host model
to regenerate, paraphrase or silently repair that final text: it would lose the
route evidence and could add a new signal. If a correction requires generation,
use the same verified route with a repaired ledger and a new output directory.

## Sources checked 2026-11-02

- [OpenAI text provenance settings and limitations](https://help.openai.com/en/articles/8912793-provenance-signals-in-openai-generated-content)
- [Responses API](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)
- [Request scoping and response metadata](https://developers.openai.com/api/reference/overview)
- [Text detector access is separate](https://developers.openai.com/api/docs/guides/content-provenance)
