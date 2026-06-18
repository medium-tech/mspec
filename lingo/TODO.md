# Lingo TODO

## Goal

Build each interpreter as both:

- an embeddable library for host-language usage
- a public CLI for running Lingo scripts

Design around beta spec families:

- `exe`
- `app`
- `page`
- `rich-text`
- `lib`

### status colors

|not started|in progress|finished|
|--|--|--|
|🔴|🟡|🟢|

---

## Scope Matrix

Planned implementation scope by interpreter:

| Language | `exe` parse+execute | `lib` import | `app` runtime | `page` runtime | `rich-text` runtime |
|---|---|---|---|---|---|
| Python | 🟡 | 🔴 | 🔴 | 🔴 | 🔴 |
| JavaScript | 🟡 | 🔴 | n/a | 🔴 | 🔴 |
| Go | 🟡 | 🔴 | 🔴 | n/a | n/a |
| Haskell | 🟡* | 🔴 | n/a | n/a | n/a |
| C | 🟡 | 🔴 | n/a | n/a | n/a |

*Haskell requires `cabal` (install via [ghcup](https://www.haskell.org/ghcup/)); test skips when absent.

Notes:

- all five languages must support `exe` + `lib`
- `app` is Python and Go only
- `page` and `rich-text` are Python and JavaScript only

---

## Target Project Layout

Add a shared cross-language assets folder for built-in scripts and test data.

```text
lingo/
├── README.md
├── TODO.md
├── interpreters/
│   ├── c/
│   ├── go/
│   ├── hs/
│   ├── js/
│   └── py/
├── specs/
│   ├── exe/
│   ├── app/
│   ├── page/
│   ├── rich-text/
│   └── lib/
├── shared/
│   ├── scripts/
│   │   ├── exe/
│   │   ├── lib/
│   │   ├── app/
│   │   ├── page/
│   │   └── rich-text/
│   ├── fixtures/
│   │   ├── cli/
│   │   ├── parser/
│   │   └── executor/
│   └── expected/
│       ├── stdout/
│       ├── stderr/
│       └── exit-codes/
└── test/
```

`shared/` is the common source for built-in examples and conformance data used
by every interpreter test suite.

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

## Milestones

### M1 - `exe` hello world parity

* 🟢 add YAML parser dependency in each interpreter package
* 🟡 implement `parse_file` and minimal `exe` dispatch in all five languages
* 🟡 implement standardized CLI:
    * 🟡 `lingo --help`
    * 🟡 `lingo exe <path>`
* 🟡 execute `lingo/shared/scripts/exe/hello-world.yaml` in all languages
    * 🟢 Python, JavaScript, Go, C passing
    * 🟡 Haskell — code written; requires `cabal` to build (install via ghcup)

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
