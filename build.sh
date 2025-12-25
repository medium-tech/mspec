#!/bin/bash

#
# build.sh - Build script for mspec
#

set -e

# Copy Browser2 UI files to data directory
echo 'Copying Browser2 UI files...'
mkdir -p src/mspec/data/mapp-ui/src
cp -r browser2/js/src/* src/mspec/data/mapp-ui/src/
echo 'Browser2 UI files copied successfully'
