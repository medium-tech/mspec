#!/bin/bash

# -h or --help: display help message
# --gui sets RUN_GUI_TESTS=1 to run GUI tests, otherwise they are skipped
# --no-gui sets RUN_GUI_TESTS=0 to skip GUI tests, otherwise they are run
# --gui-only sets GUI_ONLY=1 (and RUN_GUI_TESTS=1) to only run GUI tests, skipping all non-GUI tests
# --quick-window or -qw sets QUICK_WINDOW=1 to skip querying the OS for window region, otherwise it queries the OS for window region
# --no-quick-window or -nqw sets QUICK_WINDOW=0 to query the OS for window region, otherwise it skips querying the OS for window region
# --setup-window queries and caches the test window region, then exits without running tests


# help menu function
show_help() {
	echo "Usage: $0 [options]"
	echo "Options:"
	echo "  -h, --help            		Show this help message and exit"
	echo "  --gui                 		Run GUI tests (default: skip GUI tests)"
	echo "  --no-gui              		Skip GUI tests (default: run GUI tests)"
	echo "  --gui-only            		Only run GUI tests, skipping all non-GUI tests (implies --gui)"
	echo "  --quick-window, -qw   		Skip querying the OS for window region (default: query the OS for window region)"
	echo "  --no-quick-window, -nqw 	Query the OS for window region (default: skip querying the OS for window region)"
	echo "  --setup-window        		Query and cache the test window region, then exit"

	echo "Quick window mode:"
	echo "  In quick window mode, the script will skip querying the OS for the window region and use a cached value instead."
	echo "  This can speed up tests that require window region information, but may be less reliable if the window region changes during the test run."
}




#
# parse command line arguments
#

# reset to defaults so re-running without flags doesn't inherit a previous run's exported env vars
export RUN_GUI_TESTS=0
export GUI_ONLY=0
export QUICK_WINDOW=0
export SETUP_WINDOW=0

while [[ "$1" != "" ]]; do
	case $1 in
		-h | --help )			show_help
								exit 0
								;;
		--gui )					export RUN_GUI_TESTS=1
								;;
		--no-gui )				export RUN_GUI_TESTS=0
								;;
		--gui-only )			export RUN_GUI_TESTS=1
								export GUI_ONLY=1
								;;
		--quick-window | -qw )	export QUICK_WINDOW=1
								;;
		--no-quick-window | -nqw )	export QUICK_WINDOW=0
								;;
		--setup-window )	export SETUP_WINDOW=1
								;;
		* )						echo "Unknown option: $1"
								show_help
								exit 1
	esac
	shift
done

#
# run tests
#

if [[ "$SETUP_WINDOW" == "1" ]]; then
	python -m tests.core
	exit $?
fi

if [[ "$GUI_ONLY" == "1" ]]; then
	python -m unittest -vv lingo.test.test_display_hello_world tests.test_mtester
else
	python -m unittest -vv
fi