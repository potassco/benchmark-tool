"""
Helper functions for result parsing.
"""

import gzip
import os
from io import TextIOWrapper


def open_results(path: str, file_name: str) -> TextIOWrapper:
    """
    Open result file, automatically handling gzip-compressed files if necessary.

    Attributes:
        path (str):      The path to the directory containing the result file.
        file_name (str): The name of the result file (without the .gz extension if compressed).
    """
    path = os.path.join(path, file_name)
    gz_path = path + ".gz"
    if os.path.isfile(gz_path):
        return gzip.open(gz_path, errors="ignore", encoding="utf-8", mode="rt")
    return open(path, errors="ignore", encoding="utf-8", mode="rt")
