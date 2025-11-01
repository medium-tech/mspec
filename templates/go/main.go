package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/medium-tech/mspec/templates/go/template_module"
)

func main() {
	args := os.Args[1:]

	if len(args) == 0 {
		fmt.Fprintf(os.Stderr, "Error: no command provided\n")
		printHelp()
		os.Exit(1)
	}

	if args[0] == "-h" || args[0] == "--help" {
		printHelp()
		return
	}

	if args[0] != "template-module" {
		fmt.Fprintf(os.Stderr, "Error: unknown module '%s'\n", args[0])
		printHelp()
		os.Exit(1)
	}

	if len(args) < 4 {
		fmt.Fprintln(os.Stderr, "Error: insufficient arguments")
		printHelp()
		os.Exit(1)
	}

	model := args[1]
	protocol := args[2]
	action := args[3]

	if model != "single-model" {
		fmt.Fprintf(os.Stderr, "Error: unknown model type '%s'\n", model)
		os.Exit(1)
	}

	if protocol != "http" {
		fmt.Fprintf(os.Stderr, "Error: unknown protocol '%s'\n", protocol)
		os.Exit(1)
	}

	switch action {
	case "create":
		if len(args) < 5 {
			fmt.Fprintln(os.Stderr, "Error: missing JSON string for create")
			os.Exit(1)
		}
		template_module.CLICreateSingleModel(args[4])
	case "read":
		if len(args) < 5 {
			fmt.Fprintln(os.Stderr, "Error: missing model ID for read")
			os.Exit(1)
		}
		template_module.CLIReadSingleModel(args[4])
	case "update":
		if len(args) < 6 {
			fmt.Fprintln(os.Stderr, "Error: missing model ID or JSON string for update")
			os.Exit(1)
		}
		template_module.CLIUpdateSingleModel(args[4], args[5])
	case "delete":
		if len(args) < 5 {
			fmt.Fprintln(os.Stderr, "Error: missing model ID for delete")
			os.Exit(1)
		}
		template_module.CLIDeleteSingleModel(args[4])
	case "list":
		offset := 0
		limit := 50
		// Parse optional flags
		for i := 4; i < len(args); i++ {
			if strings.HasPrefix(args[i], "--offset=") {
				val := strings.TrimPrefix(args[i], "--offset=")
				if parsed, err := strconv.Atoi(val); err == nil {
					offset = parsed
				}
			} else if strings.HasPrefix(args[i], "--limit=") {
				val := strings.TrimPrefix(args[i], "--limit=")
				if parsed, err := strconv.Atoi(val); err == nil {
					limit = parsed
				}
			}
		}
		template_module.CLIListSingleModel(offset, limit)
	default:
		fmt.Fprintf(os.Stderr, "Error: unknown action '%s'\n", action)
		printHelp()
		os.Exit(1)
	}
}

func printHelp() {
	fmt.Println(`Usage:
  ./main -h | --help
      Displays the help information.

  ./main template-module single-model http create [<json string of model>]
      Creates a single model based on the provided JSON string on remote server via HTTP.

  ./main template-module single-model http read [<model id>]
      Reads a single model based on the provided model ID from remote server via HTTP.

  ./main template-module single-model http update [<model id>] [<json string of updated model>]
      Updates a single model based on the provided model ID and JSON string on remote server via HTTP.

  ./main template-module single-model http delete [<model id>]
      Deletes a single model based on the provided model ID from remote server via HTTP.

  ./main template-module single-model http list [--offset=<offset> default:0] [--limit=<limit> default:50]
      Lists models with optional pagination parameters.`)
}
