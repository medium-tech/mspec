import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


LINGO_DIR = Path(__file__).resolve().parents[1]
PY_INTERPRETER_SRC_DIR = LINGO_DIR / 'interpreters' / 'py' / 'src'


@dataclass(frozen=True)
class AdapterResult:
    exit_code: int
    stdout: str
    stderr: str


# adapters #

def run_exe_with_python(script_path: Path, params: dict, **kwargs) -> AdapterResult:
    if params:
        raise ValueError('exe contract params are not supported yet by the Python beta CLI')

    verbose_flag = ['-v'] if kwargs.get('verbose', False) else []

    cmd = [sys.executable, '-m', 'lingolib'] + verbose_flag + ['exe', str(script_path)]
    
    result = subprocess.run(
        cmd,
        cwd=PY_INTERPRETER_SRC_DIR,
        capture_output=True,
        text=True,
    )

    return AdapterResult(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
