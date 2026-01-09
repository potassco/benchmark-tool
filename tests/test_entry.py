"""
Test for CLI entry points.
"""

import sys
from argparse import ArgumentParser
from io import StringIO
from typing import Callable
from unittest import TestCase, mock

from benchmarktool import entry_points

# pylint: disable=protected-access, too-many-statements


class TestParser(TestCase):
    """
    Test cases for the main entry point.
    """

    def setUp(self):
        self.parser = entry_points.get_parser()

    def test_get_parser(self):
        """
        Test get parser method.
        """
        self.assertIsInstance(self.parser, ArgumentParser)
        for subcmd in [
            "conv",
            "eval",
            "gen",
            "run-dist",
            "verify",
        ]:
            self.assertIn(subcmd, self.parser._subparsers._actions[2].choices.keys())

    def test_conv(self):
        """
        Test conv subcommand.
        """
        # defaults
        args = self.parser.parse_args(["conv"])
        self.assertEqual(args.command, "conv")
        self.assertIsNone(args.resultfile)
        self.assertEqual(args.output, "out.xlsx")
        self.assertSetEqual(args.projects, set())
        self.assertEqual(args.measures, {"time": "t", "timeout": "to"})
        self.assertFalse(args.export)
        self.assertIsNone(args.jupyter_notebook)
        self.assertIsInstance(args.func, Callable)

        # resultfile
        args = self.parser.parse_args(["conv", "res.xml"])
        self.assertEqual(args.resultfile, "res.xml")
        # output
        args = self.parser.parse_args(["conv", "-o", "test.xlsx"])
        self.assertEqual(args.output, "test.xlsx")

        # projects
        args = self.parser.parse_args(["conv", "-p", "p1,p2"])
        self.assertEqual(args.projects, {"p1", "p2"})

        # measures
        args = self.parser.parse_args(["conv", "-m", "all"])
        self.assertEqual(args.measures, {})
        args = self.parser.parse_args(["conv", "-m", "test:to,other"])
        self.assertEqual(args.measures, {"test": "to", "other": None})
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            self.parser.parse_args(["conv", "-m", ":to"])

        # export
        args = self.parser.parse_args(["conv", "-e", "rs.xml"])
        self.assertTrue(args.export)

        # jupyter notebook
        args = self.parser.parse_args(["conv", "-j", "notebook.ipynb"])
        self.assertEqual(args.jupyter_notebook, "notebook.ipynb")

        # run function
        result_mock = mock.MagicMock()
        with (
            mock.patch("benchmarktool.entry_points.ResParser.parse", return_value=result_mock) as parse_mock,
            mock.patch("benchmarktool.entry_points.open"),
            mock.patch("benchmarktool.entry_points.gen_ipynb") as gen_mock,
        ):
            result_mock.gen_spreadsheet.return_value = None

            args = self.parser.parse_args(["conv"])
            args.func(args)
            parse_mock.assert_called_once_with(sys.stdin)
            result_mock.gen_spreadsheet.assert_called_once_with(
                "out.xlsx", set(), {"time": "t", "timeout": "to"}, False, 300
            )
            gen_mock.assert_not_called()

            parse_mock.reset_mock()
            result_mock.gen_spreadsheet.reset_mock()
            args = self.parser.parse_args(["conv", "-e"])
            args.func(args)
            result_mock.gen_spreadsheet.assert_called_once_with(
                "out.xlsx", set(), {"time": "t", "timeout": "to"}, True, 300
            )
            gen_mock.assert_not_called()

            parse_mock.reset_mock()
            result_mock.gen_spreadsheet.reset_mock()
            args = self.parser.parse_args(
                [
                    "conv",
                    "res.xml",
                    "-o",
                    "test.xlsx",
                    "-p",
                    "p1,p2",
                    "-m",
                    "all",
                    "-j",
                    "notebook.ipynb",
                    "--max-col-width=50",
                ]
            )
            args.func(args)
            parse_mock.assert_called_once()
            result_mock.gen_spreadsheet.assert_called_once_with("test.xlsx", {"p1", "p2"}, {}, True, 50)
            gen_mock.assert_not_called()

            ex_file = mock.Mock()
            result_mock.gen_spreadsheet.return_value = ex_file
            args.func(args)
            gen_mock.assert_called_once_with(ex_file, "notebook.ipynb")

    def test_eval(self):
        """
        Test eval subcommand.
        """
        # defaults
        args = self.parser.parse_args(["eval", "rs.xml"])
        self.assertEqual(args.command, "eval")
        self.assertEqual(args.runscript, "rs.xml")
        self.assertEqual(args.par_x, 2)
        self.assertIsInstance(args.func, Callable)

        # par-x
        args = self.parser.parse_args(["eval", "rs.xml", "--par-x", "5"])
        self.assertEqual(args.par_x, 5)

        # run function
        run_mock = mock.MagicMock()
        with (mock.patch("benchmarktool.entry_points.RunParser.parse", return_value=run_mock) as parse_mock,):
            args = self.parser.parse_args(["eval", "rs.xml", "--par-x", "3"])
            args.func(args)
            parse_mock.assert_called_once_with("rs.xml")
            run_mock.eval_results.assert_called_once_with(sys.stdout, 3)

    def test_gen(self):
        """
        Test gen subcommand.
        """
        # defaults
        args = self.parser.parse_args(["gen", "rs.xml"])
        self.assertEqual(args.command, "gen")
        self.assertEqual(args.runscript, "rs.xml")
        self.assertFalse(args.exclude)
        self.assertFalse(args.overwrite)
        self.assertIsInstance(args.func, Callable)

        # exclude
        args = self.parser.parse_args(["gen", "rs.xml", "-e"])
        self.assertTrue(args.exclude)

        # overwrite
        args = self.parser.parse_args(["gen", "rs.xml", "-o"])
        self.assertTrue(args.overwrite)

        # run function
        run_mock = mock.MagicMock()
        with (mock.patch("benchmarktool.entry_points.RunParser.parse", return_value=run_mock) as parse_mock,):
            args = self.parser.parse_args(["gen", "rs.xml", "-e", "-o"])
            args.func(args)
            parse_mock.assert_called_once_with("rs.xml")
            run_mock.gen_scripts.assert_called_once_with(True, True)
