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


@dataclass
class PipelineConfig:
    """Configuration for the validation + pruning pipeline."""

    # Pruning options
    error_type_filter: str = "all"  # "all" or "error"
    ignore_error_labels: List[str] = field(default_factory=list)

    # Validation options (passed to Validator via meta_kwargs / cits_kwargs)
    verify_id_existence: bool = False
    use_meta_endpoint: bool = False

    # ClosureValidator options
    strict_sequentiality: bool = False
    use_lmdb: bool = False
    map_size: int = 1 * 1024 ** 3  # 1 GB
    cache_dir: Optional[str] = None

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

    @property
    def pruner_config(self) -> PrunerConfig:
        """Derive a PrunerConfig from this PipelineConfig."""
        return PrunerConfig(
            error_type_filter=self.error_type_filter,
            ignore_error_labels=list(self.ignore_error_labels),
        )

    @property
    def meta_kwargs(self) -> dict:
        """Keyword arguments for the metadata Validator."""
        return {
            "verify_id_existence": self.verify_id_existence,
            "use_meta_endpoint": self.use_meta_endpoint,
            "use_lmdb": self.use_lmdb,
            "map_size": self.map_size,
            "cache_dir": self.cache_dir,
        }

    @property
    def cits_kwargs(self) -> dict:
        """Keyword arguments for the citations Validator."""
        return {
            "verify_id_existence": self.verify_id_existence,
            "use_meta_endpoint": self.use_meta_endpoint,
            "use_lmdb": self.use_lmdb,
            "map_size": self.map_size,
            "cache_dir": self.cache_dir,
        }


def load_pipeline_config(
    config_path: Optional[str] = None,
    error_type_filter: Optional[str] = None,
    ignore_labels: Optional[List[str]] = None,
    verify_id_existence: Optional[bool] = None,
    use_meta_endpoint: Optional[bool] = None,
    strict_sequentiality: Optional[bool] = None,
    use_lmdb: Optional[bool] = None,
    map_size: Optional[int] = None,
    cache_dir: Optional[str] = None,
) -> PipelineConfig:
    """
    Load pipeline configuration with proper priority.

    Priority (highest to lowest):
    1. CLI arguments
    2. Configuration file
    3. Default values

    Returns:
        PipelineConfig instance
    """
    config = PipelineConfig()

    # Load from file if available
    found_config = find_config_file(config_path)
    if found_config:
        config = _load_pipeline_config_from_file(found_config)

    # Override with CLI arguments
    if error_type_filter is not None:
        config.error_type_filter = error_type_filter
    if ignore_labels is not None:
        config.ignore_error_labels = ignore_labels
    if verify_id_existence is not None:
        config.verify_id_existence = verify_id_existence
    if use_meta_endpoint is not None:
        config.use_meta_endpoint = use_meta_endpoint
    if strict_sequentiality is not None:
        config.strict_sequentiality = strict_sequentiality
    if use_lmdb is not None:
        config.use_lmdb = use_lmdb
    if map_size is not None:
        config.map_size = map_size
    if cache_dir is not None:
        config.cache_dir = cache_dir

    # Re-validate after overrides
    config.__post_init__()

    return config


def _load_pipeline_config_from_file(config_path: Path) -> PipelineConfig:
    """Load PipelineConfig from a YAML or JSON file."""
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

    return PipelineConfig(
        error_type_filter=data.get("error_type_filter", "all"),
        ignore_error_labels=data.get("ignore_error_labels") or [],
        verify_id_existence=data.get("verify_id_existence", False),
        use_meta_endpoint=data.get("use_meta_endpoint", False),
        strict_sequentiality=data.get("strict_sequentiality", False),
        use_lmdb=data.get("use_lmdb", False),
        map_size=data.get("map_size", 1 * 1024 ** 3),
        cache_dir=data.get("cache_dir"),
    )


def generate_config_template(output_path: Path) -> None:
    """
    Generate a configuration file template.
    
    Args:
        output_path: Path where to write the template
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    template = """# oc_pruner Configuration File
# This file allows you to set default options for the pruner and pipeline.

# ============================================================
# Pruning options (used by both 'prune' and 'pipeline')
# ============================================================

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

# ============================================================
# Validation options (used by 'pipeline')
# ============================================================

# Whether to verify that bibliographic IDs exist via API lookup
verify_id_existence: false

# Whether to use the OC Meta endpoint for ID existence checks
use_meta_endpoint: false

# Whether to skip closure check when individual validations report errors
strict_sequentiality: false

# Whether to use LMDB for caching (recommended for large files)
use_lmdb: false

# Maximum size in bytes for LMDB environments (default: 1 GB)
# map_size: 1073741824

# Base directory for LMDB caches
# cache_dir: null
"""
    
    with open(output_path, "w") as f:
        f.write(template)
