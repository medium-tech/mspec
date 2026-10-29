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
	- [add a new spec](#add-a-new-spec)

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
./lingo.sh server ../../shared/scripts/app/hello-backend.yaml
./lingo.sh client ../../shared/scripts/app/hello-backend.yaml \
  --op my_app.say_hello --json '{"name": "Ada"}'
./lingo.sh client ../../shared/scripts/app/hello-backend.yaml \
  --op my_app.say_hello --params name=Ada
```

`build` is intentionally unsupported for Python wrappers (source execution only).

The app `server` command serves operations at `POST /<module>/<op>` and currently
requires the `uwsgi` executable on `PATH`. The server runs in the foreground.
The `client` command sends a JSON object as the request body and pretty-prints
the JSON response.
Use either `--json` for a complete JSON object or `--params name=value [...]`
to supply individual values. Individual values are converted using the op's
declared `bool`, `int`, `float`, or `str` parameter types. Add `-i` to prompt
for required values not supplied with `--params`; fields marked `secure: true`
are prompted with `getpass` so input is not echoed. By default, response fields
marked `secure: true` are replaced with `"REDACTED"` before display. Pass
`--show` to reveal those fields. `--show` is an explicit opt-in and should only
be used when revealing sensitive values is appropriate.

The server also serves the original app spec file (the one passed to `server`)
as YAML at `GET /lingo/spec` (`Content-Type: application/yaml; charset=utf-8`).
Fetch and print it with `client <path> --lingo spec`. The `lingo` module name is
reserved for these server routes: the server raises on start if an app spec
defines a module named `lingo`.

Server and client configuration is provided through environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `LINGO_SERVER_HOST` | `127.0.0.1` | Server bind address |
| `LINGO_SERVER_PORT` | `8000` | Server bind port |
| `LINGO_SERVER_PROCESSES` | `1` | Number of uWSGI worker processes |
| `LINGO_SERVER_MAX_BODY_BYTES` | `1048576` | Maximum accepted JSON request size |
| `LINGO_SERVER_LOG_MAX_SIZE` | `104857600` | uWSGI log rotation size in bytes |
| `LINGO_SERVER_DB_FILE` | `lingo.db` | SQLite file used to store app `models` |
| `LINGO_CLIENT_HOST` | `http://<host>:<port>` | Server base URL for the client |

#### models (CRUD + list)

Each entry under an app module's `models` gets a SQLite table (`<module>_<model>`,
created on server start; tables are never migrated, a mismatched existing table is
an error). SQLite generates each model's `id` using
`INTEGER PRIMARY KEY AUTOINCREMENT`; IDs are serialized as strings in API
responses and Lingo objects.
Models may only have scalar fields (`str`, `int`, `float`, `bool`) and cannot
define `id`, which is reserved for the generated primary key. A model cannot
share a name with an op in the same module. Request bodies are validated strictly
with no type conversion (e.g. `int` to `float`); field `default`s apply on create
and PUT.

| Request | Action | Success |
| --- | --- | --- |
| `POST /<module>/<model>` | create | `201` with the full object |
| `GET /<module>/<model>?offset=&limit=` | list (`{"items": [...], "total": n}`) | `200` |
| `GET /<module>/<model>/<id>` | read | `200` |
| `PUT /<module>/<model>/<id>` | replace (all fields) | `200` |
| `PATCH /<module>/<model>/<id>` | update a subset of fields | `200` |
| `DELETE /<module>/<model>/<id>` | delete, returns the deleted object | `200` |

Errors map to `400` (validation), `404` (unknown route or id), `405` and `500`.
Op results that are Lingo errors use the same mapping.

DB operations are available as lingo functions in app spec op functions as `db_create`, `db_read`, `db_list`,
`db_put`, `db_patch` and `db_delete`. See `my_app.create_sample` in `shared/scripts/app/hello-database.yaml` for an example. They return a `error` object for missing ids or invalid data.


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
python -m lingolib exe ../../shared/scripts/exe/hello-world.yaml
```

## development

### testing

See [Lingo Readme](../../README.md#tests)

### lingolib layout overview

The Python interpreter library lives in `./src/lingolib`:

- `api.py` - file/AST entrypoints for running and debugging spec files (`execute_file`, `display_file`, `debug_file`, ...)
- `cli.py` - cli wrapper for `api.py` (`exe`, `display`, `debug`, `server`, `client` commands)
- `symbols.py` - AST symbol definitions (`L_SYM_*`) for spec, expression, and display symbols
- `ast.py` - AST dataclasses (`LingoASTExeSpec`, `LingoASTGUISpec`, `LingoASTTextSpec`, etc.) and `lingo_ast_to_string(...)` for debugging
- `types.py` - shared value/type aliases and the accepted spec names (`app`, `data`, `exe`, `gui`, `lib`, `super`, `text`)
- `constants.py` - shared constants (text/heading formatting limits, fonts, etc.)
- `errors.py` - `LingoLibError` and subclasses
- `context.py` - `LingoContext` and runtime/parser sub-contexts (logging, tkinter state, parser file/line tracking)
- `parsing/` - parser entrypoints + expression/spec parsing + YAML line tracking
  - `state.py` - state of yaml parser, for determining yaml line numbers for lingo tracebacks (`YamlLocationLoader`, `get_yaml_line`)
  - `spec_lingo.py` - top-level `lingo` parsing, root validation (`SPEC_ROOT_RULES`, `validate_spec_root`), and spec dispatch (`create_spec_ast_from_dict`)
  - `spec_expression.py` - expression parsing (`create_expression_ast`), create `L_SYM_*` classes from `dict` objects extracted from yaml, plus shared helpers like `parse_define_symbol`
  - spec-specific AST builders:
    - `spec_exe.py`
    - `spec_text.py`
    - `spec_gui.py`
- `runtime/` - spec-level evaluation for `exe`, `text`, and `gui`
  - `eval_lingo.py` - top-level entrypoints used by `api.py` for evaluating specs: `evaluate_expression`, `evaluate_exe_spec`, `evaluate_gui_spec`, etc
  - `eval_expression.py` - lowest level evaluator
    - `evaluate_expression` - Used to execute lingo expressions, `eval_exe.py` uses this for the `main` expression, `eval_display.py` uses it for dynamic ui elements
    - `unwrap_value` - the `evaluate_expression` function may return a python primitive, `LingoValue`, or `L_SYM_value`. This function normalizes the output to a python primitive or `LingoLanguageError` if there was an error evaluating the expression
    - `unwrap_expression` - return the result of `unwrap_value` on the result of `evaluate_expression`
  - spec-specific AST evaluators:
    - `eval_exe.py` - builds on `eval_expression.py` for executing a full lingo `exe` spec with `evaluate_exe_spec`
    - `eval_display.py` - evaluate a `text` or `gui` spec by opening a `tkinter` window
      - `eval_server.py` / `eval_client.py` - serve app-spec ops through uWSGI and invoke them using urllib
  - `registry.py` - `init_registry` / `add_ops_to_registry` for making `gui` spec `ops` callable at runtime
  - `shared.py` - shared runtime helpers (`raise_runtime_error`)

### add a new symbol

This section is for adding a new expression symbol (for example `mul`, `lower`, etc.).

1. Add the symbol type in `./src/lingolib/symbols.py`
	- Create `L_SYM_<name>(NamedTuple)`.
	- Keep field order consistent:
	  - `L_SRC: str`
	  - symbol-specific fields
	  - `L_FILE: str = ''`
	  - `L_LINE: int = -1`
	- Add `L_SYM_NAME` and `L_SYM_TYPE` properties.
	- Use `L_SYM_TYPE = 'expression'` for runtime-only symbols and `L_SYM_TYPE = 'display'` for symbols rendered by `text` and `gui` specs.
	- Add the symbol to `ExpressionSymbols`.

1. Add parser support in `./src/lingolib/parsing/spec_expression.py`
	- Route by key in `create_expression_ast(...)`.
	- Follow the existing pattern: either parse inline in that function or add a small helper alongside helpers like `parse_define_symbol(...)`.
	- Return an instance of your new `L_SYM_<name>` with `L_FILE` and `L_LINE` populated from `ctx.parser.file` and `get_yaml_line(...)`.

1. Add executor support in `./src/lingolib/runtime/eval_expression.py`
	- Implement `L_EXPR_<name>(ctx, symbol)`.
	- Validate input and return `LingoLanguageError(...)` for language-level errors.
	- Register it in `EXPRESSION_HANDLERS` with key `<name>`.
	- If it is a display symbol, also add the renderer support in `./src/lingolib/runtime/eval_display.py` instead of `EXPRESSION_HANDLERS`.

1. Add tests
	- Prefer shared contract tests in `../../shared/tests/exe` + Python adapter tests in `../../test`.
	- Run: `python3 -m unittest lingo.test.test_exe_contract_py -v`.

### add a new spec

Specs are parsed at the top level in `./src/lingolib/parsing/spec_lingo.py` (`create_spec_ast_from_dict`), then routed through `./src/lingolib/api.py`.

Right now the implemented specs are `exe`, `text`, and `gui`. The type layer also reserves names like `app`, `lib`, `data`, and `super`, but those do not have full parser and runtime support in this interpreter yet.

1. Add AST dataclass in `./src/lingolib/ast.py`
	- Create `LingoAST<name>Spec` with the required symbol fields.
	- Include it in `LingoASTSpec` union.

1. Add spec parser module in `./src/lingolib/parsing`
	- Create a new module `spec_<name>.py`
	- Implement `spec_<name>_ast_from_dict(ctx, lingo, data)`.
	- Parse required top-level symbols and return your new AST dataclass.

1. Wire spec dispatch in `./src/lingolib/parsing/spec_lingo.py`
	- Add root validation rules to `SPEC_ROOT_RULES`.
	- Import your new parser.
	- Extend the `match lingo.spec:` block in `create_spec_ast_from_dict(...)` to call `spec_<name>_ast_from_dict(...)`.

1. Add execution path in `./src/lingolib/api.py`
	- Add or reuse the correct entrypoint for the new AST in `execute_ast(...)`, `execute_client_ast(...)`, `display_ast(...)`, or `serve_ast(...)`.
	- If the spec needs a new runtime evaluator, add it under `./src/lingolib/runtime/` and wire it into `api.py`.

1. Add CLI behavior as needed in `./src/lingolib/cli.py`
	- Add a new command only if the spec needs a new top-level CLI action.
	- The current CLI already supports `exe`, `display`, and `debug`.
	- `display` is the path used by the existing `text` and `gui` specs.

1. Add tests
	- Add parser/execution tests for the new spec.
	- Add/extend shared contracts if the spec has cross-interpreter behavior.
