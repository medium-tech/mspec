# Lingo Scripting and UI Spec

## Table of Contents

1. [Overview](#overview)
1. [Getting Started](#getting-started)
1. [Top-Level Keys](#top-level-keys)
   - [params](#params)
   - [state](#state) 
   - [ops](#ops)
   - [output](#output)
1. [Example Script](#example-script)
1. [Example Page](#example-page)
1. [Examples](#examples)

## Overview

There are currently two variations of this spec `script-beta-1` and `page-beta-1`. 

`page-beta-1` is a JSON or yaml markup language to create simple web pages that can be implemented in multiple languages by lightweight clients. Unlike traditional HTML/CSS/JavaScript, Browser2 pages are defined entirely in JSON/yaml with a built-in scripting language that is purely functional and type-safe.

Both page types consists of four main sections:
- **params**: Input parameters (analogous to URL query parameters)
- **state**: Application state variables that can be updated
- **ops**: Reusable operations with a JSON-based scripting language
- **output**: The output of the program, different depending on type of spec

As explained below, these specs can contain lingo expressions, those are defined in [this document](./LINGO_EXPRESSIONS.md).

## Getting Started

Discover built in example specs:

```bash
python -m mspec specs
```

For script specs you can run this like this:

```bash
python -m mspec execute basic_math.json
```
which will give you a json output:
```json
{
    "type": "float",
    "value": 20.0
}
```

You can also supply input params:

```bash
python -m mspec execute basic_math.json --params '{"a": 100, "b": 200}'
```
output:
```
{
    "type": "float",
    "value": 750.0
}
```

The `browser2` module can be use to run a GUI for page specs:
```bash
python -m mspec.browser2 --spec hello-world-page.json
```
It will check to see if that path exists in your working dir, if not it will check to see if it exists in the built in dir.
You can copy it to your directory like this:

```bash
python -m mspec example hello-world-page.json
```

And now you can edit this file and run the same command to run your local version.

Or run any spec file:

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

Defines variables that can be updated by the program to maintain state between renders. State variables can have default values or calculated values defined by a lingo expression.

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

Defines reusable functions with a JSON-based scripting language. Operations can take arguments and perform complex logic using a lingo expression.

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

For the `script-beta-1` spec the output can be any supported type returned by a lingo expression.

```json
"output": {
    "call": "mul",
    "args": {
        "a": {
            "call": "add",
            "args": {
                "a": {
                    "params": {
                        "a": {}
                    }
                },
                "b": {
                    "params": {
                        "b": {}
                    }
                }
            }
        },
        "b": {
            "value": 2.5,
            "type": "float"
        }
    }
}
```

For the `page-beta-1` spec, the output is a list of elements similar to HTML for layout. Defines text blocks, buttons, forms, and can use lingo expressions.

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

When a page is loaded the first the time, the client will iterate though the output and execute all lingo expressions. These expressions will all return 
elements suitable for display in a buffer. `{"lingo": {"state": {"counter": {}}}}` above is a references to the `counter` variable stored in state. 
To display this to a user we will return it as text, when we render this expression it will be replaced ini the buffer with `{"text": "0"}`. The client 
then takes the buffer and uses it to drive their rendering process. If the user interacts with a form or button the buffer will be regenerated from the same elements defined in `output` but if the state has been modified the output will be different.

## Example Script

Here's a complete `script-beta-1` spec:

```json
{
    "lingo": {
        "version": "script-beta-1"
    },
    "params": {
        "a": {
            "type": "int",
            "default": 5
        },
        "b": {
            "type": "int",
            "default": 3
        }
    },
    "state": {},
    "ops": {},
    "output": {
        "call": "mul",
        "args": {
            "a": {
                "call": "add",
                "args": {
                    "a": {
                        "params": {
                            "a": {}
                        }
                    },
                    "b": {
                        "params": {
                            "b": {}
                        }
                    }
                }
            },
            "b": {
                "value": 2.5,
                "type": "float"
            }
        }
    }
}
```

## Example Page

Here's a complete example of a `page-beta-1` spec.

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