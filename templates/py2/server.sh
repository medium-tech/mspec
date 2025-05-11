#!/bin/bash

# exit if .env file is not found
if [ ! -f .env ]; then
  echo ".env file not found!"
  exit 1
fi

# env vars from .env
export $(grep -v '^#' .env | xargs)

uwsgi --yaml ./dev.yaml