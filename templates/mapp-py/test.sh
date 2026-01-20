#!/bin/bash

# vars :: {"test-gen.yaml": "context.spec_path"}

set -e

# Usage/help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
	echo "Usage: $0 [--test-filter <pattern>] [--use-cache] [--servers-only]"
	echo
	echo "Options:"
	echo "  --test-filter <pattern>, -f <pattern>  Only run tests matching the pattern (ex: 'test_op*')"
	echo "  --use-cache                            Use cached test resources if available"
	echo "  --servers-only                         Start servers only without running Python tests"
	echo "  --help, -h                             Show this help menu"
	echo "  --verbose, -v                          Show detailed test output"
	echo
	echo "Example:"
	echo "  $0 --test-filter test_cli_help_menus --use-cache"
	echo "  $0 -f 'test_cli_*_crud'"
	echo "  $0 --servers-only"
	exit 0
fi

TEST_FILTERS=()
USE_CACHE=""
VERBOSE=""
SERVERS_ONLY=false

while [[ $# -gt 0 ]]; do
	case $1 in
		--test-filter|-f)
			shift
			while [[ $# -gt 0 && ! $1 =~ ^- ]]; do
				TEST_FILTERS+=("$1")
				shift
			done
			;;
		--verbose|-v)
			VERBOSE="--verbose"
			shift
			;;
		--use-cache)
			USE_CACHE="--use-cache"
			shift
			;;
		--servers-only)
			SERVERS_ONLY=true
			shift
			;;
		*)
			echo "Unknown argument: $1"
			echo "Run with --help for usage."
			exit 1
			;;
	esac
done

TF_ARGS=""
if [[ ${#TEST_FILTERS[@]} -gt 0 ]]; then
	TF_ARGS="--test-filter ${TEST_FILTERS[@]}"
fi

if [ "$SERVERS_ONLY" = true ]; then
	# Start servers only mode - setup and start servers for UI testing
	echo "Starting servers for UI testing..."
	python start_test_servers.py $USE_CACHE
else
	# Normal test execution
	python -m mapp.test dev-app.yaml --cmd ./run.sh --env-file .env $TF_ARGS $USE_CACHE --app-type python $VERBOSE
fi
