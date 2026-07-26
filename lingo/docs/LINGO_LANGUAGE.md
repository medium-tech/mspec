# Lingo Language (Beta)

## Table of Contents

1. [Overview](#overview)
1. [Universal Document Shape](#universal-document-shape)
1. [Spec Languages](#spec-languages)
1. [Related Documentation](#related-documentation)

## Overview

Lingo (beta) is a YAML-based language family. A Lingo document declares its
spec type with `lingo.spec`, then follows the structure for that spec.

Each spec represents a different runtime concern:

- `exe`: execute a `main` expression and return a value
- `app`: backend and admin CLI definition
- `ui`: UI spec that can talk to an `app` backend
- `text`: subset of `ui` for formatted text payloads
- `lib`: reusable modules and functions importable by other specs
- `test`: reusable test cases for interpreters and specs
- `super`: compose many spec files into one run target
- `data`: serialized Lingo data (backend-linked or anonymous)

Status at this stage:

- In progress: `exe` is being implemented in the python intepreter
- Drafted and evolving: `app`, `ui`, `text`, `lib`, `test`, `super`, `data`

## Universal Document Shape

Every spec starts with:

```yaml
lingo:
  spec: '<spec-name>'
  version: '0.1.0b'
```

After that root object, the allowed keys depend on the selected spec.

## Spec Languages

### exe
---
Use:

- Run one main expression and return its value.
- Primary script execution target for the current beta.

Structure:

- `lingo` (required):
  - Mapping with spec metadata.
  - `spec`: must be `exe`.
  - `version`: beta language/version string (for example `0.1.0b`).
- `main` (required):
  - A Lingo expression to execute as the script entrypoint.
  - The interpreter evaluates this expression and returns its resulting value.
  - Expression reference docs will be documented separately.
- `meta` (optional):
  - Arbitrary mapping of YAML metadata for humans and tooling.
  - Common use: description, tags, ownership, notes, or environment hints.
- `import` (optional):
  - List of relative/known import paths to other specs (commonly `lib`).
  - Imported modules/functions/types can be referenced by `main` expressions.
- `params` (optional, currently used in examples):
  - Parameter declarations available to expressions via `params` lookups.
  - Useful for external inputs to `main` at execution time.

Minimal example:

```yaml
lingo:
  spec: 'exe'
  version: '0.1.0b'

main:
  str: 'hello.world'
```

Expanded example:

```yaml
lingo:
  spec: 'exe'
  version: '0.1.0b'

meta:
  description: 'Example with params and imports.'

import:
  - 'hello-library.yaml'

params:
  name:
    define: str
    default: 'World'

main:
  call: 'hello_ns.say_hello'
  args:
    name:
      params: name
```

### app
---

Use:

- Define backend operations, models, and app-level module wiring.

Draft structure:

- Typical keys:
  - `lingo`
  - `meta`
  - `import`
  - `modules`

Placeholder:

```yaml
lingo:
  spec: 'app'
  version: '0.1.0b'

meta:
  description: 'Placeholder app spec.'

modules:
  my_app:
    ops: {}
    models: {}
```

### ui
---

Use:

- Describe frontend UI behavior and rendering that can call backend operations.

Draft structure:

- Typical keys:
  - `lingo`
  - `state`
  - `ops`
  - `output`
  - optional `backend`, `import`, `meta`

Placeholder:

```yaml
lingo:
  spec: 'ui'
  version: '0.1.0b'

state: {}
ops: {}
output: []
```

### text
---

Use:

- Represent formatted text payloads as a lightweight subset of ui-style output.

Draft structure:

- Typical keys:
  - `lingo`
  - `block`

Placeholder:

```yaml
lingo:
  spec: 'text'
  version: '0.1.0b'

block:
  - text: 'Hello from text spec.'
```

### lib
---

Use:

- Define reusable modules, functions, structs, and values.
- Imported by `exe` and other specs.

Draft structure:

- Typical keys:
  - `lingo`
  - `modules`
  - optional `meta`

Placeholder:

```yaml
lingo:
  spec: 'lib'
  version: '0.1.0b'

modules:
  sample_ns:
    greet:
      args:
        name:
          type: str
          default: 'World'
      return:
        type: str
      func:
        concat:
          - 'Hello, '
          - args: name
```

### test
---

Use:

- Define reusable executable test cases against target specs.

Draft structure:

- Typical keys:
  - `lingo`
  - `tests`

Placeholder:

```yaml
lingo:
  spec: 'test'
  version: '0.1.0b'

tests:
  - spec: 'scripts/exe/hello-world.yaml'
    tags: [smoke]
    cases:
      - name: 'default'
        params: {}
        expect:
          exit_code: 0
          stdout: 'hello.world'
```

### super
---
Use:

- Bundle multiple spec files together and choose a run target.

Draft structure:

- Typical keys:
  - `lingo`
  - `specs`
  - `run`
  - optional `meta`

Placeholder:

```yaml
lingo:
  spec: 'super'
  version: '0.1.0b'

specs:
  - 'lingo-stdlib.yaml'
  - 'hello-library.yaml'
  - 'hello-backend.yaml'

run:
  spec: 'hello-backend.yaml'
  params: {}
```

### data
---
Use:

- Store serialized Lingo data for backend-linked or anonymous data flows.

Draft structure:

- Typical keys:
  - `lingo`
  - `data`
  - optional `backend`, `meta`

Placeholder:

```yaml
lingo:
  spec: 'data'
  version: '0.1.0b'

meta:
  description: 'Placeholder data payload.'

data:
  sample:
    items:
      - id: '1'
        label: 'First item'
```

## Related Documentation

- Alpha Lingo docs live in `docs/` at repository root.
- Beta examples currently live under `lingo/shared/scripts/` and `lingo/shared/tests/`.