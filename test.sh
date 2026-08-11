#!/bin/bash

# if --gui is passed, run the GUI tests, otherwise skip them
if [[ "$1" == "--gui" ]]; then
	export RUN_GUI_TESTS=1
fi

python -m unittest