#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"


resolve_python_bin() {
    if [[ -n "${LINGO_PY_BIN:-}" ]]; then
        echo "$LINGO_PY_BIN"
        return
    fi
    if [[ -n "${LINGO_BIN:-}" ]]; then
        echo "$LINGO_BIN"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        echo 'python3'
        return
    fi
    if command -v python >/dev/null 2>&1; then
        echo 'python'
        return
    fi

    echo 'error: Python executable not found (tried python3/python).' >&2
    echo "See: $README_PATH" >&2
    exit 1
}


resolve_exe_path() {
    local input_path="$1"
    if [[ "$input_path" = /* ]]; then
        echo "$input_path"
    else
        echo "$CALLER_DIR/$input_path"
    fi
}


main() {
    local command="${1:---help}"
    local py_bin

    py_bin="$(resolve_python_bin)"

    if [[ "$command" == 'build' ]]; then
        echo 'error: build is not supported for Python; run source directly.' >&2
        echo "See: $README_PATH" >&2
        exit 2
    fi

    if [[ "$command" == 'exe' && $# -ge 2 ]]; then
        local exe_path
        exe_path="$(resolve_exe_path "$2")"
        shift 2
        set -- exe "$exe_path" "$@"
    fi

    (
        cd "$SCRIPT_DIR"
        export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
        "$py_bin" -m lingolib "$@"
    )
}


main "$@"
