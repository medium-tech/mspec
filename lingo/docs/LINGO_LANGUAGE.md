# Lingo Language (Beta)

## Table of Contents

1. [Overview](#overview)
1. [Lingo Document](#lingo-document)
1. [Language Specs](#language-specs)
1. [Language Runtimes](#language-runtimes)
1. [Related Documentation](#related-documentation)

## Overview

Lingo is a [probably-functional](#what-is-probably-functional) language and application framework serialized in YAML. A Lingo document declares its
spec type with `lingo.spec`, then follows the structure for that spec.

Each spec represents a different runtime concern:

### Specs

| name | description | runtime(s) |
| --- | --- | --- |
| [exe](#exe-spec) | execute a `main` expression and return a value | [exe](#exe-runtime) |
| [app](#app) | backend and admin CLI definition | [server](#server-runtime), [client](#client-runtime) |
| [gui](#gui) | GUI spec that can talk to an `app` backend | [display](#display-runtime) |
| [text](#text) | subset of `gui` for formatted text payloads | [display](#display-runtime) |
| [lib](#lib) | reusable modules and functions importable by other specs | *not run directy* |
| [test](#test) | reusable test cases for interpreters and specs | *not run directy* |
| [data](#data) | serialized lingo data | *not run directy* |
| [super](#super) | compose many spec files into one run target | [exe](#exe-runtime), [server](#server-runtime), [client](#client-runtime), [display](#display-runtime) |


### Runtimes
| name | description |
| --- | --- |
| [exe](#exe-runtime) | run a script via command line |
| [server](#server-runtime) | run a web server |
| [client](#client-runtime) | http client to talk to a web server |
| [display](#display-runtime) | open a window and display a graphical user interface

### Expressions
Lingo expressions return a dynamically calculated value. They are used by each spec to create a dynamic application. See [expressions](./LINGO_EXPRESSIONS.md) for more.

### Built in application framework
Lingo is not only a fully feature general purpose programming language but also an application framework supporting crud database ops and an api, cli, gui interface. The gui will support the web browser via html/css/js and also clients in multiple programming languages.

### Multiple interpreters
Yaml was chosen for serialization because its readability and availability in many languages. There are lingo interpreters planned in:
* C
* Go
* Haskell
* Python
* Javascript

All languages will support the full expression library of lingo but may not be able to run all specs. For example only python and go are planned to run the backend `app` spec. Python is the only language currently planning on specs. See [implementation](./LINGO_IMPLEMENTATION.md) for the feature scope.

### What is probably-functional?
I'm not some phd language expert so I don't know if this qualifies as purely-functional like Haskell, but this language is like if Python and Haskell had a baby. Python inspires the batteries included and simple readability while Haskell's everything-must-return-something mentality inspires the strictness of lingo. In lingo, every function must return something, there's no side effects (unless the ui state counts?), no do, for, or while loops, all iteration is done functionally. When branching, every `if` must have an `else` and the switch needs a `default` case. 

The theory is that when you combine all of these language restrictions with static typing it becomes much more difficult to write bad code. Bad code = slow and/or buggy code. By removing for and while loops and requiring functional iteration it becomes very difficult to exit iteration wrong, unlike with nested loops and break and continue statements in other languages. The limitations on branching restrict your application to only necessary paths. No side effects means that every value defined must be used at least once. Combined with static typing, lingo attempts to reduce human (developer) error by removing unnecesary language features.

## Lingo Document

A spec file is a YAML file that contains a valid lingo spec. Each lingo spec will have the following object. See below for additional requirements and features of each spec.

```yaml
lingo:
  spec: '<spec-name>'
  version: '0.1.0b'
```

## Language Specs

### exe spec
---
Use:

- Run one main expression and return its value.
- Primary script execution target for the current beta.

Structure:

- `lingo` (required):
  - Mapping with spec metadata.
  - `spec`: must be `exe`.
  - `version`: language/version string (for example `0.1.0b`).
- `main` (required):
  - A Lingo expression to execute as the script entrypoint.
  - The interpreter evaluates this expression and returns its resulting value.
  - Expression reference: [LINGO_EXPRESSIONS.md](LINGO_EXPRESSIONS.md)
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

### app spec
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

### gui spec
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

### text spec
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

### lib spec
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

### test spec
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

### super spec
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

### data spec
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

## Language Runtimes
### exe runtime
placeholder...

### server runtime
placeholder...

### client runtime
placeholder...

### display runtime
placeholder...

## Related Documentation

- Alpha Lingo docs live in `docs/` at repository root.
- Beta examples currently live under `lingo/shared/scripts/` and `lingo/shared/tests/`.
