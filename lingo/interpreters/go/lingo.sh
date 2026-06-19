#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"
DEFAULT_BIN="$SCRIPT_DIR/lingolib"


resolve_exe_path() {
    local input_path="$1"
    if [[ "$input_path" = /* ]]; then
        echo "$input_path"
    else
        echo "$CALLER_DIR/$input_path"
    fi
}


resolve_run_mode() {
    if [[ -n "${LINGO_GO_RUN_MODE:-}" ]]; then
        echo "$LINGO_GO_RUN_MODE"
        return
    fi
    if [[ -n "${LINGO_RUN_MODE:-}" ]]; then
        echo "$LINGO_RUN_MODE"
        return
    fi
    echo 'dev'
}


resolve_binary_path() {
    if [[ -n "${LINGO_GO_BIN:-}" ]]; then
        echo "$LINGO_GO_BIN"
        return
    fi
    if [[ -n "${LINGO_BIN:-}" ]]; then
        echo "$LINGO_BIN"
        return
    fi
    echo "$DEFAULT_BIN"
}


run_dev() {
    if ! command -v go >/dev/null 2>&1; then
        echo 'error: Go toolchain not found (expected `go` on PATH).' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi

    (
        cd "$SCRIPT_DIR"
        go run ./cmd/lingolib "$@"
    )
}


run_built() {
    local bin_path
    bin_path="$(resolve_binary_path)"

    if [[ ! -x "$bin_path" ]]; then
        echo "error: built binary not found or not executable: $bin_path" >&2
        echo 'hint: run `./lingo.sh build` or set LINGO_GO_BIN to a valid binary path.' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi

    "$bin_path" "$@"
}


build_binary() {
    if ! command -v go >/dev/null 2>&1; then
        echo 'error: Go toolchain not found (expected `go` on PATH).' >&2
        echo "See: $README_PATH" >&2
        exit 1
    fi

    local bin_path
    bin_path="$(resolve_binary_path)"

    (
        cd "$SCRIPT_DIR"
        go build -o "$bin_path" ./cmd/lingolib
    )
}


main() {
    local command="${1:---help}"
    local run_mode

    if [[ "$command" == 'build' ]]; then
        build_binary
        exit 0
    fi

    if [[ "$command" == 'exe' && $# -ge 2 ]]; then
        local exe_path
        exe_path="$(resolve_exe_path "$2")"
        shift 2
        set -- exe "$exe_path" "$@"
    fi

    run_mode="$(resolve_run_mode)"
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
