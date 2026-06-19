#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"


resolve_js_bin() {
    if [[ -n "${LINGO_JS_BIN:-}" ]]; then
        echo "$LINGO_JS_BIN"
        return
    fi
    if [[ -n "${LINGO_BIN:-}" ]]; then
        echo "$LINGO_BIN"
        return
    fi
    if command -v node >/dev/null 2>&1; then
        echo 'node'
        return
    fi

    echo 'error: Node.js executable not found (expected node on PATH).' >&2
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
    local js_bin

    js_bin="$(resolve_js_bin)"

    if [[ "$command" == 'build' ]]; then
        echo 'error: build is not supported for JavaScript; run source directly.' >&2
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
        "$js_bin" bin/lingolib.js "$@"
    )
}


main "$@"
