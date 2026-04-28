"""Tests for io_utils, focusing on read_validation_report format detection."""

import json
import tempfile
import unittest
from pathlib import Path

from oc_pruner.io_utils import read_validation_report


SAMPLE_ISSUES = [
    {
        "error_type": "error",
        "error_label": "extra_space",
        "position": {"table": {"0": {"id": [0]}}},
    },
    {
        "error_type": "error",
        "error_label": "br_id_format",
        "position": {"table": {"2": {"id": [0]}}},
    },
]


class TestReadValidationReportMonolithicJSON(unittest.TestCase):
    """Tests reading a monolithic JSON validation report (pre-1.0.0 format)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.report_path = Path(self.temp_dir) / "report.json"
        self.report_path.write_text(json.dumps(SAMPLE_ISSUES))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_reads_monolithic_json(self):
        issues = read_validation_report(str(self.report_path))
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["error_label"], "extra_space")
        self.assertEqual(issues[1]["error_label"], "br_id_format")

    def test_preserves_position_data(self):
        issues = read_validation_report(str(self.report_path))
        self.assertEqual(issues[0]["position"]["table"]["0"]["id"], [0])
        self.assertEqual(issues[1]["position"]["table"]["2"]["id"], [0])


class TestReadValidationReportJSONLines(unittest.TestCase):
    """Tests reading a JSON-Lines validation report (oc_validator >= 1.0.0)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.report_path = Path(self.temp_dir) / "report.jsonl"
        lines = [json.dumps(issue) for issue in SAMPLE_ISSUES]
        self.report_path.write_text("\n".join(lines))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_reads_jsonl(self):
        issues = read_validation_report(str(self.report_path))
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["error_label"], "extra_space")
        self.assertEqual(issues[1]["error_label"], "br_id_format")

    def test_preserves_position_data(self):
        issues = read_validation_report(str(self.report_path))
        self.assertEqual(issues[0]["position"]["table"]["0"]["id"], [0])
        self.assertEqual(issues[1]["position"]["table"]["2"]["id"], [0])


class TestReadValidationReportEmptyFile(unittest.TestCase):
    """Tests edge cases for read_validation_report."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_empty_file_returns_empty_list(self):
        report_path = Path(self.temp_dir) / "empty.jsonl"
        report_path.write_text("")
        issues = read_validation_report(str(report_path))
        self.assertEqual(issues, [])

    def test_jsonl_with_trailing_newline(self):
        report_path = Path(self.temp_dir) / "report.jsonl"
        lines = [json.dumps(issue) for issue in SAMPLE_ISSUES]
        report_path.write_text("\n".join(lines) + "\n")
        issues = read_validation_report(str(report_path))
        self.assertEqual(len(issues), 2)

    def test_file_not_found_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            read_validation_report("/nonexistent/path/report.json")

    def test_both_formats_produce_same_result(self):
        """Verify monolithic JSON and JSON-Lines produce identical output."""
        json_path = Path(self.temp_dir) / "report.json"
        jsonl_path = Path(self.temp_dir) / "report.jsonl"

        json_path.write_text(json.dumps(SAMPLE_ISSUES))
        lines = [json.dumps(issue) for issue in SAMPLE_ISSUES]
        jsonl_path.write_text("\n".join(lines))

        json_issues = read_validation_report(str(json_path))
        jsonl_issues = read_validation_report(str(jsonl_path))

        self.assertEqual(json_issues, jsonl_issues)


if __name__ == "__main__":
    unittest.main()
