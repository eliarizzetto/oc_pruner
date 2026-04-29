"""Tests for pipeline.py, mocking oc_validator to verify compatibility
with both old (< 1.0.0) and new (>= 1.0.0) APIs."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from oc_pruner.pipeline import run_validation
from oc_pruner.config import PipelineConfig


def _make_sample_csv(path, table_type="meta"):
    """Create a minimal valid CSV file for testing."""
    if table_type == "meta":
        content = "id,title,author,pub_date,venue,volume,issue,page,type,publisher,editor\n"
        content += "doi:10.1/a,Title,Author,2024,Journal,1,1,1,journal,Pub,Ed\n"
    else:
        content = "citing,cited\n"
        content += "doi:10.1/a,doi:10.1/b\n"
    path.write_text(content)


class TestRunValidationCallsClosureValidator(unittest.TestCase):
    """Test that run_validation passes correct args to ClosureValidator."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.meta_csv = Path(self.temp_dir) / "meta.csv"
        self.cits_csv = Path(self.temp_dir) / "cits.csv"
        _make_sample_csv(self.meta_csv, "meta")
        _make_sample_csv(self.cits_csv, "cits")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch("oc_pruner.pipeline.ClosureValidator")
    def test_passes_1_0_0_param_names(self, MockCV):
        """ClosureValidator is called with oc_validator 1.0.0 parameter names."""
        mock_instance = MagicMock()
        mock_instance.validate.return_value = (True, True)
        mock_instance.meta_validator.csv_doc = str(self.meta_csv)
        mock_instance.cits_validator.csv_doc = str(self.cits_csv)
        mock_instance.meta_validator.output_fp_json = "/out/report_meta.jsonl"
        mock_instance.cits_validator.output_fp_json = "/out/report_cits.jsonl"
        MockCV.return_value = mock_instance

        config = PipelineConfig()
        run_validation(str(self.meta_csv), str(self.cits_csv), Path(self.temp_dir), "round1", config)

        call_kwargs = MockCV.call_args[1]
        self.assertIn("meta_in", call_kwargs)
        self.assertIn("cits_in", call_kwargs)
        self.assertIn("meta_out_dir", call_kwargs)
        self.assertIn("cits_out_dir", call_kwargs)
        self.assertEqual(call_kwargs["meta_kwargs"]["verify_id_existence"], False)
        self.assertEqual(call_kwargs["cits_kwargs"]["verify_id_existence"], False)

    @patch("oc_pruner.pipeline.ClosureValidator")
    def test_output_dirs_include_round_name(self, MockCV):
        mock_instance = MagicMock()
        mock_instance.validate.return_value = (True, True)
        mock_instance.meta_validator.csv_doc = str(self.meta_csv)
        mock_instance.cits_validator.csv_doc = str(self.cits_csv)
        mock_instance.meta_validator.output_fp_json = "/out/report_meta.jsonl"
        mock_instance.cits_validator.output_fp_json = "/out/report_cits.jsonl"
        MockCV.return_value = mock_instance

        config = PipelineConfig()
        run_validation(str(self.meta_csv), str(self.cits_csv), Path(self.temp_dir), "first_round", config)

        call_kwargs = MockCV.call_args[1]
        self.assertIn("first_round", call_kwargs["meta_out_dir"])
        self.assertIn("first_round", call_kwargs["cits_out_dir"])


class TestRunValidationNewAPI(unittest.TestCase):
    """Test run_validation with oc_validator >= 1.0.0 (returns bools)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.meta_csv = Path(self.temp_dir) / "meta.csv"
        self.cits_csv = Path(self.temp_dir) / "cits.csv"
        _make_sample_csv(self.meta_csv, "meta")
        _make_sample_csv(self.cits_csv, "cits")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch("oc_pruner.pipeline.ClosureValidator")
    def test_returns_report_paths(self, MockCV):
        """run_validation should return (meta_csv, cits_csv, meta_report, cits_report)."""
        mock_instance = MagicMock()
        mock_instance.validate.return_value = (True, True)
        mock_instance.meta_validator.csv_doc = str(self.meta_csv)
        mock_instance.cits_validator.csv_doc = str(self.cits_csv)
        mock_instance.meta_validator.output_fp_json = "/out/report_meta.jsonl"
        mock_instance.cits_validator.output_fp_json = "/out/report_cits.jsonl"
        MockCV.return_value = mock_instance

        config = PipelineConfig()
        result = run_validation(str(self.meta_csv), str(self.cits_csv), Path(self.temp_dir), "round1", config)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[2], "/out/report_meta.jsonl")
        self.assertEqual(result[3], "/out/report_cits.jsonl")


class TestFinalValidationBoolReturn(unittest.TestCase):
    """Test that the final validation logic handles bool returns correctly."""

    def test_bool_true_means_valid(self):
        """When validate() returns (True, True), both tables are valid."""
        meta_result, cits_result = True, True

        if isinstance(meta_result, bool):
            meta_is_valid = meta_result
            cits_is_valid = cits_result
        else:
            meta_is_valid = not meta_result
            cits_is_valid = not cits_result

        self.assertTrue(meta_is_valid)
        self.assertTrue(cits_is_valid)

    def test_bool_false_means_invalid(self):
        """When validate() returns (False, True), metadata has issues."""
        meta_result, cits_result = False, True

        if isinstance(meta_result, bool):
            meta_is_valid = meta_result
            cits_is_valid = cits_result
        else:
            meta_is_valid = not meta_result
            cits_is_valid = not cits_result

        self.assertFalse(meta_is_valid)
        self.assertTrue(cits_is_valid)

    def test_list_empty_means_valid(self):
        """When validate() returns ([], []), both tables are valid (old API)."""
        meta_result, cits_result = [], []

        if isinstance(meta_result, bool):
            meta_is_valid = meta_result
            cits_is_valid = cits_result
        else:
            meta_is_valid = not meta_result
            cits_is_valid = not cits_result

        self.assertTrue(meta_is_valid)
        self.assertTrue(cits_is_valid)

    def test_list_nonempty_means_invalid(self):
        """When validate() returns ([issue], []), metadata has issues (old API)."""
        meta_result, cits_result = [{"error_type": "error"}], []

        if isinstance(meta_result, bool):
            meta_is_valid = meta_result
            cits_is_valid = cits_result
        else:
            meta_is_valid = not meta_result
            cits_is_valid = not cits_result

        self.assertFalse(meta_is_valid)
        self.assertTrue(cits_is_valid)


if __name__ == "__main__":
    unittest.main()
