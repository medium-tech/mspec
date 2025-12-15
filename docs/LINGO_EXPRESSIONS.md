
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

### Comparison Functions
`eq` - return true if `a` equals `b`
- `or` - bitwise OR
  - **args:**
    - **a** `any`
    - **b** `any`
  - **return:** `any`

  


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


### Date and Time Functions
`datetime.now` - return the current date and time
### Heading
```json
{"heading": {"text": "Heading Text"}, "level": 1}
```
- **level**: Integer from 1-6 (like HTML h1-h6)

### Random Functions
`random.randint` - return a random integer between `a` and `b` (inclusive)

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
