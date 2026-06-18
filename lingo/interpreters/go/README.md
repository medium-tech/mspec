# go bootstrap package

## os setup

- macOS: install Go with Homebrew: `brew install go`
- Windows: install Go from https://go.dev/dl/ or `winget install GoLang.Go`
- Linux: install Go with your package manager, for example `sudo apt install golang`

## build

```bash
go build -o lingolib ./cmd/lingolib
```

## run

```bash
./lingolib
```

On Windows, run `lingolib.exe`.
