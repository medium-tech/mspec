#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"
VERBOSE=0
RUN_MODE_OVERRIDE=''


log_info() {
    if [[ "$VERBOSE" == '1' ]]; then
        echo ":: INFO :: $*" >&2
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
        log_info "Using command-line run mode override: $RUN_MODE_OVERRIDE"
        echo "$RUN_MODE_OVERRIDE"
        return
    fi

    log_info 'Checking environment variable LINGO_HS_RUN_MODE'
    if [[ -n "${LINGO_HS_RUN_MODE:-}" ]]; then
        log_info "Using LINGO_HS_RUN_MODE: $LINGO_HS_RUN_MODE"
        echo "$LINGO_HS_RUN_MODE"
        return
    fi

    log_info 'Checking environment variable LINGO_RUN_MODE'
    if [[ -n "${LINGO_RUN_MODE:-}" ]]; then
        log_info "Using LINGO_RUN_MODE fallback: $LINGO_RUN_MODE"
        echo "$LINGO_RUN_MODE"
        return
    fi

    log_info 'No run mode env var set; defaulting to dev'
    echo 'dev'
}


require_cabal() {
    log_info 'Checking PATH for cabal'
    if ! command -v cabal >/dev/null 2>&1; then
        log_info 'cabal not found on PATH'
        echo 'error: cabal not found (install via GHCup or package manager).' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi
}


resolve_binary_path() {
    log_info 'Checking environment variable LINGO_HS_BIN'
    if [[ -n "${LINGO_HS_BIN:-}" ]]; then
        log_info "Using LINGO_HS_BIN: $LINGO_HS_BIN"
        echo "$LINGO_HS_BIN"
        return
    fi

    log_info 'Checking environment variable LINGO_BIN'
    if [[ -n "${LINGO_BIN:-}" ]]; then
        log_info "Using LINGO_BIN fallback: $LINGO_BIN"
        echo "$LINGO_BIN"
        return
    fi

    require_cabal
    log_info 'Resolving binary via cabal list-bin lingolib'
    (
        cd "$SCRIPT_DIR"
        cabal list-bin lingolib
    )
}


build_binary() {
    log_info 'Build command requested'
    require_cabal
    log_info 'Executing build: cabal build'

    (
        cd "$SCRIPT_DIR"
        cabal build
    )
}


run_dev() {
    log_info 'Execution mode selected: dev (cabal run)'
    require_cabal
    log_info "Executing: cabal run lingolib -- $*"

    (
        cd "$SCRIPT_DIR"
        cabal run lingolib -- "$@"
    )
}


run_built() {
    local bin_path
    bin_path="$(resolve_binary_path)"

    log_info 'Execution mode selected: built (resolved binary)'
    log_info "Resolved binary path: $bin_path"

    if [[ ! -x "$bin_path" ]]; then
        log_info 'Resolved binary missing or not executable'
        echo "error: built binary not found or not executable: $bin_path" >&2
        echo 'hint: run `./lingo.sh build` or set LINGO_HS_BIN to a valid binary path.' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi

    log_info "Executing prebuilt binary: $bin_path $*"
    "$bin_path" "$@"
}


main() {
    parse_wrapper_flags "$@"
    set -- "${WRAPPER_ARGS[@]}"

    local command="${1:---help}"
    local run_mode

    log_info "Wrapper cwd: $CALLER_DIR"
    log_info "Wrapper script dir: $SCRIPT_DIR"

    if [[ "$command" == 'build' ]]; then
        build_binary
        exit 0
    fi

    if [[ "$command" == 'exe' && $# -ge 2 ]]; then
        local exe_path
        log_info "Resolving exe path argument: $2"
        exe_path="$(resolve_exe_path "$2")"
        log_info "Resolved exe path: $exe_path"
        shift 2
        set -- exe "$exe_path" "$@"
    fi

    run_mode="$(resolve_run_mode)"
    log_info "Selected run mode: $run_mode"
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
