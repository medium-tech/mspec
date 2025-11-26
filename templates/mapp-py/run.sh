#!/bin/bash

# vars :: {"../../.venv/bin/python": "context.python_executable"}

# Use MAPP_ENV_FILE if set, otherwise default to .env
ENVFILE="${MAPP_ENV_FILE:-.env}"

if [ ! -f "$ENVFILE" ]; then
  echo "$ENVFILE file not found! Set MAPP_ENV_FILE to specify .env path, or use .env by default."
  exit 1
fi

set -a
. "$ENVFILE"
set +a

# Split MAPP_COMMAND into an array
read -ra CMD_ARR <<< "$MAPP_COMMAND"
# Run the command with all script arguments
"${CMD_ARR[@]}" "$@"
