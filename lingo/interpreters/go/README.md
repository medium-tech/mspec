# go lingo interpreter
This is the Go interpreter and library for the lingo language.

## setup

- macOS: install Go with Homebrew: `brew install go`
- Windows: install Go from https://go.dev/dl/ or `winget install GoLang.Go`
- Linux: install Go with your package manager, for example `sudo apt install golang`

## run

### run with standard cli
By default this will use `go run` for dev testing:

```bash
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

### run mode

Teh `lingo.sh` script has two run modes for the go interpreter:
* `dev` - uses `go run` for development testing, this is the default mode [shown above](#run-with-standard-cli)
* `built` - uses a go binary built with `go build`

We can use  to use `go build` to build a binary and then tell `lingo.sh` to use that via cli args or env variables.

```bash
# lingo's 'go build' wrapper
./lingo.sh build

# and then supply --run-mode (or -r) to use the pre-built binary 
./lingo.sh --run-mode built exe ../../shared/scripts/exe/hello-world.yaml

# or use env vars to control run mode
LINGO_GO_RUN_MODE=built ./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml

# binary override for built mode
LINGO_GO_BIN=/absolute/path/to/lingolib ./lingo.sh --run-mode built exe ../../shared/scripts/exe/hello-world.yaml

# verbose logging for debug paths and run mode
./lingo.sh -v exe ../../shared/scripts/exe/hello-world.yaml
```

You can force run mode per command with `--run-mode <dev|built>` (or `-r <dev|built>`).

Run mode and binary overrides:

```bash
LINGO_GO_RUN_MODE=dev|built
LINGO_GO_BIN=/absolute/path/to/lingolib
```

Global fallbacks are also supported: `LINGO_RUN_MODE`, `LINGO_BIN`.

Precedence for run mode selection:

1. `--run-mode <dev|built>` / `-r <dev|built>` command-line flag
2. `LINGO_GO_RUN_MODE`
3. `LINGO_RUN_MODE`
4. `lingo.sh` default value: `dev`

Verbose logging:

- use `--verbose` or `-v`
- log format: `:: DEBUG :: <msg>`

### manual build & run

```bash
go build -o lingolib ./cmd/lingolib
./lingolib exe ../../shared/scripts/exe/hello-world.yaml
```

### manual go run command
```bash
go run ./cmd/lingolib exe ../../shared/scripts/exe/hello-world.yaml
```

On Windows, run `lingolib.exe`.
