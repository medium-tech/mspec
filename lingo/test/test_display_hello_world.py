import os
import platform
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from mtester.context import MTesterConfig, MTesterContext
from mtester.ops import manual_flow


class TestLingoDisplayRunTimeHelloWorld(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_can_import_mtester(self):
        import mtester
        self.assertIsNotNone(mtester)

    def test_can_import_lingolib(self):
        import lingolib
        self.assertIsNotNone(lingolib)

        from lingolib.context import init_logger
        self.assertIsNotNone(init_logger)
