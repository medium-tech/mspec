package main

import (
	"fmt"
	"os"

	"lingolib"
)

const helpText = "usage: lingolib [--help] <command> [args]\n" +
	"\n" +
	"commands:\n" +
	"  exe <path>    load, parse, execute an exe spec and print result\n" +
	"\n" +
	"supported specs: exe\n"

func main() {
	args := os.Args[1:]
	if len(args) == 0 || args[0] == "--help" || args[0] == "-h" {
		fmt.Print(helpText)
		os.Exit(0)
	}
	command := args[0]
	switch command {
	case "exe":
		if len(args) < 2 {
			fmt.Fprintln(os.Stderr, "error: exe requires a path argument")
			os.Exit(1)
		}
		result, err := lingolib.ExecuteFile(args[1])
		if err != nil {
			fmt.Fprintln(os.Stderr, "error:", err)
			os.Exit(1)
		}
		fmt.Println(result)
	default:
		fmt.Fprintf(os.Stderr, "error: unknown command: %q\n", command)
		os.Exit(1)
	}
}
