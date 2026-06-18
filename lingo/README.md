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
