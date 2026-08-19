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

def _param_value_to_cli_str(value) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    else:
        return str(value)

def run_exe_with_python(script_path: Path, params: dict, **kwargs) -> AdapterResult:
    verbose_flag = ['-v'] if kwargs.get('verbose', False) else []

    param_args = []
    for field_name, value in params.items():
        flag = f'--{field_name.replace("_", "-")}'
        param_args.extend([flag, _param_value_to_cli_str(value)])

    cmd = [sys.executable, '-m', 'lingolib'] + verbose_flag + ['exe', str(script_path)] + param_args
    
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
