#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"
DEFAULT_BIN="$SCRIPT_DIR/lingolib"
VERBOSE=0
RUN_MODE_OVERRIDE=''


log_debug() {
    if [[ "$VERBOSE" == '1' ]]; then
        echo ":: DEBUG :: $*" >&2
    fi
}


parse_wrapper_flags() {
    local parsed=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose|-v)
                VERBOSE=1
                shift
                ;;
            --run-mode)
                if [[ $# -lt 2 ]]; then
                    echo 'error: --run-mode requires a value (dev|built)' >&2
                    exit 1
                fi
                RUN_MODE_OVERRIDE="$2"
                shift 2
                ;;
            -r)
                if [[ $# -lt 2 ]]; then
                    echo 'error: -r requires a value (dev|built)' >&2
                    exit 1
                fi
                RUN_MODE_OVERRIDE="$2"
                shift 2
                ;;
            --run-mode=*)
                RUN_MODE_OVERRIDE="${1#--run-mode=}"
                shift
                ;;
            --)
                shift
                parsed+=("$@")
                break
                ;;
            *)
                parsed+=("$1")
                shift
                ;;
        esac
    done

    set -- "${parsed[@]}"
    WRAPPER_ARGS=("$@")
}


resolve_exe_path() {
    local input_path="$1"
    if [[ "$input_path" = /* ]]; then
        echo "$input_path"
    else
        echo "$CALLER_DIR/$input_path"
    fi
}


resolve_run_mode() {
    if [[ -n "$RUN_MODE_OVERRIDE" ]]; then
        log_debug "Using command-line run mode override: $RUN_MODE_OVERRIDE"
        echo "$RUN_MODE_OVERRIDE"
        return
    fi

    log_debug 'Checking environment variable LINGO_GO_RUN_MODE'
    if [[ -n "${LINGO_GO_RUN_MODE:-}" ]]; then
        log_debug "Using LINGO_GO_RUN_MODE: $LINGO_GO_RUN_MODE"
        echo "$LINGO_GO_RUN_MODE"
        return
    fi

    log_debug 'Checking environment variable LINGO_RUN_MODE'
    if [[ -n "${LINGO_RUN_MODE:-}" ]]; then
        log_debug "Using LINGO_RUN_MODE fallback: $LINGO_RUN_MODE"
        echo "$LINGO_RUN_MODE"
        return
    fi

    log_debug 'No run mode env var set; defaulting to dev'
    echo 'dev'
}


resolve_binary_path() {
    log_debug 'Checking environment variable LINGO_GO_BIN'
    if [[ -n "${LINGO_GO_BIN:-}" ]]; then
        log_debug "Using LINGO_GO_BIN: $LINGO_GO_BIN"
        echo "$LINGO_GO_BIN"
        return
    fi

    log_debug 'Checking environment variable LINGO_BIN'
    if [[ -n "${LINGO_BIN:-}" ]]; then
        log_debug "Using LINGO_BIN fallback: $LINGO_BIN"
        echo "$LINGO_BIN"
        return
    fi

    log_debug "Using default Go binary path: $DEFAULT_BIN"
    echo "$DEFAULT_BIN"
}


run_dev() {
    log_debug 'Execution mode selected: dev (go run)'
    log_debug 'Checking PATH for go toolchain'
    if ! command -v go >/dev/null 2>&1; then
        log_debug 'Go toolchain not found on PATH'
        echo 'error: Go toolchain not found (expected `go` on PATH).' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi

    log_debug 'Go toolchain found; running go run ./cmd/lingolib'
    log_debug "Executing: go run ./cmd/lingolib $*"

    (
        cd "$SCRIPT_DIR"
        go run ./cmd/lingolib "$@"
    )
}


run_built() {
    local bin_path
    bin_path="$(resolve_binary_path)"

    log_debug 'Execution mode selected: built (prebuilt binary)'
    log_debug "Resolved built binary path: $bin_path"

    if [[ ! -x "$bin_path" ]]; then
        log_debug 'Built binary missing or not executable'
        echo "error: built binary not found or not executable: $bin_path" >&2
        echo 'hint: run `./lingo.sh build` or set LINGO_GO_BIN to a valid binary path.' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi

    log_debug "Executing prebuilt binary: $bin_path $*"

    "$bin_path" "$@"
}


build_binary() {
    log_debug 'Build command requested'
    log_debug 'Checking PATH for go toolchain'
    if ! command -v go >/dev/null 2>&1; then
        log_debug 'Go toolchain not found on PATH'
        echo 'error: Go toolchain not found (expected `go` on PATH).' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi

    local bin_path
    bin_path="$(resolve_binary_path)"

    log_debug "Build output binary path: $bin_path"
    log_debug "Executing build: go build -o $bin_path ./cmd/lingolib"

    (
        cd "$SCRIPT_DIR"
        go build -o "$bin_path" ./cmd/lingolib
    )
}


main() {
    parse_wrapper_flags "$@"
    set -- "${WRAPPER_ARGS[@]}"

    local command="${1:---help}"
    local run_mode

    log_debug "Wrapper cwd: $CALLER_DIR"
    log_debug "Wrapper script dir: $SCRIPT_DIR"

    if [[ "$command" == 'build' ]]; then
        build_binary
        exit 0
    fi

    if [[ "$command" == 'exe' && $# -ge 2 ]]; then
        local exe_path
        log_debug "Resolving exe path argument: $2"
        exe_path="$(resolve_exe_path "$2")"
        log_debug "Resolved exe path: $exe_path"
        shift 2
        set -- exe "$exe_path" "$@"
    fi

    run_mode="$(resolve_run_mode)"
    log_debug "Selected run mode: $run_mode"
    case "$run_mode" in
        dev)
            run_dev "$@"
            ;;
        built)
            run_built "$@"
            ;;
        *)
            echo "error: invalid run mode: $run_mode (expected dev|built)" >&2
            exit 1
            ;;
    esac
}


main "$@"
