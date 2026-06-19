# c lingo interpreter
This is the C interpreter and library for the lingo language.

## setup

- macOS: install Xcode Command Line Tools with `xcode-select --install`
- macOS/Linux: install libyaml headers and library (`brew install libyaml` on macOS, `sudo apt install libyaml-dev` on Debian/Ubuntu)
- Windows: install MSYS2/MinGW or Visual Studio Build Tools
- Linux: install GCC with your package manager, for example `sudo apt install build-essential`

## run

### run with standard cli
By default this will use compile+execute flow for dev testing:

```bash
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

### run mode
We can use `lingo.sh` to run `build` and then tell `lingo.sh` to use that pre-built binary via CLI args or env variables.

```bash
# lingo's C build wrapper
./lingo.sh build

# and then supply --run-mode (or -r) to use the pre-built binary
./lingo.sh --run-mode built exe ../../shared/scripts/exe/hello-world.yaml

# or use env vars to control run mode
LINGO_C_RUN_MODE=built ./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml

# verbose logging for debug paths and run mode
./lingo.sh -v exe ../../shared/scripts/exe/hello-world.yaml
```

You can force run mode per command with `--run-mode <dev|built>` (or `-r <dev|built>`).

Run mode and binary overrides:

```bash
LINGO_C_RUN_MODE=dev|built
LINGO_C_BIN=/absolute/path/to/lingolib
```

Global fallbacks are also supported: `LINGO_RUN_MODE`, `LINGO_BIN`.

Precedence for run mode selection:

1. `--run-mode <dev|built>` / `-r <dev|built>` command-line flag
2. `LINGO_C_RUN_MODE`
3. `LINGO_RUN_MODE`
4. wrapper default (`dev`)

### compiler and libyaml overrides

```bash
# choose compiler
LINGO_C_CC=clang ./lingo.sh build

# set libyaml prefix if headers/libs are not in default paths
LINGO_C_LIBYAML_PREFIX=/opt/homebrew ./lingo.sh build
```

### manual build & run

```bash
gcc -Iinclude -I/opt/homebrew/include -L/opt/homebrew/lib -o lingolib app/main.c src/lingolib.c -lyaml
./lingolib exe ../../shared/scripts/exe/hello-world.yaml
```

If you are not on Apple Silicon/Homebrew, adjust the libyaml include and library paths as needed (for example `/usr/local/include` and `/usr/local/lib`).

On Windows, run `lingolib.exe`.
