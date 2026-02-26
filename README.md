# oc_pruner

A tool for removing selected pieces of data from an OpenCitations metadata or citations table based on the table's validation report.

## Features

- **No external dependencies**: Uses only Python standard library
- **Flexible configuration**: Configure via CLI arguments or configuration files
- **Selective filtering**: Filter by error type and/or specific error labels
- **Row-level deletion**: Removes entire rows containing issues
- **Verbose output**: Detailed information about processing when needed
- **Easy to use**: Simple CLI with helpful error messages

## Installation

### Requirements

- Python 3.11 or higher

### Install from source

```bash
git clone https://github.com/eliarizzetto/oc_pruner.git
cd oc_pruner
pip install -e .
```

### Install with pip

```bash
pip install oc-pruner
```

## Quick Start

### Basic Usage

Remove all issues (errors and warnings) from a CSV file:

```bash
oc_pruner --csv input.csv --report report.json --output output.csv
```

### With Verbose Output

See detailed information about what's being processed:

```bash
oc_pruner --csv input.csv --report report.json --output output.csv --verbose
```

## Configuration

### CLI Arguments

| Argument | Required | Description |
|----------|-----------|-------------|
| `--csv PATH` | Yes | Path to the input CSV file |
| `--report PATH` | Yes | Path to the validation report JSON file |
| `--output PATH` | Yes | Path for the output CSV file |
| `--config PATH` | No | Path to configuration file (YAML or JSON) |
| `--error-type {all,error}` | No | Filter by error type (default: all) |
| `--ignore-labels LABELS` | No | Comma-separated error labels to ignore |
| `--verbose, -v` | No | Show detailed processing information |
| `--init-config` | No | Generate a configuration file template |
| `--list-labels` | No | List all valid error labels |
| `--version` | No | Show version number |
| `--help, -h` | No | Show help message |

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

# Filter by error type: "all" (errors and warnings) or "error" (errors only)
error_type_filter: "all"

# List of error labels to ignore (data with these issues will be kept)
ignore_error_labels:
  - "extra_space"
  - "br_id_format"
```

### Configuration Priority

Settings are applied in this order (later override earlier):

1. **Default values** from the code
2. **Configuration file** if found
3. **CLI arguments** (highest priority)

## Usage Examples

### Remove Only Errors

Ignore warnings and only remove rows with errors:

```bash
oc_pruner --csv data.csv --report report.json --output clean.csv --error-type error
```

### Ignore Specific Error Labels

Keep rows that have specific issues:

```bash
oc_pruner --csv data.csv --report report.json --output clean.csv \
  --ignore-labels extra_space,br_id_format
```

### Use Configuration File

Create a config file and use it:

```bash
oc_pruner --init-config
# Edit oc_pruner_config.yaml
oc_pruner --csv data.csv --report report.json --output clean.csv
```

### Combine Filters

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

## Validation Report Format

The validation report is a JSON file following the [OpenCitations validation schema](schema.json). It consists of a list of issue objects, where each object represents a validation issue tied to specific locations in the CSV table.

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

### Fields

- `validation_level`: One of "csv_wellformedness", "external_syntax", or "semantic"
- `error_type`: "error" or "warning"
- `error_label`: The specific type of error (see `--list-labels` for all options)
- `message`: Human-readable description of the issue
- `valid`: Boolean indicating if the data is valid (always `false` for errors)
- `position`: Location of the affected data
  - `located_in`: "row", "field", or "item"
  - `table`: Object mapping row numbers (as strings) to affected fields

## Error Labels Reference

The following error labels are supported:

- `br_id_existence` - Bibliographic resource ID existence
- `br_id_format` - Bibliographic resource ID format
- `br_id_syntax` - Bibliographic resource ID syntax
- `date_format` - Date format validation
- `duplicate_br` - Duplicate bibliographic resource
- `duplicate_citation` - Duplicate citation
- `duplicate_id` - Duplicate ID
- `duplicate_ra` - Duplicate reference article
- `extra_space` - Extra whitespace in fields
- `missing_citations` - Missing citations
- `missing_metadata` - Missing metadata
- `orphan_ra_id` - Orphan reference article ID
- `orphan_venue_id` - Orphan venue ID
- `page_format` - Page number format
- `page_interval` - Page interval validation
- `people_item_format` - People item format
- `publisher_format` - Publisher format
- `ra_id_existence` - Reference article ID existence
- `ra_id_syntax` - Reference article ID syntax
- `required_fields` - Missing required fields
- `required_value_cits` - Required values in citations
- `row_semantics` - Row-level semantic validation
- `self-citation` - Self-citation detection
- `type_format` - Publication type format
- `uppercase_title` - Uppercase title validation
- `venue_format` - Venue format
- `volume_issue_format` - Volume/issue format

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


## License

This project is licensed under the LICENSE file.
