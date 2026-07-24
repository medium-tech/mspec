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
- `expect.stdout`: compared as exact text, interpreter must print a newline after the output, `expect.stdout` should not contain the trailing newline as it is appended when the yaml is parsed.
