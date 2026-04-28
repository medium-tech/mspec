#!/bin/bash
# mtemplate :: {"scope": "app"}

set -e

#
# build
#

echo "Building Go binary for testing..."
go build -o main_test main.go

#
# cleanup
#

cleanup() {   
    rm -f ./main_test
}

trap cleanup EXIT INT TERM

#
# tests
#

python -m mtemplate test-spec --cmd ./main_test  --spec mapp.yaml