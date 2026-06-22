# python lingo interpreter
This is the Python interpreter and library for the lingo language.

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
- log format: `:: INFO :: <msg>`

### manual run
must be in `./src` or have `lingolib` installed in your venv
```bash
cd src
python -m lingolib exe ../../../shared/scripts/exe/hello-world.yaml
```

## development

### add a new symbol

This interpreter converts python dicts (parsed from yaml and possibly json) to symbols for the lingo ast. These will be referred to as **source objects**. This section explains how to implement a new symbol to the interpter. A symbol comes from the **source object** and represents an element of the language, either the base features of the lingo script (`spec`), or a dynamic element such as a function or value (`expression`).

1. Create symbol's `NamedTuple` in `./linglib/symbols.py` - used to build the lingo ast
	* place it in the file in the same section as others in its function group - use comments for section headers
	* class name name uses format `L_SYM_<name>` - short for "lingo symbol <name>"
	* define fields in this order:
		* first property: `L_SRC: str`	- during parsing, will be populated w/ path from source structure (dict/yaml)
		* then all fields needed to parse source dict (created from yaml)
		* then 2 fields:
			* `L_FILE: str = ''`	- if parsed from a file, the abs path to it
			* `L_LINE: int = -1`	- if available, the line from the file (not be available if not from a yaml file)
	* `@property` methods
		* `L_SYM_NAME` - the same as the key name in yaml
		* `L_SYM_TYPE` - the type of symbol, current choices:
			* `spec` - root level fields defining the basic features of a spec
			* `expression` - anything that could be used to calculate something
	* add type to `ExpressionSymbols` - there is a line for each function group
1. Add parsing logic in `./linglib/parsing.py`
	* For `L_SYM_TYPE=spec`:
		* conversion from source object to `L_SYM_<name>` is done in an ast creation function. This process will vary for each new spec, but see existing ones for patterns:
			* `lingo` - global spec symbol parsed in `create_spec_ast_from_dict` function
			* `main` - specific to `exe` spec in `spec_exe_ast_from_dict`
	* For `L_SYM_TYPE=expression` the process is more mechanical than for `spec`s
		* add mapping from source object keys in `create_expression_ast_from_dict` to `L_SYM_<name>`
			* place it in the file in the same section as others in its function group - use comments for section headers
		* add expression logic in `./linglib/expressions.py`
			* place it in the file in the same section as others in its function group - use comments for section headers
			* function name uses format `L_EXPR_<name>` for "lingo expression <name>"
				* accepts `c`tx:LingoContext, symbol:symbols.L_SYM_<name>` arguments
				* perform argument checking
					* **return** `LingoLanguageError` if wrong types or other errors encountered
				* perform calculation and return result