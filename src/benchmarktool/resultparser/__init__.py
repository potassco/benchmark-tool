"""
Helper functions for result parsing.
"""

import gzip
import os
import re
from io import TextIOWrapper
from typing import Any

runlim_re = {
    "time": ("float", re.compile(r"^\[runlim\] real:\s*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "rstatus": ("string", re.compile(r"^\[runlim\] status:\s*(?P<val>.*)$")),
    "mem": ("float", re.compile(r"^\[runlim\] space:\s*(?P<val>[0-9]+(\.[0-9]+)?) MB")),
}


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


def parse_watcher(path: str) -> dict[str, tuple[str, Any]]:
    """
    Extract runlim measures from the text watcher output.

    Attributes:
        path (str): The path to the directory containing the watcher output.
    """
    result: dict[str, tuple[str, Any]] = {}
    with open_results(path, "runsolver.watcher") as file:
        for line in file:
            for name, (kind, pattern) in runlim_re.items():
                match = pattern.match(line)  # pylint: disable=maybe-no-member
                if match:
                    value = match.group("val")
                    result[name] = (kind, float(value) if kind == "float" else value)
    return result
