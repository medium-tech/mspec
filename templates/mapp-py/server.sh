
#!/bin/bash

# ===================================== #
#  mspec template: server.sh launcher   #
# ===================================== #

set -e

# Defaults
ENV_FILE=".env"
PID_FILE="app/server.pid"
CONFIG_FILE="./uwsgi.yaml"

usage() {
  echo "\nUsage: $0 [options]\n"
  echo "Options:"
  echo "  --env-file <path>     Path to .env file (default: .env)"
  echo "  --pid-file <path>     Path to PID file (default: app/server.pid)"
  echo "  --config <path>       Path to uwsgi config file (default: ./uwsgi.yaml)"
  echo "  -h, --help            Show this help message and exit\n"
  exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env-file)
      ENV_FILE="$2"
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
if [ -f "$ENV_FILE" ]; then
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
fi

# If first argument is 'stop', stop uwsgi using the pid file
if [[ "$1" == "stop" ]]; then
  uwsgi --stop "$PID_FILE"
  exit $?
else
  uwsgi --yaml "$CONFIG_FILE" --pidfile "$PID_FILE"
  exit $?
fi
