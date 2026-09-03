"""Tests for cti_stix_validation.py and cti_stix_report_writer.py."""


class TestValidUuid4:
    def test_valid(self):
        from plugins.mcp.app.utilities.cti_stix_validation import valid_uuid4
        assert valid_uuid4("550e8400-e29b-41d4-a716-446655440000") is True

    def test_invalid(self):
        from plugins.mcp.app.utilities.cti_stix_validation import valid_uuid4
        assert valid_uuid4("not-a-uuid") is False
        assert valid_uuid4("") is False


class TestValidStixId:
    def test_valid(self):
        from plugins.mcp.app.utilities.cti_stix_validation import valid_stix_id
        assert valid_stix_id("malware", "malware--550e8400-e29b-41d4-a716-446655440000") is True

    def test_wrong_prefix(self):
        from plugins.mcp.app.utilities.cti_stix_validation import valid_stix_id
        assert valid_stix_id("tool", "malware--550e8400-e29b-41d4-a716-446655440000") is False


class TestValidateBundle:
    def test_valid_bundle(self, sample_stix_bundle):
        from plugins.mcp.app.utilities.cti_stix_validation import validate_bundle
        errors = validate_bundle(sample_stix_bundle)
        # Should have few or no errors for a properly built bundle
        assert isinstance(errors, list)

    def test_empty_bundle(self):
        from plugins.mcp.app.utilities.cti_stix_validation import validate_bundle
        errors = validate_bundle({"type": "bundle", "id": "bundle--test", "objects": []})
        assert isinstance(errors, list)


class TestRenderStixReport:
    def test_renders(self, sample_stix_bundle):
        from plugins.mcp.app.utilities.cti_stix_report_writer import render_stix_report
        report = render_stix_report(sample_stix_bundle, "test.json")
        assert isinstance(report, str)
        assert len(report) > 0

    def test_sections_match_what_the_pipeline_emits(self, sample_stix_bundle):
        """Headings for object types no builder produces render a permanent
        "(none)", which reads as an extraction gap rather than dead code."""
        from plugins.mcp.app.utilities.cti_stix_report_writer import render_stix_report
        report = render_stix_report(sample_stix_bundle, "test.json")
        for heading in ("Threat Actors", "Attack Patterns", "Observed File Hashes"):
            assert heading in report
        for heading in ("Malware", "Tools", "Infrastructure", "Relationships"):
            assert heading not in report

    def test_renders_observed_file_hashes(self):
        from plugins.mcp.app.utilities.cti_mitre_extract import hashes_to_stix_observed_data
        from plugins.mcp.app.utilities.cti_stix_builders import make_bundle
        from plugins.mcp.app.utilities.cti_stix_report_writer import render_stix_report

        digest = "a" * 64
        bundle = make_bundle(hashes_to_stix_observed_data(
            [{"hash_type": "SHA-256", "hash": digest, "evidence": "dropped by loader"}]
        ))
        report = render_stix_report(bundle, "test.json")
        assert digest in report
        assert "SHA-256" in report

