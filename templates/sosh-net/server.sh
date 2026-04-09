#!/bin/bash

# ===================================== #
#  mspec template: server.sh launcher   #
# ===================================== #

set -e

if [ ! -d "app" ]; then
  mkdir -p "app"
fi

# Defaults
ENVFILE=".env"
PID_FILE="app/server.pid"
LOG_FILE="app/server.log"
CONFIG_FILE="./uwsgi.yaml"
STOP=false
TAIL_AFTER=false

# If ENVFILE env var is set, use it for env file path
if [ -n "$MAPP_ENV_FILE" ]; then
  ENVFILE="$MAPP_ENV_FILE"
fi

usage() {
  echo -e "\nUsage: $0 <command> [options]\n"
  echo "Commands:"
  echo "  start                 Start the uwsgi server"
  echo "  stop                  Stop the uwsgi server"
  echo "  restart               Restart the uwsgi server"
  echo "  log                   Tail the uwsgi log file"
  echo "  status                Check uwsgi server status"
  echo ""
  echo "Options:"
  echo "  --log-file <path>      Path to uwsgi log file (default: app/server.log)"
  echo "  --env-file <path>     Path to .env file (default: .env) "
  echo "                          or supply via MAPP_ENV_FILE env var"
  echo "  --pid-file <path>     Path to PID file (default: app/server.pid)"
  echo "  --config <path>       Path to uwsgi config file (default: ./uwsgi.yaml)"
  echo "  --ui-src <path>      Path to MAPP UI files source directory"
  echo "                          if provided will be used to set MAPP_UI_FILE_SOURCE env var"
  echo "  --dev                 Shortcut for --ui-src ../../browser2/js/src"
  echo "  --tail                Tail log after starting or restarting the server"
  echo -e "  -h, --help            Show this help message and exit\n"

  local error_msg="$1"

  if [ -n "$error_msg" ]; then
    echo -e "\n  Error: $error_msg\n" >&2
  fi

  exit 0
}

# Parse arguments

# Require a command (start or stop)
if [[ $# -lt 1 ]]; then
  usage "Missing command"
fi

COMMAND="$1"
shift

# if COMMAND is -h or --help, show usage
if [[ "$COMMAND" == "-h" || "$COMMAND" == "--help" || "$COMMAND" == "help" ]]; then
  usage
fi

while [[ $# -gt 0 ]]; do
  case $1 in
    --log-file)
      LOG_FILE="$2"
      shift 2
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
    --dev)
      export MAPP_UI_FILE_SOURCE="../../browser2/js/src"
      shift
      ;;
    --tail)
      TAIL_AFTER=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      usage "Unknown option: $1"
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
printf "%-${COL_WIDTH}s %s\n" ":: log file"    "$LOG_FILE"
printf "%-${COL_WIDTH}s %s\n" ":: ui src" "${MAPP_UI_FILE_SOURCE:- }"
printf "%-${COL_WIDTH}s %s\n" ":: venv"       "${VIRTUAL_ENV:-}"
printf "%-${COL_WIDTH}s %s\n" ":: port" "$PORT"
printf "%-${COL_WIDTH}s %s\n" ":: local url"    "http://localhost:$PORT"
printf "%-${COL_WIDTH}s %s\n" ":: uwsgi"      "$(which uwsgi)"
printf "%-${COL_WIDTH}s %s\n" ":: python" "$(which python)"
printf "%-${COL_WIDTH}s %s\n" ":: pip "    "$(which pip)"




# --- Reusable functions for server control --- #

start_server() {
  printf "\n::\n:: starting uwsgi\n::\n\n"
  uwsgi --yaml "$CONFIG_FILE" --daemonize "$LOG_FILE"
  printf "\n\n:: uwsgi started\n\n"

  if [ "$TAIL_AFTER" = true ]; then
    printf "\n::\n:: tailing uwsgi log\n::\n\n"
    tail -f "$LOG_FILE"
  fi
}

stop_server() {
  printf "\n::\n:: stopping uwsgi\n::\n\n"
  uwsgi --stop "$PID_FILE"
  printf ":: uwsgi stopped\n\n"
}

# Returns 0 if running, 1 if stopped
is_server_running() {
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
      return 0
    fi
  fi
  return 1
}

print_server_status() {
  printf "\n::\n:: uwsgi status\n::\n\n"
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
      echo -e ":: RUNNING - uwsgi is running (pid: $PID)\n"
    else
      echo -e ":: STOPPED - uwsgi pid file exists, but process is not running\n"
    fi
  else
    echo -e ":: STOPPED - uwsgi pid file does not exist\n"
  fi
}

# --- Command dispatch --- #

case "$COMMAND" in
  status)
    print_server_status
    exit 0
    ;;
  start)
    if is_server_running; then
      printf "\n::\n:: uwsgi is already running\n::\n\n"
      exit 0
    fi
    start_server
    exit $?
    ;;
  stop)
    stop_server
    exit $?
    ;;
  restart)
    
    # call stop_server if is_server_running, otherwise just print message
    if is_server_running; then
      stop_server
    else
      printf "\n::\n:: uwsgi is not running, starting it\n::\n\n"
    fi

    # Poll for process to stop (max 10s)
    TIMEOUT=10
    INTERVAL=0.333
    ELAPSED=0
    while is_server_running; do
      if (( $(echo "$ELAPSED >= $TIMEOUT" | bc -l) )); then
        echo ":: ERROR: uwsgi did not stop after $TIMEOUT seconds. Aborting restart."
        exit 1
      fi
      sleep $INTERVAL
      ELAPSED=$(echo "$ELAPSED + $INTERVAL" | bc)
    done
    start_server
    exit $?
    ;;
  log)
    printf "\n::\n:: tailing uwsgi log\n::\n\n"
    tail -f "$LOG_FILE"
    ;;
  *)
    usage "Invalid command: $COMMAND."
    ;;
esac