"""
oc_pruner - A tool for removing selected pieces of data from an OpenCitations 
metadata or citations table based on the table's validation report.
"""

__version__ = "0.1.0"
__author__ = "Elia Rizzetto"

from oc_pruner.core import prune

__all__ = ["prune"]