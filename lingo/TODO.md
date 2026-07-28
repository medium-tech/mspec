# Lingo TODO

### status colors

|not started|in progress|working but no test coverage|finished with test coverage|not planned|
|--|--|--|--| --|
|🔴|🟡|🟠|🟢|n/a|

## outline of python module

```text
lingo/interpreters/py/src/lingolib/
  api.py
  cli.py
  context.py
  errors.py
  types.py
  parsing/
	__init__.py
	envelope.py
	symbols.py
	expr_core.py
	expr_numeric.py
	expr_text.py
	expr_data.py
	spec_exe.py
	spec_lib.py
	spec_app.py
	spec_ui.py
  runtime/
	__init__.py
	execute.py
	expressions.py
	resolver.py	(for imports)
	eval_exe.py
	eval_lib.py
	eval_app.py
	eval_ui.py
```

* 🟡 initial interpreter implementation (update hardcoded `str` functions)
	* 🟡 py
		* 🟢 verbose logging
		* 🟡 exe
			* 🟢 hello-world.yaml
			* 🟢 hello-str.yaml
			* 🟢 hello-int.yaml
			* 🟢 hello-error.yaml
			* 🟢 hello-unhandled-error.yaml
			* 🔴 hello-flow-control.yaml
			* 🔴 hello-params.yaml
			* 🔴 hello-list.yaml
			* 🔴 hello-struct.yaml
			* 🔴 hello-validate.yaml
			* 🔴 hello-import.yaml
		* 🔴 app
			* 🔴 hello-app.yaml
			* 🔴 hello-backend.yaml
		* 🔴 ui
			* 🔴 hello-ui.yaml
			* 🔴 hello-frontend.yaml
			* 🔴 hello-inputs.yaml
		* 🔴 lib
			* 🔴 imports
		* 🔴 text
			* 🔴 hello-text.yaml
			* 🔴 text-formatting.yaml
		* 🔴 super
			* 🔴 hello-super.yaml
		* 🔴 data
			* 🔴 hello-data.yaml
			* 🔴 hello-anonymous-data.yaml
	* 🔴 js
	* 🔴 go
	* 🔴 hs
	* 🔴 c

## Goal

Build each interpreter as both:

- an embeddable library for host-language usage
- a public CLI for running Lingo scripts

---

## Public API Plan

Every interpreter exposes equivalent high-level API functions:

- `parse_file(path)`
- `parse_text(text, format)`
- `execute_exe(document)`
- `execute_file(path)`
- `render_help()`

For future specs:

- `run_app(document)` (py, go)
- `render_page(document)` (py, js)
- `render_rich_text(document)` (py, js)
- `load_lib(document_or_path)` (all)

API design rules:

- typed return or typed error (no silent failures)
- stable public functions under `api` namespace/module
- parser and evaluator internals live under `internal`

---

## Standardized CLI Plan

Required baseline behavior for each interpreter binary (`lingo` placeholder):

- `lingo --help`
- `lingo exe <path>`

Exit behavior:

- `0`: successful execution
- non-zero: parse/validation/runtime/usage errors

Help menu minimum sections:

- usage line
- supported commands
- supported specs for that implementation
- examples for `exe`

CLI implementation rule:

- avoid heavy parser frameworks for now (no `argparse` dependency and no
    equivalent large CLI framework in other languages)
- implement small, explicit argument parsing for cross-language parity

---

## Testing Regime (Next Level)

### 1. Cross-language CLI contract tests (Python harness)

`lingo/test/` verifies standardized behavior across all interpreters:

- `--help` output shape
- `exe <path>` success path
- stderr and exit code on parse/runtime errors
- unsupported-command behavior

### 2. Per-language internal tests

Each interpreter validates parser/evaluator internals natively:

- parser unit tests
- executor unit tests
- `lib` import resolution tests
