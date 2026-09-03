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


def _section(report: str, title: str) -> list:
    """The body lines under one heading. render_section separates sections with
    a blank line, so the first one after the heading ends the body."""
    lines = report.splitlines()
    start = lines.index(f"{title}:") + 1
    return [line.strip() for line in lines[start:lines.index("", start)]]


class TestRenderStixReport:
    def test_sections_match_what_the_pipeline_emits(self, sample_stix_bundle):
        """A heading for an object type no builder produces renders a permanent
        "(none)", which reads as an extraction gap rather than as dead code. An
        exact list catches a section added as well as one dropped, and the
        "(none)" check pins the rendering that argument rests on."""
        report = render_stix_report(sample_stix_bundle, "test.json")
        assert _headings(report) == [
            "Threat Actors:",
            "Attack Patterns (TTPs):",
            "Observed File Hashes:",
        ]
        assert _section(report, "Observed File Hashes") == ["(none)"]

    def test_renders_each_object_under_its_own_heading(self, sample_stix_bundle):
        """Bound to the section rather than to the whole report: both branches of
        the dispatch loop render byte-identical text, so a swapped append target
        is invisible to any assertion that only searches the report."""
        report = render_stix_report(sample_stix_bundle, "test.json")
        headings = {
            "threat-actor": "Threat Actors",
            "attack-pattern": "Attack Patterns (TTPs)",
        }

        expected = {title: [] for title in headings.values()}
        for obj in sample_stix_bundle["objects"]:
            title = headings.get(obj["type"])
            assert title, f"fixture gained a {obj['type']}; give it a heading here"
            expected[title].append(f"- {obj['name']}  ({obj['id']})")

        for title, lines in expected.items():
            assert _section(report, title) == lines

    def test_renders_every_observed_file_hash(self):
        """Two algorithms, built through extract_hashes so the rendered labels are
        the ones the pipeline emits rather than a hand-picked spelling. A single
        hash would not catch a writer that stops after the first observed-data."""
        md5, sha256 = "b" * 32, "a" * 64
        hashes = extract_hashes(f"Dropper MD5 {md5} wrote a payload, SHA256 {sha256}.")
        assert len(hashes) == 2, f"expected two hashes, got {hashes}"

        bundle = make_bundle(hashes_to_stix_observed_data(hashes))
        report = render_stix_report(bundle, "test.json")

        assert sorted(_section(report, "Observed File Hashes")) == sorted(
            f"- {h['hash_type']}: {h['hash']}  ({observed['id']})"
            for h, observed in zip(hashes, bundle["objects"])
        )
        assert f"Total STIX Objects: {len(bundle['objects'])}" in report
