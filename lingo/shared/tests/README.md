# lingo shared tests

Shared contract fixtures for cross-language lingo interpreter tests.

## directory layout

- `exe/` stores contract fixtures for `lingo.spec: 'exe'` scripts.
- scripts are referenced from `lingo/shared/scripts/...`.

## exe fixture schema

Each fixture file is YAML and follows this shape:

```yaml
lingo_test:
    spec: 'exe'
    version: '0.1.0b'

script: 'scripts/exe/hello-world.yaml'

tags:
    - smoke

cases:
    - name: 'default'
      params: {}
      expect:
          exit_code: 0
          stdout: 'hello.world'
```

## field notes

- `script`: path relative to `lingo/shared/`.
- `tags`: used for filtering (`smoke`, `error`, etc).
- `cases`: one or more execution cases.
- `params`: reserved for future CLI params support.
- `expect.stdout`: compared as exact text, interpreter must print a newline after the output, `expect.stdout` should not contain the trailing newline as it is appended when the contract is loaded. When using yaml block syntax to define stdout, ensure that it does not contain a trailing line break; use a chomping indicator (`|-`) to strip it if needed, see below for example:

```yaml
cases:
    - name: 'default'
      params: {}
      expect:
          exit_code: 0
          stdout: |-
              LINGO_ERROR [ERROR] - i am a test error
              LINGO_ERROR [ERROR_W_CODE] - i am an error w a code
              LINGO_ERROR [TYPE_ERROR] - args must be int or float for add symbol, got a: str and b: str
              LINGO_ERROR [ERROR] - cannot convert 'i am not a number' to int with base 10: invalid literal for int() with base 10: 'i am not a number'
              LINGO_ERROR [ERROR] - all items for concat symbol must be str
```
