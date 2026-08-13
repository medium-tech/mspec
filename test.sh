#!/bin/bash

# -h or --help: display help message
# --gui sets RUN_GUI_TESTS=1 to run GUI tests, otherwise they are skipped
# --no-gui sets RUN_GUI_TESTS=0 to skip GUI tests, otherwise they are run
# --quick-window or -qw sets QUICK_WINDOW=1 to skip querying the OS for window region, otherwise it queries the OS for window region
# --no-quick-window or -nqw sets QUICK_WINDOW=0 to query the OS for window region, otherwise it skips querying the OS for window region


# help menu function
show_help() {
	echo "Usage: $0 [options]"
	echo "Options:"
	echo "  -h, --help            		Show this help message and exit"
	echo "  --gui                 		Run GUI tests (default: skip GUI tests)"
	echo "  --no-gui              		Skip GUI tests (default: run GUI tests)"
	echo "  --quick-window, -qw   		Skip querying the OS for window region (default: query the OS for window region)"
	echo "  --no-quick-window, -nqw 	Query the OS for window region (default: skip querying the OS for window region)"

	echo "Quick window mode:"
	echo "  In quick window mode, the script will skip querying the OS for the window region and use a cached value instead."
	echo "  This can speed up tests that require window region information, but may be less reliable if the window region changes during the test run."
}




#
# parse command line arguments
#

while [[ "$1" != "" ]]; do
	case $1 in
		-h | --help )			show_help
								exit 0
								;;
		--gui )					export RUN_GUI_TESTS=1
								;;
		--no-gui )				export RUN_GUI_TESTS=0
								;;
		--quick-window | -qw )	export QUICK_WINDOW=1
								;;
		--no-quick-window | -nqw )	export QUICK_WINDOW=0
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

python -m unittest -vv