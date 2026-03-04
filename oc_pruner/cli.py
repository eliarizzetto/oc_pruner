"""
Command-line interface for oc_pruner.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from oc_pruner.config import load_config, generate_config_template
from oc_pruner.core import prune
from oc_pruner.schema import ERROR_LABELS


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="oc_pruner",
        description="Remove invalid rows from an OpenCitations metadata or citations table based on the table's validation report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove all issues (errors and warnings)
  oc_pruner --csv input.csv --report report.json --output output.csv

  # Remove only errors (ignore warnings)
  oc_pruner --csv input.csv --report report.json --output output.csv --error-type error

  # Remove all issues except specific labels
  oc_pruner --csv input.csv --report report.json --output output.csv --ignore-labels extra_space,br_id_format

  # Use a configuration file
  oc_pruner --csv input.csv --report report.json --output output.csv --config config.yaml

  # Generate a configuration template
  oc_pruner --init-config

For more information, see: https://github.com/eliarizzetto/oc_pruner
        """
    )
    
    # Required arguments
    parser.add_argument(
        "-t",
        "--csv",
        type=str,
        metavar="PATH",
        help="Path to the input CSV file"
    )
    
    parser.add_argument(
        "-r",
        "--report",
        type=str,
        metavar="PATH",
        help="Path to the validation report JSON file"
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="PATH",
        help="Path for the output CSV file"
    )
    
    # Optional arguments
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="PATH",
        help="Path to configuration file (YAML or JSON)"
    )
    
    parser.add_argument(
        "-e",
        "--error-type",
        type=str,
        choices=["all", "error"],
        default=None,
        help="Filter issues by error type: 'all' (errors and warnings) or 'error' (errors only). Default: from config file or 'all'"
    )
    
    parser.add_argument(
        "-i",
        "--ignore-labels",
        type=str,
        metavar="LABELS",
        help="Comma-separated list of error labels to ignore. Example: extra_space,br_id_format,type_format"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed processing information"
    )
    
    # Special operations
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Generate a configuration file template in the current directory"
    )
    
    parser.add_argument(
        "--list-labels",
        action="store_true",
        help="List all valid error labels and exit"
    )
    
    return parser


def parse_ignore_labels(labels_str: str) -> List[str]:
    """
    Parse a comma-separated string of error labels.
    
    Args:
        labels_str: Comma-separated labels
        
    Returns:
        List of label strings
    """
    if not labels_str:
        return []
    
    labels = [label.strip() for label in labels_str.split(",")]
    labels = [label for label in labels if label]  # Remove empty strings
    
    return labels


def list_all_labels() -> None:
    """Print all valid error labels and exit."""
    print("Valid error labels:")
    for i, label in enumerate(ERROR_LABELS, 1):
        print(f"  {label}")
    print(f"\nTotal: {len(ERROR_LABELS)} labels")
    print("\nUse these labels with --ignore-labels to ignore specific issues.")


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special operations
    if args.list_labels:
        list_all_labels()
        return 0
    
    if args.init_config:
        config_path = Path.cwd() / "oc_pruner_config.yaml"
        try:
            generate_config_template(config_path)
            print(f"Configuration template created: {config_path}")
            print("Edit this file to set your default options.")
            return 0
        except Exception as e:
            print(f"Error creating config template: {e}", file=sys.stderr)
            return 1
    
    # Validate required arguments
    if not args.csv:
        parser.error("--csv is required")
    
    if not args.report:
        parser.error("--report is required")
    
    if not args.output:
        parser.error("--output is required")
    
    # Parse ignore labels
    ignore_labels = None
    if args.ignore_labels:
        ignore_labels = parse_ignore_labels(args.ignore_labels)
    
    # Load configuration
    try:
        config = load_config(
            config_path=args.config,
            error_type_filter=args.error_type,
            ignore_labels=ignore_labels
        )
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return 1
    
    # Run pruning
    try:
        prune(
            csv_path=args.csv,
            report_path=args.report,
            output_path=args.output,
            config=config,
            verbose=args.verbose
        )
        return 0
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())