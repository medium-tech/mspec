# python bootstrap package

## setup

- macOS: install Python 3 with Homebrew: `brew install python`
- Windows: install Python 3 from https://www.python.org/downloads/ or `winget install Python.Python.3`
- Linux: install Python 3 with your package manager, for example `sudo apt install python3`

### venv setup

create and activate a virtual environment (recommended), then install editable for dev testing:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## run

### with standard cli

```bash
./lingo.sh --help
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

wrapper binary overrides:

```bash
LINGO_PY_BIN=/absolute/path/to/python ./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

global fallback is also supported: `LINGO_BIN`.

### manual run
must be in `./src` or have `lingolib` installed in your venv
```bash
python -m lingolib exe ../../../shared/scripts/exe/hello-world.yaml
```
