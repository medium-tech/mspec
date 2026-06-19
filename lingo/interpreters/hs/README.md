# haskell bootstrap package

## setup

- macOS: install GHC and cabal with Homebrew: `brew install ghc cabal-install`
- Windows: install via GHCup (recommended): https://www.haskell.org/ghcup/
- Linux: install GHC and cabal with your package manager, for example `sudo apt install ghc cabal-install`

If you already have `ghc` but not `cabal`, install `cabal-install` separately.

### optional dependency lock (reproducible builds)

After a successful build, generate a freeze file with exact dependency versions:

```bash
cabal freeze
```

### run with standard cli
By default this will use `cabal run` for dev testing:

```bash
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

### run mode
We can use `lingo.sh` to use `cabal build` to build a binary and then tell `lingo.sh` to use that via cli args or env variables.

```bash
# lingo's 'go build' wrapper
./lingo.sh build

# and then supply --run-mode (or -r) to use the pre-built binary 
./lingo.sh --run-mode built exe ../../shared/scripts/exe/hello-world.yaml

# or use env vars to control run mode
LINGO_HS_RUN_MODE=built ./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml

# verbose logging for debugg paths and run mode
./lingo.sh -v exe ../../shared/scripts/exe/hello-world.yaml
```

You can force run mode per command with `--run-mode <dev|built>` (or `-r <dev|built>`).

Run mode and binary overrides:

```bash
LINGO_HS_RUN_MODE=dev|built
LINGO_HS_BIN=/absolute/path/to/lingolib
```

Global fallbacks are also supported: `LINGO_RUN_MODE`, `LINGO_BIN`.

Precedence for run mode selection:

1. `--run-mode <dev|built>` / `-r <dev|built>` command-line flag
2. `LINGO_HS_RUN_MODE`
3. `LINGO_RUN_MODE`
4. wrapper default (`dev`)

Verbose logging:

- use `--verbose` or `-v`
- log format: `:: INFO :: <msg>`

### manual build & run

```bash
cabal build
$(cabal list-bin lingolib) --help
$(cabal list-bin lingolib) exe ../../shared/scripts/exe/hello-world.yaml
```

On Windows (PowerShell):

```powershell
cabal build
& (cabal list-bin lingolib) --help
& (cabal list-bin lingolib) exe ..\..\shared\scripts\exe\hello-world.yaml
```

## vs code extension

Install `ghcup` on your machine, then install the `Haskell` and `Haskell Syntax Highlighting` extensions.