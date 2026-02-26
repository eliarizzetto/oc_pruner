"""Unit tests for CLI functionality."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from oc_pruner.cli import create_parser, parse_ignore_labels, list_all_labels


class TestCreateParser(unittest.TestCase):
    """Tests for create_parser function."""
    
    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        self.assertIsNotNone(parser)
    
    def test_required_arguments(self):
        """Test that required arguments are defined in parser."""
        parser = create_parser()
        
        # Check that parser has the required arguments
        required_args = ['--csv', '--report', '--output']
        for arg in required_args:
            self.assertIsNotNone(parser._option_string_actions.get(arg))
    
    def test_csv_argument(self):
        """Test CSV argument parsing."""
        parser = create_parser()
        args = parser.parse_args(["--csv", "test.csv", "--report", "report.json", "--output", "out.csv"])
        
        self.assertEqual(args.csv, "test.csv")
    
    def test_error_type_argument(self):
        """Test error_type argument parsing."""
        parser = create_parser()
        
        args_all = parser.parse_args([
            "--csv", "test.csv",
            "--report", "report.json",
            "--output", "out.csv",
            "--error-type", "all"
        ])
        self.assertEqual(args_all.error_type, "all")
        
        args_error = parser.parse_args([
            "--csv", "test.csv",
            "--report", "report.json",
            "--output", "out.csv",
            "--error-type", "error"
        ])
        self.assertEqual(args_error.error_type, "error")
    
    def test_invalid_error_type(self):
        """Test that invalid error_type raises error."""
        parser = create_parser()
        
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "--csv", "test.csv",
                "--report", "report.json",
                "--output", "out.csv",
                "--error-type", "invalid"
            ])


class TestParseIgnoreLabels(unittest.TestCase):
    """Tests for parse_ignore_labels function."""
    
    def test_empty_string(self):
        """Test parsing empty string."""
        labels = parse_ignore_labels("")
        self.assertEqual(labels, [])
    
    def test_single_label(self):
        """Test parsing single label."""
        labels = parse_ignore_labels("extra_space")
        self.assertEqual(labels, ["extra_space"])
    
    def test_multiple_labels(self):
        """Test parsing multiple labels."""
        labels = parse_ignore_labels("extra_space,br_id_format,type_format")
        self.assertEqual(labels, ["extra_space", "br_id_format", "type_format"])
    
    def test_labels_with_spaces(self):
        """Test parsing labels with spaces."""
        labels = parse_ignore_labels("extra_space , br_id_format , type_format")
        self.assertEqual(labels, ["extra_space", "br_id_format", "type_format"])
    
    def test_empty_items(self):
        """Test that empty items are filtered out."""
        labels = parse_ignore_labels("extra_space,,br_id_format, ,type_format")
        self.assertEqual(labels, ["extra_space", "br_id_format", "type_format"])


class TestListAllLabels(unittest.TestCase):
    """Tests for list_all_labels function."""
    
    def test_list_labels_output(self):
        """Test that list_all_labels prints labels."""
        from io import StringIO
        import sys
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            list_all_labels()
            output = sys.stdout.getvalue()
            
            self.assertIn("Valid error labels:", output)
            self.assertIn("extra_space", output)
            self.assertIn("Total:", output)
        finally:
            sys.stdout = old_stdout


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for the CLI."""
    
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
    
    def test_cli_basic_usage(self):
        """Test basic CLI usage."""
        result = subprocess.run(
            [
                sys.executable, "-m", "oc_pruner.cli",
                "--csv", str(self.csv_path),
                "--report", str(self.report_path),
                "--output", str(self.output_path)
            ],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.output_path.exists())
        
        # Verify output
        output_content = self.output_path.read_text()
        lines = output_content.strip().split("\n")
        
        # Should have header + rows 1 and 3 (removed rows 0 and 2)
        self.assertEqual(len(lines), 3)
    
    def test_cli_with_verbose(self):
        """Test CLI with verbose flag."""
        result = subprocess.run(
            [
                sys.executable, "-m", "oc_pruner.cli",
                "--csv", str(self.csv_path),
                "--report", str(self.report_path),
                "--output", str(self.output_path),
                "--verbose"
            ],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Loading CSV file:", result.stdout)
        self.assertIn("Results:", result.stdout)
    
    def test_cli_with_ignore_labels(self):
        """Test CLI with ignore-labels argument."""
        result = subprocess.run(
            [
                sys.executable, "-m", "oc_pruner.cli",
                "--csv", str(self.csv_path),
                "--report", str(self.report_path),
                "--output", str(self.output_path),
                "--ignore-labels", "extra_space"
            ],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Verify output - should only remove row 2 (br_id_format)
        output_content = self.output_path.read_text()
        lines = output_content.strip().split("\n")
        
        # Should have header + rows 0, 1, 3 (only row 2 removed)
        self.assertEqual(len(lines), 4)
    
    def test_cli_missing_required_argument(self):
        """Test CLI with missing required argument."""
        result = subprocess.run(
            [
                sys.executable, "-m", "oc_pruner.cli",
                "--csv", str(self.csv_path),
                "--report", str(self.report_path)
            ],
            capture_output=True,
            text=True
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--output", result.stderr)


if __name__ == "__main__":
    unittest.main()