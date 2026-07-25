# python lingo interpreter
This is the Python interpreter and library for the lingo language.

## table of contents

- [setup](#setup)
	- [venv setup](#venv-setup)
- [run](#run)
	- [run with standard cli](#run-with-standard-cli)
	- [manual run](#manual-run)
- [development](#development)
	- [testing](#testing)
	- [lingolib layout overview](#lingolib-layout-overview)
	- [add a new symbol](#add-a-new-symbol)
	- [add a new spec](#add-a-new-spec-appuilib)

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

### run with standard cli

```bash
./lingo.sh --help
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
./lingo.sh -v exe ../../shared/scripts/exe/hello-world.yaml
```

`build` is intentionally unsupported for Python wrappers (source execution only).

wrapper binary overrides:

```bash
LINGO_PY_BIN=/absolute/path/to/python ./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

global fallback is also supported: `LINGO_BIN`.

Verbose logging:

- use `--verbose` or `-v`
- log format: `:: DEBUG :: <msg>`

### manual run
must be in `./src` or have `lingolib` installed in your venv
```bash
cd src
python -m lingolib exe ../../../shared/scripts/exe/hello-world.yaml
```

## development

### testing
From root of repository:

	python -m unittest lingo.test.test_exe_contract_py
	python -m unittest lingo.test.test_spec_root_contracts_py

### lingolib layout overview

The Python interpreter library lives in `./src/lingolib` and is split by responsibility:

- `symbols.py`
  - AST symbol definitions (`L_SYM_*`) for both `spec` and `expression` symbols.
- `types.py`
  - shared value/type aliases and supported spec names (`app`, `exe`, `lib`, `ui`).
- `parsing/`
  - YAML line tracking + parser entrypoints + expression/spec parsing.
  - `state.py`: `YamlLocationLoader` and `get_yaml_line(...)`.
  - `envelope.py`: top-level `lingo` parsing and spec dispatch.
  - `spec_exe.py`: `exe` spec parser.
  - `expr_entry.py`, `expr_core.py`, `expr_numeric.py`, `expr_text.py`: expression parsing.
  - `ast.py`: AST dataclasses and `lingo_ast_to_string(...)`.
- `expressions.py`
  - expression execution functions (`L_EXPR_*`) and `EXPRESSION_HANDLERS` dispatch registry.
- `api.py`
  - parse file -> AST -> execute for supported specs.
- `cli.py`
  - CLI command handling and debug pathways.

### add a new symbol

This section is for adding a new **expression symbol** (for example `mul`, `lower`, etc.).

1. Add the symbol type in `./src/lingolib/symbols.py`
	- Create `L_SYM_<name>(NamedTuple)`.
	- Keep field order consistent:
	  - `L_SRC: str`
	  - symbol-specific fields
	  - `L_FILE: str = ''`
	  - `L_LINE: int = -1`
	- Add `L_SYM_NAME` and `L_SYM_TYPE` properties (`'expression'`).
	- Add the symbol to `ExpressionSymbols`.

1. Add parser support in `./src/lingolib/parsing`
	- Route by key in `expr_core.py` (`parse_expression_ast_from_dict`).
	- Implement parser helper in the appropriate file:
	  - numeric: `expr_numeric.py`
	  - text: `expr_text.py`
	  - or create a new `expr_<group>.py` module if needed.
	- Return an instance of your new `L_SYM_<name>` with `L_FILE` and `L_LINE` populated.

1. Add executor support in `./src/lingolib/expressions.py`
	- Implement `L_EXPR_<name>(ctx, symbol)`.
	- Validate input and return `LingoLanguageError(...)` for language-level errors.
	- Register it in `EXPRESSION_HANDLERS` with key `<name>`.

1. Add tests
	- Prefer shared contract tests in `../../shared/tests/exe` + Python adapter tests in `../../test`.
	- Run: `python -m unittest lingo.test.test_exe_contract_py -v`.

### add a new spec (app/ui/lib)

Specs are parsed at the top level, then executed by the API layer.

1. Add AST dataclass in `./src/lingolib/parsing/ast.py`
	- Create `LingoAST<name>Spec` with the required symbol fields.
	- Include it in `LingoASTSpec` union.

1. Add spec parser module in `./src/lingolib/parsing`
	- Create a new module `spec_<name>.py`
	- Implement `spec_<name>_ast_from_dict(ctx, lingo, data, create_expression_ast)`.
	- Parse required top-level symbols and return your new AST dataclass.

1. Wire spec dispatch in `./src/lingolib/parsing/envelope.py`
	- Import your new parser.
	- Extend `create_spec_ast_from_dict(...)`:
	  - `if lingo.spec == '<name>': return spec_<name>_ast_from_dict(...)`
	  - same pattern for `ui` or `lib`.

1. Add execution path in `./src/lingolib/api.py`
	- Add an executor function for the new AST (`execute_<name>_spec`, etc.).
	- Extend `execute_file(...)` type dispatch to call it.

1. Add CLI behavior as needed in `./src/lingolib/cli.py`
	- will need a new command `<name>`, for each spec, currently only `exe` is implemented

1. Add tests
	- Add parser/execution tests for the new spec.
	- Add/extend shared contracts if the spec has cross-interpreter behavior.
