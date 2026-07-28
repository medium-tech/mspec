# Lingo Expressions (Beta)

## Table of Contents

1. [Overview](#overview)
1. [Types](#types)
1. [Control Flow](#control-flow)
1. [Functions](#functions)
1. [Expression Notes](#expression-notes)

## Overview

In Lingo, an expression is a YAML mapping that describes a single
operation or value-producing step.

Expressions can contain:

- a literal value (`'hello'`, `123`, `true`)
- a typed value (`type` + `value`)
- a function expression (`add`, `str`, `join`, etc.)
- a control flow expression (`branch`, `switch`)

## Types

Lingo expression types are:

- `bool`
- `int`
- `float`
- `str`
- `list`
- `struct`

Values can be created in lingo either by specifying a literal yaml value (like the `a` arg below) or as a mapping (like the `b` arg below) with `type` and `value` fields.

```yaml
add:
	a: 0
	b: 
		type: int
		value: 1
```


## Control Flow

Control flow functions can be used to branch code.

### branch

`branch` runs ordered conditional cases and returns the first matching `then`. 

* The first case must be an `if` condition and supply a return expression in `then`
* The last case must define a return expression in `else`
* All other cases must supply an `elif` condition and define a return expression in `then`
* There must be at least 2 cases

Shape:

```yaml
branch:
  - if: <expression-returning-bool>
    then: <expression>
  - elif: <expression-returning-bool>
    then: <expression>
  - else: <expression>
```

### switch

`switch` evaluates `expression`, compares it to `case` values, and returns
the matching `then`. If no case matches, it returns `default`.

* must provide at least 1 case
* must provide default

Shape:

```yaml
switch:
  expression: <expression>
  cases:
    - case: <literal-or-expression-result>
      then: <expression>
  default: <expression>
```

Reference example: [lingo/shared/scripts/exe/hello-flow-control.yaml](lingo/shared/scripts/exe/hello-flow-control.yaml)

## Functions

This section documents all functions currently used in shared beta `exe`
scripts.

### String Functions

#### str

Converts input to a string.

Arguments:

- object: any expression or literal

Returns:

- `str`

Example:

```yaml
str:
  add:
    a: 1
    b: 2
```

#### concat

Concatenates a list of string items in order.

Arguments:

- list items (short form)

Returns:

- `str`

Example:

```yaml
concat:
  - 'hello, '
  - params: name
```

#### join

Joins string items with a separator.

Arguments:

- `separator`: `str`
- `items`: list of string expressions/literals

Returns:

- `str`

Example:

```yaml
join:
  separator: '\n'
  items:
    - str: true
    - str: false
```

### Numeric And Comparison Functions

#### int

Casts input to an integer.

Arguments:

- number/string expression

Returns:

- `int` on success
- error value on invalid conversion

Example:

```yaml
int:
  type: str
  value: '10'
```

#### add

Adds two numeric expressions.

Arguments:

- `a`: numeric expression
- `b`: numeric expression

Returns:

- `int` or `float`

Example:

```yaml
add:
  a: 1
  b: 2
```

#### eq

Compares two values for equality.

Arguments:

- `a`: expression
- `b`: expression

Returns:

- `bool`

Example:

```yaml
eq:
  a: 2
  b: 2
```

#### lt

Compares two values and returns true if `a < b`.

Arguments:

- `a`: expression
- `b`: expression

Returns:

- `bool`

Example:

```yaml
lt:
  a: 2
  b: 3
```

### List Functions

#### list

Declares a list value. Used both as plain YAML list literals and as typed list
objects.

Common shapes:

```yaml
list: [1, 2, 3]
```

```yaml
type: list
element_type: int
value: [7, 8]
```

Returns:

- `list`

#### append

Appends one item or many items to the end of a list.

Arguments:

- `to`: target list expression
- one of:
  - `item`: single item to append
  - `items`: multiple items to append

Returns:

- `list`

Example:

```yaml
append:
  item: 6
  to:
    list: [3, 4, 5]
```

#### prepend

Prepends one item or many items to the beginning of a list.

Arguments:

- `to`: target list expression
- one of:
  - `item`: single item to prepend
  - `items`: multiple items to prepend

Returns:

- `list`

Example:

```yaml
prepend:
  item: 0
  to:
    list: [1, 2, 3]
```

### Struct And Validation Functions

#### get

Gets a field from a struct/module value.

Arguments:

- `field`: field name
- `from`: source struct/module value

Returns:

- field value

Example:

```yaml
get:
  field: 'name'
  from:
    name: 'Joe'
    age: 42
```

#### validate

Validates an item against a type/schema definition.

Arguments:

- `item`: value/expression to validate
- `against`: schema definition

Returns:

- validated value on success
- error value on validation failure

Example:

```yaml
validate:
  item:
    name: 'Joe'
    age: 42
  against:
    define: struct
    fields:
      name:
        define: str
      age:
        define: int
```

### Module Call Functions

#### call

Calls an imported module function.

Arguments:

- `call`: namespaced function name (for example `hello_ns.say_hello`)
- `args`: argument mapping for that function

Returns:

- function return value

Example:

```yaml
call: 'hello_ns.say_hello'
args:
  name: 'World'
```

### Error Handling Function

#### error

Creates a language error value.

Arguments:

- `error`: human-readable message string
- `code` (optional): machine-readable code string

Returns:

- language error value

Example:

```yaml
error: 'i am a test error'
```

#### handle

Evaluates an expression and converts any resulting language error into a string
value instead of propagating the error.

Arguments:

- expression to execute inside `handle`

Returns:

- normal value if no error occurs
- stringified error if an error occurs

Example:

```yaml
handle:
  int: 'not-a-number'
```

### Parameter Access Expression

#### params

Reads an input parameter declared in spec-level `params`.

Arguments:

- parameter name

Returns:

- parameter value

Example:

```yaml
params: name
```

## Expression Notes

- Expressions are recursively evaluated from leaves to root.
- Many expression arguments are themselves expressions.
- Shared beta examples are under [lingo/shared/scripts/exe](lingo/shared/scripts/exe).