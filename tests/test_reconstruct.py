import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/text-cleanroom/scripts"
sys.path.insert(0, str(SCRIPTS))
import reconstruct
import route_policy


class ReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / "original.md"
        self.original.write_text("Ada pays 20. Use `--dry-run`.", encoding="utf-8")
        self.original_hash = hashlib.sha256(self.original.read_bytes()).hexdigest()
        self.evidence = {
            "schema_version": 1, "organization": "org-test123", "project": "proj_test123",
            "observed_at": datetime.now(timezone.utc).isoformat(), "observer": "test fixture",
            "organization_watermarking": False, "project_watermarking": "inherit",
            "organization_settings_url": "https://platform.openai.com/settings/organization/data-controls/text-provenance",
            "project_settings_url": "https://platform.openai.com/settings/proj_test123/text-provenance",
        }
        self.route = {"schema_version": 1, "provider": "openai_platform", "model": "test-model",
                      "organization": "org-test123", "project": "proj_test123", "credential_env": "TC_TEST_API_KEY",
                      "evidence_file": "evidence.json", "evidence_sha256": ""}
        self.ledger = {"schema_version": 1, "original_sha256": self.original_hash,
                       "language": "English", "tone": "neutral",
                       "facts": [{"id": "F1", "text": "Ada pays 20."},
                                 {"id": "F2", "text": "Use `--dry-run`."}],
                       "immutable": ["Ada", "`--dry-run`"]}
        self.candidate = "Use `--dry-run`. Ada pays 20."
        self.response = {"id": "resp_test", "status": "completed", "model": "test-model",
                         "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({
                             "candidate": self.candidate, "fact_map": [
                                 {"fact_id": "F1", "candidate_quote": "Ada pays 20."},
                                 {"fact_id": "F2", "candidate_quote": "Use `--dry-run`."}]})}]}]}
        self.islands = reconstruct.freeze(self.original.read_text(), self.ledger["immutable"])
        raw = self.response["output"][0]["content"][0]["text"]
        for island in self.islands:
            raw = raw.replace(island["text"], island["placeholder"])
        self.response["output"][0]["content"][0]["text"] = raw
        self.save()

    def save(self):
        evidence = json.dumps(self.evidence).encode()
        (self.root / "evidence.json").write_bytes(evidence)
        self.route["evidence_sha256"] = hashlib.sha256(evidence).hexdigest()
        (self.root / "route.json").write_text(json.dumps(self.route))
        (self.root / "ledger.json").write_text(json.dumps(self.ledger))

    def run_candidate(self, dry_run=False):
        return reconstruct.run(self.original, self.root / "ledger.json", self.root / "route.json",
                               self.root / "output", dry_run)

    def test_preflight_never_calls_provider_or_writes_output(self):
        with mock.patch.object(reconstruct, "api_call") as request:
            result = self.run_candidate(True)
        request.assert_not_called()
        self.assertFalse((self.root / "output").exists())
        self.assertEqual(result["status"], "preflight_only")
        self.assertEqual(result["settings_basis"], "operator_observed_off_not_provider_attestation")

    def test_stale_future_and_naive_evidence_fail(self):
        for stamp in [datetime.now(timezone.utc) - timedelta(days=2),
                      datetime.now(timezone.utc) + timedelta(hours=1), datetime.now()]:
            with self.subTest(stamp=stamp):
                self.evidence["observed_at"] = stamp.isoformat()
                self.save()
                with self.assertRaises(ValueError):
                    self.run_candidate(True)

    def test_unknown_on_or_mismatched_route_is_rejected(self):
        original = copy.deepcopy(self.evidence)
        for field, value in [("organization_watermarking", True), ("organization_watermarking", 0),
                             ("project_watermarking", "unknown"), ("project_watermarking", 0),
                             ("project", "proj_other"), ("observer", "")]:
            self.evidence = {**original, field: value}
            self.save()
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.run_candidate(True)

    def test_evidence_hash_and_duplicate_json_keys_rejected(self):
        (self.root / "evidence.json").write_text(json.dumps({**self.evidence, "observer": "changed"}))
        with self.assertRaises(ValueError):
            self.run_candidate(True)
        (self.root / "route.json").write_text('{"provider":"openai_platform","provider":"other"}')
        with self.assertRaises(ValueError):
            self.run_candidate(True)

    def test_custom_endpoint_or_provider_not_silently_accepted(self):
        self.route["endpoint"] = "https://evil.invalid"
        self.save()
        with self.assertRaises(ValueError):
            self.run_candidate(True)
        del self.route["endpoint"]
        self.route["provider"] = "chatgpt_oauth"
        self.save()
        with self.assertRaises(ValueError):
            self.run_candidate(True)

    def test_wrong_original_and_absent_immutable_fail(self):
        self.ledger["original_sha256"] = "0" * 64
        self.save()
        with self.assertRaises(ValueError):
            self.run_candidate(True)

    def test_oversized_prose_facts_or_ledger_fail_before_network(self):
        with mock.patch.object(reconstruct, "api_call") as call:
            self.original.write_text("x" * 4097)
            with self.assertRaises(ValueError):
                self.run_candidate(True)
            self.original.write_text("Ada pays 20. Use `--dry-run`.")
            self.ledger["facts"] = [{"id": str(i), "text": "A fact"} for i in range(25)]
            self.save()
            with self.assertRaises(ValueError):
                self.run_candidate(True)
            self.ledger["facts"] = [{"id": "F1", "text": "x" * 8193}]
            self.save()
            with self.assertRaises(ValueError):
                self.run_candidate(True)
            call.assert_not_called()
        self.assertFalse((self.root / "output").exists())
        self.ledger["original_sha256"] = self.original_hash
        self.ledger["immutable"].append("not in original")
        self.save()
        with self.assertRaises(ValueError):
            self.run_candidate(True)

    def test_missing_or_oauth_credentials_do_not_call_network(self):
        for key in ["", "oauth-token", "sk-proj-bad\nvalue"]:
            with mock.patch.dict(os.environ, {"TC_TEST_API_KEY": key}), mock.patch.object(reconstruct, "api_call") as call:
                with self.assertRaises(ValueError):
                    self.run_candidate()
                call.assert_not_called()

    def test_success_preserves_original_and_exact_candidate_but_requires_review(self):
        with mock.patch.dict(os.environ, {"TC_TEST_API_KEY": "sk-proj-test-placeholder"}), \
                mock.patch.object(reconstruct, "api_call", return_value=(self.response, {"project": None})) as call:
            result = self.run_candidate()
        self.assertEqual(call.call_count, 1)
        self.assertNotIn("original", call.call_args.args[1])
        self.assertEqual((self.root / "output/candidate.md").read_bytes(), self.candidate.encode())
        self.assertEqual(hashlib.sha256(self.original.read_bytes()).hexdigest(), self.original_hash)
        self.assertEqual(result["status"], "candidate_requires_review")
        self.assertEqual(result["semantic_check"], "not_performed")
        self.assertEqual(result["watermark_status"], "not_verified")
        self.assertEqual(result["immutable_handling"], "local_exact_reinsertion")
        self.assertEqual(result["strategy"], "restructure")
        diagnostic = json.loads((self.root / "output/transformation.json").read_text())
        self.assertEqual(diagnostic["status"], "wording_diagnostics_only")
        self.assertNotIn("[[TCI:", (self.root / "output/fact-map.json").read_text())
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE((self.root / "output").stat().st_mode), 0o700)
            for path in (self.root / "output").iterdir():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_existing_output_is_never_overwritten(self):
        (self.root / "output").mkdir()
        with mock.patch.object(reconstruct, "api_call") as call, self.assertRaises(ValueError):
            self.run_candidate()
        call.assert_not_called()

    def test_failure_does_not_fallback_or_leave_candidate_ready(self):
        with mock.patch.dict(os.environ, {"TC_TEST_API_KEY": "sk-proj-test-placeholder"}), \
                mock.patch.object(reconstruct, "api_call", side_effect=ValueError("refused")) as call:
            with self.assertRaises(ValueError):
                self.run_candidate()
        self.assertEqual(call.call_count, 1)
        self.assertFalse((self.root / "output/candidate.md").exists())
        self.assertFalse(json.loads((self.root / "output/failure.json").read_text())["candidate_ready"])

    def test_missing_code_placeholder_fails_without_deliverable(self):
        response = copy.deepcopy(self.response)
        response["output"][0]["content"][0]["text"] = response["output"][0]["content"][0]["text"].replace(self.islands[1]["placeholder"], "--force")
        with mock.patch.dict(os.environ, {"TC_TEST_API_KEY": "sk-proj-test-placeholder"}), \
                mock.patch.object(reconstruct, "api_call", return_value=(response, {})):
            with self.assertRaises(ValueError):
                self.run_candidate()
        self.assertFalse((self.root / "output/candidate.md").exists())

    def test_strategy_and_marker_collisions_rejected_before_network(self):
        with self.assertRaises(ValueError):
            reconstruct.ledger_input(self.root / "ledger.json", self.original.read_text(), self.original_hash, "unknown")
        self.ledger["facts"][0]["text"] = "[[TCI:spoof]]"
        self.save()
        with mock.patch.object(reconstruct, "api_call") as call, self.assertRaises(ValueError):
            self.run_candidate(True)
        call.assert_not_called()

    def test_explain_strategy_is_explicit_and_no_extra_request(self):
        with mock.patch.dict(os.environ, {"TC_TEST_API_KEY": "sk-proj-test-placeholder"}), \
                mock.patch.object(reconstruct, "api_call", return_value=(self.response, {})) as call:
            result = reconstruct.run(self.original, self.root / "ledger.json", self.root / "route.json",
                                     self.root / "explain", strategy="explain")
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[1]["strategy"], reconstruct.STRATEGIES["explain"])
        self.assertEqual(result["strategy"], "explain")

    def test_truncation_refusal_and_incomplete_fact_map_rejected(self):
        bad = [dict(self.response, status="incomplete"),
               dict(self.response, output=[{"type": "message", "content": [{"type": "refusal"}]}])]
        response = copy.deepcopy(self.response)
        result = json.loads(response["output"][0]["content"][0]["text"])
        result["fact_map"] = result["fact_map"][:1]
        response["output"][0]["content"][0]["text"] = json.dumps(result)
        bad.append(response)
        for response in bad:
            with self.subTest(response=response), self.assertRaises(ValueError):
                reconstruct.parse_candidate(response, self.ledger)

    def test_http_redirects_and_errors_are_not_followed_or_dumped(self):
        for status in [302, 401, 429, 500]:
            connection = mock.MagicMock()
            connection.getresponse.return_value.status = status
            connection.getresponse.return_value.read.return_value = b'secret-bearing-error'
            with mock.patch.object(reconstruct.http.client, "HTTPSConnection", return_value=connection) as factory:
                with self.assertRaises(ValueError) as caught:
                    reconstruct.api_call(self.route, {}, "sk-proj-test-placeholder")
            self.assertNotIn("secret-bearing", str(caught.exception))
            self.assertEqual(factory.call_count, 1)
            self.assertEqual(connection.request.call_count, 1)
            self.assertEqual(factory.call_args.args[0], "api.openai.com")

    def test_mismatched_server_scope_rejected(self):
        connection = mock.MagicMock()
        response = connection.getresponse.return_value
        response.status = 200
        response.read.return_value = json.dumps(self.response).encode()
        response.getheader.side_effect = ["org-other", "proj_other"]
        with mock.patch.object(reconstruct.http.client, "HTTPSConnection", return_value=connection), self.assertRaises(ValueError):
            reconstruct.api_call(self.route, {}, "sk-proj-test-placeholder")

    def test_legacy_organization_name_requires_exact_project_echo(self):
        for project in ["proj_test123", None, "proj_other"]:
            connection = mock.MagicMock()
            response = connection.getresponse.return_value
            response.status = 200
            response.read.return_value = json.dumps(self.response).encode()
            response.getheader.side_effect = ["user-legacy-name", project]
            with mock.patch.object(reconstruct.http.client, "HTTPSConnection", return_value=connection):
                if project == self.route["project"]:
                    _, headers = reconstruct.api_call(self.route, {}, "sk-proj-test-placeholder")
                    self.assertEqual(headers["organization_basis"], "non_id_or_absent_not_independently_mapped")
                else:
                    with self.assertRaises(ValueError):
                        reconstruct.api_call(self.route, {}, "sk-proj-test-placeholder")

    def test_conflicting_organization_id_is_not_treated_as_a_legacy_name(self):
        connection = mock.MagicMock()
        response = connection.getresponse.return_value
        response.status = 200
        response.read.return_value = json.dumps(self.response).encode()
        response.getheader.side_effect = ["org-other", "proj_test123"]
        with mock.patch.object(reconstruct.http.client, "HTTPSConnection", return_value=connection), self.assertRaises(ValueError):
            reconstruct.api_call(self.route, {}, "sk-proj-test-placeholder")

    def test_model_change_rejected_without_second_request(self):
        response = dict(self.response, model="different-model")
        with mock.patch.dict(os.environ, {"TC_TEST_API_KEY": "sk-proj-test-placeholder"}), \
                mock.patch.object(reconstruct, "api_call", return_value=(response, {})) as call:
            with self.assertRaises(ValueError):
                self.run_candidate()
        self.assertEqual(call.call_count, 1)
        self.assertFalse((self.root / "output/candidate.md").exists())


if __name__ == "__main__":
    unittest.main()
