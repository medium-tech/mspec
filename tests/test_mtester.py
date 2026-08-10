import unittest

class TestMTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_can_import_mtester(self):
        import mtester
        self.assertIsNotNone(mtester)

    def _disabled_test_failure(self):
        self.assertEqual(1, 12)