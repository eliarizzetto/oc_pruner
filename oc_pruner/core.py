"""
Core functionality for pruning CSV files based on validation reports.
"""

from typing import List, Set
from oc_pruner.config import PrunerConfig
from oc_pruner.io_utils import read_csv, write_csv, read_validation_report


def should_ignore_issue(issue: dict, config: PrunerConfig) -> bool:
    """
    Determine if an issue should be ignored based on configuration.
    
    Args:
        issue: Issue object from validation report
        config: PrunerConfig instance
        
    Returns:
        True if the issue should be ignored, False otherwise
    """
    # Check error_type filter
    if config.error_type_filter == "error" and issue["error_type"] == "warning":
        return True
    
    # Check if error_label is in ignore list
    if issue["error_label"] in config.ignore_error_labels:
        return True
    
    return False


def extract_affected_rows(issue: dict) -> Set[int]:
    """
    Extract all row numbers affected by an issue.
    
    Args:
        issue: Issue object from validation report
        
    Returns:
        Set of row numbers (0-indexed)
    """
    rows = set()
    position = issue.get("position", {})
    
    if not position:
        return rows
    
    table = position.get("table", {})
    
    # The table dict has row numbers as keys (as strings)
    for row_str in table.keys():
        try:
            row_num = int(row_str)
            rows.add(row_num)
        except (ValueError, TypeError):
            # Skip invalid row numbers
            continue
    
    return rows


def determine_rows_to_remove(
    issues: List[dict],
    config: PrunerConfig,
    verbose: bool = False
) -> Set[int]:
    """
    Determine which rows should be removed based on issues and configuration.
    
    Args:
        issues: List of issue objects from validation report
        config: PrunerConfig instance
        verbose: If True, print detailed information about processing
        
    Returns:
        Set of row numbers to remove (0-indexed)
    """
    rows_to_remove = set()
    ignored_issues = []
    processed_issues = []
    
    for issue in issues:
        if should_ignore_issue(issue, config):
            ignored_issues.append(issue)
            continue
        
        # Extract affected rows
        affected_rows = extract_affected_rows(issue)
        rows_to_remove.update(affected_rows)
        
        if verbose:
            processed_issues.append({
                "issue": issue,
                "rows": affected_rows,
                "action": "REMOVE"
            })
    
    if verbose:
        print(f"\nProcessing issues:")
        for info in processed_issues:
            issue = info["issue"]
            rows = sorted(info["rows"])
            print(f"  - {issue['error_label']} (row(s) {', '.join(map(str, rows))}): REMOVE")
        
        if ignored_issues:
            print(f"\nIgnored issues:")
            for issue in ignored_issues:
                print(f"  - {issue['error_label']}")
    
    return rows_to_remove


def prune(
    csv_path: str,
    report_path: str,
    output_path: str,
    config: PrunerConfig,
    verbose: bool = False
) -> None:
    """
    Prune a CSV file based on its validation report and user configuration.
    
    This function reads a CSV file and its validation report, determines which
    rows contain data with issues that should not be ignored, and writes a
    cleaned version of the CSV file with those rows removed.
    
    Args:
        csv_path: Path to the input CSV file
        report_path: Path to the validation report JSON file
        output_path: Path for the output CSV file
        config: PrunerConfig instance with user preferences
        verbose: If True, print detailed processing information
    """
    # Read input files
    csv_data = read_csv(csv_path)
    issues = read_validation_report(report_path)
    
    if verbose:
        print(f"Loading CSV file: {csv_path} ({len(csv_data)} rows)")
        print(f"Loading validation report: {report_path} ({len(issues)} issues)")
        print(f"Configuration: Remove {config.error_type_filter} issues, ignore {len(config.ignore_error_labels)} labels")
    
    # Determine which rows to remove
    rows_to_remove = determine_rows_to_remove(issues, config, verbose=verbose)
    
    # Filter CSV data (keep header and rows not in removal set)
    header_row = csv_data[0] if csv_data else []
    data_rows = csv_data[1:] if csv_data else []
    
    # Keep rows that are not in the removal set
    filtered_data = [header_row]
    for idx, row in enumerate(data_rows):
        if idx not in rows_to_remove:
            filtered_data.append(row)
    
    # Write output
    write_csv(filtered_data, output_path)
    
    removed_count = len(rows_to_remove)
    kept_count = len(data_rows) - removed_count

    if verbose:
        print(f"\nResults:")
        print(f"  Original rows: {len(csv_data)}")
        print(f"  Rows removed: {removed_count} ({', '.join(map(str, sorted(rows_to_remove)))})")
        print(f"  Rows kept: {kept_count}")
        print(f"  Output written to: {output_path}")
    else:
        print(f"Removed {removed_count} out of {len(data_rows)} original rows. Output written to: {output_path}")