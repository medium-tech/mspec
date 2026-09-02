# mtemplate

mtemplate is a code templating system that allows you to extract dynamic templates from syntactically valid code. Instead of writing templates in Jinja2 syntax (which can't be run directly), mtemplate embeds templating commands in language comments, allowing template applications to remain fully runnable and testable.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Template Commands](#template-commands)
  - [Comment Syntax by Language](#comment-syntax-by-language)
- [Render Template Commands](#render-template-commands)
  - [vars](#vars)
  - [if / elif / else branching](#if--elif--else-branching)
  - [for](#for)
  - [ignore](#ignore)
  - [insert](#insert)
  - [replace](#replace)
  - [macro](#macro)
- [Parent / Child Template Commands](#parent--child-template-commands)
  - [slot](#slot)
  - [parent](#parent)
- [About Parent/Child Slots](#about-parentchild-slots)
- [API](#api)
- [CLI](#cli)

## Overview

The `mtemplate` system solves a fundamental problem with traditional templating: templates are not syntactically valid in their target language, making them impossible to run and test directly. `mtemplate` embeds templating directives in code comments, allowing the template application to be a fully functional, runnable application. It currently supports several languages, [see below](#comment-syntax-by-language).

`mtemplate` parses the source file and extracts commands from code comments. It then creates a [jinja](https://pypi.org/project/Jinja2/) template and renders it with provided variables.

For example, instead of writing this invalid Python code with jinja syntax:

```python
port = {{ config.port }}  # Invalid Python syntax
```

You write this valid Python code with mtemplate commands:
```python
# vars :: {"8080": "config.port"}
port = 8080
```

The mtemplate extractor processes this file and generates a jinja template:
```python
port = {{ config.port }}
```

## Template Commands

mtemplate commands follow the pattern: `<comment_start> <command> :: <arguments> <comment_end>`. 

* `<comment_start>` - this will vary by language
* `<command>` - the name of the command to use
* `<arguments>` - see docs for each command's arguments
* `<comment_end>` - depending on the language an end comment may be needed.

**Quotes** Many commands accept a json object as an argument, for these, most languages expect standard json using double quotes `"` to enclose strings. But when embedding in JSON, single quotes `'` are used to avoid unreadable escaping. See example below the table.

### Comment Syntax by Language

mtemplate automatically detects the appropriate comment syntax based on the following chart. If the file extension is not defined it will default to Python. Extensions are case insensitive.

| Language 				| Extension 			| JSON Quotes 	| Comment Start	| Commend End 	| Example [vars](#vars) command |
|----------				|-----------			|---			|---------------|---------------|---------|
| Python 				| `.py` 				| `"`			| `#` 			|		n/a		| `# vars :: {"old": "new"}` |
| JavaScript/TypeScript | `.js`, `.ts` 			| `"`			| `//` 			|		n/a		| `// vars :: {"old": "new"}` |
| HTML 					| `.html`, `.htm` 		| `"`			| `<!--` 		| 	`-->` 		| `<!-- vars :: {"old": "new"} -->` |
| CSS 					| `.css` 				| `"`			| `/*` 			| 	`*/` 		| `/* vars :: {"old": "new"} */` |
| JSON 					| `.json` 				| `'`			| `"_": "`	 	|	`",`		| `"_": " vars :: {'old': 'new'}",` |
| Markdown				| `.md`					| `"`			| `####` 		|		n/a		| `#### vars :: {"old": "new"}` |
| Yaml					| `.yaml`, `.yml`		| `"`			| `#`			|		n/a		| `# vars :: {"old": "new"}` |


**Note**: JSON doesn't have comments, so mtemplate uses a soecial key with a string value containing the template command, it must all be on a single line to work correctly. Example:

```json
{
    "_": " vars :: {'template_app': 'project_name'}",
    "name": "template_app"
}
```

If passed `mtemplate` as the `project_name` variable when rendering, the above template would output the following: 
```json
{
    "name": "mtemplate"
}
```

## Render Template Commands

The following commands can be used with the render api.

### vars

The `vars` command defines template variables for string replacement in the current file.

**Syntax:**
```
<comment> vars :: <variable definition>
```

**Arguments:**
- `<variable definition>` - JSON object mapping strings to replace with Jinja2 template variables
  - the keys represent the string in the template to be replaced with the jinja variable in each string.
  - ex: {"template_string": "jinja_variable"}

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

### for

The `for` command creates Jinja2 for loops in templates, with variable replacements within the loop block. `for` loops may be nested.

**Syntax:**
```
<comment> for :: <jinja_for_expression> :: <replacement_vars>
... loop content ...
<comment> end for ::
```

**Arguments:**
- `<jinja_for_expression>` - for loop expression using [jinja syntax](https://jinja.palletsprojects.com/en/stable/templates/#for) (e.g., `{% for item in collection %}`)
- `<replacement_vars>` - JSON object mapping strings to replace within the loop with template variables (or a Python dict literal, which is `eval`'d if it isn't valid JSON)

**Modifiers:**
- `<comment> end for :: rstrip` - omits the trailing newline after the emitted `{% endfor %}`, useful when nesting loops so that only the innermost iteration adds a newline

**Examples:**

Python nested loops, see [templates/tests/test_for.py](../templates/tests/test_for.py):
```python
# for :: {% for msg in msgs -%} :: {"hello": "msg", "hello_lower": "msg.lower()"}
# say - hello_lower
# for :: {% for name in names -%} :: {"john": "name"}
print('hello john')
# end for ::
# end for ::
```

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

### ignore

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

### insert

The `insert` command inserts a Jinja2 expression directly into the template at the specified location.

**Syntax:**
```
<comment> insert :: <jinja_expression>
```

**Arguments:**
- `<jinja_expression>` - Any valid [Jinja2 expression](https://jinja.palletsprojects.com/en/stable/templates) (variables, function calls, etc.)

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

### replace

The `replace` command replaces a block of lines with a single Jinja2 expression.

**Syntax:**
```
<comment> replace :: <jinja_expression>
... lines to replace ...
<comment> end replace ::
```

**Arguments:**
- `<jinja_expression>` - Any valid [Jinja2 expression](https://jinja.palletsprojects.com/en/stable/templates) (variables, function calls, etc.)

**Examples:**

Python:
```python
# replace :: model.name.pascal_case + "Fields"
class DefaultFields:
    pass
# end replace ::
```

This replaces the entire class definition with `{{ model.name.pascal_case + "Fields" }}`.

### macro

The `macro` command defines reusable template macros that can be called from other templates.

**Syntax:**
```
<comment> macro :: <macro_name> :: <parameter_mapping>
... macro content ...
<comment> end macro ::
```

**Arguments:**
- `<macro_name>`: Name of the macro to be defined
- `<parameter_mapping>`: JSON object mapping template strings to macro parameter names

**Examples:**

Python:
```python
# macro :: greet_person :: {"Person": "name"}
print('Greetings Person!')
# end macro ::
```

This creates a macro with one argument `name` that can be called like:
```python
# insert :: macro.greet_person(name='Python')
```

You can also call it with a template variable:
```python
# insert :: macro.greet_person(name=my_variable)
```

## Parent / Child Template Commands

The following commands are used with the slots API.

### slot

The `slot` command is used for parenting. In a parent template the slot defines the location to be replaced and in a child it is used with an `end slot` command to define the region that will be replaced in the parent. Slots are used in conjunction with the `parent` command to create a parent-child template relationship, see [About Parent/Child Slots](#about-parentchild-slots) for more.

Each slot defined in the child must have a `slot` and `end slot` command, but in the parent each slot is only a `slot` command.

⚠️ Unlike other commands, `slot`/`parent` are currently only recognized with the Python `#` comment prefix, regardless of the file's extension (see `apply_template_slots` in `src/mtemplate/core.py`).

**Syntax:**

parent templates
```
... content in parent file ...
# slot :: <slot_name>
... more content in parent file ...
```

child templates
```
... content in child file ...
# slot :: <slot_name>
... child slot content ...
# end slot ::
... content in child file ...
```

**Arguments:**
- `slot_name`: Unique identifier for the slot within the template

**Example (see [templates/tests/test_parent.py](../templates/tests/test_parent.py) and [templates/tests/test_child.py](../templates/tests/test_child.py)):**

Parent:
```python
# slot :: custom_imports

print('i am the parent template')

# slot :: custom_code
```

Child:
```python
# slot :: custom_imports
from typing import List
# end slot ::

print('i am the parent template')

# slot :: custom_code
def custom_function():
    pass
# end slot ::

# parent :: ./test_parent.py
```

### parent

The `parent` command establishes a parent-child relationship between templates, it is used to define a template as a child and what file is its parent. See [About Parent/Child Slots](#about-parentchild-slots) for more.

**Syntax:**
```
# parent :: <relative_path_to_parent>
```

**Arguments:**
- `relative_path_to_parent`: Path to the parent template, relative to the child template

**Example:**

```python
# parent :: ./test_parent.py
```

**Location:**
The `parent` command should be placed at the end of the child template file, after all slot definitions. This isn't necessary, but when the child is re-generated the `parent` line will be emitted as the last line because the parser doesn't know where it should be placed. A child template may only have one `parent` command.

## About Parent/Child Slots

⚠️ This feature currently only supports python.

The slots feature allows us to create parent child templates by inserting the parent template into a child template. When using the slots API, all commands from the [render commands](#render-template-commands) are ignored, this allows the child to be rendered after it is synchronized with the parent.

**Workflow (see [templates/tests/test_parent.py](../templates/tests/test_parent.py), [templates/tests/test_child.py](../templates/tests/test_child.py) and `test_cli_slots` in [tests/test_mtemplate.py](../tests/test_mtemplate.py)):**

1. **Define parent template** with slots:
   ```python
   # slot :: custom_imports

   print('i am the parent template')

   # slot :: custom_code
   ```

1. **Create child template** with parent reference and slot overrides:
   ```python
   # slot :: custom_imports
   from typing import List
   # end slot ::

   print('i am the parent template')

   # slot :: custom_code
   def custom_function():
       pass
   # end slot ::

   # parent :: ./test_parent.py
   ```
    Copy and paste the parent to create the child, then add code variations using slots in the child and create a corresponding slot in the parent where the variation should go. 

1. **Make changes in parent template**
    ```python
   # slot :: custom_imports

   print('i am a unittest for slots')

   # slot :: custom_code
   ```

1. **Synchronize changes to child** by running:
   ```bash
   python -m mtemplate slots -s <path_to_child_template> [-o <output_path>]
   ```

   This command:
   - Reads the child template's `parent` command to find its parent template
   - Replaces each `# slot :: <name>` line in the parent with the corresponding slot content (including the `slot`/`end slot` lines) from the child
   - Preserves the `parent` command at the end
   - If `-o`/`--output` is given, writes the result to that path (commonly the child template's own path, to update it in place); otherwise prints the result to stdout

1. **Child template output** will now have the new import with all of it's custom code right where it's supposed to be
    ```python
   # slot :: custom_imports
   from typing import List
   # end slot ::

   print('i am a unittest for slots')

   # slot :: custom_code
   def custom_function():
       pass
   # end slot ::

   # parent :: ./test_parent.py
   ```

**Error Handling:**
- If a child has a slot not present in the parent: `ValueError` raised
- If a parent has a slot not defined in the child: `ValueError` raised
- If no parent is defined in the child template: `ValueError` raised
- If multiple parent commands exist in the child template: `ValueError` raised
- If a `parent` command appears inside a slot, or an `end slot` appears without a matching `slot`, or slots are nested: `ValueError` raised


## API

The core API lives in `src/mtemplate/core.py` and is used to extract templates from a directory of source files and render them with a set of variables.

### MTemplateExtractor

`MTemplateExtractor` loads every file in a source directory, parses out template commands and macros, and exposes a jinja environment that can render any of the loaded templates by relative path.

**Creating an extractor:**
```python
from mtemplate.core import MTemplateExtractor

extractor = MTemplateExtractor.init_from_dir('templates/tests')
```

`init_from_dir(source, **kwargs)` accepts:
- `source`: `str | Path` - directory to recursively scan for template files
- `debug`: `bool` - when `True`, `render_template` returns the raw (unrendered) jinja template string instead of the rendered output; if `output` is also given, the raw template is written to `<output>.jinja2` and the normal rendered output is still written to `output`
- `disable_strict`: `bool` - when `True`, undefined variables render as empty instead of raising an error **(not recommended outside of debugging)**

**Rendering a template:**
```python
rendered = extractor.render_template('test_hello_world.py', {'user_name': 'Alice'})
```

`render_template(name, vars=None, output=None)` accepts:
- `name`: relative path (as a string) of the template file within `source`, e.g. `'test_hello_world.py'`
- `vars`: dict of variables available to the template during rendering
- `output`: optional `Path | str`, if given the rendered output is written to this path

Errors are raised as `mtemplate.core.MTemplateError` (invalid template commands) or `jinja2.TemplateError` (undefined variables, invalid jinja syntax) with the template name included in the message.

**Example (see [tests/test_mtemplate.py](../tests/test_mtemplate.py) for more):**
```python
from pathlib import Path
from mtemplate.core import MTemplateExtractor

sample_dir = Path('templates/tests')
extractor = MTemplateExtractor.init_from_dir(sample_dir)

rendered_template = extractor.render_template('test_branching.py', {'color': 'green', 'option': True})
```

### apply_template_slots

`apply_template_slots(child_path, output=None)` implements the [slot](#slot)/[parent](#parent) synchronization described in [About Parent/Child Slots](#about-parentchild-slots). It reads the child template at `child_path`, finds its `parent` template, and returns the parent's content with each `# slot :: <name>` line replaced by the matching slot block from the child. If `output` (`Path | str`) is given, the result is also written to that path. Raises `ValueError` for the error cases listed under [About Parent/Child Slots](#about-parentchild-slots).

**Example (see `test_cli_slots` in [tests/test_mtemplate.py](../tests/test_mtemplate.py)):**
```python
from mtemplate.core import apply_template_slots

regenerated_child = apply_template_slots('templates/tests/test_child.py')
```

## CLI

The CLI entry point is `src/mtemplate/__main__.py`, invoked as `python -m mtemplate`.

```bash
python -m mtemplate render --source <dir> --template <name> [--vars <json>] [--output <path>] [--debug] [--disable-strict]
python -m mtemplate slots --source <child_template_path> [--output <path>]
```

**Arguments:**
- `command`: `render` or `slots`
- `--source`, `-s`: for `render`, the source directory to scan for templates; for `slots`, the path to the child template file
- `--template`, `-t`: relative path of the template file to render (`render` only)
- `--vars`: JSON string of variables passed to the template (`render` only)
- `--output`, `-o`: file path to write the result to; if omitted, the result is printed to stdout
- `--debug`: print/write the raw jinja template instead of the rendered output (writes to `<output>.jinja2` if `--output` is set) (`render` only)
- `--disable-strict`: disable strict undefined-variable checking, **not recommended for general use, only debugging** (`render` only)

**`render` examples (see [tests/test_mtemplate.py](../tests/test_mtemplate.py) for more):**
```bash
python -m mtemplate render -s templates/tests/ -t test_hello_world.py --vars '{"user_name": "Alice"}'
```
```bash
python -m mtemplate render -s templates/tests/ -t test_for.py --vars '{"msgs": ["Hello", "Goodbye"], "names": ["Alice", "Bob"]}'
```

If a required variable is missing, the command exits with a non-zero return code and prints an error to stderr, e.g. `'user_name' is undefined`.

**`slots` examples (see `test_cli_slots` in [tests/test_mtemplate.py](../tests/test_mtemplate.py)):**
```bash
# print the regenerated child template to stdout
python -m mtemplate slots -s templates/tests/test_child.py
```
```bash
# regenerate the child template in place
python -m mtemplate slots -s templates/tests/test_child.py -o templates/tests/test_child.py
```
