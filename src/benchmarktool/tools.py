"""
Created on Jan 15, 2010

@author: Roland Kaminski
"""

import importlib.util
import os
import re
import stat
import sys
from types import ModuleType


def mkdir_p(path: str) -> None:
    """
    Simulates `mkdir -p` functionality.

    Attributes:
        path (str): A string holding the path to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def xml_to_seconds_time(str_rep: str) -> int:
    """
    Converts `[<D>d] [<H>h] [<M>m] [<S>s]` time format to seconds.

    Attributes:
        str_rep (str): String representation.
    """
    mult = {"d": 86400, "h": 3600, "m": 60, "s": 1, "so": 1}
    m = re.fullmatch(
        r"(?P<so>[0-9]+)|(?:(?P<d>[0-9]+)d)?\s*(?:(?P<h>[0-9]+)h)?\s*(?:(?P<m>[0-9]+)m)?\s*(?:(?P<s>[0-9]+)s)?", str_rep
    )
    accu = 0
    if m is not None:
        for key, val in m.groupdict().items():
            if val is not None:
                accu += int(val) * mult[key]
    return accu


def seconds_to_xml_time(int_rep: int) -> str:
    """
    Converts time in seconds to `[<D>d] [<H>h] [<M>m] [<S>s]` time format.

    Attributes:
        int_rep (int): Int representation.
    """
    s = int_rep % 60
    int_rep //= 60
    m = int_rep % 60
    int_rep //= 60
    h = int_rep % 24
    d = int_rep // 24
    return f"{d:02}d {h:02}h {m:02}m {s:02}s"


def seconds_to_slurm_time(int_rep: int) -> str:
    """
    Converts time in seconds to `DD-HH:MM:SS` time format.

    Attributes:
        int_rep (int): Int representation.
    """
    s = int_rep % 60
    int_rep //= 60
    m = int_rep % 60
    int_rep //= 60
    h = int_rep % 24
    d = int_rep // 24
    return f"{d:02}-{h:02}:{m:02}:{s:02}"


def set_executable(filename: str) -> None:
    """
    Set execution permissions for given file.

    Attributes:
        filename (str): A file
    """
    filestat = os.stat(filename)
    os.chmod(filename, filestat[0] | stat.S_IXUSR)


def import_from_path(module_name: str, file_path: str) -> ModuleType:  # nocoverage
    """
    Helper function to import modules from path.

    Attributes:
        module_name (str):  Name of the module.
        file_path (str):    Path to the module.
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
