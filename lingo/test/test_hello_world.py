import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EXPECTED_OUTPUT = 'hello.world'
LINGO_SRC_DIR = Path(__file__).resolve().parents[1] / 'interpreters'
HELLO_WORLD_SCRIPT = Path(__file__).resolve().parents[1] / 'shared' / 'scripts' / 'exe' / 'hello-world.yaml'


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
        result = self._run_command(
            [sys.executable, '-m', 'lingolib', 'exe', str(HELLO_WORLD_SCRIPT)],
            script_dir / 'src',
        )
        self._assert_run_result(result)

    def test_javascript_hello_world(self):
        self._require_command('node', 'Node.js is required to run the JavaScript beta bootstrap.')

        script_dir = LINGO_SRC_DIR / 'js'
        install_result = self._run_command(['npm', 'install'], script_dir)
        self.assertEqual(install_result.returncode, 0, msg=install_result.stderr)
        result = self._run_command(
            ['node', 'bin/lingolib.js', 'exe', str(HELLO_WORLD_SCRIPT)],
            script_dir,
        )
        self._assert_run_result(result)

    def test_go_hello_world(self):
        self._require_command('go', 'Go is required to run the Go beta bootstrap.')

        script_dir = LINGO_SRC_DIR / 'go'
        with tempfile.TemporaryDirectory() as build_dir:
            binary_path = self._binary_path(build_dir, 'lingolib-go')
            build_result = self._run_command(
                ['go', 'build', '-o', str(binary_path), './cmd/lingolib'],
                script_dir,
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr or build_result.stdout)

            run_result = self._run_command(
                [str(binary_path), 'exe', str(HELLO_WORLD_SCRIPT)],
                script_dir,
            )
            self._assert_run_result(run_result)

    def test_haskell_hello_world(self):
        if not shutil.which('cabal'):
            self.skipTest('cabal not found; install via ghcup (https://www.haskell.org/ghcup/) to run Haskell tests')

        script_dir = LINGO_SRC_DIR / 'hs'

        build_result = self._run_command(['cabal', 'build'], script_dir)
        self.assertEqual(build_result.returncode, 0, msg=build_result.stderr or build_result.stdout)

        # locate the compiled binary (requires cabal >= 3.4)
        list_result = self._run_command(['cabal', 'list-bin', 'lingolib'], script_dir)
        self.assertEqual(list_result.returncode, 0, msg=list_result.stderr)
        binary_path = list_result.stdout.strip()

        run_result = self._run_command(
            [binary_path, 'exe', str(HELLO_WORLD_SCRIPT)],
            script_dir,
        )
        self._assert_run_result(run_result)

    def test_c_hello_world(self):
        compiler = shutil.which('gcc') or shutil.which('cc')
        self.assertIsNotNone(compiler, 'A C compiler (gcc or cc) is required to run the C beta bootstrap.')

        script_dir = LINGO_SRC_DIR / 'c'
        with tempfile.TemporaryDirectory() as build_dir:
            binary_path = self._binary_path(build_dir, 'lingolib-c')
            # requires libyaml: brew install libyaml  /  apt install libyaml-dev
            extra_flags = self._libyaml_flags()
            build_result = self._run_command(
                [compiler, '-Iinclude'] + extra_flags + ['-o', str(binary_path), 'app/main.c', 'src/lingolib.c', '-lyaml'],
                script_dir,
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr or build_result.stdout)

            run_result = self._run_command(
                [str(binary_path), 'exe', str(HELLO_WORLD_SCRIPT)],
                script_dir,
            )
            self._assert_run_result(run_result)

    @staticmethod
    def _libyaml_flags() -> list[str]:
        """Return extra compiler flags for libyaml when headers/libs are in a
        non-default prefix (e.g. Homebrew on Apple Silicon)."""
        import platform
        flags: list[str] = []
        candidates = ['/opt/homebrew', '/usr/local']
        for prefix in candidates:
            header = Path(prefix) / 'include' / 'yaml.h'
            lib = Path(prefix) / 'lib'
            if header.exists():
                flags += [f'-I{prefix}/include', f'-L{lib}']
                break
        return flags


if __name__ == '__main__':
    unittest.main()
