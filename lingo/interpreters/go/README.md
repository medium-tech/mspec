# go bootstrap package

## setup

- macOS: install Go with Homebrew: `brew install go`
- Windows: install Go from https://go.dev/dl/ or `winget install GoLang.Go`
- Linux: install Go with your package manager, for example `sudo apt install golang`

## run

### run with standard cli

```bash
./lingo.sh build
./lingo.sh --help
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

Run mode and binary overrides:

```bash
LINGO_GO_RUN_MODE=dev|built
LINGO_GO_BIN=/absolute/path/to/lingolib
```

Global fallbacks are also supported: `LINGO_RUN_MODE`, `LINGO_BIN`.

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
