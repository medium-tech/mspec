#!/bin/bash

# vars :: {"test-gen.yaml": "context.spec_path"}

set -e

python -m mtemplate test-spec --cmd ./run.sh  --spec test-gen.yaml --env-file .env
