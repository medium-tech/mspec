# mspec

This project defines specs for:
* creating applications
* scripting
* browsing

All specs are written in either json or yaml. The structure is the same regardless of the serialization format.
Yaml was chosen because it's simple syntax is both human readable and machine parsable.
JSON was chosen because because of it's wide availability, many languages have a built in parser.
Both of them generally serialize the same data and have simple serialization/deserialization apis so implementing both is trivial.

### lingo script spec
A scripting language embedded in either json or yaml that maps similarly to the builtin python library. Here's a simple math function in JSON:
```json
{
    "call": "add",
    "args": {
        "a": {"int": 2},
        "b": {"int": 4}
    }
}
```

Or the a and b variables can be parsed from user input, available in the scripting language with `params`:

```json
{
    "call": "add",
    "args": {
        "a": {
            "params": {"a": {}}
        },
        "b": {
            "params": {"b": {}}
        }
    }
}
```

See [bl-mspec-dev](https://github.com/medium-tech/bl-mspec-dev) for a node based editor to generate these spec files.


### lingo page spec
Building on the lingo scripting spec, the lingo page spec is a language independent browsing protocol (in json or yaml) designed to be a faster, safer more reliable web browsing experience. It allows a ui page including state, layout, styling, and scripting.

### mapp spec
The [mapp spec](./docs/MAPP_SPEC.md) is used to define an application in a json or yaml file an get:
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

Currently this is implemented in python, but eventually other languages like `go` as well. The template app in `templates/mapp-py` shows how to create a python app using this spec. The framework logic that runs it located in `src/mapp`. Eventually this framework app will be made into
a template so that a user can autogenerate a static application for full control of the underlying code. It will use the `mtemplate` syntax to
embed templating commands inside the working python files.

## Table of Contents

⚠️ this project is currently in alpha and incomplete ⚠️

* [about this project](#mspec)
    * [mapp framework](#mapp-framework)
    * [app generator](#app-generator)
    * [browser 2.0](#browser-20)
    * [the problem this project aims to solve](#the-problem-this-project-solves)
* documentation
    * mtemplate
        * [app generator / spec](./docs/MAPP_SPEC.md)
        * [template extractor](./docs/MTEMPLATE_EXTRACTOR.md)
        * [template syntax](./docs/MTEMPLATE_SYNTAX.md)
        * [example repo](https://github.com/medium-tech/mspec-apps)
    * browser2 (lingo page spec)
        * [write a browser2 page](./docs/LINGO_SPEC.md)
        * [python gui client](#pybrowser2)
* [development](#development)
    * [code layout](#code-layout)
    * [setup dev enviro](#setup-dev-environment)
    * [run and edit template apps](#edit-and-run-template-apps)
    * [generate apps using templates](#generate-apps-using-templates)
    * [test app generator](#test-app-generator)
* [code style guidelines](#code-style-guidelines)
* [contributing](#contributing)
* [deploying to pypi](#deploying-to-pypi)

## mapp framework

The `mapp` framework is the first python implementation of the `mapp` spec. The code is in `src/mapp` and an example using it is in `templates/mapp-py`. See this page for the [mapp spec documentation](./docs/MAPP_SPEC.md).

## app generator
This is currently being refactored. `templates/mapp-py` is an implementation of a mapp framework application. `go`, `browser1` and `py` and are all deprecated templates. The `mapp-py` template is used to bootstrap a mapp framework app, eventually templating syntax will be added to the mapp framework code so that it can be used to generate a low level static app if a user wants to customize the framework logic. Once this is complete in python, then the same framework style app will be built in go, and then add template extraction to it.

### how is this different than other code templating projects?
I speculate that other approaches such as openapi and json schema haven't resulted in a robust templating culture because they are too complex. Instead of focusing on abstracting everything a developer could possibly need, this project will focus on the most common boiler plate code and a consistent developer exprience across multiple languages and front vs backend. If you generate an app with a Go backend an a python GUI and JS webpage the apps will all be laid out similarly reducing the learning curve. If the developer needs an additional types or logic not provided by this library then they'll have an easy way of extending the generated app, or they could just modify the generated code directly.

## browser 2.0

The browsing protocol is an attempt to make a language independent browsing protocol. Modern web pages are required to use html and can also use CSS and Javascript and/or other Javascript~ish languages like JSX and TS. But why not Go, python or Rust? The language stack goes: machine code -> assembly -> C++ -> HTML -> JS -> JSX/TS -> JS. This is overengineering. Cmbined with the fact that browsers are not fully compatible with one another and you get a nightmare of development and support process. The solution is to make a simpler markup language. When HTML and Javascript were created we didn't know where they were going and how they would change the world. Now that we've seen that, its time to make version 2 of the web browser. One that is language independent, more secure, faster, and doesn't let developers create all the the things that we hate about using a web browser.

This is built for the user, not the developer. As a user, I cannot stand most websites. It takes 8 seconds to load, then I have to click the cookie monster button, then I have to search for the close button on the prompt asking for my email. I finally find it and click it, but an image loaded and the button moved and I accidentally clicked another button and takes me to a different page. So then I click back and repeat the process again. This markup protocol will be intentionally limited so that you can't fucking do that. It will force a product to be impressive on its on without flashy animations.

It needs to be able to accomplish everything we need the browser to do without any of the other stuff. What the user actually needs is different than what the developer, marketin,g and product teams believe the user needs. In order to do that this protocol has intentional limitations when compared to the legacy browser.

### protocol summary
A JSON definition will define the app's document sctructure as well as logic with a built in scripting language. This language has no io operations and only allows safe operations such as math, comparison, logic, branching, date formatting, etc. Outside of scripting, IO operations are still possible but must be registered using model definitions. Models can have multiple fields and define their types such as bool, int, foat, str, or lists of these types.

The scripting language will be purely functional and every operation has to return something. These limitations exist for (a) the functional bro memes and (b) to create front-end apps that "just work". What I found when working with Haskell is that is that when you remove looping (`for`, `while`, etc), side-effects and require that every code path return something, once you finish writing the code it pretty much just works. Combined with static typing the only place left for bugs to hide is logic that works but is incorrect. Haskell taught me that side-effects are not needed and by removing them you elimate possible bugs with them. Exit conditions with looping structures such as `for` and `while` can often have non-obvious edge cases, but you can't exit an iteration from a `filter`, `map` or `accumulator` function incorrectly.

Model fields can define computed properties that are based on an expression. This expression has access to user input (forms) and application state models. User input from forms and button can trigger state updated.

The style and layout will be realatively simple, a bit more advanced that markdown but not nearly as extensive as HTML/CSS. It will have text blocks such as paragraphs, headings, and lists, images, and audio/video players. Layout items such as grids and columns and font style and color options. This is not an exhaustive list but enough to get an idea of the document structure. Elements will also be able to be dynamically generated using scripting.

The scripting, layout and styling will all be in one language instead of three like the current browser (JS, HTML and CSS). The templating system will be able to generate an app from this JSON for quick bootstrapping.

### speed and reliability

A quick anecdote. When I was a kid we had a 56k modem that ran at 14.4k because we were so far away from the phone company and web pages took 10 seconds to load.
Then we got satellite, which had better bandwidth but higher latency so web pages still took 10 seconds to load. Now, I have a fiber connection with 500Gbs up an down and a 9-14ms ping and web pages still take 10 seconds to load because they're downloading an initializing mountains of node modules or something.

Of course anecdotes of high performance websites exist as well. But what if we made a protocol that if you make a valid app syntactically, not only will it "just work" but it will also "just be quick". I feel like most websites I use (aside from social media) actually only single digit MBs of text and perhaps several MBs of images.

The internet should be almost instant today and yet it's not. It's only instant for doom scrollers that monetize attention.

In theory most modern apps shouldn't be network network limited, so what is it? Slow backend? Slow frontend? I think it's because we're expecting the web browser to do too much. It doesn't need to do everything. The internet is a battlefield of people trying to hack your info, we don't want the browser to do everything. We want it to show us text, images and videos. We want it to be quick and reliable. The modern web stack has not demonstrated the ability to provide that experience consistently. Some devs can, but many can't, including "enterprise" devs.

So let's not give devs the ability to write shitty apps. This protocol will not let you open so many media files that the page crashes.
It won't let you make so many network requests for your spyware that it hangs the tab. If your app requires more than 1 a/v stream being played to the end user it doesn't belong in the web browser. The web browser is for browsing. It's for browsing text, media (images/audio/video), and viewing data and graphs. If you need more than that, write a native desktop or mobile app.

In `$current_year` apps on the web browser should **"just work quickly"**.

### security and privacy

All inputs from users (ie. form data) will have model definitions. All requests and responses to and from servers, and application state (both short and long term storage) will also be defined. This eliminates bugs and security vulnerabilities caused by dynamic typing mistakes. It increases auditability. And by defining and registering "unsafe" operations the client could go into a "read only" mode where the application is read but not executed. Specific IO ops could be enabled on an ad-hoc basis.

Apps can define backend operations in the same JSON making the document a full stack application definition. The backend could be remote or local, allowing the user to choose where to store the data. This puts the user in control of their data.

### content based addressing

Browser2.0 also goes above and beyond the web browser, it is also an attempt to minimize link rot. 

Browser2.0 will use content based addressing instead of location based addressing. The current browser is location based `example.com/path/to/article`, but these urls break over time which make news articles and and written information degrade in quality over time. Content based addressing uses a file signature (checksum) to find and recall information, so that as a webpage is changed and modified over the years as long as they (or other server) continues to host the content it will always be discoverable. Additionally documents will be versioned and links will convey versions and be able to quote passages in the documents. A client will be able to easily expand a quote to see full context and find current or former versions of the same document. As new versions of a document are released, other documents can be updated to reference the new version of the source. This is a manual process because the author should review the changes as their conclusions may warrant revision based on the new information.

## the problem this project solves
In short, this project aims to solve complexity and reliability of modern application development.

It's 2025, the internet is faster than its ever been, software development is more accessible and yet somehow apps and websites still don't "just work". They're also slow. Even enterprise websites can take 10 seconds to load, not because they're network constrained but because the software is overengineered. Most of the web is just a CRUD app with a bit of dynamic logic in the back or front end. This project aims to reduce the complexity of deploying and maintaining applications. 

It also aims to improve the browsing experience by creating a simple markup language that can be implemented in any language. Instead of having a monolithic browser, the browser could be just at home in your office suite, your email client or a video game. 
Limiting the browser to just Javascript limits our software creativity. Additionally, the added complexity of modern HTML/CSS/JS has demonstrated an unrelaiable, slow means of information exchange. If the language allows people to write crappy software, they will.
This protocol is designed to prevent writing unreliable code and slow websites.

Of course there are examples of fast websites but in my day to day experience is does not seem to be even a majority of websites.

# Documentation

## pybrowser2
A browser2 implementation in Python using the built in `tkinter` library.

    python -m mspec.browser2

You can open any spec json file with this:

    python -m mspec.browser2 --spec functions.json

`functions.json` is a built in example spec and the above command will work even if that file is not in your working directory. the `--spec` arg will first be check to see if the path exists, if not then the arg will be checked against built in specs.

To list built in examples:

    python -m mspec specs

For more examples and complete documentation on creating JSON pages, see **[here](./docs/LINGO_SPEC.md)**.

⚠️ Be careful with untrusted input as this project is still in alpha phase. ⚠️

# Development

## code layout
The `./src` folder contains two modules:

* `mtemplate` - extracts templates from template apps and using them to generate apps based on yaml definition files in `./spec`
* `mspec` - parse yaml spec files, browser2 and lingo
* `mapp` - python framework for mapp spec applications

The `./templates` folder contains template apps from which templates are extracted.

## setup dev environment
This environment will be used to develop the template apps, mspec and mtemplate modules and browser2 python implementation.

    git clone https://github.com/medium-tech/mspec.git
    cd mspec
    python3 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    pip install -e .
    pip install -e templates/py

## edit and run template apps

**WARNING** this section is outdated because the templating is being refactored

As mentioned, the templates are extracted from working apps in `./templates`, this allows you to run the templates directly for fast development and testing. This section explains how to run the apps from which templates are extracted. If you want to change the features that generated apps have you need to edit the template apps as described in this section. If you want to learn how to generate template apps from a yaml spec go to [generate apps from spec files](#generate-apps-from-spec-files).

### python template app
Follow the setup instructions in [./templates/py/README.md](./templates/py/README.md), except use the `venv` you just setup instead of creating a separate. You can create a second `venv` but it's easier for testing to use the one that also has the other modules in this repo installed.

The readme has instructions to install deps, run the server, run the python gui and run tests.

The api and frontend are served from the same server, you can access them at `http://localhost:5005`.

### html / js gui template

The frontend files are served staticly from `./templates/browser1/srv` and can be accessed at `http://localhost:5005`. No dependencies are needed for running the frontend however `playwright` is used for testing. See [./templates/browser1/README.md](./templates/browser1/README.md) to learn how to run tests.


## generate apps using templates

To generate apps from spec files, first follow steps in [setup dev environment](#setup-dev-environment).

Then run:

    python -m mtemplate render

By default this will use the spec file `./spec/test-gen.yaml` and output the files in `./dist/test-gen` but you can supply custom arguments like this:

    python -m mtemplate render --spec <yaml spec file> --output <output dir>

Or render just the python or frontend like this:

    python -m mtemplate render-py
    python -m mtemplate render-browser1

If you customize the output path of the browser1 files, they will need to be output to the same directory as the python app in order for the server to find them.

With either mtemplate command you can also supply `--debug` and it will output the jinja template files for inspection and it will also not delete the existing output directory before generating files.

Or for help:

    python -m mtemplate -h

## run and test generated apps

**WARNING** this section is outdated because the templating is being refactored

After following the above steps to render the python and browser1 files you can run the apps as follows. You need to be in the output directory that contains the `browser1` and `py` directories which using the default spec and output is `dist/test-gen`

    cd <output dir>/py
    python3 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    python -m pip install -e .

Then to run the python server:

    ./server.sh

The server is now available at `http://localhost:6006` for the api and frontend *(the port number is configured in the spec file, it may not always be 6006)*. If you followed the above steps for running the [python template app](#run-the-python-server) the `.env` file you created will be copied over for you. If not, the app will not run. Follow the above instructions and create the `.env` file manually in this directory.

Once the server is running you can run the python tests:

    ./test.sh

As with the template apps, 0 dependencies are required to deploy the app, however npm and playwright can be used to run tests:

    cd ../browser1
    npm install
    npm run test


## Code Style Guidelines

This project follows specific code style preferences to maintain consistency and readability:

### Quote Preferences
- **Single quotes** (`'`) for string literals
- **Triple double quotes** (`"""`) for docstrings only

```python
# Preferred
bl_label = 'My Node'
def my_function():
    """This is a docstring"""
    return 'result'

# Avoid
bl_label = "My Node"
def my_function():
    '''This is a docstring'''
    return "result"
```

**F string quotes**
```python

name = 'Brad'
data = {'age': 37}

# for simple f-strings: single quotes
greeting = f'Hello, {name}'

# for complex f-strings: 
#   double quotes to define the f-string, single quotes inside the f-string
msg = f"Brad is {data['age'] years old}"
```

### unused
- no unused imports
- no unused variables

### Section Headers

**Major sections** use hash borders:
```python
#
# section name
#
```

**Minor sections** use hash suffixes:
```python
# section name #
```

**Descriptive comments** are simple:
```python
# example explaining what is going on at this point in the code
```

### Whitespace
* 2 lines around major section headers and between classes
* 1 line around minor section headers and between functions
```python
import bpy


#
# value nodes
#


class MyValueNode(Node):
    """Node for handling values"""
    bl_label = 'Value Node'
    
    def init(self, context):
        # Create the output socket
        self.outputs.new('NodeSocketInt', 'value')


class MyOtherValueNode(Node):
    """Node for handling values"""
    bl_label = 'Value Node'
    
    def init(self, context):
        # Create the output socket
        self.outputs.new('NodeSocketInt', 'value')


# helper functions #

def create_default_value():
    # Return a sensible default
    return 42

def create_another_default_value():
    # Return a sensible default
    return 33


#
# registration
#


classes = [
    MyValueNode,
]
```

### Error handling
#### Fail early, fail loudly.

```python

# fails early with KeyError if x doesn't exist
x:int = data['x']

# fails later when we try to use None but expect int
x:int = data.get('x')
# we'll have a traceback unrelated to the fact that 
# x wasn't provided, making it harder to troubleshoot

# an exception to this rule is when we plan to use a default
x:int = data.get('x', 42)
```

#### Raise exceptions, don't exit
```python

# prefer exceptions because they provide tracebacks
try:
    do_something()
except:
    raise ValueError('Something bad happened')
    
# when we exit, we lose our traceback
try:
    do_something()
except:
    print('Something bad happened')
    sys.exit(1)

```

# Contributing

## General steps
* make branch from `main` branch
* make changes
* update TODO.md by changing color of jewel next to item you're working on
    * change to 🟡 if item is started but not completed
    * change to 🟢 if item is complete and has passing unittests
* create pull request to `main` branch

## template apps
* python - backend and frontend are in `./templates/py`
* legacy browser frontend is in `./templates/browser1`

See [TODO.md](./TODO.md) for desired template app languages/features and current progress.

#### For new languages

Create `./templates/<language>` and within it a readme file and anything needed for the application to be built and run.

Applications should keep dependencies to a bare minimum, when possible use a built in solution. Frameworks and high level abstractions should be avoided if a lower level option is available and reduces the dependency footprint. The python frontend has no deps and the backend is only dependent on a server protocol and 2 libs for passwords and cryptography. The legacy browser implementation is only dependent on a testing suite. 0 dependencies is not the goal, simplicity, lightweight and maintainable are the goals.

To the extent possible by your language the code layout should be similar to the python one. All apps (server/gui/clients) should go under one folder for the language. 

The template syntax is [documented here](./docs/MTEMPLATE_SYNTAX.md).

## browser2.0

Browser2 implementations go in `./browser2/<language>`. For languages not yet implemented, a proof of concept app should be able to render the `src/mspec/data/lingo/pages/hello-world-page.json` hello world page. Full implementations should be able to render all `src/mspec/data/lingo/pages/*` and have unittests. See the [python implementation](#run-browser-20) for an example implementation of what the product should look like.

For complete documentation on the Browser2.0 JSON page format, see **[here](./docs/LINGO_SPEC.md)**.

See [TODO.md](./TODO.md) for desired language implementation and current progress.

---
[back to top of page](#mspec)

# deploying to pypi

### install build dependencies:

    pip install -r requirements-dev.txt

### finalizing release
1. run `python -m mtemplate cache` to ensure distributed templates are up to date

1. increment version in `pyproject.toml` file

1. run full test suite `./test.sh`

### build and publish release:

1. build distributions

        python3 -m build --sdist
        python3 -m build --wheel

1. check distributions for errors

        ./build_test.py
        twine check dist/*

1. upload to pypi (will prompt for api key, no other config needed)

        twine upload dist/*