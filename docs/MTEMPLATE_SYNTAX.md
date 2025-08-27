# mtemplate - template syntax

mtemplate is a code templating system that allows you to extract dynamic templates from syntactically valid code. Instead of writing templates in Jinja2 syntax (which can't be run directly), mtemplate embeds templating commands in language comments, allowing template applications to remain fully runnable and testable.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Comment Syntax by Language](#comment-syntax-by-language)
- [Template Commands](#template-commands)
  - [vars](#vars-command)
  - [for](#for-command)
  - [ignore](#ignore-command)
  - [insert](#insert-command)
  - [replace](#replace-command)
  - [macro](#macro-command)

## Overview

The mtemplate system solves a fundamental problem with traditional templating: Jinja2 templates are not syntactically valid in their target language, making them impossible to run and test directly. mtemplate embeds templating directives in code comments, allowing the template application to be a fully functional, runnable application.

For example, instead of writing this invalid Python code:
```python
port = {{ config.port }}  # Invalid Python syntax
```

You write this valid Python code with mtemplate commands:
```python
# vars :: {"8080": "config.port"}
port = 8080  # Valid Python that can be run and tested
```

The mtemplate extractor processes this file and generates a Jinja2 template:
```python
port = {{ config.port }}
```

## How It Works

Currently this project is tightly coupled to the template apps in `./templates`, they have custom code in the `mtemplate` module that helps dynamically generate them. 

1. **Template Applications**: You create working applications in `templates/` directories that can be run and tested
2. **Templating Commands**: You embed mtemplate commands in code comments
3. **Template Extraction**: The `mtemplate` tool processes these files and creates Jinja2 templates
4. **Code Generation**: The templates are used with YAML spec files to generate new applications

## Comment Syntax by Language

mtemplate automatically detects the appropriate comment syntax based on file extensions:

| Language | Extension | Comment Syntax | Example |
|----------|-----------|----------------|---------|
| Python | `.py` | `#` | `# vars :: {"old": "new"}` |
| JavaScript/TypeScript | `.js`, `.ts` | `//` | `// vars :: {"old": "new"}` |
| HTML | `.html`, `.htm` | `<!-- -->` | `<!-- vars :: {"old": "new"} -->` |
| CSS | `.css` | `/* */` | `/* vars :: {"old": "new"} */` |
| JSON | `.json` | `"_": " ",` | `"_": " vars :: {'old': 'new'}",` |

**Note**: JSON doesn't have native comments, so mtemplate uses a special `"_"` key with single quotes inside the string to work around this limitation.

## Template Commands

All mtemplate commands follow the pattern: `<comment_start> <command> :: <arguments> <comment_end>`

### vars Command

The `vars` command defines template variables for string replacement in the current file.

**Syntax:**
```
<comment> vars :: {"old_string": "jinja_template_variable"}
```

**Arguments:**
- JSON object mapping strings to replace with Jinja2 template variables

**Examples:**

Python:
```python
# vars :: {"8080": "config.port", "myapp": "project.name.snake_case"}
port = 8080
app_name = "myapp"
```

JavaScript:
```javascript
// vars :: {"localhost": "config.host", "3000": "config.port"}
const host = "localhost";
const port = 3000;
```

HTML:
```html
<!-- vars :: {"My App": "project.name.title_case", "template-module": "module.name.kebab_case"} -->
<title>My App</title>
<a href="/template-module">Module</a>
```

JSON:
```json
{
    "_": " vars :: {'template_app': 'project.name.snake_case'}",
    "name": "template_app"
}
```

JSON doesn't have comments so we hack the system by defining the comment prefix to `"_": "` and comment ending to `",`

### for Command

The `for` command creates Jinja2 for loops in templates, with variable replacements within the loop block.

**Syntax:**
```
<comment> for :: <jinja_for_expression> :: <replacement_vars>
... loop content ...
<comment> end for ::
```

**Arguments:**
- Jinja2 for loop expression (e.g., `{% for item in collection %}`)
- JSON object mapping strings to replace within the loop with template variables

**Examples:**

Python:
```python
# for :: {% for model in module.models.values() %} :: {"single_model": "model.name.snake_case"}
from template_module.single_model.client import *
from template_module.single_model.db import *
# end for ::
```

HTML:
```html
<!-- for :: {% for model in module.models.values() %} :: {"single-model": "model.name.kebab_case", "single model": "model.name.lower_case"} -->
<li><a href="/template-module/single-model">single model</a></li>
<!-- end for :: -->
```

JavaScript:
```javascript
// for :: {% for field in model.fields.values() %} :: {"field_name": "field.name.snake_case"}
test('validate field_name', () => {
    // test code here
});
// end for ::
```

### ignore Command

The `ignore` command excludes lines from the generated template. Useful for template-specific code that shouldn't appear in generated applications.

**Syntax:**
```
<comment> ignore ::
... lines to ignore ...
<comment> end ignore ::
```

**Examples:**

Python:
```python
# ignore ::
# This import is only needed in the template app
import template_specific_module
# end ignore ::
```

HTML:
```html
<!-- ignore :: -->
<li><a href="/template-module/example-only">Template Example</a></li>
<!-- end ignore :: -->
```

### insert Command

The `insert` command inserts a Jinja2 expression directly into the template at the specified location.

**Syntax:**
```
<comment> insert :: <jinja_expression>
```

**Arguments:**
- Any valid Jinja2 expression (variables, function calls, etc.)

**Examples:**

Python:
```python
# insert :: macro.py_create_tables(all_models)
```

This generates:
```python
{{ macro.py_create_tables(all_models) }}
```

JavaScript:
```javascript
// insert :: config.api_endpoints | join(', ')
```

### replace Command

The `replace` command replaces a block of lines with a single Jinja2 expression.

**Syntax:**
```
<comment> replace :: <jinja_expression>
... lines to replace ...
<comment> end replace ::
```

**Examples:**

Python:
```python
# replace :: model.name.pascal_case + "Fields"
class DefaultFields:
    pass
# end replace ::
```

This replaces the entire class definition with `{{ model.name.pascal_case + "Fields" }}`.

### macro Command

The `macro` command defines reusable template macros that can be called from other templates.

**Syntax:**
```
<comment> macro :: <macro_name> :: <parameter_mapping>
... macro content ...
<comment> end macro ::
```

**Arguments:**
- `macro_name`: Name of the macro to be defined
- `parameter_mapping`: JSON object mapping template strings to macro parameter names

**Examples:**

Python:
```python
# macro :: py_create_model_table :: {"single_model": "model_name_snake_case", "field_list": "field_names"}
cursor.execute("CREATE TABLE IF NOT EXISTS single_model(id INTEGER PRIMARY KEY, field_list)")
# end macro ::
```

This creates a macro that can be called like:
```python
# insert :: macro.py_create_model_table({"model_name_snake_case": "user", "field_names": "name, email"})
```
