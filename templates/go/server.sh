#!/usr/bin/env bash
# mtemplate :: {"scope": "app"}
set -e

export MAPP_SERVER_PORT=${MAPP_SERVER_PORT}
export MAPP_DB_FILE=${MAPP_DB_FILE}

if [ "$1" == "dev" ]; then
    echo "Starting Go server in development mode..."
    exec go run main.go server
else
    # if main does not exist, build it first
    if [ ! -f ./main ]; then
        ./build.sh
    fi
    ./main server
fi