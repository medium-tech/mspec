#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"
VERBOSE=0


log_debug() {
    if [[ "$VERBOSE" == '1' ]]; then
        echo ":: DEBUG :: $*" >&2
    fi
}


parse_wrapper_flags() {
    local parsed=()
    local arg

    for arg in "$@"; do
        case "$arg" in
            --verbose|-v)
                VERBOSE=1
                ;;
            *)
                parsed+=("$arg")
                ;;
        esac
    done

    set -- "${parsed[@]}"
    WRAPPER_ARGS=("$@")
}


resolve_python_bin() {
    log_debug 'Checking environment variable LINGO_PY_BIN'
    if [[ -n "${LINGO_PY_BIN:-}" ]]; then
        log_debug "Using LINGO_PY_BIN: $LINGO_PY_BIN"
        echo "$LINGO_PY_BIN"
        return
    fi

    log_debug 'Checking environment variable LINGO_BIN'
    if [[ -n "${LINGO_BIN:-}" ]]; then
        log_debug "Using LINGO_BIN fallback: $LINGO_BIN"
        echo "$LINGO_BIN"
        return
    fi

    log_debug 'Checking PATH for python3'
    if command -v python3 >/dev/null 2>&1; then
        log_debug 'Using python3 from PATH'
        echo 'python3'
        return
    fi

    log_debug 'Checking PATH for python'
    if command -v python >/dev/null 2>&1; then
        log_debug 'Using python from PATH'
        echo 'python'
        return
    fi

    log_debug 'No usable Python executable found'
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
    parse_wrapper_flags "$@"
    set -- "${WRAPPER_ARGS[@]}"

    local command="${1:---help}"
    local py_bin

    log_debug "Wrapper cwd: $CALLER_DIR"
    log_debug "Wrapper script dir: $SCRIPT_DIR"
    log_debug 'Run mode: source (python module execution)'

    py_bin="$(resolve_python_bin)"
    log_debug "Selected Python binary: $py_bin"

    if [[ "$command" == 'build' ]]; then
        log_debug 'Build command requested (unsupported for Python wrapper)'
        echo 'error: build is not supported for Python; run source directly.' >&2
        echo "See: $README_PATH" >&2
        exit 2
    fi

    if [[ "$command" == 'exe' && $# -ge 2 ]]; then
        local exe_path
        log_debug "Resolving exe path argument: $2"
        exe_path="$(resolve_exe_path "$2")"
        log_debug "Resolved exe path: $exe_path"
        shift 2
        set -- exe "$exe_path" "$@"
    fi

    (
        cd "$SCRIPT_DIR"
        export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
        log_debug "Set PYTHONPATH: $PYTHONPATH"
        log_debug "Executing: $py_bin -m lingolib $*"
        "$py_bin" -m lingolib "$@"
    )
}


main "$@"
