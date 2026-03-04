"""
Configuration management for oc_pruner.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import yaml

from oc_pruner.schema import ERROR_TYPES, ERROR_LABELS


@dataclass
class PrunerConfig:
    """Configuration for the CSV pruner."""
    
    error_type_filter: str = "all"  # "all" or "error"
    ignore_error_labels: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.error_type_filter not in ["all", "error"]:
            raise ValueError(
                f"error_type_filter must be 'all' or 'error', got '{self.error_type_filter}'"
            )
        
        for label in self.ignore_error_labels:
            if label not in ERROR_LABELS:
                raise ValueError(
                    f"Invalid error label '{label}'. Valid labels are: {', '.join(ERROR_LABELS)}"
                )


def find_config_file(config_path: Optional[str] = None) -> Optional[Path]:
    """
    Find a configuration file.
    
    Priority:
    1. Explicitly provided config_path
    2. Current directory: oc_pruner_config.yaml or oc_pruner_config.json
    3. Home directory: ~/.oc_pruner_config.yaml
    
    Args:
        config_path: Explicit path to config file
        
    Returns:
        Path to config file if found, None otherwise
    """
    if config_path:
        path = Path(config_path)
        if path.exists():
            return path
        return None
    
    # Check current directory
    cwd = Path.cwd()
    for filename in ["oc_pruner_config.yaml", "oc_pruner_config.json"]:
        path = cwd / filename
        if path.exists():
            return path
    
    # Check home directory
    home = Path.home()
    home_config = home / ".oc_pruner_config.yaml"
    if home_config.exists():
        return home_config
    
    return None


def load_config_from_file(config_path: Path) -> PrunerConfig:
    """
    Load configuration from a YAML or JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        PrunerConfig instance
        
    Raises:
        ValueError: If file format is not supported or content is invalid
    """
    suffix = config_path.suffix.lower()
    
    if suffix == ".json":
        import json
        with open(config_path, "r") as f:
            data = json.load(f)
    elif suffix in [".yaml", ".yml"]:
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
        except ImportError:
            raise ValueError(
                "YAML configuration requires PyYAML package. "
                "Install with: pip install pyyaml"
            )
    else:
        raise ValueError(
            f"Unsupported config file format: {suffix}. "
            "Use .json, .yaml, or .yml"
        )
    
    if data is None:
        data = {}
    
    return PrunerConfig(
        error_type_filter=data.get("error_type_filter", "all"),
        ignore_error_labels=data.get("ignore_error_labels") or []
    )


def load_config(
    config_path: Optional[str] = None,
    error_type_filter: Optional[str] = None,
    ignore_labels: Optional[List[str]] = None
) -> PrunerConfig:
    """
    Load configuration with proper priority.
    
    Priority (highest to lowest):
    1. CLI arguments (error_type_filter, ignore_labels)
    2. Configuration file
    3. Default values
    
    Args:
        config_path: Explicit path to config file
        error_type_filter: Override from CLI
        ignore_labels: Override from CLI
        
    Returns:
        PrunerConfig instance
    """
    # Start with defaults
    config = PrunerConfig()
    
    # Load from file if available
    found_config = find_config_file(config_path)
    if found_config:
        try:
            config = load_config_from_file(found_config)
        except ValueError as e:
            raise ValueError(f"Error loading config file '{found_config}': {e}")
    
    # Override with CLI arguments
    if error_type_filter is not None:
        config.error_type_filter = error_type_filter
    
    if ignore_labels is not None:
        config.ignore_error_labels = ignore_labels
    
    # Re-validate after overrides
    config.__post_init__()
    
    return config


def generate_config_template(output_path: Path) -> None:
    """
    Generate a configuration file template.
    
    Args:
        output_path: Path where to write the template
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    template = """# oc_pruner Configuration File
# This file allows you to set default options for the CSV pruner

# Filter by error type: "all" (errors and warnings) or "error" (errors only)
error_type_filter: "all"

# List of error labels to ignore (data with these issues will be kept)
# Uncomment and add labels as needed
ignore_error_labels:
  # - "br_id_existence"
  # - "br_id_format"
  # - "br_id_syntax"
  # - "date_format"
  # - "duplicate_br"
  # - "duplicate_citation"
  # - "duplicate_id"
  # - "duplicate_ra"
  # - "extra_space"
  # - "missing_citations"
  # - "missing_metadata"
  # - "orphan_ra_id"
  # - "orphan_venue_id"
  # - "page_format"
  # - "page_interval"
  # - "people_item_format"
  # - "publisher_format"
  # - "ra_id_existence"
  # - "ra_id_syntax"
  # - "required_fields"
  # - "required_value_cits"
  # - "row_semantics"
  # - "self-citation"
  # - "type_format"
  # - "uppercase_title"
  # - "venue_format"
  # - "volume_issue_format"
"""
    
    with open(output_path, "w") as f:
        f.write(template)
