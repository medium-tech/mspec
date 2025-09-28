#!/bin/bash

# ./test.sh [--quick] [--full]

# function to print help menu
print_help() {
  echo "Usage: $0 [--quick] [--full]"
  echo ""
  echo "Options:"
  echo "  --quick    Run a quick set of tests"
  echo "  --full     Run the full set of tests (for before a release)"
  echo "  -h, --help Show this help message"
}

# get arguments
QUICK_TEST=0
FULL_TEST=0

for arg in "$@"; do
  case $arg in
    --quick)
      QUICK_TEST=1
      shift
      ;;
    --full)
      FULL_TEST=1
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      shift
      ;;
  esac
done

# if quick and full are provided exit with error
if [ $QUICK_TEST -eq 1 ] && [ $FULL_TEST -eq 1 ]; then
  echo "Error: Cannot use --quick and --full together."
  exit 1
fi

# Test runner for mspec app generator tests
QUICK_TEST=$QUICK_TEST FULL_TEST=$FULL_TEST python -m unittest discover tests -b