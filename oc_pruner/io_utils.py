"""
I/O utilities for reading and writing CSV and JSON files.
"""

import csv
import json
from pathlib import Path
from typing import List


def read_csv(csv_path: str) -> List[List[str]]:
    """
    Read a CSV file and return it as a list of lists.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of rows, where each row is a list of strings
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        IOError: If there's an error reading the file
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    rows = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        csv.field_size_limit = 1000000
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def write_csv(data: List[List[str]], output_path: str) -> None:
    """
    Write data to a CSV file.
    
    Args:
        data: List of rows to write
        output_path: Path to the output CSV file
        
    Raises:
        IOError: If there's an error writing the file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(data)


def read_validation_report(report_path: str) -> List[dict]:
    """
    Read a validation report JSON file.
    
    Args:
        report_path: Path to the validation report JSON file
        
    Returns:
        List of issue objects
        
    Raises:
        FileNotFoundError: If the report file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"Validation report not found: {report_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        issues = json.load(f)
    
    if not isinstance(issues, list):
        raise ValueError(
            f"Validation report must be a list of issues, got {type(issues).__name__}"
        )
    
    return issues
