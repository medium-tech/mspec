#!/bin/bash

# ===================================== #
#  mspec template: server.sh launcher   #
# ===================================== #

set -e

# Defaults
ENVFILE=".env"
PID_FILE="app/server.pid"
CONFIG_FILE="./uwsgi.yaml"
STOP=false

# If ENVFILE env var is set, use it for env file path
if [ -n "$MAPP_ENV_FILE" ]; then
  ENVFILE="$MAPP_ENV_FILE"
fi

usage() {
  echo -e "\nUsage: $0 [options]\n"
  echo "Options:"
  echo "  --env-file <path>     Path to .env file (default: .env) "
  echo "                          or supply via MAPP_ENV_FILE env var"
  echo "  --pid-file <path>     Path to PID file (default: app/server.pid)"
  echo "  --config <path>       Path to uwsgi config file (default: ./uwsgi.yaml)"
  echo "  -h, --help            Show this help message and exit\n"
  exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    stop)
      STOP=true
      shift
      ;;
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

echo "Using env file: $ENVFILE"
echo "Using PID file: $PID_FILE"
echo "Using config file: $CONFIG_FILE"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"

# echo output of "which python"
echo "Using Python executable: $(which python)"

# If first argument is 'stop', stop uwsgi using the pid file
if [[ "$STOP" == true ]]; then
  uwsgi --stop "$PID_FILE"
  exit $?
else
  uwsgi --yaml "$CONFIG_FILE"
  exit $?
fi
