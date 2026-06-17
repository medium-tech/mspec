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
python -m unittest lingo.test.test_hello_world
```
