#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
README_PATH="$SCRIPT_DIR/README.md"
CALLER_DIR="$PWD"
DEFAULT_BIN="$SCRIPT_DIR/lingolib"
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

    log_info 'Checking environment variable LINGO_C_RUN_MODE'
    if [[ -n "${LINGO_C_RUN_MODE:-}" ]]; then
        log_info "Using LINGO_C_RUN_MODE: $LINGO_C_RUN_MODE"
        echo "$LINGO_C_RUN_MODE"
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


resolve_binary_path() {
    log_info 'Checking environment variable LINGO_C_BIN'
    if [[ -n "${LINGO_C_BIN:-}" ]]; then
        log_info "Using LINGO_C_BIN: $LINGO_C_BIN"
        echo "$LINGO_C_BIN"
        return
    fi

    log_info 'Checking environment variable LINGO_BIN'
    if [[ -n "${LINGO_BIN:-}" ]]; then
        log_info "Using LINGO_BIN fallback: $LINGO_BIN"
        echo "$LINGO_BIN"
        return
    fi

    log_info "Using default C binary path: $DEFAULT_BIN"
    echo "$DEFAULT_BIN"
}


resolve_compiler() {
    log_info 'Checking environment variable LINGO_C_CC'
    if [[ -n "${LINGO_C_CC:-}" ]]; then
        log_info "Using LINGO_C_CC: $LINGO_C_CC"
        echo "$LINGO_C_CC"
        return
    fi

    log_info 'Checking environment variable CC'
    if [[ -n "${CC:-}" ]]; then
        log_info "Using CC fallback: $CC"
        echo "$CC"
        return
    fi

    log_info 'Checking PATH for gcc'
    if command -v gcc >/dev/null 2>&1; then
        log_info 'Using gcc from PATH'
        echo 'gcc'
        return
    fi

    log_info 'Checking PATH for cc'
    if command -v cc >/dev/null 2>&1; then
        log_info 'Using cc from PATH'
        echo 'cc'
        return
    fi

    log_info 'No usable C compiler found'
    echo 'error: C compiler not found (expected gcc or cc on PATH).' >&2
    echo "See: $README_PATH" >&2
    exit 1
}


resolve_libyaml_flags() {
    local flags=()

    log_info 'Checking environment variable LINGO_C_LIBYAML_PREFIX'
    if [[ -n "${LINGO_C_LIBYAML_PREFIX:-}" ]]; then
        flags+=("-I${LINGO_C_LIBYAML_PREFIX}/include" "-L${LINGO_C_LIBYAML_PREFIX}/lib")
        log_info "Using libyaml prefix from LINGO_C_LIBYAML_PREFIX: $LINGO_C_LIBYAML_PREFIX"
        printf '%s\n' "${flags[@]}"
        return
    fi

    local prefix
    for prefix in /opt/homebrew /usr/local; do
        if [[ -f "$prefix/include/yaml.h" ]]; then
            flags+=("-I$prefix/include" "-L$prefix/lib")
            log_info "Detected libyaml in prefix: $prefix"
            printf '%s\n' "${flags[@]}"
            return
        fi
    done

    log_info 'No explicit libyaml prefix detected; relying on default compiler paths'
}


compile_binary() {
    local output_path="$1"
    local compiler
    local yaml_flags=()

    compiler="$(resolve_compiler)"

    while IFS= read -r line; do
        [[ -n "$line" ]] && yaml_flags+=("$line")
    done < <(resolve_libyaml_flags)

    local cmd=("$compiler" "-Iinclude")
    if [[ ${#yaml_flags[@]} -gt 0 ]]; then
        cmd+=("${yaml_flags[@]}")
    fi
    cmd+=("-o" "$output_path" "app/main.c" "src/lingolib.c" "-lyaml")

    log_info "Executing build: ${cmd[*]}"
    (
        cd "$SCRIPT_DIR"
        "${cmd[@]}"
    )
}


build_binary() {
    log_info 'Build command requested'
    local bin_path
    bin_path="$(resolve_binary_path)"
    log_info "Build output binary path: $bin_path"
    compile_binary "$bin_path"
}


run_dev() {
    log_info 'Execution mode selected: dev (compile + execute)'
    local temp_bin
    temp_bin="$(mktemp "$SCRIPT_DIR/lingolib-dev-XXXXXX")"
    chmod +x "$temp_bin"

    log_info "Compiling temporary dev binary: $temp_bin"
    compile_binary "$temp_bin"

    log_info "Executing temporary dev binary: $temp_bin $*"
    "$temp_bin" "$@"

    rm -f "$temp_bin"
    log_info 'Removed temporary dev binary'
}


run_built() {
    local bin_path
    bin_path="$(resolve_binary_path)"

    log_info 'Execution mode selected: built (prebuilt binary)'
    log_info "Resolved built binary path: $bin_path"

    if [[ ! -x "$bin_path" ]]; then
        log_info 'Built binary missing or not executable'
        echo "error: built binary not found or not executable: $bin_path" >&2
        echo 'hint: run `./lingo.sh build` or set LINGO_C_BIN to a valid binary path.' >&2
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
