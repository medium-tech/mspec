# javascript lingo interpreter
This is the JavaScript interpreter and library for the lingo language.

## setup

- macOS: install Node.js with Homebrew: `brew install node`
- Windows: install Node.js from https://nodejs.org/ or `winget install OpenJS.NodeJS`
- Linux: install Node.js with your package manager, for example `sudo apt install nodejs`

### npm setup

```bash
npm install
```

## run

### run with standard cli

```bash
./lingo.sh --help
./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
./lingo.sh -v exe ../../shared/scripts/exe/hello-world.yaml
```

`build` is intentionally unsupported for JavaScript wrappers (source execution only).

wrapper binary overrides:

```bash
LINGO_JS_BIN=/absolute/path/to/node ./lingo.sh exe ../../shared/scripts/exe/hello-world.yaml
```

global fallback is also supported: `LINGO_BIN`.

Verbose logging:

- use `--verbose` or `-v`
- log format: `:: INFO :: <msg>`

### manual run

```bash
node bin/lingolib.js -h
node bin/lingolib.js exe ../../shared/scripts/exe/hello-world.yaml
```
