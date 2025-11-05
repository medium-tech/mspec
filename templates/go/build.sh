#!/usr/bin/env bash
# mtemplate :: {"scope": "app"}
set -e
echo "=== Building Go Application ==="
go build -o main main.go