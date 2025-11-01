package main

import (
	"fmt"
	"os"

	"github.com/medium-tech/mspec/templates/go/template_module"
)

//
// parse and run CLI commands
//

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

	if len(args) < 4 {
		fmt.Fprintln(os.Stderr, "Error: insufficient arguments")
		printHelp()
		os.Exit(1)
	}

	module := args[0]
	switch module {
	case "template-module":
		model := args[1]
		switch model {
		case "single-model":
			template_module.CLIParseSingleModel(args)
		default:
			fmt.Fprintf(os.Stderr, "Error: unknown model type '%s'\n", model)
			os.Exit(1)
		}
	default:
		fmt.Fprintf(os.Stderr, "Error: unknown module '%s'\n", module)
		printHelp()
		os.Exit(1)
	}

}

//
// help menu
//

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
