#!/bin/bash

# vars :: {"test-gen.yaml": "context.spec_path"}

set -e

python -m mapp.test test-gen.yaml --cmd ./run.sh --env-file .env --test-filter "test_cli_help_menus" --use-cache
