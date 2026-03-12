
## edit and run template apps

⚠️ ⚠️ **WARNING** this section is outdated because the templating is being refactored ⚠️ ⚠️

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
