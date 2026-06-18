import shutil
import sys
import unittest


class TestLanguageSetup(unittest.TestCase):

    def test_python_setup(self):
        self.assertIsNotNone(
            shutil.which(sys.executable),
            f'Python interpreter not found: {sys.executable}',
        )

    def test_javascript_setup(self):
        self.assertIsNotNone(
            shutil.which('node'),
            'Node.js (node) is required to build and run the JavaScript interpreter.',
        )

    def test_go_setup(self):
        self.assertIsNotNone(
            shutil.which('go'),
            'Go (go) is required to build and run the Go interpreter.',
        )

    def test_haskell_setup(self):
        self.assertIsNotNone(
            shutil.which('ghc'),
            'GHC (ghc) is required to build and run the Haskell interpreter.',
        )

    def test_haskell_cabal_setup(self):
        self.assertIsNotNone(
            shutil.which('cabal'),
            'cabal is required to build the Haskell interpreter (cabal >= 3.4); install via ghcup: https://www.haskell.org/ghcup/',
        )

    def test_c_setup(self):
        compiler = shutil.which('gcc') or shutil.which('cc')
        self.assertIsNotNone(
            compiler,
            'A C compiler (gcc or cc) is required to build and run the C interpreter.',
        )


if __name__ == '__main__':
    unittest.main()
