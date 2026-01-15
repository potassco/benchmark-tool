"""
Test cases for ipynb file generation.
"""

import os
from unittest import TestCase

from benchmarktool.result.ipynb_gen import gen_ipynb


class TestIpynbGen(TestCase):
    """
    Test cases for ipynb gen.
    """

    def test_gen_ipynb(self):
        """
        Test gen_ipynb_gen function.
        """
        name = "./tests/ref/test"
        gen_ipynb("x.parquet", name)
        self.assertTrue(os.path.isfile(name + ".ipynb"))
        os.remove(name + ".ipynb")
