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

See here for [full language](./docs/LINGO_FUNCTIONS.md) function documentation.

## Table of Contents

* specs
	* scripting
		* samples files
		* python cli
	* pages
		* sample files
		* python cli
		* python browser2
		* legacy browser
	* application
		* sample files
		* running
			* server
			* cli
		* gui
			* legacy browser
			* python
* testing
	* python repo tests
	* mapp
	* browser2
		* legacy
		* pybrowser
* other
	* mtester
	* mtemplate

# language overview

# 



# testing

## main python tests
* mspec cli
* lingo page/script execution
* mtester

### run all
```bash
python -m unittest
```
### run individually
```bash
python -m unittest tests.test_lingo 
python -m unittest tests.test_mspec
python -m unittest tests.test_mtester
```