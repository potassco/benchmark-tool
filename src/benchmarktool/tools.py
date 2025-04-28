"""
Created on Jan 15, 2010

@author: Roland Kaminski
"""

import os
import random
import stat
from collections.abc import MutableSequence
from typing import Any, no_type_check


def mkdir_p(path: str) -> None:
    """
    Simulates "mkdir -p" functionality.

    Keyword arguments:
    path -- a string holding the path to create
    """
    if not os.path.exists(path):
        os.makedirs(path)


def xmlTime(strRep: str) -> int:
    """
    Converts [[h:]m:]s time format to integer value in seconds.
    """
    timeout = strRep.split(":")
    seconds = int(timeout[-1])
    minutes = hours = 0
    if len(timeout) > 1:
        minutes = int(timeout[-2])
    if len(timeout) > 2:
        hours = int(timeout[-3])
    return seconds + minutes * 60 + hours * 60 * 60


def pbsTime(intRep: int) -> str:
    s = intRep % 60
    intRep //= 60
    m = intRep % 60
    intRep //= 60
    h = intRep
    return "{0:02}:{1:02}:{2:02}".format(h, m, s)


def medianSorted(sequence: MutableSequence[Any]) -> Any:
    """
    Returns the median of a sorted sequence.
    (Returns 0 if the sequence is empty.)
    """
    if len(sequence) == 0:
        return 0
    middle = len(sequence) // 2
    value = sequence[middle]
    if 2 * middle == len(sequence):
        value = (value + sequence[middle - 1]) / 2.0
    return value


def median(sequence: MutableSequence[Any]) -> Any:
    """
    Returns the median of an unordered sequence.
    (Returns 0 if the sequence is empty.)
    """

    def partition(sequence: MutableSequence[Any], left: int, right: int) -> int:
        """
        Selects a pivot element and moves all smaller(bigger)
        elements to the left(right).
        """
        pivotIndex = random.randint(left, right)
        pivotValue = sequence[pivotIndex]
        sequence[pivotIndex], sequence[right] = sequence[right], sequence[pivotIndex]
        storeIndex = left
        for i in range(left, right):
            if sequence[i] < pivotValue:
                sequence[storeIndex], sequence[i] = sequence[i], sequence[storeIndex]
                storeIndex = storeIndex + 1
        sequence[right], sequence[storeIndex] = sequence[storeIndex], sequence[right]
        return storeIndex

    def select(sequence: MutableSequence[Any], left: int, right: int, k: int) -> Any:
        """
        Selects the k-th element as in the ordered sequence.
        """
        pivotIndex = partition(sequence, left, right)
        if k == pivotIndex:
            return sequence[k]
        elif k < pivotIndex:
            return select(sequence, left, pivotIndex - 1, k)
        else:
            return select(sequence, pivotIndex + 1, right, k)

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


def setExecutable(filename: str) -> None:
    filestat = os.stat(filename)
    os.chmod(filename, filestat[0] | stat.S_IXUSR)


# make the benchmark tool forward compatible with python 3
def cmp(a: Any, b: Any) -> int:
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0


# mypy doesnt like python2 __cmp__
class Sortable:
    @no_type_check
    def __le__(self, other: "Sortable") -> bool:
        return self.__cmp__(other) <= 0

    @no_type_check
    def __ge__(self, other: "Sortable") -> bool:
        return self.__cmp__(other) >= 0

    @no_type_check
    def __lt__(self, other: "Sortable") -> bool:
        return self.__cmp__(other) < 0

    @no_type_check
    def __gt__(self, other: "Sortable") -> bool:
        return self.__cmp__(other) > 0

    @no_type_check
    def __eq__(self, other: "Sortable") -> bool:
        return self.__cmp__(other) == 0
