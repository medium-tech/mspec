import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EXPECTED_OUTPUT = 'hello.world'
LINGO_SRC_DIR = Path(__file__).resolve().parents[1] / 'interpreters'


class TestHelloWorldScripts(unittest.TestCase):

    def _binary_path(self, build_dir: str, name: str) -> Path:
        suffix = '.exe' if os.name == 'nt' else ''
        return Path(build_dir) / f'{name}{suffix}'

    def _require_command(self, command: str, message: str) -> None:
        self.assertIsNotNone(shutil.which(command), message)

    def _run_command(self, command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
        )

    def _assert_run_result(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(result.stdout.strip(), EXPECTED_OUTPUT, msg=result.stdout)
        self.assertEqual(result.stderr.strip(), '')

    def test_python_hello_world(self):
        script_dir = LINGO_SRC_DIR / 'py'
        result = self._run_command([sys.executable, 'main.py'], script_dir)
        self._assert_run_result(result)

    def test_javascript_hello_world(self):
        self._require_command('node', 'Node.js is required to run the JavaScript beta bootstrap.')

        script_dir = LINGO_SRC_DIR / 'js'
        result = self._run_command(['node', 'main.js'], script_dir)
        self._assert_run_result(result)

    def test_go_hello_world(self):
        self._require_command('go', 'Go is required to run the Go beta bootstrap.')

        script_dir = LINGO_SRC_DIR / 'go'
        with tempfile.TemporaryDirectory() as build_dir:
            binary_path = self._binary_path(build_dir, 'hello-world-go')
            build_result = self._run_command(
                ['go', 'build', '-o', str(binary_path), 'main.go'],
                script_dir,
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr or build_result.stdout)

            run_result = self._run_command([str(binary_path)], script_dir)
            self._assert_run_result(run_result)

    def test_haskell_hello_world(self):
        self._require_command('ghc', 'GHC is required to run the Haskell beta bootstrap.')

        script_dir = LINGO_SRC_DIR / 'hs'
        with tempfile.TemporaryDirectory() as build_dir:
            binary_path = self._binary_path(build_dir, 'hello-world-hs')
            build_result = self._run_command(
                [
                    'ghc',
                    '-outputdir',
                    build_dir,
                    '-o',
                    str(binary_path),
                    'main.hs',
                ],
                script_dir,
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr or build_result.stdout)

            run_result = self._run_command([str(binary_path)], script_dir)
            self._assert_run_result(run_result)

    def test_c_hello_world(self):
        compiler = shutil.which('gcc') or shutil.which('cc')
        self.assertIsNotNone(compiler, 'A C compiler (gcc or cc) is required to run the C beta bootstrap.')

        script_dir = LINGO_SRC_DIR / 'c'
        with tempfile.TemporaryDirectory() as build_dir:
            binary_path = self._binary_path(build_dir, 'hello-world-c')
            build_result = self._run_command(
                [compiler, '-o', str(binary_path), 'main.c'],
                script_dir,
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr or build_result.stdout)

            run_result = self._run_command([str(binary_path)], script_dir)
            self._assert_run_result(run_result)


if __name__ == '__main__':
    unittest.main()
