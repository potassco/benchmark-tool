"""
Created on Jan 15, 2010

@author: Roland Kaminski
"""

import os
import re
import stat


def mkdir_p(path: str) -> None:
    """
    Simulates "mkdir -p" functionality.

    Attributes:
        path (str): A string holding the path to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def get_int_time(str_rep: str) -> int:
    """
    Converts '[<D>d] [<H>h] [<M>m] [<S>s]' time format to integer value in seconds.

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


def get_xml_time(int_rep: int) -> str:
    """
    Converts integer value in seconds to '[<D>d] [<H>h] [<M>m] [<S>s]' time format.

    Attributes:
        int_rep (int): Int representation.
    """
    s = int_rep % 60
    int_rep //= 60
    m = int_rep % 60
    int_rep //= 60
    h = int_rep % 24
    d = int_rep // 24
    return "{0:02}d {1:02}h {2:02}m {3:02}s".format(d, h, m, s)


def get_slurm_time(int_rep: int) -> str:
    """
    Converts integer value in seconds to [[h:]m:]s time format.

    Attributes:
        int_rep (int): Int representation.
    """
    s = int_rep % 60
    int_rep //= 60
    m = int_rep % 60
    int_rep //= 60
    h = int_rep % 24
    d = int_rep // 24
    return "{0:02}-{1:02}:{2:02}:{3:02}".format(d, h, m, s)


def set_executable(filename: str) -> None:
    """
    Set execution permissions for given file.

    Attributes:
        filename (str): A file
    """
    filestat = os.stat(filename)
    os.chmod(filename, filestat[0] | stat.S_IXUSR)
