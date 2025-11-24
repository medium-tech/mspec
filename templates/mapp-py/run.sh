#!/bin/bash

# vars :: {"../../.venv/bin/python": "context.python_executable"}

# exit if .env file is not found
if [ ! -f .env ]; then
  echo ".env file not found!"
  exit 1
fi

# env vars from .env
export $(grep -v '^#' .env | xargs)

# pass all remaining args to mapp
../../.venv/bin/python -m mapp "$@"