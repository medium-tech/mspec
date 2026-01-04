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
  echo "  --ui-src <path>      Path to MAPP UI files source directory"
  echo "                          if provided will be used to set MAPP_UI_FILE_SOURCE env var"
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
    --ui-src)
      export MAPP_UI_FILE_SOURCE="$2"
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

PORT=$(grep '^[[:space:]]*http:' "$CONFIG_FILE" | sed -E 's/.*http:[[:space:]]*:[[:space:]]*([0-9]+).*/\1/')

# Set column width for printf (default: 20, override with COL_WIDTH env var)
COL_WIDTH="${COL_WIDTH:-16}"

printf "\n::\n:: init mapp environment\n::\n\n"

printf "%-${COL_WIDTH}s %s\n" ":: env file"   "$ENVFILE"
printf "%-${COL_WIDTH}s %s\n" ":: pid file"   "$PID_FILE"
printf "%-${COL_WIDTH}s %s\n" ":: config file" "$CONFIG_FILE"
printf "%-${COL_WIDTH}s %s\n" ":: ui src" "${MAPP_UI_FILE_SOURCE:- }"
printf "%-${COL_WIDTH}s %s\n" ":: venv"       "${VIRTUAL_ENV:-}"
printf "%-${COL_WIDTH}s %s\n" ":: port" "$PORT"
printf "%-${COL_WIDTH}s %s\n" ":: local url"    "http://localhost:$PORT"
printf "%-${COL_WIDTH}s %s\n" ":: uwsgi"      "$(which uwsgi)"
printf "%-${COL_WIDTH}s %s\n" ":: python" "$(which python)"
printf "%-${COL_WIDTH}s %s\n" ":: pip "    "$(which pip)"

# If first argument is 'stop', stop uwsgi using the pid file
if [[ "$STOP" == true ]]; then
  printf "\n::\n:: stopping uwsgi\n::\n\n"
  uwsgi --stop "$PID_FILE"
  exit $?
else
  printf "\n::\n:: starting uwsgi\n::\n\n"
  uwsgi --yaml "$CONFIG_FILE"
  exit $?
fi
