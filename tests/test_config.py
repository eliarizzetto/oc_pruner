"""Unit tests for config.py functionality."""

import json
import tempfile
import unittest
from pathlib import Path

from oc_pruner.config import (
    PrunerConfig,
    find_config_file,
    load_config_from_file,
    load_config,
    generate_config_template
)


class TestPrunerConfig(unittest.TestCase):
    """Tests for PrunerConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PrunerConfig()
        
        self.assertEqual(config.error_type_filter, "all")
        self.assertEqual(config.ignore_error_labels, [])
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PrunerConfig(
            error_type_filter="error",
            ignore_error_labels=["extra_space", "br_id_format"]
        )
        
        self.assertEqual(config.error_type_filter, "error")
        self.assertEqual(config.ignore_error_labels, ["extra_space", "br_id_format"])
    
    def test_invalid_error_type_filter(self):
        """Test that invalid error_type_filter raises ValueError."""
        with self.assertRaises(ValueError) as context:
            PrunerConfig(error_type_filter="invalid")
        
        self.assertIn("error_type_filter must be 'all' or 'error'", str(context.exception))
    
    def test_invalid_error_label(self):
        """Test that invalid error label raises ValueError."""
        with self.assertRaises(ValueError) as context:
            PrunerConfig(ignore_error_labels=["invalid_label"])
        
        self.assertIn("Invalid error label 'invalid_label'", str(context.exception))
    
    def test_valid_error_label(self):
        """Test that valid error labels are accepted."""
        config = PrunerConfig(ignore_error_labels=["extra_space", "type_format"])
        # Should not raise any exception
        self.assertEqual(config.ignore_error_labels, ["extra_space", "type_format"])


class TestFindConfigFile(unittest.TestCase):
    """Tests for find_config_file function."""
    
    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
    
    def tearDown(self):
        """Clean up and restore original working directory."""
        import shutil
        import os
        shutil.rmtree(self.temp_dir)
        os.chdir(self.original_cwd)
    
    def test_explicit_config_path(self):
        """Test finding explicitly specified config file."""
        config_path = Path(self.temp_dir) / "custom_config.yaml"
        config_path.write_text("test: value")
        
        found = find_config_file(str(config_path))
        self.assertEqual(found, config_path)
    
    def test_current_directory_yaml(self):
        """Test finding config file in current directory (YAML)."""
        import os
        
        os.chdir(self.temp_dir)
        config_path = Path(self.temp_dir) / "oc_pruner_config.yaml"
        config_path.write_text("test: value")
        
        found = find_config_file()
        self.assertEqual(found, config_path)
    
    def test_current_directory_json(self):
        """Test finding config file in current directory (JSON)."""
        import os
        
        os.chdir(self.temp_dir)
        config_path = Path(self.temp_dir) / "oc_pruner_config.json"
        config_path.write_text('{"test": "value"}')
        
        found = find_config_file()
        self.assertEqual(found, config_path)
    
    def test_no_config_file(self):
        """Test when no config file exists."""
        import os
        os.chdir(self.temp_dir)
        
        found = find_config_file()
        self.assertIsNone(found)


class TestLoadConfigFromFile(unittest.TestCase):
    """Tests for load_config_from_file function."""
    
    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_json_config(self):
        """Test loading configuration from JSON file."""
        config_path = Path(self.temp_dir) / "config.json"
        config_data = {
            "error_type_filter": "error",
            "ignore_error_labels": ["extra_space"]
        }
        config_path.write_text(json.dumps(config_data))
        
        config = load_config_from_file(config_path)
        
        self.assertEqual(config.error_type_filter, "error")
        self.assertEqual(config.ignore_error_labels, ["extra_space"])
    
    def test_load_empty_config(self):
        """Test loading an empty configuration file."""
        config_path = Path(self.temp_dir) / "config.json"
        config_path.write_text("{}")
        
        config = load_config_from_file(config_path)
        
        # Should have default values
        self.assertEqual(config.error_type_filter, "all")
        self.assertEqual(config.ignore_error_labels, [])
    
    def test_unsupported_file_format(self):
        """Test loading unsupported file format."""
        config_path = Path(self.temp_dir) / "config.txt"
        config_path.write_text("test")
        
        with self.assertRaises(ValueError) as context:
            load_config_from_file(config_path)
        
        self.assertIn("Unsupported config file format", str(context.exception))
    
    def test_yaml_without_pyyaml(self):
        """Test loading YAML when PyYAML is not installed."""
        # Create a YAML file
        config_path = Path(self.temp_dir) / "config.yaml"
        config_path.write_text("error_type_filter: error")
        
        # This should raise ValueError about PyYAML
        with self.assertRaises(ValueError) as context:
            load_config_from_file(config_path)
        
        self.assertIn("PyYAML package", str(context.exception))


class TestLoadConfig(unittest.TestCase):
    """Tests for load_config function."""
    
    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
    
    def tearDown(self):
        """Clean up and restore original working directory."""
        import shutil
        import os
        shutil.rmtree(self.temp_dir)
        os.chdir(self.original_cwd)
    
    def test_load_defaults(self):
        """Test loading default configuration."""
        import os
        os.chdir(self.temp_dir)
        
        config = load_config()
        
        self.assertEqual(config.error_type_filter, "all")
        self.assertEqual(config.ignore_error_labels, [])
    
    def test_load_from_file(self):
        """Test loading configuration from file."""
        import os
        
        config_path = Path(self.temp_dir) / "oc_pruner_config.json"
        config_data = {
            "error_type_filter": "error",
            "ignore_error_labels": ["extra_space"]
        }
        config_path.write_text(json.dumps(config_data))
        
        os.chdir(self.temp_dir)
        config = load_config()
        
        self.assertEqual(config.error_type_filter, "error")
        self.assertEqual(config.ignore_error_labels, ["extra_space"])
    
    def test_cli_override(self):
        """Test that CLI arguments override file configuration."""
        import os
        
        config_path = Path(self.temp_dir) / "oc_pruner_config.json"
        config_data = {
            "error_type_filter": "all",
            "ignore_error_labels": ["extra_space"]
        }
        config_path.write_text(json.dumps(config_data))
        
        os.chdir(self.temp_dir)
        config = load_config(
            error_type_filter="error",
            ignore_labels=["br_id_format"]
        )
        
        # CLI arguments should override file
        self.assertEqual(config.error_type_filter, "error")
        self.assertEqual(config.ignore_error_labels, ["br_id_format"])


class TestGenerateConfigTemplate(unittest.TestCase):
    """Tests for generate_config_template function."""
    
    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_generate_template(self):
        """Test generating a configuration template."""
        output_path = Path(self.temp_dir) / "config_template.yaml"
        
        generate_config_template(output_path)
        
        self.assertTrue(output_path.exists())
        
        content = output_path.read_text()
        self.assertIn("error_type_filter", content)
        self.assertIn("ignore_error_labels", content)
        self.assertIn("# oc_pruner Configuration File", content)
    
    def test_template_creates_parent_dirs(self):
        """Test that template generation creates parent directories."""
        output_path = Path(self.temp_dir) / "subdir" / "config.yaml"
        
        generate_config_template(output_path)
        
        self.assertTrue(output_path.exists())
        self.assertTrue(output_path.parent.exists())


if __name__ == "__main__":
    unittest.main()