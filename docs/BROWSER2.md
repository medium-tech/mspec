# Browser2 JSON Page Documentation
Learn how to create a JSON Browser2 page.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Top-Level Keys](#top-level-keys)
   - [params](#params)
   - [state](#state) 
   - [ops](#ops)
   - [output](#output)
4. [Simple Demo Page](#simple-demo-page)
5. [Complete Reference](#complete-reference)
   - [Data Types](#data-types)
   - [Built-in Functions](#built-in-functions)
   - [Control Flow](#control-flow)
   - [UI Elements](#ui-elements)
   - [Expressions](#expressions)
6. [Examples](#examples)

## Overview

Browser2 uses a JSON-based markup language to create simple web pages that can be implemented in multiple languages by lightweight clients. Unlike traditional HTML/CSS/JavaScript, Browser2 pages are defined entirely in JSON with a built-in scripting language that is purely functional and type-safe.

A Browser2 JSON page consists of four main sections:
- **params**: Input parameters (analogous to URL query parameters)
- **state**: Application state variables that can be updated
- **ops**: Reusable operations with a JSON-based scripting language
- **output**: Layout elements similar to HTML for defining the page structure

## Getting Started

To run a Browser2 page using the Python implementation:

```bash
python -m mspec.browser2 --spec path/to/your/page.json
```

## Top-Level Keys

### params

Defines input values, analogous to URL/query parameters in a traditional web page. Each parameter has a type and optional default value.

```json
{
  "params": {
    "user_id": {"type": "int", "default": 0},
    "debug_mode": {"type": "bool", "default": false},
    "title": {"type": "str", "default": "My Page"}
  }
}
```

### state

Defines variables that can be updated by the program to maintain state between renders. State variables can have default values or calculated values.

```json
{
  "state": {
    "counter": {"type": "int", "default": 0},
    "user_name": {"type": "str", "default": ""},
    "greeting": {
      "type": "str", 
      "default": "",
      "calc": {
        "branch": [
          {"if": {"params": {"debug_mode": {}}}, "then": "Debug: Hello"},
          {"else": "Hello"}
        ]
      }
    }
  }
}
```

### ops

Defines reusable functions with a JSON-based scripting language. Operations can take arguments and perform complex logic.

```json
{
  "ops": {
    "increment_counter": {
      "args": {"amount": {"type": "int"}},
      "func": {
        "set": {"state": {"counter": {}}},
        "to": {"call": "add", "args": {"a": {"state": {"counter": {}}}, "b": {"args": "amount"}}}
      }
    }
  }
}
```

### output

A list of elements similar to HTML for layout. Defines text blocks, buttons, forms, and can use dynamic expressions.

```json
{
  "output": [
    {"heading": {"text": "Welcome"}, "level": 1},
    {"text": "Current count: "},
    {"lingo": {"state": {"counter": {}}}},
    {"break": 1},
    {"button": {"op": {"increment_counter": {"amount": 1}}}, "text": "Click me!"}
  ]
}
```

## Simple Demo Page

Here's a complete example that demonstrates all four top-level keys:

```json
{
  "params": {
    "initial_value": {"type": "int", "default": 42}
  },
  
  "state": {
    "counter": {
      "type": "int", 
      "default": 0,
      "calc": {"params": {"initial_value": {}}}
    },
    "user_name": {
      "type": "str",
      "default": ""
    }
  },
  
  "ops": {
    "increment": {
      "args": {"amount": {"type": "int"}},
      "func": {
        "set": {"state": {"counter": {}}},
        "to": {"call": "add", "args": {"a": {"state": {"counter": {}}}, "b": {"args": "amount"}}}
      }
    }
  },
  
  "output": [
    {"heading": {"text": "Demo Page"}, "level": 1},
    {"text": "This page demonstrates all Browser2 features."},
    {"break": 2},
    
    {"text": "Counter value: "},
    {"lingo": {"state": {"counter": {}}}},
    {"break": 1},
    
    {"text": "Enter your name: "},
    {"input": {"type": "text"}, "bind": {"state": {"user_name": {}}}},
    {"break": 1},
    
    {"button": {"op": {"increment": {"amount": 1}}}, "text": "Add 1"},
    {"text": " "},
    {"button": {"op": {"increment": {"amount": 5}}}, "text": "Add 5"},
    {"break": 2},
    
    {"text": "Current time: "},
    {"lingo": {"call": "datetime.now"}},
    {"break": 1},
    
    {"text": "Today is "},
    {"switch": {
      "expression": {"call": "current.weekday"},
      "cases": [
        {"case": 0, "then": {"text": "Monday"}},
        {"case": 1, "then": {"text": "Tuesday"}},
        {"case": 2, "then": {"text": "Wednesday"}},
        {"case": 3, "then": {"text": "Thursday"}},
        {"case": 4, "then": {"text": "Friday"}}
      ],
      "default": {"text": "the weekend"}
    }},
    {"text": "!"},
    {"break": 1},
    
    {"text": "Random number: "},
    {"lingo": {"call": "random.randint", "args": {"a": 1, "b": 100}}}
  ]
}
```

## Complete Reference

### Data Types

The following data types are supported for params and state:

- **str**: String values
- **int**: Integer numbers
- **float**: Floating-point numbers  
- **bool**: Boolean true/false values

### Built-in Functions

#### Logic Functions
- `bool`: Convert value to boolean
- `not`: Logical NOT operation
- `and`: Logical AND operation
- `or`: Logical OR operation

#### Math Functions
- `add`: Addition (a + b)
- `sub`: Subtraction (a - b)
- `mul`: Multiplication (a * b)
- `div`: Division (a / b)
- `pow`: Exponentiation (a ^ b)
- `neg`: Negation (-a)

#### Comparison Functions
- `eq`: Equal (a == b)
- `ne`: Not equal (a != b)
- `lt`: Less than (a < b)
- `le`: Less than or equal (a <= b)
- `gt`: Greater than (a > b)
- `ge`: Greater than or equal (a >= b)

#### Date/Time Functions
- `datetime.now`: Current date and time
- `current.weekday`: Current day of week (0=Monday, 6=Sunday)

#### Random Functions
- `random.randint`: Random integer between a and b (inclusive)

### Control Flow

#### Branch (if/elif/else)
```json
{
  "branch": [
    {"if": condition, "then": result},
    {"elif": condition, "then": result},
    {"else": result}
  ]
}
```

#### Switch Statement
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

### UI Elements

#### Heading
```json
{"heading": {"text": "Heading Text"}, "level": 1}
```
- **level**: Integer from 1-6 (like HTML h1-h6)

#### Text
```json
{"text": "Plain text content"}
```

#### Line Break
```json
{"break": 1}
```
- **break**: Number of line breaks to insert

#### Button
```json
{"button": {"op": {"operation_name": {"arg": "value"}}}, "text": "Button Text"}
```

#### Input Field
```json
{"input": {"type": "text"}, "bind": {"state": {"field_name": {}}}}
```
- **type**: Input type (currently "text")
- **bind**: Must bind to a state variable

#### Link
```json
{"link": "https://example.com", "text": "Link Text"}
```
- **text**: Optional display text (defaults to URL)

#### Block Container
```json
{"block": [
  {"text": "First element"},
  {"text": "Second element"}
]}
```

#### Dynamic Expression (Lingo)
```json
{"lingo": expression}
```
Renders the result of any expression as text.

### Expressions

#### State Access
```json
{"state": {"field_name": {}}}
```

#### Parameter Access  
```json
{"params": {"param_name": {}}}
```

#### Function Call
```json
{"call": "function_name", "args": {"a": value1, "b": value2}}
```

#### Operation Call
```json
{"op": {"operation_name": {"arg": "value"}}}
```

#### State Setting
```json
{
  "set": {"state": {"field_name": {}}},
  "to": expression
}
```

#### Argument Access (within ops)
```json
{"args": "argument_name"}
```

## Examples

### Simple Counter
```json
{
  "params": {},
  "state": {
    "count": {"type": "int", "default": 0}
  },
  "ops": {
    "increment": {
      "args": {},
      "func": {
        "set": {"state": {"count": {}}},
        "to": {"call": "add", "args": {"a": {"state": {"count": {}}}, "b": 1}}
      }
    }
  },
  "output": [
    {"heading": {"text": "Counter"}, "level": 1},
    {"text": "Count: "},
    {"lingo": {"state": {"count": {}}}},
    {"break": 1},
    {"button": {"op": {"increment": {}}}, "text": "Click to increment"}
  ]
}
```

### User Input Form with Conditional Display
```json
{
  "params": {},
  "state": {
    "name": {"type": "str", "default": ""}
  },
  "ops": {},
  "output": [
    {"heading": {"text": "Greeting Form"}, "level": 1},
    {"text": "Enter your name: "},
    {"input": {"type": "text"}, "bind": {"state": {"name": {}}}},
    {"break": 2},
    {"branch": [
      {"if": {"call": "ne", "args": {"a": {"state": {"name": {}}}, "b": ""}}, "then": {"block": [
        {"text": "Hello, "},
        {"lingo": {"state": {"name": {}}}},
        {"text": "!"}
      ]}},
      {"else": {"text": "Please enter your name above."}}
    ]}
  ]
}
```

### Random Number Generator
```json
{
  "params": {},
  "state": {
    "number": {"type": "int", "default": 0}
  },
  "ops": {
    "generate_random": {
      "args": {"max": {"type": "int"}},
      "func": {
        "set": {"state": {"number": {}}},
        "to": {"call": "random.randint", "args": {"a": 1, "b": {"args": "max"}}}
      }
    }
  },
  "output": [
    {"heading": {"text": "Random Number Generator"}, "level": 1},
    {"text": "Random number: "},
    {"lingo": {"state": {"number": {}}}},
    {"break": 1},
    {"button": {"op": {"generate_random": {"max": 100}}}, "text": "Generate (1-100)"}
  ]
}
```