# c bootstrap package

## os setup

- macOS: install Xcode Command Line Tools with `xcode-select --install`
- macOS/Linux: install libyaml headers and library (`brew install libyaml` on macOS, `sudo apt install libyaml-dev` on Debian/Ubuntu)
- Windows: install MSYS2/MinGW or Visual Studio Build Tools
- Linux: install GCC with your package manager, for example `sudo apt install build-essential`

## build

```bash
gcc -Iinclude -I/opt/homebrew/include -L/opt/homebrew/lib -o lingolib app/main.c src/lingolib.c -lyaml
```

If you are not on Apple Silicon/Homebrew, adjust the libyaml include and library paths as needed (for example `/usr/local/include` and `/usr/local/lib`).

## run

```bash
./lingolib exe ../../shared/scripts/exe/hello-world.yaml
```

On Windows, run `lingolib.exe`.
