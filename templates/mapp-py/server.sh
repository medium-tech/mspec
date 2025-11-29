#!/bin/bash

# ===================================== #
#  mspec template: server.sh launcher   #
# ===================================== #

set -e

# Defaults
ENVFILE=".env"
PID_FILE="app/server.pid"
CONFIG_FILE="./uwsgi.yaml"

# If ENVFILE env var is set, use it for env file path
if [ -n "$ENVFILE" ]; then
  ENVFILE="$ENVFILE"
fi

usage() {
  echo "\nUsage: $0 [options]\n"
  echo "Options:"
  echo "  --env-file <path>     Path to .env file (default: .env) "
  echo "                          or supply via ENVFILE env var"
  echo "  --pid-file <path>     Path to PID file (default: app/server.pid)"
  echo "  --config <path>       Path to uwsgi config file (default: ./uwsgi.yaml)"
  echo "  -h, --help            Show this help message and exit\n"
  exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env-file)
      ENVFILE="$2"
      shift 2
      ;;
    --pid-file)
      PID_FILE="$2"
      shift 2
      ;;
    --config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

# Load environment variables if env file exists
if [ -f "$ENVFILE" ]; then
  set -o allexport
  source "$ENVFILE"
  set +o allexport
fi

# If first argument is 'stop', stop uwsgi using the pid file
if [[ "$1" == "stop" ]]; then
  uwsgi --stop "$PID_FILE"
  exit $?
else
  uwsgi --yaml "$CONFIG_FILE"
  exit $?
fi
