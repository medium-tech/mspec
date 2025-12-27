#!/bin/bash

#
# build.sh - Build script for mspec
#

set -e

# Copy Browser2 UI files to data directory (excluding index.html)
echo 'Copying Browser2 UI files...'
mkdir -p src/mspec/data/mapp-ui/src
cp browser2/js/src/markup.js src/mspec/data/mapp-ui/src/
cp browser2/js/src/style.css src/mspec/data/mapp-ui/src/
echo 'Browser2 UI files copied successfully'
