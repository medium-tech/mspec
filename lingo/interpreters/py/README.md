# python bootstrap package

## setup

- macOS: install Python 3 with Homebrew: `brew install python`
- Windows: install Python 3 from https://www.python.org/downloads/ or `winget install Python.Python.3`
- Linux: install Python 3 with your package manager, for example `sudo apt install python3`

### venv setup

editable for dev testing
```bash
python -m pip install -e .
```

## run 

### with standard cli

```bash
./lingo.sh --help
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

### manual run

```bash
cd src
python -m lingolib exe ../../../shared/scripts/exe/hello-world.yaml
```
