# mspec

This project creates a single scripting and markup rendering language that is able to build:
* server/client apps w/ crud db operations
* interactive user interfaces

It is designed to be **lightweight, cross-os and cross-language** w/ interpreters and renderers in `python` and `js` currently, eventually also supporting c, go and haskell. `JS` and `YAML` have been chosen as the serialization format. Unlike the modern browser where your state is spread between 3 languages (html/js/css) a single `JS` or `YAML` file defines all of it. A simple syntax is able to define models with fields and their types and then a framework app creates server endpoints, cli commands and db operations for the models. There is another syntax for rendering visual elements such as buttons, text and inputs and their layouts. Both share an extension set of functions for scripting.

It will have the batteries included philosophy of python with the strictness of static typing and is inspired by the functional nature of haskell.

To accomplish this there and three script specs:
* **scripting** - for running a result and returning a machine readable response (cli)
* **pages** - for rendering an interactive page
* **application** - for defining a crud application w/ server, cli, gui, and db

⚠️ currently in alpha phase - incomplete, api will change ⚠️ 

## Table of Contents

* language specs
	* scripting
	* pages
	* application
* clients
	* python cli
	* pybrowser2
	* legacy browser
	* mapp framework
* development
	* setup dev environment
	* code layout
	* deploying to pypi
* testing
	* python repo tests
	* mapp
	* browser2
		* legacy
		* pybrowser
* other
	* mtester
	* mtemplate

# language specs

See here for [full language](./docs/LINGO_FUNCTIONS.md) function documentation.

## scripting

This scripting spec enables executing a script and returning an output in a machine readable format. Ideally suited for cli and automation.

[creating a script spec](./docs/LINGO_SCRIPTING_AND_PAGE_SPEC.md)

**sample files:** `src/mspec/data/lingo/scripts`

**bootstrap example file:** `python -m mspec example basic_math.json`

**execute w python cli:** `python -m mspec execute basic_math.json`

**clients**
* [python - cli](#python-cli)


## pages

This scripting spec allows rendering an interactive page including layout, style, scripting and state.

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

...placeholder...

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

	python -m mspec.browser2 --spec functions.json

`functions.json` is a built in example spec and the above command will work even if that file is not in your working directory. the `--spec` arg will first be check to see if the path exists, if not then the arg will be checked against built in specs.

⚠️ Be careful with untrusted input as this project is still in alpha phase. ⚠️

### testing
⚠️ No tests yet.

## legacy browser2 dev server
...placeholder...

### testing
...placeholder...

## mapp framework

The `mapp` python framework code is in `src/mapp`. It uses the mapp spec to define an app.

The example implementation of a `mapp` app is in `templates/mapp-py`, use this for testing the framework.

The UI for a mapp app is defined by lingo page files in `src/mspec/data/lingo/pages`, specifically the files in this dir starting with `builtin-mapp`.

The mapp application serves these wrapped in html for the browser. mapp does this when creating static file routes in `src/mapp/server.py`. These files are also dependent on the lingo script JS interpreter which is in `browser2/js`.

To test develop and test the JS lingo interpreter use the dev lingo server `browser2/js/server.py` and navigate to it in your browser.

Use `./build.sh` to sync the files in `browser2/js` to the python mapp app in `src/mspec/data/mapp-ui/src`. These are the lingo interpreter files that the template app `templates/mapp-py` will use for it's UI. For development testing you can run the `mapp-py` server like this to force it to use the development js interpreter without needing to use `build.sh` to sync your chages.

    ./server.sh --ui-src ../../browser2/js/src/

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
	* run tests - `./test.sh`
	* test logs and data in dir: `./mapp-tests`
* browser
	* start server - `./test.sh --servers-only`
	* in another terminal run test
		* headless: `npm run test`
		* interactively: `npm run test-ui`

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


# Other

## mtester

Testing framework to automate gui testing across languages

⚠️ proof of concept only ⚠️


## mtemplate
A templating project to embed templating commands into real code. 

⚠️ Currently in refactoring state ⚠️

Templates in `./templates`:
* `mapp-py` - incomplete - for the [mapp framework](#mapp-framework) once the framework stabilizes.
* `go` - deprecated
* `py` - deprecated
* `browser1` - deprecated

see docs:
* [extractor](./docs/MTEMPLATE_EXTRACTOR.md)
* [syntax](./docs/MTEMPLATE_SYNTAX.md)
* [legacy](./docs/MTEMPLATE_SYNTAX.md)