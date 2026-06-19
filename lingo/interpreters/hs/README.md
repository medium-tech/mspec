# haskell lingo interpreter
This is the haskell interpreter and library for the lingo language.

## os setup

- macOS: install GHC and cabal with Homebrew: `brew install ghc cabal-install`
- Windows: install via GHCup (recommended): https://www.haskell.org/ghcup/
- Linux: install GHC and cabal with your package manager, for example
	`sudo apt install ghc cabal-install`

If you already have `ghc` but not `cabal`, install `cabal-install` separately.

## build
(run `cabal update` if this fails)
```bash
cabal build
```

## lock dependencies (reproducible build)

After a successful build, generate a freeze file with exact dependency versions:

```bash
cabal freeze
```

## run

```bash
$(cabal list-bin lingolib) --help
$(cabal list-bin lingolib) exe ../../shared/scripts/exe/hello-world.yaml
```

On Windows (PowerShell):

```powershell
& (cabal list-bin lingolib) --help
& (cabal list-bin lingolib) exe ..\..\shared\scripts\exe\hello-world.yaml
```

## vs code extension
First install `ghcup` on your machine, then extensions "Haskell" and "Haskell Syntax Highlighting" from the Haskell publisher.