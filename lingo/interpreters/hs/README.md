# haskell bootstrap package

## os setup

- macOS: install GHC with Homebrew: `brew install ghc`
- Windows: install GHC via GHCup from https://www.haskell.org/ghcup/
- Linux: install GHC with your package manager, for example `sudo apt install ghc`

## build

```bash
ghc -isrc -o lingolib app/Main.hs
```

## run

```bash
./lingolib
```

On Windows, run `lingolib.exe`.
