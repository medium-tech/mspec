#!/bin/bash 

# help menu
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  echo "Usage: test.sh [--debug]"
  echo ""
  echo "Options:"
  echo "  --debug    Run tests in debug mode (do not clean up test directories after tests)"
  exit 0
fi

# set debug flag if provided as arg
if [[ "$1" == "--debug" ]]; then
  DEBUG_TESTS=1
else
  DEBUG_TESTS=0
fi

# Test runner for mspec app generator tests
DEBUG_TESTS=$DEBUG_TESTS python -m unittest discover tests -v