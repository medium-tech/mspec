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

### 3. Shared fixtures and expected outputs

All interpreters consume the same files from `lingo/shared/fixtures` and
`lingo/shared/expected`.

Rules:

- every parity bug adds a shared fixture
- every new spec feature adds parser and executor fixtures
- avoid interpreter-specific golden files unless unavoidable

---

## Python Reorganization Plan (Before `lib` / `app` / `ui`)

Goal: keep existing `exe` behavior stable while restructuring internals so
`lib`, `app`, and `ui` can be added without large rewrites.

### 1) 🟢 Replace dynamic expression dispatch with explicit registry

Current pattern (works, but gets fragile as symbol count grows):

```python
# expressions.py (current)
expr_callable = globals()[f'L_EXPR_{expr.L_SYM_NAME}']
```

Target pattern (single source of truth):

```python
# runtime/registry.py (target)
EXPR_HANDLERS = {
	'value': L_EXPR_value,
	'error': L_EXPR_error,
	'handle': L_EXPR_handle,
	'eq': L_EXPR_eq,
	'int': L_EXPR_int,
	'add': L_EXPR_add,
	'str': L_EXPR_str,
	'concat': L_EXPR_concat,
	'join': L_EXPR_join,
}

def get_handler(sym_name: str):
	try:
		return EXPR_HANDLERS[sym_name]
	except KeyError:
		raise LingoLibError(f'unsupported expression symbol: {sym_name!r}')
```

```python
# runtime/execute.py (target)
def execute_expression(ctx, expr):
	if isinstance(expr, LingoLanguageError):
		return expr
	if isinstance(expr, (bool, int, float, str, LingoValue)):
		return expr

	handler = get_handler(expr.L_SYM_NAME)
	return handler(ctx, expr)
```

Why this helps:

- no hidden dependency on global names
- easier to test unsupported symbols
- safer refactors when splitting files

### 2) 🟢 Split expression parsing into small parser modules

Current pattern (single long chain):

```python
# parsing.py (current)
def create_expression_ast_from_dict(ctx, data, L_SRC):
	if keys == {'handle'}:
		...
	elif 'error' in keys:
		...
	elif keys == {'type', 'value'}:
		...
	elif keys == {'eq'}:
		...
	elif 'int' in keys:
		...
	elif keys == {'add'}:
		...
	elif keys == {'str'}:
		...
	elif keys == {'concat'}:
		...
	elif keys == {'join'}:
		...
	else:
		raise LingoSyntaxError(...)
```

Target pattern (router + focused parser funcs):

```python
# parsing/expr_core.py (target)
EXPR_PARSERS = {
	'eq': parse_expr_eq,
	'int': parse_expr_int,
	'add': parse_expr_add,
	'str': parse_expr_str,
	'concat': parse_expr_concat,
	'join': parse_expr_join,
	'handle': parse_expr_handle,
	'error': parse_expr_error,
	'value': parse_expr_value,
}

def parse_expression_dict(ctx, data, src):
	sym_name = detect_symbol_name(data)
	parser = EXPR_PARSERS.get(sym_name)
	if parser is None:
		raise LingoSyntaxError(f'Unknown symbol: {sym_name}')
	return parser(ctx, data, src)
```

Why this helps:

- adding `list`, `struct`, `get`, `validate`, `call` is localized
- file size and cognitive load stay manageable

### 3) Introduce centralized type/value normalization

Current pattern (validation/coercion spread across parsing + executors):

```python
# parsing.py (current)
if data['type'] not in LingoPrimitiveTypeNames:
	raise LingoSyntaxError(...)

# expressions.py (current)
def unwrap_value(...):
	...
```

Target pattern (one normalizer used everywhere):

```python
# runtime/types_normalize.py (target)
def normalize_typed_value(expected_type, raw_value, path, mode):
	"""
	mode: 'strict' | 'permissive'
	return: normalized primitive/list/struct or LingoLanguageError
	"""
	...
```

Examples this must handle consistently:

```yaml
# allowed in strict mode
type: int
value: '42'

# rejected in strict mode (avoid bool->int bleed)
type: int
value: true
```

Why this helps:

- same coercion behavior for `int`, `validate`, models, and state updates
- prevents drift across symbol implementations

### 4) 🟢 Add explicit spec root contracts (even before execution support)

Current pattern (`exe` works, other roots not contract-validated yet):

```python
# api.py/parsing.py (current)
if isinstance(lingo_ast, LingoASTExeSpec):
	return execute_exe_spec(...)
```

Target pattern (root validation by spec name):

```python
# parsing/envelope.py (target)
SPEC_ROOT_RULES = {
	'exe': {'required': {'lingo', 'main'}, 'optional': {'meta', 'import'}},
	'lib': {'required': {'lingo', 'modules'}, 'optional': {'meta'}},
	'app': {'required': {'lingo', 'modules'}, 'optional': {'meta', 'import'}},
	'ui':  {'required': {'lingo', 'state', 'ops', 'output'}, 'optional': {'meta', 'backend', 'import'}},
}

def validate_spec_root(spec_name, doc):
	...
```

Why this helps:

- non-`exe` files can fail early with clear messages
- future runtime work starts from stable schema assumptions

### 5) Add resolver layer for dotted names and imports

Current pattern: no dedicated resolver abstraction; resolution logic will
otherwise become scattered.

Target pattern:

```python
# runtime/resolver.py (target)
class Resolver:
	def __init__(self, local_scope, imported_modules, builtins):
		self.local_scope = local_scope
		self.imported_modules = imported_modules
		self.builtins = builtins

	def resolve(self, dotted_ref: str):
		# precedence: local -> imports -> builtins
		...
```

Why this helps:

- one place for collision policy and namespace precedence
- shared behavior for `call`, `get`, `validate against`, model refs, and widgets

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
	types_normalize.py
	eval_exe.py
	eval_lib.py
	eval_app.py
	eval_ui.py
```

### Migration Strategy

1. Move code with no behavior changes first.
2. Add registry, keep old executor names so tests stay green.
3. Split parser into modules while preserving current AST output.
4. Add root validators for `lib` / `app` / `ui` (parse-only).
5. Add resolver abstraction before implementing `import`/`call` semantics.
6. Run `python -m unittest lingo.test.test_exe_contract_py -v` after each step.

---

## Milestones

### M1 - `exe` hello world parity

* 🟢 add YAML parser dependency in each interpreter package
* 🟢 implement `parse_file` and minimal `exe` dispatch in all five languages
* 🟢 implement standardized CLI:
    * 🟢 `lingo --help`
    * 🟢 `lingo exe <path>`
* 🟢 execute `lingo/shared/scripts/exe/hello-world.yaml` in all languages

### M2 - `lib` support for `exe`

* 🔴 add `lib` spec folder under `lingo/specs/lib`
* 🔴 implement import resolution from `exe` into `lib`
* 🔴 add shared fixtures for successful and failing imports

### M3 - framework/runtime split

* 🔴 Python `app` runner using beta naming
* 🔴 Go `app` runner using beta naming
* 🔴 Python `page` runtime
* 🔴 JavaScript `page` runtime
* 🔴 rich-text subset support in page runtimes

---

## Priority Backlog

* 🟢 P0 create `lingo/shared/` with scripts, fixtures, expected outputs
* 🟡 P0 implement YAML parse pipeline and envelope validation in all languages
* 🟡 P0 implement common CLI help/usage behavior in all languages
* 🔴 P1 define and freeze public `api` module/function names per interpreter
* 🔴 P1 add cross-language contract tests for help, exe success/failure, exit codes
* 🔴 P1 add native parser+executor tests in each interpreter package
* 🔴 P2 add `lib` import conformance fixtures and tests
* 🔴 P2 map alpha sample data from `src/mspec/data` to beta `lingo/specs` and `lingo/shared`
