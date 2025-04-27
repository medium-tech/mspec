# mspec

This project is two things: an [app generator](#app-generator) using code templating as an alternative to frameworks and [browser 2.0](#browser-20): a protocol for defining a language independent browsing protocol.

🚨 this project is currently in alpha and incomplete 🚨

## app generator

The `mtemplate` module in this repository can be used to generate an app using code templating based off a user supplied yaml file. The generated app has an integration with sqlite, a web server, an http client, a cli and a gui frontend. Currently only python and html/js are implemented but eventually other languages such as Go and C/C++ will be supported [see TODO](./TODO.md). There is a pure python gui using python's built in tkinter library as well as an html/js frontend.

The generated python app has 0 dependencies other than Python itself, and the generated html frontend also has no dependencies or build/packaging process. The generated html files are served staticly from the uwsgi server that also serves the python app.

The goal of this project is to provide an alternative to frameworks. I've found over the years that frameworks have their pros and cons. **Pro:** don't have to recreate all the wheels **Con:** the abstraction hides the lower level code from the developer and bloated dependencies become a liability as versions become incompatible with one other.

I believe the answer is to generate apps using code templating. This means we don't have to recreate all the wheels but also never need to worry about this library changing versions because the generated code will always stand on its own without this library.

Jinja is used for code templating (while generated apps have no deps, this library does have a couple). This library also attempts to make writing the templates easier by providing template exctration from syntacticly valid code. The jinja templating syntax is incompatible with Python syntax meaning you can't run your template directly to test if it works. Templating syntax is embedded in code comments in a working app with unittests.

Take the following example:

    # vars :: {"hello.world": "template_variable"}

    my_variable = 'hello.world'

The template extractor will read the source code file and dynamically create a jinja template by replacing each instance of the string `http://localhost:9009` with the jinja template variable `client.default_host`. It will generate a valid jinja template that looks like this:

    my_variable = '{{ template_variable }}'

### how is this different than other code templating projects?
I speculate that other approaches such as openapi haven't resulted in a robust templating culture because they are too complex. Instead of focusing on abstracting everything a developer could possibly need, this project will focus on the most common boiler plate code and a consistent developer exprience across multiple languages. If you generate an app with a Go backend an a python GUI and JS webpage the apps will all be laid out similarly reducing the learning curve. If the developer needs an additional types not supported by this library then they'll have an easy way of extending the generated app, or they could just modify the generated code directly.

## browser 2.0

The browsing protocol is an attempt to make a language independency browsing protocol. Modern web pages are required to use html and can also use CSS and Javascript and/or other Javascript~ish languages like JSX and TS. But why not Go, python or Rust? The language stack goes: machine code -> assembly -> C -> JS -> TS -> JS. This u-turn is overengineering. You combine that with the fact that browsers are not fully compatible with one another and you get a nightmare of development and support process. The solution is to make a simpler markup language. When HTML and Javascript were created we didn't know where they were going and how they would change the world. Now that we've seen that, its time to make version 2 of the web browser. One that is language independent, more secure, faster, and doesn't let developers create all the the things that we hate about using a web browser.

This is built for the user, not the developer. I cannot stand most websites. It takes 8 seconds to load, then I have to click the cookie monster button, then I have to search for the close button on the prompt asking for my email. I finally find it and click it, but an image loaded and the button moved and I accidentally clicked another button and takes me to a different page. So then I click back and repeat the process again. This markup protocol will be intentionally limited so that you can't fucking do that. It will force a product to be impressive on its on without flashy JS animations.

It needs to be able to accomplish everything we need the browser to do without any of the other stuff. What the user actually needs is different than what the developer and marketing teams believe the user needs.

But it also needs to go above and beyond the web browser.

### speed and reliability

...

### security and privacy

...

### content based addressing
Browser2.0 will use content based addressing instead of location based addressing. The current browser is location based `github.com/path/to/my/project` ... but these urls break over time which make news articles and and written information degrade in quality over time. Content based addressing uses a file signature (checksum) to find and recall information, so that as a webpage is changed and modified over the years as long as they (or other server) continues to host the content it will always be discoverable. This has the possibility of being as profound an improvement for the internet as the dewey decimal system was for libraries.

# Development

## code layout
The `./src` folder contains three modules:

* `mtemplate` - extracts templates from template apps and using them to generate apps based on yaml definition files in `./spec`
* `mspec` - parse yaml spec files in `./spec`
* `lingo` - markup language and `tkinter` gui renderer for browser2.0

The `./templates` folder contains template apps from which templates are extracted.

## setup dev environment

    python3 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    pip install -e .
    pip install -e templates/py

## template apps

The templating system enables you to create the following by defining a simple yaml file:
* web server that has:
    * an api for CRUD ops using sqlite as a database (more db flexibility planned in the future)
    * html/js based frontend for CRUD ops
* python gui frontend
* python http client for CRUD ops
* python client that directly accessess the db for CRUD ops
* cli for CRUD ops

The yaml config currently is not documented as it is expected to change, but you can look at `./spec/test-gen.yaml` for a workin' example.

As mentioned, the templates are extracted from working apps in `./templates`, this allows you to run the templates directly for fast development and testing. The template extraction syntax is embedded into code comments to allow the template apps to run on their own, this syntax is not currently documented.

### run the python server

    cd templates/py

Create a file `.env` file with the following variables:

    MSTACK_AUTH_SECRET_KEY=my_auth_key
    UWSGI_STATIC_SAFE=/path/to/static/files

`MSTACK_AUTH_SECRET_KEY` - an auth key can be generated using a command like: `openssl rand -hex 32`

`UWSGI_STATIC_SAFE` - uwsgi requires static files be configured with **absolute paths** for security reasons. However, the uwsgi config in this project uses relative paths for portability. By setting this value to the **absolute path** on your local system that points to the `templates/html/srv` directory in this repository will allow the relative paths to work.

Then run the following command to start the web server:

    ./server.sh 

It uses `uwsgi` as the server, the main entry point for the web server is `./src/core/server.py`, and the config file is `./dev.yaml`.

The api and frontend are served from the same server, you can access them at `http://localhost:9009`.

To run unittests for the python backend, ensure the backend is running and then:

    ./test.sh

### html / js frontend

The frontend files are served staticly from `templates/html/srv` and can be accessed at `http://localhost:9009`. No dependencies are needed for running the frontend however `playwright` is used for testing.

To run frontend tests, ensure the backend is running and then from the `templates/html` directory:

    npm install
    npm run test

Alternatively, you can run the tests with a ui:

    npm run test-ui

Additionally, playwright provides a gui to help interactively create tests, you can access it using:

    npm run test-gen

### python frontend

There is a (currently incomplete) front end implemented in python using the built in `tkinter` library. To run it:

    python -m core gui

## generate apps from spec files

    ... 

## run and test generated apps

    ...

## run browser 2.0

    ...

