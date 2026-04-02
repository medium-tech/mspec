#!/bin/bash


set -e

# Usage/help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
	echo "Usage: $0 [--test-filter <pattern>] [--use-cache]"
	echo
	echo "Options:"
	echo "  --test-filter <pattern>, -f <pattern>  Only run tests matching the pattern (ex: 'test_op*')"
	echo "  --use-cache                            Use cached test resources if available"
	echo "  --help, -h                             Show this help menu"
	echo "  --npm-run                              Start test servers only, then run 'npm run <arg>', if <arg> not provided, defaults to 'npm run test'"
	echo "  --verbose, -v                          Show detailed test output"
	echo
	echo "Example:"
	echo "  $0 --test-filter test_cli_help_menus --use-cache"
	echo "  $0 -f 'test_cli_*_crud'"
	echo "  $0 --npm-run"
	echo "  $0 --npm-run test-ui"
	echo "  $0 --npm run test-gen"
	exit 0
fi

TEST_FILTERS=()
USE_CACHE=""
VERBOSE=""
NPM_RUN=""
NPM_CMD=""

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
		--npm-run)
			NPM_RUN="--npm-run"
			shift
			if [[ $# -gt 0 && ! $1 =~ ^- ]]; then
				NPM_CMD="$1"
				shift
				# else, if no command provided, default to 'test'
			else
				NPM_CMD="test"
			fi
			;;
		*)
			echo "Unknown argument: $1"
			echo "Run with --help for usage."
			exit 1
			;;
	esac
done

TF_ARGS=""
if [ "${TEST_FILTERS[*]}" != "" ]; then
    TF_ARGS="--test-filter ${TEST_FILTERS[@]}"
fi

python -m mapp.test fix-me.yaml --cmd ./run.sh --env-file .env $TF_ARGS $USE_CACHE --app-type python $VERBOSE $NPM_RUN $NPM_CMD