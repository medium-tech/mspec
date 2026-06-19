#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"
VERBOSE=0


log_info() {
    if [[ "$VERBOSE" == '1' ]]; then
        echo ":: INFO :: $*" >&2
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
    log_info 'Checking environment variable LINGO_PY_BIN'
    if [[ -n "${LINGO_PY_BIN:-}" ]]; then
        log_info "Using LINGO_PY_BIN: $LINGO_PY_BIN"
        echo "$LINGO_PY_BIN"
        return
    fi

    log_info 'Checking environment variable LINGO_BIN'
    if [[ -n "${LINGO_BIN:-}" ]]; then
        log_info "Using LINGO_BIN fallback: $LINGO_BIN"
        echo "$LINGO_BIN"
        return
    fi

    log_info 'Checking PATH for python3'
    if command -v python3 >/dev/null 2>&1; then
        log_info 'Using python3 from PATH'
        echo 'python3'
        return
    fi

    log_info 'Checking PATH for python'
    if command -v python >/dev/null 2>&1; then
        log_info 'Using python from PATH'
        echo 'python'
        return
    fi

    log_info 'No usable Python executable found'
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

    log_info "Wrapper cwd: $CALLER_DIR"
    log_info "Wrapper script dir: $SCRIPT_DIR"
    log_info 'Run mode: source (python module execution)'

    py_bin="$(resolve_python_bin)"
    log_info "Selected Python binary: $py_bin"

    if [[ "$command" == 'build' ]]; then
        log_info 'Build command requested (unsupported for Python wrapper)'
        echo 'error: build is not supported for Python; run source directly.' >&2
        echo "See: $README_PATH" >&2
        exit 2
    fi

    if [[ "$command" == 'exe' && $# -ge 2 ]]; then
        local exe_path
        log_info "Resolving exe path argument: $2"
        exe_path="$(resolve_exe_path "$2")"
        log_info "Resolved exe path: $exe_path"
        shift 2
        set -- exe "$exe_path" "$@"
    fi

    (
        cd "$SCRIPT_DIR"
        export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
        log_info "Set PYTHONPATH: $PYTHONPATH"
        log_info "Executing: $py_bin -m lingolib $*"
        "$py_bin" -m lingolib "$@"
    )
}


main "$@"
