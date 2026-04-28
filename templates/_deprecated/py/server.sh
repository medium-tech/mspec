#!/bin/bash

# exit if .env file is not found
if [ ! -f .env ]; then
  echo ".env file not found!"
  exit 1
fi

# env vars from .env
export $(grep -v '^#' .env | xargs)

# if arg 'stop' is given, stop the server, else start it
if [ "$1" == "stop" ]; then
  uwsgi --stop src/core/server.pid
else
  uwsgi --yaml ./dev.yaml
fi