# oc_pruner

A tool for removing rows from an OpenCitations metadata or citations table based on the table's validation report, with support for running complete validation and pruning pipelines.

## Features

- **Selective filtering**: Filter by error type (error/warning) and/or specific error labels
- **Flexible configuration**: Configure via CLI arguments or configuration files
- **Row-level deletion**: Removes entire rows containing issues
- **Verbose output**: Detailed information about processing when needed
- **Complete pipeline**: Run validation + pruning pipeline with multiple rounds for thorough cleaning
- **Configurable pipeline**: Customise validation and pruning options when running the pipeline via CLI flags or config files


## Quick Start

### Run the Complete Pipeline

Run a full validation and pruning pipeline for metadata and citations files:

```bash
oc_pruner pipeline --meta metadata.csv --cits citations.csv --out-dir output_dir
```

This will:
1. Validate both files
2. Remove invalid rows
3. Re-validate the cleaned files
4. Repeat the process to catch any newly exposed issues
5. Perform a final validation check

You can customise the pipeline behaviour (which errors to ignore, whether to verify ID existence, etc.) via CLI flags or a configuration file:

```bash
# Using CLI flags
oc_pruner pipeline -m metadata.csv -c citations.csv -o output_dir --ignore-labels br_id_syntax --verify-id-existence

# Using a config file
oc_pruner pipeline -m metadata.csv -c citations.csv -o output_dir --config pipeline_config.yaml
```

See the [Configuration](#configuration) section for details on the available options.

### Prune a Single Table Based On Its Existing Validation Report

Remove all issues (errors and warnings) from a CSV file:

```bash
oc_pruner --csv input.csv --report report.json --output output.csv
```

Or use the explicit `prune` subcommand:

```bash
oc_pruner prune --csv input.csv --report report.json --output output.csv
```

### With Verbose Output

See detailed information about what's being processed:

```bash
oc_pruner prune --csv input.csv --report report.json --output output.csv --verbose
```

## Configuration

### CLI Arguments for `pipeline` mode (`pipeline` subcommand)

| Argument                  | Abbreviation | Required | Description                                                        |
|---------------------------|--------------|----------|--------------------------------------------------------------------|
| `--meta PATH`             | `-m`         | Yes      | Path to the input metadata CSV file                                |
| `--cits PATH`             | `-c`         | Yes      | Path to the input citations CSV file                               |
| `--out-dir PATH`          | `-o`         | Yes      | Path to the output directory where to write the output (pruned) files |
| `--config PATH`           | —            | No       | Path to a YAML/JSON configuration file for pipeline options        |
| `--error-type`            | `-e`         | No       | Filter issues by error type: `all` or `error`                     |
| `--ignore-labels LABELS`  | `-i`         | No       | Comma-separated list of error labels to ignore                     |
| `--verify-id-existence`   | —            | No       | Verify that bibliographic IDs exist via API lookup                 |
| `--use-meta-endpoint`     | —            | No       | Use the OC Meta endpoint for ID existence checks                   |
| `--strict-sequentiality`  | —            | No       | Skip closure check when individual validations report errors       |
| `--help`                  | `-h`         | No       | Show help message                                                  |

### CLI Arguments for single document mode (`prune` subcommand)

| Argument          | Abbreviation | Required | Description                               |
|-------------------|--------------|----------|-------------------------------------------|
| `--csv PATH`      | `-t`         | Yes      | Path to the input CSV file                |
| `--report PATH`   | `-r`         | Yes      | Path to the validation report JSON file   |
| `--output PATH`   | `-o`         | Yes      | Path for the output CSV file              |
| `--config PATH`   | `-c`         | No       | Path to configuration file (YAML or JSON) |
| `--error-type`    | `-e`         | No       | Filter by error type: all or error        |
| `--ignore-labels` | `-i`         | No       | Comma-separated error labels to ignore    |
| `--verbose`       | `-v`         | No       | Show detailed processing information      |
| `--init-config`   | —            | No       | Generate a configuration file template    |
| `--list-labels`   | —            | No       | List all valid error labels               |
| `--help`          | `-h`         | No       | Show help message                         |


### Configuration File

Create a configuration file for default settings. The tool looks for:

1. Explicitly specified file (via `--config`)
2. `oc_pruner_config.yaml` or `oc_pruner_config.json` in current directory
3. `~/.oc_pruner_config.yaml` in home directory

Generate a template:

```bash
oc_pruner --init-config
```

Example `oc_pruner_config.yaml`:

```yaml
# oc_pruner Configuration File

# ============================================================
# Pruning options (used by both 'prune' and 'pipeline')
# ============================================================

# Filter by error type: "all" (errors and warnings) or "error" (errors only)
error_type_filter: "all"

# List of error labels to ignore (rows with these issues will be kept, unless interested by other issues)
ignore_error_labels:
  - "extra_space"
  - "br_id_format"

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
```

### Configuration Priority

Settings are applied in this order (later override earlier):

1. **Default values** from the code
2. **Configuration file** if found
3. **CLI arguments** (highest priority)

## Usage Examples

### Run the Complete Validation + Pruning Pipeline from CLI

For thorough cleaning of OpenCitations metadata and citations files, use the `pipeline` command:

```bash
oc_pruner pipeline -m metadata.csv -c citations.csv -o output_dir
```

**Pipeline Arguments:**

| Argument       | Abbreviation | Required | Description                          |
|----------------|--------------|----------|--------------------------------------|
| `--meta PATH`  | `-m`         | Yes      | Path to original metadata CSV        |
| `--cits PATH`  | `-c`         | Yes      | Path to original citations CSV       |
| `--out-dir`    | `-o`         | Yes      | Base output directory for results    |
| `--config PATH` | —           | No       | Path to a YAML/JSON config file for pipeline options |
| `--error-type` | `-e`         | No       | Filter issues by error type: `all` or `error` |
| `--ignore-labels` | `-i`      | No       | Comma-separated error labels to ignore |
| `--verify-id-existence` | — | No       | Verify bibliographic IDs via API lookup |
| `--use-meta-endpoint` | —   | No       | Use OC Meta endpoint for ID checks   |
| `--strict-sequentiality` | — | No      | Skip closure check on validation errors |

**What the pipeline does:**

1. **First validation**: Validates both metadata and citations files
2. **First pruning**: Removes rows with validation errors
3. **Second validation**: Re-validates the cleaned files to catch new issues
4. **Second pruning**: Removes any newly exposed errors
5. **Third validation**: Re-validates again (removing citations may expose further metadata issues)
6. **Third pruning**: Final cleanup of any remaining errors
7. **Final validation**: Performs a sanity check on the final cleaned files

You can customise the pipeline via CLI flags or a config file. CLI flags override the config file:

```bash
# Using CLI flags
oc_pruner pipeline -m metadata.csv -c citations.csv -o output_dir --ignore-labels br_id_syntax --verify-id-existence

# Using a config file
oc_pruner pipeline -m metadata.csv -c citations.csv -o output_dir --config pipeline_config.yaml
```

The pipeline creates the following structure in the output directory:

```
output_dir/
├── cleaned/
│   ├── metadata.csv       # Final cleaned metadata
│   └── citations.csv      # Final cleaned citations
└── validation_reports/
    ├── first_round/
    │   ├── metadata/
    │   └── citations/
    ├── second_round/
    │   ├── metadata/
    │   └── citations/
    ├── third_round/
    │   ├── metadata/
    │   └── citations/
    └── final_round/
        ├── metadata/
        └── citations/
```

All operations are logged to `logs/pipeline_YYYYMMDD_HHMMSS.log`.

### Remove Only Errors (Single Document)

Ignore warnings and only remove rows with errors:

```bash
oc_pruner --csv data.csv --report report.json --output clean.csv --error-type error
```

### Ignore Specific Error Labels (Single Document)

Keep rows that have specific issues:

```bash
oc_pruner --csv data.csv --report report.json --output clean.csv \
  --ignore-labels extra_space,br_id_format
```

### Use Configuration File (Single Document)

Create a config file and use it:

```bash
oc_pruner --init-config
# Edit oc_pruner_config.yaml
oc_pruner --csv data.csv --report report.json --output clean.csv
```

### Combine Filters (Single Document)

Remove only errors except for specific labels:

```bash
oc_pruner --csv data.csv --report report.json --output clean.csv \
  --error-type error \
  --ignore-labels extra_space,type_format
```

### List Available Error Labels

See all valid error labels:

```bash
oc_pruner --list-labels
```

## Validation Report Model

The validation report is a JSON file following the [validation report schema](schema.json). It consists of a list of issue objects, where each object represents a validation issue tied to specific locations in the CSV table.

### Issue Object Structure

```json
{
  "validation_level": "csv_wellformedness",
  "error_type": "error",
  "error_label": "extra_space",
  "message": "The value in this field is not expressed in compliance with the syntax...",
  "valid": false,
  "position": {
    "located_in": "item",
    "table": {
      "0": {
        "id": [1]
      }
    }
  }
}
```


### Error Labels Reference

The supported issue labels are listed in the [validation report schema](schema.json) and the associated issues are explained [in this summary table](errors_map.csv).

## How It Works

1. **Load Files**: Reads the CSV file and validation report
2. **Filter Issues**: Based on configuration, determines which issues to consider
   - `--error-type error`: Only considers "error" type issues
   - `--ignore-labels`: Ignores issues with specified labels
3. **Extract Affected Rows**: For each relevant issue, extracts row numbers from the position data
4. **Remove Rows**: Removes entire rows that contain any non-ignored issue
5. **Write Output**: Saves the cleaned CSV file

**Important**: If a row has both an ignorable issue and a non-ignorable issue, the entire row is removed (the non-ignorable issue takes precedence).

## API Usage

You can also use oc_pruner as a Python library:

### Prune a Single Document

```python
from oc_pruner import prune
from oc_pruner.config import PrunerConfig

# Create configuration
config = PrunerConfig(
    error_type_filter="all",
    ignore_error_labels=["extra_space"]
)

# Prune the CSV file
prune(
    csv_path="input.csv",
    report_path="report.json",
    output_path="output.csv",
    config=config,
    verbose=True
)
```

### Run the Pipeline

```python
from oc_pruner.pipeline import run_pruning_pipeline
from oc_pruner.config import PipelineConfig

# Create pipeline configuration
config = PipelineConfig(
    error_type_filter="all",
    ignore_error_labels=["extra_space"],
    verify_id_existence=False,
    use_meta_endpoint=False,
    strict_sequentiality=False,
)

# Run the pipeline
run_pruning_pipeline(
    original_fp_meta="metadata.csv",
    original_fp_cits="citations.csv",
    base_out_dir="output",
    pipeline_config=config,
)
```
