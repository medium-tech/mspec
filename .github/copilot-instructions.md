# mspec AI Coding Agent Instructions

## Project Overview

**mspec** is a dual-purpose project combining an app generator (mtemplate) and Browser 2.0 - a language-independent browsing protocol. The project is in alpha and uses a novel code templating approach where templates are extracted from syntactically valid "template apps" rather than written directly in Jinja2.

### Core Architecture

1. **mtemplate**: Code templating system that extracts Jinja2 templates from working applications
2. **mspec**: YAML spec parser, Browser2 renderer, and Lingo scripting language evaluator
3. **Template Apps** (`./templates/`): Runnable applications that serve as template sources
4. **Generated Apps**: Full-stack CRUD applications created from YAML specs

## Critical Concepts

### Template Extraction Philosophy

Unlike traditional templating where you write Jinja2 syntax directly, mtemplate embeds templating directives in **code comments** of syntactically valid applications:

```python
# vars :: {"8080": "config.port"}
port = 8080  # Valid Python that runs and can be tested
```

This extracts to: `port = {{ config.port }}`

**Why**: Template apps in `./templates/` must be fully runnable and testable. They're not templates until processed by `MTemplateExtractor`.

### Template Command Reference

- `# vars :: {<json>}` - String replacements throughout file
- `# for :: {% for ... %} :: {<json>}` - Loop with variable replacements inside
- `# if :: <condition>` / `# elif ::` / `# else ::` / `# end if ::` - Branching
- `# macro :: <name> :: {<json>}` ... `# end macro ::` - Reusable template snippets
- `# insert :: <jinja_expr>` - Insert template expression
- `# replace :: <jinja_expr>` ... `# end replace ::` - Replace block with expression
- `# ignore ::` ... `# end ignore ::` - Exclude from generated template

**Comment syntax varies by language**: `#` (Python), `//` (JS/TS), `<!-- -->` (HTML), `/* */` (CSS), `"_": " ",` (JSON hack)

### Template Prefixes System

Each `MTemplateProject` subclass defines `prefixes` dict mapping directory paths to template types:

```python
prefixes = {
    'src/template_module': 'module',        # Rendered once per module
    'src/template_module/single_model': 'model',  # Rendered per model
    'src/template_module/multi_model': 'macro_only'  # Only extracts macros
}
```

Files not matching any prefix are `'app'` templates (rendered once per project).

### Two-Phase Template System

1. **Extraction Phase**: `python -m mtemplate cache` reads template apps, extracts macros and Jinja2 templates, writes to `src/mtemplate/.cache/<app_name>/`
2. **Rendering Phase**: `python -m mtemplate render` loads cached templates, injects macros into spec context, renders with YAML data

**Key**: Macros from all templates become globally available as `spec['macro'][<macro_name>]` during rendering.

## Development Workflows

### Running Template Apps Directly

Template apps are **full working applications** you can run:

```bash
# Python template app (API + GUI + DB client)
cd templates/py
source ../../.venv/bin/activate
./server.sh  # Start uwsgi server at http://localhost:5005
./test.sh    # Run Python tests

# browser1 template app (HTML/JS frontend)
cd templates/browser1
npm install
npm run test  # Playwright tests
```

These should be run and tested frequently when modifying template features.

### Generating Apps from Specs

```bash
# Full workflow with caching
python -m mtemplate cache --spec <yaml_file>    # Extract templates once
python -m mtemplate render --spec <yaml_file> --output ./out  # Generate app

# Quick iteration without cache (slower)
python -m mtemplate render --spec test-gen.yaml --no-cache

# Debug mode (outputs .jinja2 files alongside generated files)
python -m mtemplate render --spec test-gen.yaml --debug

# Generate only one app type
python -m mtemplate render --app py --spec my-spec.yaml
python -m mtemplate render --app browser1 --spec my-spec.yaml
```

### Testing Strategy

```bash
# Fast: cache/generate tests only, skip running apps
./test.sh --quick

# Medium: tests template source apps + basic generation
./test.sh --templates

# Dev: tests caching + runs 1 generated app
./test.sh --dev

# Full: tests caching, multiple spec generations, runs all apps (slow ~5-10min)
./test.sh

# Specific test modules
./test.sh --cli      # CLI tests only
./test.sh --markup   # Lingo/markup tests only
```

**Test execution**: `test_app_generator.py` creates temp dirs in `tests/tmp/`, generates apps, installs deps, runs servers, executes tests, then cleans up.

## YAML Spec Structure

Specs define projects with modules containing models with typed fields:

```yaml
project:
  name:
    lower_case: my app  # Required, others auto-generated
  port: 6006

modules:
  my_module:
    name:
      lower_case: my module
    models:
      user:
        name:
          lower_case: user
        auth:
          require_login: true
          max_models_per_user: 1
        fields:
          username:
            name:
              lower_case: username
            type: str
            examples: ["alice"]
```

**Auto-generated naming**: `load_generator_spec()` converts `lower_case` to `snake_case`, `kebab_case`, `camel_case`, `pascal_case` for all project/module/model/field names.

**Reserved field**: `user_id` (type `str`) enables auth features.

## Browser2 / Lingo

Browser2 pages are JSON documents with 4 sections:

- `params`: Input parameters (like query params)
- `state`: Variables that can update
- `ops`: Reusable functions in Lingo scripting language
- `output`: Layout/UI elements

**Lingo** is a purely functional scripting language (no loops, no side effects except state updates). Operations: `add`, `sub`, `mul`, `div`, `call`, `branch` (if/elif/else), `filter`, `map`, `slice`, list operations.

Run Browser2 pages: `python -m mspec.browser2 --spec <json_file>`

## Key Files & Their Roles

- `src/mtemplate/__init__.py` - Base `MTemplateProject`, `MTemplateExtractor`, template extraction logic
- `src/mtemplate/py.py` - Python-specific template project with custom macros
- `src/mtemplate/browser1.py` - Browser1 (HTML/JS) template project
- `src/mspec/__init__.py` - Spec loading, name generation utilities
- `src/mspec/markup.py` - Lingo scripting language interpreter, Browser2 renderer
- `templates/py/` - Python template app (server, DB client, tkinter GUI, HTTP client)
- `templates/browser1/` - HTML/JS template app (static frontend with Playwright tests)
- `tests/test_app_generator.py` - Integration tests that generate and run apps

## Common Pitfalls

1. **Don't edit generated apps** - Edit template apps in `./templates/`, regenerate
2. **Cache invalidation** - Run `python -m mtemplate cache` after template changes
3. **Template syntax errors** - Use `--debug` flag to inspect generated .jinja2 files
4. **String replacement order** - `sort_dict_by_key_length()` ensures longest keys replaced first (prevents substring issues)
5. **User ID field** - Must be type `str`, enables auth when `require_login: true`
6. **Macro scope** - Macros extracted from any template become globally available
7. **Non-list field handling** - `model['non_list_fields']` and `model['list_fields']` are pre-computed sorted lists

## Package Structure

```
src/
  mspec/              # Spec parsing, Browser2, Lingo
  mtemplate/          # Template extraction & rendering
    .cache/           # Cached Jinja2 templates (git-ignored)
      py/
      browser1/
templates/            # Source template apps (runnable)
  py/                 # Python backend + GUI
  browser1/           # HTML/JS frontend
tests/
  tmp/                # Generated test apps (git-ignored)
dist/                 # PyPI build output
```

## Dependencies

**Core (published)**: `pyyaml==6.0.2`, `Jinja2==3.1.4`

**Template apps**: Python templates use `uwsgi`, `bcrypt`, `cryptography`. Browser1 uses `@playwright/test` for testing only (zero runtime deps).

**Philosophy**: Minimize dependencies. Generated apps are lightweight and standalone - this library is **build-time only**, not a runtime dependency.

## Deployment

Before PyPI release:

1. `python -m mtemplate cache` - Ensure distributed cache is current
2. Increment version in `pyproject.toml`
3. `./test.sh` - Full test suite
4. `python3 -m build --sdist && python3 -m build --wheel`
5. `twine check dist/*`
6. `twine upload dist/*`

## Current State (Alpha)

- ✅ Python + Browser1 template apps working
- ✅ YAML spec → full CRUD app generation
- ✅ Browser2 Python client (tkinter)
- 🟡 Auth system (login works, needs OAuth, ACLs)
- 🔴 Go, C, Haskell template apps (planned)
- 🔴 File upload/CID support (planned)

See `TODO.md` for detailed roadmap with status indicators (🔴 not started, 🟡 in progress, 🟢 finished).


# Code Style Guidelines

All code generated for this repository must follow the code style guidelines in the project README. Key points:

- **Quotes:**
  - Use single quotes (`'`) for string literals
  - Use triple double quotes (`"""`) for docstrings only
  - For f-strings: use single quotes for simple cases, double quotes for complex f-strings with single quotes inside
- **Whitespace:**
  - Two lines around major section headers and between classes
  - One line around minor section headers and between functions
- **Section Headers:**
  - Major: `#` borders (e.g. `#\n# section name\n#`)
  - Minor: hash suffix (e.g. `# section name #`)
  - Descriptive comments should be simple and clear
- **Unused code:**
  - No unused imports or variables
- **Error handling:**
  - Fail early and loudly (prefer exceptions over silent failure)
  - Raise exceptions, do not call `sys.exit()` in library code
- **General:**
  - Follow the example code blocks in the README
  - Match the layout and conventions of the Python template app

Refer to the [README](../README.md#code-style-guidelines) for full details and examples. All Copilot completions and code suggestions must adhere to these rules.
