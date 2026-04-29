# ISC License
#
# Copyright (c) 2026 Elia Rizzetto
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

"""
I/O utilities for reading and writing CSV and JSON files.
"""

import csv
import json
from pathlib import Path
from typing import List
import sys


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
        maxInt = sys.maxsize
        while True:
            # decrease the maxInt value by factor 10 
            # as long as the OverflowError occurs.
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt/10)
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
    Read a validation report file (JSON array or JSON-Lines).

    Supports both monolithic JSON (a single JSON array of issue objects)
    and JSON-Lines format (one JSON object per line), as produced by
    different versions of oc_validator.

    Args:
        report_path: Path to the validation report file

    Returns:
        List of issue objects

    Raises:
        FileNotFoundError: If the report file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"Validation report not found: {report_path}")

    raw = path.read_text(encoding="utf-8").strip()

    if not raw:
        return []

    # Try monolithic JSON array first (pre-1.0.0 oc_validator)
    try:
        issues = json.loads(raw)
        if isinstance(issues, list):
            return issues
    except json.JSONDecodeError:
        pass

    # Fall back to JSON-Lines (oc_validator >= 1.0.0)
    issues = []
    for line in raw.splitlines():
        line = line.strip()
        if line:
            issues.append(json.loads(line))

    if not issues:
        raise ValueError(
            f"Validation report contains no parseable issues: {report_path}"
        )

    return issues
