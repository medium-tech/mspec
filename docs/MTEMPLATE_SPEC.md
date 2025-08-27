# mtemplate - YAML Specification

The mtemplate system uses YAML specification files to define the structure and data for generating dynamic applications from template code. This document describes the format and requirements for these YAML spec files.

## Table of Contents

- [Overview](#overview)
- [CLI Usage](#cli-usage)
- [Required Top-Level Fields](#required-top-level-fields)
  - [project](#project)
  - [server](#server)
  - [client](#client)
- [Modules, Models and Fields](#modules-models-and-fields)
  - [modules](#modules)
  - [models](#models)
  - [fields](#fields)
- [Field Types and Examples](#field-types-and-examples)
  - [Basic Types](#basic-types)
  - [List Types](#list-types)
  - [Enum Types](#enum-types)
  - [Custom Random Generators](#custom-random-generators)
- [Complete Example](#complete-example)

## Overview

The YAML spec file defines the structure for generating applications using the mtemplate system. It specifies project metadata, server/client configuration, and most importantly, the data models that will be used to generate CRUD applications with various field types.

The spec file drives the template extraction process, where template applications in `templates/py` and `templates/browser1` are processed to create dynamic applications based on the specified models and fields.

## CLI Usage

Once you have created a YAML spec file, you can use it with the mtemplate command to generate applications:

```bash
# Generate both Python and Browser1 applications
python -m mtemplate render --spec my-spec.yaml

# Generate only a Python application
python -m mtemplate render --spec my-spec.yaml --app py

# Generate only a Browser1 application  
python -m mtemplate render --spec my-spec.yaml --app browser1

# Specify custom output directory
python -m mtemplate render --spec my-spec.yaml --output ./my-generated-app
```

You can also validate and inspect your spec file:

```bash
# View the parsed spec structure
python -m mspec spec --spec my-spec.yaml
```

## Required Top-Level Fields

All YAML spec files must include these three top-level fields: `project`, `server`, and `client`.

### project

The `project` field defines metadata about the generated application:

```yaml
project:
  name:
    lower_case: 'my project name'
  description: 'A description of what this project does'
  author:
    name: 'Your Name'
    email: 'your.email@example.com'
```

**Required subfields:**
- `name.lower_case`: The project name in lowercase with spaces (automatically generates snake_case, pascal_case, kebab_case, and camel_case variations)
- `description`: A text description of the project
- `author.name`: The author's full name
- `author.email`: The author's email address

### server

The `server` field configures the backend server settings:

```yaml
server:
  port: 8080
```

**Required subfields:**
- `port`: The port number the server will listen on

### client

The `client` field configures client-side settings:

```yaml
client:
  default_host: 'http://localhost:8080'
```

**Required subfields:**
- `default_host`: The default host URL the client will connect to

## Modules, Models and Fields

### modules

The `modules` field defines one or more modules, each containing related models:

```yaml
modules:
  my_module:
    name:
      lower_case: 'my module name'
    models:
      # ... model definitions
```

**Required subfields:**
- `name.lower_case`: The module name in lowercase with spaces (automatically generates name variations)
- `models`: A collection of [model](#models) definitions

### models

Each [module](#modules) must contain one or more models:

```yaml
models:
  user_model:
    name:
      lower_case: 'user'
    fields:
      # ... field definitions
```

**Required subfields:**
- `name.lower_case`: The model name in lowercase with spaces (automatically generates name variations)
- `fields`: A collection of [field](#fields) definitions

### fields

Each [model](#models) must contain one or more fields that define the data structure:

```yaml
fields:
  username:
    type: str
    examples:
      - "john_doe"
      - "jane_smith"
    random: custom_username_generator  # optional
```

**Required subfields:**
- `type`: The field data type (see [Field Types](#field-types-and-examples))
- `examples`: An array of one or more example values

**Optional subfields:**
- `random`: Custom random generator name (overrides the default generator for the field type)

## Field Types and Examples

### Basic Types

**bool**: Boolean values
```yaml
is_active:
  type: bool
  examples:
    - true
    - false
```

**int**: Integer numbers
```yaml
age:
  type: int
  examples:
    - 25
    - 30
    - 45
```

**float**: Floating point numbers
```yaml
price:
  type: float
  examples:
    - 19.99
    - 99.50
    - 0.99
```

**str**: String values
```yaml
name:
  type: str
  examples:
    - "Alice"
    - "Bob"
    - "Charlie"
```

**datetime**: Date and time values (format `%Y-%m-%dT%H:%M:%S` per python datetime formatting)
```yaml
created_at:
  type: datetime
  examples:
    - "2023-01-15T10:30:00"
    - "2023-12-25T09:00:00"
```

### List Types

Lists can contain any of the basic types by specifying `element_type`:

```yaml
tags:
  type: list
  element_type: str
  examples:
    - ["red", "blue", "green"]
    - ["important", "urgent"]

scores:
  type: list
  element_type: int
  examples:
    - [95, 87, 92]
    - [100]
```

### Enum Types

String fields can be restricted to specific values using `enum`:

```yaml
status:
  type: str
  enum:
    - active
    - inactive
    - pending
  examples:
    - active
    - pending

colors:
  type: list
  element_type: str
  enum:
    - red
    - blue
    - green
    - yellow
  examples:
    - ["red", "blue"]
    - ["green"]
```

### Custom Random Generators

Fields can specify custom random generators to override the default random value generation:

```yaml
username:
  type: str
  examples:
    - "alice123"
    - "bob_the_builder"
  random: random_user_name

email:
  type: str
  examples:
    - "user@example.com"
  random: random_email

phone:
  type: str
  examples:
    - "+1 (555) 123-4567"
  random: random_phone_number
```

## Complete Example

Here's a complete YAML spec file demonstrating all the features:

```yaml
project:
  name:
    lower_case: 'my sample store'

  description: 'A sample project for mspec-alpha python app generator'

  author:
    name: 'B rad C'
    email: 'sample@email.com'

server:
  port: 7007

client:
  default_host: 'http://localhost:7007'

modules:
  store:
    name:
      lower_case: 'store'

    models:
      products:
        name:
          lower_case: 'products'

        fields:

          product_name:
            type: str
            examples:
              - 'Laptop'
              - 'Smartphone'
              - 'Tablet'

            random: random_thing_name

          price:
            type: float
            examples:
              - 999.99
              - 499.99
              - 299.99

          in_stock:
            type: bool
            examples:
              - true
              - false
      
      customers:
        name:
          lower_case: 'customers'

        fields:

          customer_name:
            type: str
            examples:
              - 'Alice'
              - 'Bob'
              - 'Charlie'
            random: random_person_name

          email:
            type: str
            examples:
              - 'alice@email.com'
              - 'bob@email.com'
            random: random_email

          phone_number:
            type: str
            examples:
              - '+1 (123) 456-7890'
              - '+1 (987) 654-3210'
            random: random_phone_number

  admin:
    name:
      lower_case: 'admin'

    models:
      employees:
        name:
          lower_case: 'employees'

        fields:

          employee_name:
            type: str
            examples:
              - 'David'
              - 'Eve'
              - 'Frank'
            random: random_person_name

          position:
            type: str
            enum:
              - 'Manager'
              - 'Sales'
              - 'Support'
            examples:
              - 'Manager'
              - 'Sales'
              - 'Support'

          hire_date:
            type: str
            examples:
              - '2000-01-11T12:34:56'
              - '2020-10-02T15:30:00'

          email:
            type: str
            examples:
              - 'my-name@email.com'
            random: random_email

          phone_number:
            type: str
            examples:
              - '+1 (123) 456-7890'
              - '+1 (987) 654-3210'
            random: random_phone_number

          salary:
            type: float
            examples:
              - 60000.00
              - 45000.00
              - 35000.00

```

This YAML spec file can be used with the mtemplate system to generate applications from the template code in `templates/py` and `templates/browser1`.