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

    def test_get_int_time(self):
        """
        Test get_int_time function.
        """
        self.assertEqual(tools.get_int_time("10s"), 10)
        self.assertEqual(tools.get_int_time("10m 10s"), 610)
        self.assertEqual(tools.get_int_time("10h 10m 10s"), 36610)
        self.assertEqual(tools.get_int_time("1d 1h 1m 1s"), 90061)
        self.assertEqual(tools.get_int_time("320"), 320)
        self.assertEqual(tools.get_int_time("1d 3s"), 86403)

    def test_get_xml_time(self):
        """
        Test get_xml_time function.
        """
        self.assertEqual(tools.get_xml_time(10), "00d 00h 00m 10s")
        self.assertEqual(tools.get_xml_time(610), "00d 00h 10m 10s")
        self.assertEqual(tools.get_xml_time(36610), "00d 10h 10m 10s")
        self.assertEqual(tools.get_xml_time(90061), "01d 01h 01m 01s")
        self.assertEqual(tools.get_xml_time(86403), "01d 00h 00m 03s")

    def test_get_slurm_time(self):
        """
        Test get_slurm_time function.
        """
        self.assertEqual(tools.get_slurm_time(10), "00-00:00:10")
        self.assertEqual(tools.get_slurm_time(610), "00-00:10:10")
        self.assertEqual(tools.get_slurm_time(36610), "00-10:10:10")
        self.assertEqual(tools.get_slurm_time(90061), "01-01:01:01")
        self.assertEqual(tools.get_slurm_time(86403), "01-00:00:03")

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
