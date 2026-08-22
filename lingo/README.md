# lingo beta

This directory contains the beta rewrite bootstrap for Lingo across five
language interpreters: Python, JavaScript, Go, Haskell, and C.

Each interpreter should support:

- a library API for embedding
- a CLI for script execution

**Quick Links:**
* [CLI](#standardized-interpreter-entrypoint-lingosh)
* [Testing](#tests)
* [GUI Tests](#gui-tests)
* [Python Interpreter Readme](./interpreters/py/README.md)
* [Lingo Language Docs](./docs/LINGO_LANGUAGE.md)
* [Implementation Status](./docs/LINGO_IMPLEMENTATION.md)

## Development Status
The core of the language is being worked out in the [python interpreter](./interpreters/py/README.md). Once the design is finished and hello worlds work and are tested for all specs and runtimes, we'll use AI to brute force the functions in the [alpha language](../docs/LINGO_FUNCTIONS.md) to expand the vocabulary. Then the lingo language will be fully defined and AI will blast through each other languages' interpreter using python as a reference. Not all specs/runtimes are planned in every language, see [lingo implementation](./docs/LINGO_IMPLEMENTATION.md) for feature matrix.

## Language overview
This project creates a single scripting and markup rendering language that is able to build:
* server/client apps w/ crud db operations
* interactive user interfaces
* general purpose programs

The language's primary notation format will be a visual node editor. Proof of concept for an old alpha lingo version exists in [this repo](https://github.com/medium-tech/bl-mspec-dev). YAML will be the serialization layer and could also be used as a notation format.

It is designed to be **lightweight, cross-os and cross-language** w/ interpreters and renderers in multiple languages. Unlike the modern browser where your state is spread between 3 languages (html/js/css) a single `YAML` file defines everything. Layout, style, scripting, even the backend data model for CRUD operations and custom backend functions `ops`.

The language is intentionally simple in its syntax and features, very strict, but with a deep pythonic vocabulary. It is designed to make it difficult to write buggy or slow applications. See [language documentation](./docs/LINGO_LANGUAGE.md) for more.

## standardized interpreter entrypoint (lingo.sh)

Each interpreter directory should expose the same wrapper entrypoint:

- `./lingo.sh --help`
- `./lingo.sh exe <path>`
- `./lingo.sh display <path>`
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
- verbose log format must be: `:: DEBUG :: <msg>`
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
├── shared/
│   ├── scripts/
│   │   └── exe/
│   │       └── hello-str.yaml
│   │   └── ..other-specs.../
│   ├── tests/	# cross-language input/output test data
│   └── docs/   # spec-specific notes used by all interpreters
└── test/		# cross-language tests written in python	(uses mtester)
src/
├── mtester/	# tests for cross language guis w/ screenshotting, OCR and pixel evaluation
tests/
├── test_mtester.py	# tests for the mtester module
```


The `shared/` directory is the cross-language source of truth for built-in
scripts and test data. Interpreter-specific tests should consume the same files.

## relation to alpha data

Besides the code listed above in [layout](#layout) most of the code and docs are for the alpha version.

Alpha specs from `src/mspec/data/` have been renamed:

- `./generator/` --> renamed to `app`
- `./lingo/pages` --> renamed to `gui`
- `./lingo/rich-text` --> renamed to `text`
- `./lingo/scripts` --> renamed to `exe`

## tests

From the repository root:

```bash
./test.sh
```
This script runs tests _(only for beta version)_ in:
* `./tests/`
* `lingo/test`

### GUI tests
GUI tests will launch windows and take control of your mouse to simulate clicks, when you run the tests you should wait for them to complete before using your computer again, or the tests may fail.

The GUI tests **do not work in a VSCode sandbox**, but are run like this: 
```bash
./test.sh --gui
```

#### GUI Test Config
A config is needed to define the coordinates of the window for the screen capture process. It goes in `./.mtester/config.json`, example:
```json
{
    "window_region": {
        "height": 828,
        "width": 800,
        "x": 5,
        "y": 35
    }
}
```
This can be created automatically with:

```bash
./test.sh --setup-window
```

This command currently **requires OSX** and [cliclick](https://github.com/BlueM/cliclick)

```bash
brew install cliclick
```

To create one manually you need to fill out the config values based on the window location/size of the tkinter window when you run lingo `gui` or `text` specs.

#### full cli
```   
Usage: ./test.sh [options]
Options:
  -h, --help            		Show this help message and exit
  --gui                 		Run GUI tests (default: skip GUI tests)
  --no-gui              		Skip GUI tests (default: run GUI tests)
  --gui-only            		Only run GUI tests, skipping all non-GUI tests (implies --gui)
  --quick-window, -qw   		Skip querying the OS for window region (default: query the OS for window region)
  --no-quick-window, -nqw 	Query the OS for window region (default: skip querying the OS for window region)
  --setup-window        		Query and cache the test window region, then exit
Quick window mode:
  In quick window mode, the script will skip querying the OS for the window region and use a cached value instead.
  This can speed up tests that require window region information, but may be less reliable if the window region changes during the test run.
  This requires running the script once with --setup-window to cache the window region before running tests in quick window mode.
Setup Window:
  In setup window mode, the script will query the OS for the window region and cache it for future runs.
  It currently has limited OS support, see README.md for details.
```
