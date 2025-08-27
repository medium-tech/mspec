# template app
## browser1 - gui
This app is designed to be served by the python app in `../py`. Check out the [readme](../py/README.md) to learn how to setup and run the server. There is no additional setup needed to run this app, however, see below to learn how to install deps and use [playwright](https://playwright.dev) to test this app.

## run tests
To installing testing dependencies:

    npm install

After they are installed, to run the tests:

    npm run test

Additional commands:

* `npm run test-ui` - same as `npm run test` but with an interactive ui
* `npm run test-report` - after running tests, show playwright testing report
* `npm run test-gen` - open interactive window to generate tests