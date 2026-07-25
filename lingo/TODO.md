# Lingo TODO

## finish reviewing package refactor before merging
* 🟢 review and test hello world to package refactor
	* 🟢 py
	* 🟢 js
	* 🟢 go
	* 🟢 hs
	* 🟢 c
* 🟡 initial interpreter implementation (update hardcoded `str` functions)
	* 🟡 py
		* 🟢 verbose logging
		* 🟡 exe scripts
			* 🟢 hello-world.yaml
			* 🟢 hello-str.yaml
			* 🟢 hello-int.yaml
			* 🔴 hello-list.yaml
			* 🔴 hello-struct.yaml
			* 🟢 hello-error.yaml
			* 🟢 hello-unhandled-error.yaml
			* 🔴 hello-validate.yaml
			* 🔴 hello-import.yaml
		* 🔴 app scripts
			* 🔴 hello-app.yaml
			* 🔴 hello-backend.yaml
		* 🔴 ui scripts
			* 🔴 hello-ui.yaml
			* 🔴 hello-form.yaml
			* 🔴 hello-type-display.yaml
			* 🔴 hello-frontend.yaml
			* 🔴 hello-rich-text.yaml
	* 🔴 js
	* 🔴 go
	* 🔴 hs
	* 🔴 c

## Goal

Build each interpreter as both:

- an embeddable library for host-language usage
- a public CLI for running Lingo scripts

Design around beta spec families:

- `exe`
- `app`
- `page`
- `text`
- `lib`

### status colors

|not started|in progress|working but no test coverage|finished with test coverage|not planned|
|--|--|--|--| --|
|🔴|🟡|🟠|🟢|n/a|

---

## Scope Matrix

Planned implementation scope by interpreter:

| Language | `exe` parse+execute | `lib` import | `app` runtime | `page` runtime | `rich-text` runtime |
|---|---|---|---|---|---|
| Python | 🟡 | 🔴 | 🔴 | 🔴 | 🔴 |
| JavaScript | 🔴 | 🔴 | n/a | 🔴 | 🔴 |
| Go | 🔴 | 🔴 | 🔴 | n/a | n/a |
| Haskell | 🔴 | 🔴 | n/a | n/a | n/a |
| C | 🔴 | 🔴 | n/a | n/a | n/a |

---

## Parser Dependencies (YAML)

Each interpreter package should explicitly include a YAML parser dependency.

| Language | Dependency | Task |
|---|---|---|
| Python | `PyYAML` | ensure installed and pinned in package metadata |
| JavaScript | `yaml` | add to `dependencies` in `package.json` |
| Go | `gopkg.in/yaml.v3` | add module dependency in `go.mod` |
| Haskell | `yaml` | add to `build-depends` in `.cabal` |
| C | `libyaml` | add build/install notes and compile/link flags |

Parser contract for all languages:

- parse YAML file from disk
- validate minimal envelope (`lingo.spec`, `lingo.version`)
- dispatch by spec type (`exe`, `app`, `page`, `rich-text`, `lib`)
- return consistent parser errors with line/context when available

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

### Proposed Python Internal Layout

```text
lingo/interpreters/py/src/lingolib/
  api.py
  cli.py
  context.py
  errors.py
  types.py
  symbols.py
  parsing/
	__init__.py
	envelope.py
	expr_core.py
	expr_numeric.py
	expr_text.py
	expr_data.py      # list/struct/get/validate/call
	spec_exe.py
	spec_lib.py
	spec_app.py
	spec_ui.py
  runtime/
	__init__.py
	execute.py
	registry.py
	resolver.py
	eval_exe.py
	eval_lib.py
	eval_app.py
	eval_ui.py
```
