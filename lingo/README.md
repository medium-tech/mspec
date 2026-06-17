# lingo beta

This directory contains the beta rewrite bootstrap for Lingo.

It adds a shared layout for the Python, JavaScript, Go, Haskell, and C
implementations, plus a Python `unittest` suite that can build or run each
language-specific hello-world entry point.

## layout

```text
lingo/
├── README.md
├── src/
│   ├── c/
│   ├── go/
│   ├── h/
│   ├── js/
│   └── py/
└── test/
```

## tests

From the repository root:

```bash
python -m unittest lingo.test.test_setup
python -m unittest lingo.test.test_hello_world
```

`test_setup.py` checks that all required build and run commands are available for
each language. `test_hello_world.py` builds and runs the hello-world entry point
for each language and verifies the output. Both test suites fail (not skip) if a
required tool is missing.
