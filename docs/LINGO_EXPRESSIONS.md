
# Lingo Expressions

- [Data Types](#data-types)
- [Built-in Functions](#built-in-functions)
- [Control Flow](#control-flow)
- [UI Elements](#ui-elements)
- [Expressions](#expressions)

## Data Types

### Primitives

- **bool**: Boolean true/false values
- **int**: Integer numbers
- **float**: Floating-point numbers
- **str**: String values
- **datetime**: datetime objects

### collections

- **list** - A list of elements, all elements must be the same type. All primitives are supported.

## Functions

### Logic Functions
- `bool`: Convert value to boolean
- `not`: Logical NOT operation
- `neg`: Arithmetic negation (-a)
- `and`: Bitwise AND (a & b)
- `or`: Bitwise OR (a | b)

### Math Functions
- `add`: Addition (a + b)
- `sub`: Subtraction (a - b)
- `mul`: Multiplication (a * b)
- `div`: Division (a / b)
- `floordiv`: Floor division (a // b)
- `mod`: Modulo (a % b)
- `pow`: Exponentiation (a ** b)
- `min`: Minimum of two values
- `max`: Maximum of two values
- `abs`: Absolute value

### Comparison Functions
- `eq`: Equal (a == b)
- `ne`: Not equal (a != b)
- `lt`: Less than (a < b)
- `le`: Less than or equal (a <= b)
- `gt`: Greater than (a > b)
- `ge`: Greater than or equal (a >= b)

### Integer/Float/String Functions
- `int`: Convert to integer (from number or string, with optional base)
- `float`: Convert to float
- `round`: Round float to nearest integer or to given number of digits
- `str`: Convert to string
- `join`: Join list of items with separator

### Sequence Functions
- `len`: Length of string or list
- `range`: Range of integers (start, stop, step)
- `slice`: Slice a list (start, stop, step)
- `any`: True if any element is true
- `all`: True if all elements are true
- `sum`: Sum of elements (with optional start)
- `sorted`: Sorted list

### Sequence Operations
- `map`: Map a function over a list
- `filter`: Filter a list by function
- `dropwhile`: Drop elements while function is true
- `takewhile`: Take elements while function is true
- `reversed`: Reverse a list
- `accumulate`: Accumulate results of a function over a list
- `reduce`: Reduce a list to a single value using a function

### Date/Time Functions
- `datetime.now`: Current date and time
- `current.weekday`: Current day of week (0=Monday, 6=Sunday)

### Random Functions
- `random.randint`: Random integer between a and b (inclusive)

## Control Flow

### Branch (if/elif/else)
```json
{
  "branch": [
    {"if": condition, "then": result},
    {"elif": condition, "then": result},
    {"else": result}
  ]
}
```

### Switch Statement
```json
{
  "switch": {
    "expression": value_expression,
    "cases": [
      {"case": value1, "then": result1},
      {"case": value2, "then": result2}
    ],
    "default": default_result
  }
}
```

## UI Elements

### Heading
```json
{"heading": {"text": "Heading Text"}, "level": 1}
```
- **level**: Integer from 1-6 (like HTML h1-h6)

### Text
```json
{"text": "Plain text content"}
```

### Line Break
```json
{"break": 1}
```
- **break**: Number of line breaks to insert

### Button
```json
{"button": {"op": {"operation_name": {"arg": "value"}}}, "text": "Button Text"}
```

### Input Field
```json
{"input": {"type": "text"}, "bind": {"state": {"field_name": {}}}}
```
- **type**: Input type (currently "text")
- **bind**: Must bind to a state variable

### Link
```json
{"link": "https://example.com", "text": "Link Text"}
```
- **text**: Optional display text (defaults to URL)

### Block Container
```json
{"block": [
  {"text": "First element"},
  {"text": "Second element"}
]}
```

### Dynamic Expression (Lingo)
```json
{"lingo": expression}
```
Renders the result of any expression as text.

## Expressions

### State Access
```json
{"state": {"field_name": {}}}
```

### Parameter Access  
```json
{"params": {"param_name": {}}}
```

### Function Call
```json
{"call": "function_name", "args": {"a": value1, "b": value2}}
```

### Operation Call
```json
{"op": {"operation_name": {"arg": "value"}}}
```

### State Setting
```json
{
  "set": {"state": {"field_name": {}}},
  "to": expression
}
```

### Argument Access (within ops)
```json
{"args": "argument_name"}
```
