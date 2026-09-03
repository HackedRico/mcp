"""Tests for cti_stix_validation.py and cti_stix_report_writer.py."""

from plugins.mcp.app.utilities.cti_linguistics import extract_hashes
from plugins.mcp.app.utilities.cti_mitre_extract import hashes_to_stix_observed_data
from plugins.mcp.app.utilities.cti_stix_builders import make_bundle
from plugins.mcp.app.utilities.cti_stix_report_writer import render_stix_report
from plugins.mcp.app.utilities.cti_stix_validation import (
    valid_stix_id,
    valid_uuid4,
    validate_bundle,
)


class TestValidUuid4:
    def test_valid(self):
        assert valid_uuid4("550e8400-e29b-41d4-a716-446655440000") is True

    def test_invalid(self):
        assert valid_uuid4("not-a-uuid") is False
        assert valid_uuid4("") is False


class TestValidStixId:
    def test_valid(self):
        assert valid_stix_id("malware", "malware--550e8400-e29b-41d4-a716-446655440000") is True

    def test_wrong_prefix(self):
        assert valid_stix_id("tool", "malware--550e8400-e29b-41d4-a716-446655440000") is False


class TestValidateBundle:
    def test_valid_bundle(self, sample_stix_bundle):
        errors = validate_bundle(sample_stix_bundle)
        # Should have few or no errors for a properly built bundle
        assert isinstance(errors, list)

    def test_empty_bundle(self):
        errors = validate_bundle({"type": "bundle", "id": "bundle--test", "objects": []})
        assert isinstance(errors, list)


def _headings(report: str) -> list:
    """Section headings are the only rendered lines that end in a colon."""
    return [line for line in report.splitlines() if line.endswith(":")]


class TestRenderStixReport:
    def test_sections_match_what_the_pipeline_emits(self, sample_stix_bundle):
        """A heading for an object type no builder produces renders a permanent
        "(none)", which reads as an extraction gap rather than as dead code. An
        exact list catches a section added as well as one dropped."""
        report = render_stix_report(sample_stix_bundle, "test.json")
        assert _headings(report) == [
            "Threat Actors:",
            "Attack Patterns (TTPs):",
            "Observed File Hashes:",
        ]

    def test_renders_the_objects_it_was_given(self, sample_stix_bundle):
        report = render_stix_report(sample_stix_bundle, "test.json")
        for obj in sample_stix_bundle["objects"]:
            assert obj["name"] in report
            assert obj["id"] in report

    def test_renders_observed_file_hashes(self):
        """Built through extract_hashes so the rendered algorithm label is the
        one the pipeline emits, not a hand-picked spelling."""
        digest = "a" * 64
        hashes = extract_hashes(f"The dropper, SHA256 {digest}, was written to disk.")
        assert hashes, "extract_hashes produced nothing to build from"

        report = render_stix_report(make_bundle(hashes_to_stix_observed_data(hashes)), "test.json")
        assert f"{hashes[0]['hash_type']}: {digest}" in report
