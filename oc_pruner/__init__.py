"""
oc_pruner - A tool for removing invalid rows from OpenCitations 
metadata or citations tables based on the table's validation report.
"""

__version__ = "0.1.0"
__author__ = "Elia Rizzetto"

from oc_pruner.core import prune

__all__ = ["prune"]