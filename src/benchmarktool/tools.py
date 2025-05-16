"""
Created on Jan 15, 2010

@author: Roland Kaminski
"""

import os
import random
import stat
from collections.abc import MutableSequence
from typing import Any


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


def median_sorted(sequence: MutableSequence[Any]) -> Any:
    """
    Returns the median of a sorted sequence.
    (Returns 0 if the sequence is empty.)

    Attributes:
        sequence (MutableSequence[Any]): Sequence
    """
    if len(sequence) == 0:
        return 0
    middle = len(sequence) // 2
    value = sequence[middle]
    if 2 * middle == len(sequence):
        value = (value + sequence[middle - 1]) / 2.0
    return value


# unsused -> np.median
# consider removing
# pylint: disable=consider-using-max-builtin
def median(sequence: MutableSequence[Any]) -> Any:
    """
    Returns the median of an unordered sequence.
    (Returns 0 if the sequence is empty.)

    Attributes:
        sequence (MutableSequence[Any]): Sequence
    """

    def partition(sequence: MutableSequence[Any], left: int, right: int) -> int:
        """
        Selects a pivot element and moves all smaller(bigger)
        elements to the left(right).

        Attributes:
            sequence (MutableSequence[Any]): Sequence
            left (int):                      left index
            right (int):                     right index
        """
        pivot_idx = random.randint(left, right)
        pivot_value = sequence[pivot_idx]
        sequence[pivot_idx], sequence[right] = sequence[right], sequence[pivot_idx]
        store_idx = left
        for i in range(left, right):
            if sequence[i] < pivot_value:
                sequence[store_idx], sequence[i] = sequence[i], sequence[store_idx]
                store_idx = store_idx + 1
        sequence[right], sequence[store_idx] = sequence[store_idx], sequence[right]
        return store_idx

    def select(sequence: MutableSequence[Any], left: int, right: int, k: int) -> Any:
        """
        Selects the k-th element as in the ordered sequence.

        Attributes:
            sequence (MutableSequence[Any]): Sequence
            left (int):                      left index
            right (int):                     right index
        """
        pivot_idx = partition(sequence, left, right)
        if k == pivot_idx:
            return sequence[k]
        if k < pivot_idx:
            return select(sequence, left, pivot_idx - 1, k)
        return select(sequence, pivot_idx + 1, right, k)

    if len(sequence) == 0:
        return 0
    middle = len(sequence) // 2
    select(sequence, 0, len(sequence) - 1, middle)
    value = sequence[middle]
    if 2 * middle == len(sequence):
        maximum = sequence[middle - 1]
        for x in sequence[: middle - 1]:
            if x > maximum:
                maximum = x
        value = (value + maximum) / 2.0
    return value


def set_executable(filename: str) -> None:
    """
    Set execution permissions for given file.

    Attributes:
        filename (str): A file
    """
    filestat = os.stat(filename)
    os.chmod(filename, filestat[0] | stat.S_IXUSR)
