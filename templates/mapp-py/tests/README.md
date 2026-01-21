# MAPP UI Playwright Tests

This directory contains Playwright tests for the MAPP UI framework.

## Setup

1. From the root of this repo:
   ```bash
   build.sh
   ```

1. Install dependencies:
   ```bash
   cd templates/mapp-ui
   npm install
   ```

1. Install Playwright browsers (first time only):
   ```bash
   npx playwright install
   ```

## Running Tests

### Option 1: Run tests with automatic server management

The test.sh script will start the test servers, run the tests, and shut them down:

```bash
# Start servers only (for manual testing or development)
./test.sh --servers-only

# The servers will continue running until you press Enter
# In another terminal, you can run the playwright tests:
npm test
```

### Option 2: Run tests against already running servers

If you have the servers running from `./test.sh --servers-only`, you can run the tests in a separate terminal:

```bash
npm test
```

## Environment Files

The test servers automatically create environment files in `mapp-tests/`:
- `crud.env` - Configuration for the CRUD test environment
- `pagination.env` - Configuration for the pagination test environment

These files contain the `MAPP_CLIENT_HOST` variable that the tests use to connect to the correct server.

## Development

To run tests in UI mode for debugging:
```bash
npm run test-ui
```

To view the test report:
```bash
npm run test-report
```
