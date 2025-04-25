# mspec

This project is two things: an app generator using code templating as an alternative to frameworks and a protocol for defining a language independent browsing protocol.

## app generator

The `mtemplate` module in this repository can be used to generate an app using code templating based off a user supplied yaml file. The generated app has an integration with sqlite, a web server, an http client, a cli and a gui frontend. Currently only python and html/js are implemented but eventually other languages such as Go and C/C++ will be supported [see TODO](./TODO.md). There is a pure python gui using python's built in tkinter library as well as an html/js frontend.

The generated python app has 0 dependencies other than Python itself, and the generated html frontend also has no dependencies or build/packaging process. You can use the playwright depenency for testing the app, but the dep is not required for deployment. The generated html files are served staticly from the uwsgi server that also serves the python app.

The goal of this project is to provide an alternative to frameworks. I've found over the years that frameworks have their pros and cons. **Pro:** don't have to recreate all the wheels **Con:** the abstraction hides the lower level code from the developer and bloated dependencies become a liability as versions become incompatible with one other.

I believe the answer is to generate apps using code templating. This means we don't have to recreate all the wheels but also never need to worry about this library changing versions because the generated code will always stand on its own without this library.

Jinja is used for code templating (while generated apps have no deps, this library does have a couple). This library also attempts to make writing the templates easier by providing template exctration from syntacticly valid code. The jinja templating syntax is incompatible with Python syntax meaning you can't run your template directly to test if it works. Templating syntax is embedded in code comments in a working app with unittests.

The following code comment will replace the string `http://localhost:9009` with the jinja template variable `client.default_host`.

    # vars :: {"http://localhost:9009": "client.default_host"}

### how is this different than other code templating projects?
I speculate that other approaches such as openapi haven't resulted in a robust templating culture because they are too complex. Instead of focusing on abstracting everything a developer could need, this project will focus on the most common boiler plate code and a consistent developer exprience across multiple languages. If the developer needs an additional type not supported by this library then they'll have an easy way of extending the generated app, or they could just modify the generated code directly.

## browser 2.0

The browsing protocol is an attempt to make a language independency browsing protocol. Modern web pages are required to use html and can also use CSS and Javascript and/or other Javascript~ish languages like JSX and TS. But why not Go, python or C? The language stack goes: machine code -> assembly -> C -> JS -> TS -> JS. This is overengineering. You combine that with the fact that browsers are not fully compatible with one another and you get a nightmare of development and support process. The solution is to make a simpler markup language. When HTML and Javascript were created we didn't know where they were going and how they would change the world. Now that we've seen that, its time to make version 2 of the web browser. One that is language independent, more secure, faster, and doesn't let developers create all the the things that we hate about using a web browser.

This is built for the user, not the developer. I cannot stand most websites. It takes 8 seconds to load, then I have to click the cookie monster button, then I have to search for the close button on the prompt asking for my email. I finally find it and click it, but an image loaded and the button moved and I accidentally clicked another button and takes me to a different page. So then I click back and repoeat the process again. This markup protocol will be intentionally limited so that you can't fucking do that. It will force a product to be impressive on its on without flashy JS animations.

It needs to be able to accomplish everything we need the browser to do without any of the other stuff.

But it also needs to go above and beyond the web browser. This protocol will use content based addressing instead of location based addressing. The current browser is location based `github.com/path/to/my/project` ... but these urls break over time which make news articles and and written information degrade in quality over time. Content based addressing uses a file signature (checksum) to find and recall information, so that as a webpage is changed and modified over the years as long as they (or other server) continues to host the content it will always be available. This has the possibility of being as profound an improvement for the internet as the dewey decimal system was for libraries.

## how are these projects related?


### setup dev environment

    python3 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    pip install -e .
    pip install -e templates/py
