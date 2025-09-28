#!/bin/bash

# ./test.sh [--quick] [--dev]

# function to print help menu
print_help() {
  echo "Usage: $0 [--quick] [--dev] [-h|--help]"
  echo ""
  echo "Options:"
  echo "  --quick    Test templates, caching, and app generatation, but don't run and test apps"
  echo "  --dev      Useful for development, tests templates, caching, and generates 1 app and runs its tests but skips exhaustive app tests"
  echo "  -h, --help Show this help message" 
}

# get arguments
QUICK_TEST=0
DEV_TEST=0

for arg in "$@"; do
  case $arg in
    --quick)
        QUICK_TEST=1
        shift
        ;;
    --dev)
        DEV_TEST=1
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

# if quick and dev are provided exit with error
if [ $QUICK_TEST -eq 1 ] && [ $DEV_TEST -eq 1 ]; then
  echo "Error: Cannot use --quick and --dev together."
  exit 1
fi

# Test runner for mspec app generator tests
QUICK_TEST=$QUICK_TEST DEV_TEST=$DEV_TEST python -m unittest discover tests -b