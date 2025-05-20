"""
Created on Jan 15, 2010

@author: Roland Kaminski
"""

import os
import stat


def mkdir_p(path: str) -> None:
    """
    Simulates "mkdir -p" functionality.

    Attributes:
        path (str): A string holding the path to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def xml_time(str_rep: str) -> int:
    """
    Converts [[h:]m:]s time format to integer value in seconds.

    Attributes:
        str_rep (str): String representation.
    """
    timeout = str_rep.split(":")
    seconds = int(timeout[-1])
    minutes = hours = 0
    if len(timeout) > 1:
        minutes = int(timeout[-2])
    if len(timeout) > 2:
        hours = int(timeout[-3])
    return seconds + minutes * 60 + hours * 60 * 60


def pbs_time(int_rep: int) -> str:
    """
    Converts integer value in seconds to [[h:]m:]s time format.

    Attributes:
        int_rep (int): Int representation.
    """
    s = int_rep % 60
    int_rep //= 60
    m = int_rep % 60
    int_rep //= 60
    h = int_rep
    return "{0:02}:{1:02}:{2:02}".format(h, m, s)


def set_executable(filename: str) -> None:
    """
    Set execution permissions for given file.

    Attributes:
        filename (str): A file
    """
    filestat = os.stat(filename)
    os.chmod(filename, filestat[0] | stat.S_IXUSR)
