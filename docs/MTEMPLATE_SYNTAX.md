# mtemplate - template syntax

mtemplate is a code templating system that allows you to extract dynamic templates from syntactically valid code. Instead of writing templates in Jinja2 syntax (which can't be run directly), mtemplate embeds templating commands in language comments, allowing template applications to remain fully runnable and testable.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Comment Syntax by Language](#comment-syntax-by-language)
- [Template Commands](#template-commands)
  - [vars](#vars-command)
  - [if / elif / else branching](#if--elif--else-branching)
  - [for](#for-command)
  - [ignore](#ignore-command)
  - [insert](#insert-command)
  - [replace](#replace-command)
  - [macro](#macro-command)
  - [slot](#slot-command)
  - [parent](#parent-command)
- [About Parent/Child Slots](#about-parentchild-slots)

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

JSON doesn't have comments so we hack the system by defining the comment prefix to `"_": "` and comment ending to `",`.
As long as including the `"_"` key in the JSON doesn't affect any programs that use it when can template the JSON.

### if / elif / else branching
Conditional branching may be used in templates with `if`, `elif`, `else`, and `end if` commands. A conditional block begins with an `if` statement, may include zero or more `elif` statements, may include an optional `else` statement, and must end with an `end if` statement. The `if`, `elif` statements may include a condition that evaluates to `true` or `false`. The block of code following the `if` or `elif` statement is rendered in the template if the condition is `true`.

**Syntax:**

basic
```
<comment> if :: <statement>
... template content ...
<comment> end if ::
```

full
```
<comment> if :: <statement>
... template content ...
<comment> elif :: <statement>
... template content ...
<comment> else :: <statement>
... template content ...
<comment> end if ::
```

**Examples:**
Python:
```python
# if :: model.auth.require_login is true
# insert :: macro.py_test_model_seed_pagination_login(model=model)
# end if ::
```

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
This creates a macro that can be called like:
```python
# insert :: macro.py_create_model_table({"model_name_snake_case": "user", "field_names": "name, email"})
```

### slot Command

The `slot` command is used for parenting. In a parent template the slot defines the location to be replaced and in a child it is used with a `slot end` command to define the regoin that will be replaced in the parent. Slots are used in conjunction with the `parent` command to create a parent-child template relationship, see [About Parent/Child Slots](#about-parentchild-slots) for more.

Each slot defined in the child must have a `slot` and `end slot` command, but in the parent each slot is only a `slot` command.

**Syntax:**

parent templates
```
... content in parent file ...
<comment> slot :: <slot_name>
... more content in parent file ...
```

child templates
```
... content in parent file ...
<comment> slot :: <slot_name>
... child slot content ...
<comment> end slot ::
... content in parent file ...
```

**Arguments:**
- `slot_name`: Unique identifier for the slot within the template

### parent Command

The `parent` command establishes a parent-child relationship between templates, it is used to define a template as a child and what file is its parent. See [About Parent/Child Slots](#about-parentchild-slots) for more.

**Syntax:**
```
<comment> parent :: <relative_path_to_parent>
```

**Arguments:**
- `relative_path_to_parent`: Relative path from the child template to its parent template

**Example:**

Python:
```python
# parent :: ../single_model/__init__.py
```

**Location:**
The `parent` command should be placed at the end of the child template file, after all slot definitions. This isn't necessary, but when the child is re-generated the `parent` line will be emitted in the last line because the parser doesn't know where it should be placed.

## About Parent/Child Slots

**Motivation**
The `mtemplate` system is a template system that extracts templates from syntactically valid code. As such variations in templates may require multiple templates and duplicated template code. For example, the model in `templates/.../single_model/db.py` does not require authentican, but `templates/.../multi_model/db.py` does. Both templates are needed to create a `db.py`, the one in `single_model` is the parent template and the `multi_model` is the child. The child defines an authentication macro inside a slot and the parent uses conditional statements to apply the variation (macro) when needed. The several lines inside the children's slots are the only thing different about it than the parent template. When changes to parent model are made they can be syncronized to the child template using slots. The `slot` and `slot end` commands in the child define the variation, and the matching `slot` command in the parent defines where the variation should be placed in the parent.

**Workflow:**

1. **Define parent template** with slots:
   ```python
   # slot :: custom_imports
   
   from core import *
   
   # slot :: custom_code
   ```

1. **Create child template** with parent reference and slot overrides:
   ```python
   # slot :: custom_imports
   from typing import List
   # end slot ::
   
   from core import *
   
   # slot :: custom_code
   def custom_function():
       pass
   # end slot ::
   
   # parent :: ../single_model/__init__.py
   ```
    Copy and paste the parent to create the child, then add code variations using slots in the child and create a corresponding slot in the parent where the variation should go. 

1. **Make changes in parent template**
    ```python
   # slot :: custom_imports
   
   from core import *
   from other_module import more_code
   
   # slot :: custom_code
   ```

1. **Synchronize templates** by running:
   ```bash
   python -m mtemplate slots
   ```
   
   This command:
   - Finds all child templates (templates with a `parent` command) in `./templates/`
   - For each child, reads its parent template
   - Replaces slots in the parent with corresponding slot content from the child
   - Writes the result back to the child template file
   - Preserves the `parent` command at the end

1. **Child template output** will now have the new import with all of it's custom code right where it's supposed to be
    ```python
   # slot :: custom_imports
   from typing import List
   # end slot ::
   
   from core import *
   from other_module import more_code
   
   # slot :: custom_code
   def custom_function():
       pass
   # end slot ::
   
   # parent :: ../single_model/__init__.py
   ```

**Error Handling:**
- If a child has a slot not present in the parent: Error raised
- If a parent has a slot not defined in the child: Error raised
- If no parent is defined in a child template passed to `apply_template_slots()`: `NoParentDefinedError` raised
- If multiple parent commands exist: Error raised

**Debug Mode:**
```bash
python -m mtemplate slots --debug
```

In debug mode, the command shows what would be updated without actually modifying files, and may show warnings.
