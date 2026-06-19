#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"


print_help() {
    cat <<EOF
usage: ./lingo.sh [--help] <command> [args]

commands:
  exe <path>    load, parse, execute an exe spec and print result

unsupported commands:
  build         not required for Python (runs source directly)

environment:
  LINGO_PY_BIN  Python executable to use (overrides fallback)
  LINGO_BIN     Global fallback executable (used if LINGO_PY_BIN is unset)

notes:
  - Beta wrappers are not guaranteed to behave identically on all OS/toolchains.
  - Manual interpreter instructions: $README_PATH
EOF
}


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

    case "$command" in
        --help|-h)
            print_help
            ;;
        build)
            echo 'error: build is not supported for Python; run source directly with exe.' >&2
            echo "See: $README_PATH" >&2
            exit 2
            ;;
        exe)
            shift
            if [[ $# -lt 1 ]]; then
                echo 'error: exe requires a path argument' >&2
                exit 1
            fi
            local py_bin
            local exe_path
            py_bin="$(resolve_python_bin)"
            exe_path="$(resolve_exe_path "$1")"
            shift
            (
                cd "$SCRIPT_DIR"
                export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
                "$py_bin" -m lingolib exe "$exe_path" "$@"
            )
            ;;
        *)
            echo "error: unknown command: $command" >&2
            print_help >&2
            exit 1
            ;;
    esac
}


main "$@"
