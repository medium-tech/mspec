# mspec

This project is two things: an [app generator](#app-generator) using code templating as an alternative to frameworks and [browser 2.0](#browser-20): a language independent browsing protocol designed to be a faster, safer more reliable web browsing experience. Read more about [the problem to be solved](#the-problem-this-project-solves)

⚠️ this project is currently in alpha and incomplete ⚠️

* [about this project](#mspec)
    * [app generator](#app-generator)
    * [browser 2.0](#browser-20)
    * [the problem this project aims to solve](#the-problem-this-project-solves)
* documentation
    * mtemplate
        * [app generator / spec](./docs/MTEMPLATE_SPEC.md)
        * [template extractor](./docs/MTEMPLATE_EXTRACTOR.md)
        * [template syntax](./docs/MTEMPLATE_SYNTAX.md)
    * browser2
        * [write a browser2 page](./docs/BROWSER2.md)
        * [pybrowser2 - gui client](#pybrowser2)
* [development](#development)
    * [setup dev enviro](#setup-dev-environment)
    * [run and edit template apps](#edit-and-run-template-apps)
    * [generate apps from templates](#generate-apps-from-spec-files)
    * [run and test template apps](#run-and-test-generated-apps)
    * [run browser 2.0](#run-browser-20)
* [contributing](#contributing)
* [deploying to pypi](#deploying-to-pypi)

## app generator

The `mtemplate` module in this repository can be used to [generate an app using code templating](#generate-apps-from-spec-files) based off a user supplied yaml file. The yaml file describes data models and the generated apps will have:

* a web server that has:
    * an api for CRUD ops using sqlite as a database (more db flexibility planned in the future)
    * html/js based frontend for CRUD ops
* a gui frontend
* a http client for CRUD ops against server
* a client that directly accessess the db for CRUD ops
* a cli for CRUD ops

The current proof of concept has a python backend/frontend and html/js frontend. Eventually other languages such as Go and Haskell will be supported [see TODO](./TODO.md).

The generated python app is lightweight only requiring 3 stable dependencies, and the generated html frontend has no dependencies or build/packaging process. The generated html files are served staticly from the uwsgi server that also serves the python app.

The goal of this project is to provide an alternative to frameworks. I've found over the years that frameworks have their pros and cons. **Pro:** don't have to recreate all the wheels **Con:** the abstraction hides the lower level code from the developer and dependency creep becomes a liability. If you rebuild the wheel you can adjust any level of the stack however it takes longer to see results. I think a middle ground is to generate the wheel instead of rebuild it. This means we don't have to waste time on wheels but also, devs never need to worry about this library changing versions because the generated code will always stand on its own without this library.

However, the process of editing templates is not ideal. This library also attempts to make writing templates easier by providing template exctration from syntacticly valid code. The jinja templating syntax is incompatible with Python syntax meaning the template can't be run directly to test if it works. This library embeds templating syntax into the language's comments so that the template app itself is syntacticly valid in its language.

Take the following python example:

    # vars :: {"8080": "config.port"}

    port = 8080

The `#` begins a comment and then `vars` is a command to tell the `mtemplate` extractor to set template variables. The variables are supplied in json after the `::`. The template extractor will read the above source code file and dynamically create a jinja template by replacing each instance of the string `8080` with the jinja template variable `config.port`. It will generate a file that is a valid jinja template but not valid python syntax:

    port = {{ config.port }}

The template variables are replaced with values in the yaml spec file, used to render the new app and then discarded.

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

After [setting up your dev environment](#setup-dev-environment) run the following:

    cd browser2/py/src
    ./pybrowser2.py

You can open any spec json file with this:

    ./pybrowser2.py --spec file.json

For more examples and complete documentation on creating JSON pages, see **[here](./docs/BROWSER2.md)**.

⚠️ Be careful with untrusted input as this project is still in alpha phase. ⚠️

# Development

## code layout
The `./src` folder contains two modules:

* `mtemplate` - extracts templates from template apps and using them to generate apps based on yaml definition files in `./spec`
* `mspec` - parse yaml spec files in `./spec`, parse and process browser2.0 json pages

The `./templates` folder contains template apps from which templates are extracted.

The `browser2/py` file contains the tkinter window and renderer for the browser2.0 python implementation.

## setup dev environment
This environment will be used to develop the template apps, mspec and mtemplate modules and browser2 python implementation.

    git clone https://github.com/medium-tech/mspec.git
    cd mspec
    python3 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    pip install -e .
    pip install -e templates/py

## edit and run template apps
As mentioned, the templates are extracted from working apps in `./templates`, this allows you to run the templates directly for fast development and testing. This section explains how to run the apps from which templates are extracted. If you want to change the features that generated apps have you need to edit the template apps as described in this section. If you want to learn how to generate template apps from a yaml spec go to [generate apps from spec files](#generate-apps-from-spec-files).

### python template app
Follow the setup instructions in [./templates/py/README.md](./templates/py/README.md), except use the `venv` you just setup instead of creating a separate. You can create a second `venv` but it's easier for testing to use the one that also has the other modules in this repo installed.

The readme has instructions to install deps, run the server, run the python gui and run tests.

The api and frontend are served from the same server, you can access them at `http://localhost:5005`.

### html / js gui template

The frontend files are served staticly from `./templates/browser1/srv` and can be accessed at `http://localhost:5005`. No dependencies are needed for running the frontend however `playwright` is used for testing. See [./templates/browser1/README.md](./templates/browser1/README.md) to learn how to run tests.



## generate apps from spec files

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

## test app generator

To run the app generator tests that verify the mtemplate functionality:

    ./test.sh

The tests verify that:
- The mtemplate system can generate py and browser1 apps from the test-gen.yaml spec
- Generated apps have the correct file structure and content
- Template syntax is properly resolved without errors
- Both individual and combined app generation work correctly
- Generated apps can be set up and their tests can be run

# Contributing

## General steps
* make branch from dev branch
* make changes
* update TODO.md by changing color of jewel next to item you're working on
    * change to 🟡 if item is started but not completed
    * change to 🟢 if item is complete and has passing unittests
* create pull request to dev branch

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

Browser2 implementations go in `./browser2/<language>`. For languages not yet implemented, a proof of concept app should be able to render the `src/mspec/data/hello-world-page.json` hello world page. Full implementations should be able to render `src/mspec/data/test-page.json` and have unittests. See the [python implementation](#run-browser-20) for an example implementation of what the product should look like.

For complete documentation on the Browser2.0 JSON page format, see **[here](./docs/BROWSER2.md)**.

See [TODO.md](./TODO.md) for desired language implementation and current progress.

---
[back to top of page](#mspec)

# deploying to pypi

install build and publish deps

1. increment version in `pyproject.toml` file

        pip install -r requirements-dev.txt

1. build distributions

        python3 -m build --sdist
        python3 -m build --wheel

1. check distributions for errors

        twine check dist/*

1. upload to pypi

        twine upload dist/*