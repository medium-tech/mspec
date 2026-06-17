# c bootstrap package

## os setup

- macOS: install Xcode Command Line Tools with `xcode-select --install`
- Windows: install MSYS2/MinGW or Visual Studio Build Tools
- Linux: install GCC with your package manager, for example `sudo apt install build-essential`

## build

```bash
gcc -Iinclude -o lingolib app/main.c src/lingolib.c
```

## run

```bash
./lingolib
```

On Windows, run `lingolib.exe`.
