"""
Tests for utility functions.
"""

import os
from unittest import TestCase, mock

from benchmarktool import tools


class TestTools(TestCase):
    """
    Test cases for tool functions.
    """

    def test_mkdir_p(self):
        """
        Test mkdir_p function.
        """
        with mock.patch("benchmarktool.tools.os.makedirs") as mkdir:
            tools.mkdir_p("path/to/create")
            mkdir.assert_called_once_with("path/to/create")
            mkdir.reset_mock()
            tools.mkdir_p("tests/ref")
            mkdir.assert_not_called()

    def test_xml_time(self):
        """
        Test xml_time function.
        """
        self.assertEqual(tools.xml_time("10"), 10)
        self.assertEqual(tools.xml_time("10:10"), 610)
        self.assertEqual(tools.xml_time("10:10:10"), 36610)

    def test_pbs_time(self):
        """
        Test pbs_time function.
        """
        self.assertEqual(tools.pbs_time(10), "00:00:10")
        self.assertEqual(tools.pbs_time(610), "00:10:10")
        self.assertEqual(tools.pbs_time(36610), "10:10:10")

    def test_set_executable(self):
        """
        Test set_executable function.
        """
        f = "./tests/ref/test.txt"
        open(f, "a", encoding="utf8").close()  # pylint: disable=consider-using-with
        with mock.patch("benchmarktool.tools.os.chmod") as chmod:
            tools.set_executable(f)
            chmod.assert_called_once()
        os.remove(f)
