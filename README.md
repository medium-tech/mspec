# mspec

This project creates a single scripting and markup rendering language that is able to build:
* server/client apps w/ crud db operations
* interactive user interfaces

It is designed to be **lightweight, cross-os and cross-language** w/ interpreters and renderers in `python` and `js` currently, eventually also supporting c, go and haskell. `JS` and `YAML` have been chosen as the serialization format. Unlike the modern browser where your state is spread between 3 languages (html/js/css) a single `JS` or `YAML` file defines everything. Layout, style, scripting, even the data model for CRUD operations. A simple syntax is able to define models with fields and their types and then a framework app creates server endpoints, cli commands and db operations for the models. There is another syntax for rendering visual elements such as buttons, text and inputs and their layouts. Both share an extension set of functions for scripting.

To accomplish this there and three script specs:
* **scripting** - for running a result and returning a machine readable response (cli)
* **pages** - for rendering an interactive page
* **application** - for defining a crud application w/ server, cli, gui, and db

⚠️ currently in alpha phase - incomplete, api will change ⚠️ 


## Table of Contents

- [Language Specs](#language-specs)
  - [Scripting](#scripting)
  - [Pages](#pages)
  - [Application](#application)
- [Clients and Frameworks](#clients-and-frameworks)
  - [Python CLI](#python-cli)
  - [pybrowser2](#pybrowser2)
  - [Legacy Browser2 Dev Server](#legacy-browser2-dev-server)
  - [mapp Framework](#mapp-framework)
- [Development](#development)
  - [Setup Dev Environment](#setup-dev-environment)
  - [Code Layout](#code-layout)
  - [Deploying to PyPI](#deploying-to-pypi)
- [Philosophy](#philosophy)
- [Other](#other)
  - [mtester](#mtester)
  - [mtemplate](#mtemplate)

# language specs

See here for [full language](./docs/LINGO_FUNCTIONS.md) function documentation.

## scripting

This scripting spec enables executing a script and returning an output in a machine readable format. Ideally suited for cli and automation.

**spec name:** `script-beta-1`

[creating a script spec](./docs/LINGO_SCRIPTING_AND_PAGE_SPEC.md)

**sample files:** `src/mspec/data/lingo/scripts`

**bootstrap example file:** `python -m mspec example basic_math.json`

**execute w python cli:** `python -m mspec execute basic_math.json`

**clients**
* [python - cli](#python-cli)


## pages

This scripting spec allows rendering an interactive page including layout, style, scripting and state.

**spec name:** `page-beta-1`

[creating a page spec](./docs/LINGO_SCRIPTING_AND_PAGE_SPEC.md)

**sample files:** `src/mspec/data/lingo/pages`

**bootstrap example file:** `python -m mspec example hello-world-page.yaml`

**execute and dump json buffer:** `python -m mspec run hello-world-page.yaml`

**open in pybrowser2:** `python -m mspec.browser2 --spec hello-world-page.yaml`

**clients**
* [python - cli](#python-cli)
* [pybrowser2 - gui](#pybrowser2)
* [browser - gui](#legacy-browser2-dev-server)

## application

**spec name:** `generator-beta-1`

A spec for defining an application. Define data models with fields and their types and drive a framework with db crud ops and http api server, cli and gui interfaces wrapping them. Define an operation with input param types and return types and get a server, cli and gui interface to wrap it.

[creating an application spec](./docs/LINGO_MAPP_SPEC.md)

**sample files:** `src/mspec/data/generator`

**bootstrap example file:** `python -m mspec example my-sample-store.yaml`

[running the test app](#running-the-mapp-test-app)

**clients**
* [python - cli](#python-cli)
* [mapp framework](#mapp-framework)


# clients and frameworks

## python cli

The python cli can output built in example files, execute scripts and return the output or render and print the document buffer of a page spec.

****
```python
# Print names of all built in specs:
python -m mspec specs

# Copy builtin spec to cwd:
python -m mspec example basic_math.json

# Execute script and print output:
python -m mspec execute basic_math.json          
{
    "type": "float",
    "value": 20.0
}

# Render a page spec's document buffer and print to screen:
python -m mspec run hello-world-page.yaml
[
    {
        "heading": "Hello, World",
        "level": 1
    },
    {
        "text": "I am a sample page!"
    }
]
```

### testing
Covers:
* mspec cli
* execute script spec
* render buffer for page spec

Run commands from root of repo:
#### run all
```bash
python -m unittest
```

#### run individually
```bash
python -m unittest tests.test_lingo 
python -m unittest tests.test_mspec
python -m unittest tests.test_mtester
```


## pybrowser2
A browser2 implementation in Python using the built in `tkinter` library.

	python -m mspec.browser2

You can open any spec json file with this:

	python -m mspec.browser2 --spec hello-world-page.json

`hello-world-page.json` is a built in example spec and the above command will work even if that file is not in your working directory. the `--spec` arg will first be check to see if the path exists, if not then the arg will be checked against built in specs.

⚠️ Be careful with untrusted input as this project is still in alpha phase. ⚠️

### testing
⚠️ No tests yet.

## legacy browser2 dev server
The javascript *(legacy browser)* browser2 implementation is available in `browser2/js`.

**setup**

	cd browser2/js 
	npm install

**run dev server**

	./server.py

Check output for localhost address (ex: `http://localhost:8000`)

### testing
With dev server running, in another terminal run:

	npm run test

⚠️ If these tests fail you may need to run `build.sh` from the root of the repo.

## mapp framework
The mapp framework is used to run an application defined in the [application spec](#application). Its features include:
* db crud/list ops for data models
* procedured defined in scripting language
* server with:
    * crud/list endpoints for all data models
        * validates incoming data
    * POST endoints for all ops
        * validates incoming user params
        * validates output response before sending
* http client that calls the server
    * functions for each endpoint (models and ops)
* cli for everything
    * run crud/list using local db or remote server
    * run ops locally or via remote server
* authentication and users

### code

The `mapp` python framework code is in `src/mapp`. It uses the mapp spec to define an app.

The development implementation of a `mapp` app is in `templates/mapp-py`, use this for testing the framework. It is also used by the [mtemplate](#mtemplate) module as a template for boostrapping new mapp framework apps. Use the following command for boostrapping:

    python -m mtemplate render --output <output dir> --spec <spec file>

`--spec` can be a built in spec file or path to any spec file.

The UI for a mapp app is defined by lingo page files in `src/mspec/data/lingo/pages`, specifically the files in this dir starting with `builtin-mapp`.

The mapp application serves these wrapped in html for the browser. mapp does this when creating static file routes in `src/mapp/server.py`. These files are also dependent on the lingo script JS interpreter which is in `browser2/js`.

To test develop and test the JS lingo interpreter use the dev lingo server `browser2/js/server.py` and navigate to it in your browser.

Use `./build.sh` to sync the files in `browser2/js` to the python mapp app in `src/mspec/data/mapp-ui/src`. These are the lingo interpreter files that the template app `templates/mapp-py` will use for it's UI. For development testing you can run the `mapp-py` server like this to force it to use the development js interpreter without needing to use `build.sh` to sync your chages.


### running the mapp test app

Eventually this spec will be able to generate an app including python, html, shell scripts, etc. The template is still being finished so that's not available yet. For now the test app can be run against the test spec as follows.

Change to mapp directory:

	cd templates/mapp-py

run server:
	
	./server.sh --ui-src ../../browser2/js/src/

With server running:
* tail logs - `tail -f ./app/server.log`
* cli - `./run.sh -h`
* view ui in browser - http://localhost:3003 (confirm port in server out/logs)


### testing
Tests will run their own servers, with own sqlite file, on different ports that don't overlap with default port used by `./server.sh`.

**From dir:** `cd templates/mapp-py`

* python
	* run tests: `./test.sh`
	* test logs and data in dir: `./mapp-tests`
    * use cached test data: `./test.sh --use-cache`
* browser
	* run tests - `./test.sh --npm-run`
        * this will start the same test servers used in the python tests and then run `npm run test` against them
	* run specific npm commands w/ test servers/data
		* tests with gui: `./test.sh --npm-run test-ui`
        * test generator: `./test.sh --npm-run test-gen`
    * use cached test data: `./test.sh --use-cache --npm-run`

# Development

See here for code [style guidelines](./docs/CODE_STYLE.md).

## setup dev environment
This environment will be used to develop the template apps, mspec and mtemplate modules and browser2 python implementation.

    git clone https://github.com/medium-tech/mspec.git
    cd mspec
    python3 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    pip install -e .

## code layout

**python**
* `./src/mapp/` - mapp framework for server application spec
* `./src/mspec/` - language parsing, executing, buffering
* `./src/mspec/pybrowser2` - browser2 implementation (page spec gui)
* `./src/mtemplate/` - templating ([see here](#mtemplate))
* `./src/mtester/` - testing ([see here](#mtester))

**javascript**
* `browser2/js` - browser2 implementation (page spec gui) & dev server

**templates**
template apps from which templates are extracted.
* `./templates/mapp-py` - implementation of mapp framework
* `./templates/*` -  Currently `mapp-py` is in use with the mapp framework, and the others are deprecated. ([see here for more info](#mtemplate))

## deploying to pypi

### install build dependencies:

    pip install -r requirements-dev.txt

### finalizing release
1. run `python -m mtemplate cache` to ensure distributed templates are up to date

1. increment version in `pyproject.toml` file

1. run tests
	* mspec cli
	* mapp cli tests
	* mapp browser tests
	* browser2 js dev tests

### build and publish release:

1. build distributions

        python3 -m build --sdist
        python3 -m build --wheel

1. check distributions for errors

        ./build_test.py
        twine check dist/*

1. upload to pypi (will prompt for api key, no other config needed)

        twine upload dist/*


# Philosophy
* lightweight
* pythonic
* it just works, quickly

All specs are written in either json or yaml. The structure is the same regardless of the serialization format.
Yaml was chosen because it's simple syntax is both human readable and machine parsable.
JSON was chosen because because of it's wide availability, many languages have a built in parser.
Both of them generally serialize the same data and have simple serialization/deserialization apis so implementing both is trivial.


# Other

## mtester

Testing framework to automate gui testing across languages

⚠️ proof of concept only ⚠️


## mtemplate
A templating project to embed templating commands into real code. 

⚠️ Currently in refactoring state, docs may be out of date ⚠️

Templates in `./templates`:
* `mapp-py` - used to bootstrap a [mapp framework](#mapp-framework) app
* `go` - deprecated
* `py` - deprecated
* `browser1` - deprecated

see docs:
* [syntax](./docs/MTEMPLATE_SYNTAX.md)
* [legacy](./docs/MTEMPLATE_SYNTAX.md)