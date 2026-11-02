"""Validate operator-observed Platform settings, not the presence of a watermark."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import stat

MAX_JSON = 1024 * 1024
MAX_AGE_SECONDS = 24 * 60 * 60
ENDPOINT = "https://api.openai.com/v1/responses"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_json(path):
    source = Path(path)
    if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode):
        raise ValueError("JSON input must be a regular, non-symlink file")
    with source.open("rb") as handle:
        raw = handle.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise ValueError("JSON input exceeds 1 MiB")
    value = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value, digest(raw)


def require_keys(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError("unexpected or missing configuration fields")


def checked_string(value, pattern):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("invalid route identifier")
    return value


def validate_route(path, now=None):
    route, route_hash = load_json(path)
    require_keys(route, {"schema_version", "provider", "model", "organization",
                         "project", "credential_env", "evidence_file", "evidence_sha256"})
    if type(route["schema_version"]) is not int or route["schema_version"] != 1:
        raise ValueError("unsupported route schema")
    if route["provider"] != "openai_platform":
        raise ValueError("only the explicit OpenAI Platform API route is supported")
    checked_string(route["model"], r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
    checked_string(route["organization"], r"org-[A-Za-z0-9]{3,100}")
    checked_string(route["project"], r"proj_[A-Za-z0-9]{3,100}")
    checked_string(route["credential_env"], r"[A-Z][A-Z0-9_]{0,79}")
    checked_string(route["evidence_sha256"], r"[a-f0-9]{64}")
    if not isinstance(route["evidence_file"], str) or not route["evidence_file"]:
        raise ValueError("evidence_file is required")
    evidence_path = Path(path).resolve().parent / route["evidence_file"]
    evidence, evidence_hash = load_json(evidence_path)
    if evidence_hash != route["evidence_sha256"]:
        raise ValueError("settings evidence hash mismatch")
    require_keys(evidence, {"schema_version", "organization", "project", "observed_at",
                            "observer", "organization_watermarking", "project_watermarking",
                            "organization_settings_url", "project_settings_url"})
    if type(evidence["schema_version"]) is not int or evidence["schema_version"] != 1:
        raise ValueError("unsupported evidence schema")
    for key in ("organization", "project"):
        if evidence[key] != route[key]:
            raise ValueError("settings evidence does not match the selected route")
    # A deliberately narrow policy: organization OFF, project OFF or inherited.
    if evidence["organization_watermarking"] is not False:
        raise ValueError("organization watermark setting must have been observed OFF")
    if evidence["project_watermarking"] is not False and evidence["project_watermarking"] != "inherit":
        raise ValueError("project watermark setting must be OFF or inherited")
    if evidence["organization_settings_url"] != "https://platform.openai.com/settings/organization/data-controls/text-provenance":
        raise ValueError("unexpected organization evidence URL")
    expected_url = f"https://platform.openai.com/settings/{route['project']}/text-provenance"
    if evidence["project_settings_url"] != expected_url:
        raise ValueError("unexpected project evidence URL")
    if not isinstance(evidence["observer"], str) or not evidence["observer"].strip():
        raise ValueError("an identified settings observer is required")
    if not isinstance(evidence["observed_at"], str):
        raise ValueError("observed_at must be an ISO timestamp")
    observed = datetime.fromisoformat(evidence["observed_at"].replace("Z", "+00:00"))
    if observed.tzinfo is None:
        raise ValueError("settings timestamp must include a timezone")
    now = now or datetime.now(timezone.utc)
    age = (now - observed).total_seconds()
    if age < 0 or age > MAX_AGE_SECONDS:
        raise ValueError("settings evidence is future-dated or older than 24 hours")
    receipt = {
        "endpoint": ENDPOINT, "provider": route["provider"], "model_requested": route["model"],
        "organization": route["organization"], "project": route["project"],
        "route_sha256": route_hash, "evidence_sha256": evidence_hash,
        "settings_observed_at": evidence["observed_at"],
        "settings_basis": "operator_observed_off_not_provider_attestation",
        "watermark_status": "not_verified",
    }
    return route, receipt
