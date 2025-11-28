#!/bin/bash

# vars :: {"test-gen.yaml": "context.spec_path"}

set -e

# Usage/help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
	echo "Usage: $0 [--test-filter <pattern>] [--use-cache]"
	echo
	echo "Options:"
	echo "  --test-filter <pattern>, -f <pattern>  Only run tests matching the pattern (e.g. test_cli_help_menus)"
	echo "  --use-cache                            Use cached test resources if available"
	echo "  --help, -h                             Show this help menu"
	echo
	echo "Example:"
	echo "  $0 --test-filter test_cli_help_menus --use-cache"
	exit 0
fi

TEST_FILTER=""
USE_CACHE=""

while [[ $# -gt 0 ]]; do
	case $1 in
		--test-filter|-f)
			TEST_FILTER="--test-filter $2"
			shift 2
			;;
		--use-cache)
			USE_CACHE="--use-cache"
			shift
			;;
		*)
			echo "Unknown argument: $1"
			echo "Run with --help for usage."
			exit 1
			;;
	esac
done

python -m mapp.test test-gen.yaml --cmd ./run.sh --env-file .env $TEST_FILTER $USE_CACHE
