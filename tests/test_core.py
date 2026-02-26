"""Unit tests for core.py functionality."""

import json
import tempfile
import unittest
from pathlib import Path

from oc_pruner.config import PrunerConfig
from oc_pruner.core import (
    should_ignore_issue,
    extract_affected_rows,
    determine_rows_to_remove,
    prune
)


class TestShouldIgnoreIssue(unittest.TestCase):
    """Tests for should_ignore_issue function."""
    
    def test_ignore_by_error_type(self):
        """Test that warnings are ignored when error_type_filter is 'error'."""
        config = PrunerConfig(error_type_filter="error", ignore_error_labels=[])
        
        error_issue = {
            "error_type": "error",
            "error_label": "extra_space"
        }
        warning_issue = {
            "error_type": "warning",
            "error_label": "extra_space"
        }
        
        self.assertFalse(should_ignore_issue(error_issue, config))
        self.assertTrue(should_ignore_issue(warning_issue, config))
    
    def test_ignore_by_label(self):
        """Test that issues are ignored when their label is in ignore list."""
        config = PrunerConfig(
            error_type_filter="all",
            ignore_error_labels=["extra_space", "br_id_format"]
        )
        
        ignored_issue = {
            "error_type": "error",
            "error_label": "extra_space"
        }
        not_ignored_issue = {
            "error_type": "error",
            "error_label": "type_format"
        }
        
        self.assertTrue(should_ignore_issue(ignored_issue, config))
        self.assertFalse(should_ignore_issue(not_ignored_issue, config))
    
    def test_ignore_both_conditions(self):
        """Test that issues are ignored if either condition matches."""
        config = PrunerConfig(
            error_type_filter="error",
            ignore_error_labels=["extra_space"]
        )
        
        # Warning (ignored by error_type)
        warning_issue = {
            "error_type": "warning",
            "error_label": "type_format"
        }
        # Error with ignored label
        labeled_issue = {
            "error_type": "error",
            "error_label": "extra_space"
        }
        
        self.assertTrue(should_ignore_issue(warning_issue, config))
        self.assertTrue(should_ignore_issue(labeled_issue, config))


class TestExtractAffectedRows(unittest.TestCase):
    """Tests for extract_affected_rows function."""
    
    def test_single_row_issue(self):
        """Test extracting a single row from an issue."""
        issue = {
            "position": {
                "located_in": "item",
                "table": {
                    "0": {
                        "id": [0]
                    }
                }
            }
        }
        
        rows = extract_affected_rows(issue)
        self.assertEqual(rows, {0})
    
    def test_multiple_rows_issue(self):
        """Test extracting multiple rows from an issue."""
        issue = {
            "position": {
                "located_in": "row",
                "table": {
                    "9": {"id": [0]},
                    "13": {"id": [0]}
                }
            }
        }
        
        rows = extract_affected_rows(issue)
        self.assertEqual(rows, {9, 13})
    
    def test_no_position(self):
        """Test handling issues with no position."""
        issue = {}
        
        rows = extract_affected_rows(issue)
        self.assertEqual(rows, set())
    
    def test_invalid_row_numbers(self):
        """Test handling invalid row numbers."""
        issue = {
            "position": {
                "table": {
                    "0": {"id": [0]},
                    "invalid": {"id": [0]},
                    "3": {"id": [0]}
                }
            }
        }
        
        rows = extract_affected_rows(issue)
        self.assertEqual(rows, {0, 3})


class TestDetermineRowsToRemove(unittest.TestCase):
    """Tests for determine_rows_to_remove function."""
    
    def test_all_issues_processed(self):
        """Test processing all issues without ignoring any."""
        config = PrunerConfig(error_type_filter="all", ignore_error_labels=[])
        
        issues = [
            {
                "error_type": "error",
                "error_label": "extra_space",
                "position": {
                    "table": {"0": {"id": [0]}}
                }
            },
            {
                "error_type": "error",
                "error_label": "br_id_format",
                "position": {
                    "table": {"1": {"id": [0]}}
                }
            }
        ]
        
        rows = determine_rows_to_remove(issues, config)
        self.assertEqual(rows, {0, 1})
    
    def test_ignored_labels(self):
        """Test that issues with ignored labels are not processed."""
        config = PrunerConfig(
            error_type_filter="all",
            ignore_error_labels=["extra_space"]
        )
        
        issues = [
            {
                "error_type": "error",
                "error_label": "extra_space",
                "position": {
                    "table": {"0": {"id": [0]}}
                }
            },
            {
                "error_type": "error",
                "error_label": "br_id_format",
                "position": {
                    "table": {"1": {"id": [0]}}
                }
            }
        ]
        
        rows = determine_rows_to_remove(issues, config)
        self.assertEqual(rows, {1})
    
    def test_ignored_warnings(self):
        """Test that warnings are ignored when error_type_filter is 'error'."""
        config = PrunerConfig(error_type_filter="error", ignore_error_labels=[])
        
        issues = [
            {
                "error_type": "warning",
                "error_label": "extra_space",
                "position": {
                    "table": {"0": {"id": [0]}}
                }
            },
            {
                "error_type": "error",
                "error_label": "br_id_format",
                "position": {
                    "table": {"1": {"id": [0]}}
                }
            }
        ]
        
        rows = determine_rows_to_remove(issues, config)
        self.assertEqual(rows, {1})
    
    def test_duplicate_rows(self):
        """Test that duplicate row numbers are handled correctly."""
        config = PrunerConfig(error_type_filter="all", ignore_error_labels=[])
        
        issues = [
            {
                "error_type": "error",
                "error_label": "extra_space",
                "position": {
                    "table": {"0": {"id": [0]}}
                }
            },
            {
                "error_type": "error",
                "error_label": "br_id_format",
                "position": {
                    "table": {"0": {"id": [1]}}
                }
            }
        ]
        
        rows = determine_rows_to_remove(issues, config)
        self.assertEqual(rows, {0})


class TestPrune(unittest.TestCase):
    """Tests for the main prune function."""
    
    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test CSV
        self.csv_path = Path(self.temp_dir) / "test.csv"
        csv_content = """id,title,author
row0,title0,author0
row1,title1,author1
row2,title2,author2
row3,title3,author3
"""
        self.csv_path.write_text(csv_content)
        
        # Create test validation report
        self.report_path = Path(self.temp_dir) / "report.json"
        report = [
            {
                "error_type": "error",
                "error_label": "extra_space",
                "position": {"table": {"0": {"id": [0]}}}
            },
            {
                "error_type": "error",
                "error_label": "br_id_format",
                "position": {"table": {"2": {"id": [0]}}}
            }
        ]
        self.report_path.write_text(json.dumps(report))
        
        self.output_path = Path(self.temp_dir) / "output.csv"
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_prune_removes_rows(self):
        """Test that prune removes the correct rows."""
        config = PrunerConfig(error_type_filter="all", ignore_error_labels=[])
        
        prune(
            str(self.csv_path),
            str(self.report_path),
            str(self.output_path),
            config,
            verbose=False
        )
        
        # Check output exists
        self.assertTrue(self.output_path.exists())
        
        # Read and verify output
        output_content = self.output_path.read_text()
        lines = output_content.strip().split("\n")
        
        # Should have header + rows 1 and 3 (removed rows 0 and 2)
        self.assertEqual(len(lines), 3)
        self.assertIn("row1", lines[1])
        self.assertIn("row3", lines[2])
    
    def test_prune_with_ignored_labels(self):
        """Test prune with ignored error labels."""
        config = PrunerConfig(
            error_type_filter="all",
            ignore_error_labels=["extra_space"]
        )
        
        prune(
            str(self.csv_path),
            str(self.report_path),
            str(self.output_path),
            config,
            verbose=False
        )
        
        output_content = self.output_path.read_text()
        lines = output_content.strip().split("\n")
        
        # Should have header + rows 0, 1, 3 (only row 2 removed)
        self.assertEqual(len(lines), 4)
        self.assertIn("row0", lines[1])
        self.assertIn("row1", lines[2])
        self.assertIn("row3", lines[3])


if __name__ == "__main__":
    unittest.main()