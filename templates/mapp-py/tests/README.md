# Playwright Tests for MAPP UI

This directory contains Playwright tests for the MAPP UI.

## Setup

First, make sure you've run the build script from the root of the repository:

```bash
cd /path/to/mspec
./build.sh
```

Then install the Playwright dependencies:

```bash
cd templates/mapp-py
npm install
npx playwright install
```

## Running Tests

### Start the Test Servers

The tests require two servers running (crud and pagination environments). Start them with:

```bash
./test.sh --servers-only
```

This will:
1. Create the test databases
2. Seed the databases with test data
3. Start servers on ports defined in `mapp-tests/crud.env` and `mapp-tests/pagination.env`
4. Keep the servers running until you press Ctrl+C

The environment files will be created in the `mapp-tests/` directory with the `MAPP_CLIENT_HOST` variable set for each environment.

### Run the Playwright Tests

In a separate terminal, run the tests:

```bash
npm test
```

Or to run with the Playwright UI:

```bash
npm run test-ui
```

## Test Structure

- `setup.js` - Helper functions to load environment variables from `.env` files
- `spec.spec.js` - Tests for loading the spec from different environments

## Environment Files

The `--servers-only` mode creates two environment files:

- `mapp-tests/crud.env` - Configuration for the CRUD test environment
- `mapp-tests/pagination.env` - Configuration for the pagination test environment

Each file contains the `MAPP_CLIENT_HOST` variable that points to the respective server.
