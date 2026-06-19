# lingo beta

This directory contains the beta rewrite bootstrap for Lingo across five
language interpreters: Python, JavaScript, Go, Haskell, and C.

The beta is organized around a shared spec model plus language-idiomatic
interpreter packages. Each interpreter should support:

- a library API for embedding
- a CLI for script execution

## beta specs

Beta naming and intent:

- `exe`: execute a `main` function and return a value
- `app`: backend and admin CLI definition (renamed from `generator`)
- `page`: UI spec that can talk to an `app` backend
- `rich-text`: subset of `page` for formatted text payloads
- `lib`: reusable function/module definitions importable by other scripts

## implementation scope by language

Current target scope:

- all interpreters (`py`, `js`, `go`, `hs`, `c`) parse and execute `exe`
- `exe` supports importing `lib`
- `py` and `go` implement `app`
- `py` and `js` implement `page`
- `rich-text` is implemented with the `page` stack (`py`, `js`)

## standardized cli contract

`lingo` below stands in for each language binary.

- `lingo --help`: print help menu
- `lingo exe <path>`: load, parse, execute, print result

Notes:

- keep CLI behavior standardized across languages
- avoid large CLI frameworks for now; use small manual parsing for parity

## standardized entrypoint contract (lingo.sh)

Each interpreter directory should expose the same wrapper entrypoint:

- `./lingo.sh --help`
- `./lingo.sh exe <path>`
- `./lingo.sh --verbose <command> [args]` (or `-v`)
- `./lingo.sh --run-mode <dev|built> <command> [args]` (or `-r`, for interpreters that support build/run modes)

Build command support:

- Python: no `build` command (runs source directly)
- JavaScript: no `build` command (runs source directly)
- Go: supports `./lingo.sh build` (and `exe` via `go run` or built binary)
- Haskell: supports `./lingo.sh build` (cabal build)
- C: supports `./lingo.sh build` (native compile)

Wrapper behavior requirements:

- normalize command names and usage text across languages
- print clear, language-specific toolchain prerequisites in `--help`
- fail with actionable next steps and point to interpreter README when build/run is unavailable on the current OS
- keep beta caveats explicit: not all build paths are expected to work on every OS/toolchain combination
- support wrapper troubleshooting logs with `--verbose` / `-v`
- verbose log format must be: `:: INFO :: <msg>`
- verbose logging should include: env var checks, selected binary/toolchain, selected run mode, and key build/run steps

Optional configuration knobs for wrappers:

- language-specific run mode: `LINGO_GO_RUN_MODE`, `LINGO_HS_RUN_MODE`, `LINGO_C_RUN_MODE` (`dev|built`)
- language-specific binary override: `LINGO_GO_BIN`, `LINGO_HS_BIN`, `LINGO_C_BIN`, `LINGO_PY_BIN`, `LINGO_JS_BIN`
- C compiler override: `LINGO_C_CC`
- C libyaml discovery override: `LINGO_C_LIBYAML_PREFIX=<prefix>`
- optional global fallbacks (for ad-hoc usage): `LINGO_RUN_MODE`, `LINGO_BIN`

Precedence order for wrapper configuration:

- command-line flag
- language-specific environment variable
- global fallback environment variable
- wrapper default

The goal is one muscle-memory interface for daily work while preserving
language-native build and execution details under each interpreter package.

## layout

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
├── shared/
│   ├── scripts/
│   │   └── exe/
│   │       └── hello-world.yaml
│   ├── fixtures/     # cross-language input/output test data
│   └── docs/         # spec-specific notes used by all interpreters
└── test/
```

The `shared/` directory is the cross-language source of truth for built-in
scripts and test data. Interpreter-specific tests should consume the same files.

## relation to alpha data

Alpha examples live in `src/mspec/data/`, including:

- `src/mspec/data/generator` (renamed to `app` in beta)
- `src/mspec/data/lingo/pages`
- `src/mspec/data/lingo/rich-text`
- `src/mspec/data/lingo/scripts` (mapped to `exe`/`lib` in beta naming)

Beta work should migrate selected examples into `lingo/specs/` and
`lingo/shared/` with the new naming.

## tests

From the repository root:

```bash
python -m unittest lingo.test.test_setup
python -m unittest lingo.test.test_hello_world
```

`test_setup.py` checks required toolchains. `test_hello_world.py` builds/runs
each interpreter and validates output.

Next iteration expands tests into:

- cross-language CLI contract tests in Python
- per-language internal unit tests in each interpreter package
- shared fixtures in `lingo/shared/fixtures`
