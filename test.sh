#!/bin/bash

# function to print help menu
print_help() {
  echo "Usage: $0 [--quick] [--templates] [--dev] [--cli] [--markup] [-h|--help]"
  echo ""
  echo "Options:"
  echo "  --quick       Test template extraction, caching, and app generation, but don't run and test apps"
  echo "  --templates   Test template extraction, caching, and app generation, run server and tests for template source apps only"
  echo "  --dev         Useful for development, tests templates, caching, and runs 1 app and its tests but skips exhaustive app running"
  echo "  --cli         Only run CLI tests"
  echo "  --markup      Only run Markup tests"
  echo "  -h, --help    Show this help message"
}

# get arguments
QUICK_TEST=0
TEMPLATE_TEST=0
DEV_TEST=0
CLI_TEST=0
MARKUP_TEST=0

for arg in "$@"; do
  case $arg in
    --quick)
        QUICK_TEST=1
        shift
        ;;
    --templates)
        TEMPLATE_TEST=1
        shift
        ;;
    --dev)
        DEV_TEST=1
        shift
        ;;
    --cli)
        CLI_TEST=1
        shift
        ;;
    --markup)
        MARKUP_TEST=1
        shift
        ;;
    -h|--help)
        print_help
        exit 0
        ;;
    *)
        echo "Unknown option: $arg"
        exit 1
        shift
      ;;
  esac
done

# can only run one of quick/dev/template modes
# add each variable together and ensure the sum is <= 1
MODE_SUM=$((QUICK_TEST + TEMPLATE_TEST + DEV_TEST + CLI_TEST + MARKUP_TEST))
if [ $MODE_SUM -gt 1 ]; then
  echo "Error: Only one of --quick, --templates, --dev, --cli, or --markup can be specified at a time."
  exit 1
fi

TESTS="discover"

# if CLI_TEST then
if [ $CLI_TEST -eq 1 ]; then
  TESTS="tests.test_cli"
fi

# if MARKUP_TEST then
if [ $MARKUP_TEST -eq 1 ]; then
  TESTS="tests.test_markup"
fi

# echo "Running tests with settings - QUICK_TEST: $QUICK_TEST, TEMPLATE_TEST: $TEMPLATE_TEST, DEV_TEST: $DEV_TEST, CLI_TEST: $CLI_TEST, MARKUP_TEST: $MARKUP_TEST"
# echo "Running tests in: $TESTS"

# Test runner for mspec app generator tests
QUICK_TEST=$QUICK_TEST DEV_TEST=$DEV_TEST TEMPLATE_TEST=$TEMPLATE_TEST python -m unittest "$TESTS"