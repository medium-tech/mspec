package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/medium-tech/mspec/templates/go/mapp"
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

	// Global help
	if args[0] == "-h" || args[0] == "--help" || args[0] == "help" {
		printHelp()
		return
	}

	module := args[0]

	// Module-level help
	if len(args) >= 2 && args[1] == "help" {
		switch module {
		case "template-module":
			printTemplateModuleHelp()
		default:
			fmt.Fprintf(os.Stderr, "Error: unknown module '%s'\n", module)
			os.Exit(1)
		}
		return
	}

	// Model-level help
	if len(args) >= 2 {
		model := args[1]
		if len(args) == 2 || (len(args) >= 3 && args[2] == "help") {
			switch module {
			case "template-module":
				switch model {
				case "single-model":
					template_module.PrintSingleModelHelp()
				default:
					fmt.Fprintf(os.Stderr, "Error: unknown model type '%s'\n", model)
					os.Exit(1)
				}
			default:
				fmt.Fprintf(os.Stderr, "Error: unknown module '%s'\n", module)
				os.Exit(1)
			}
			return
		}
	}

	// Require at least 4 args for actual commands
	if len(args) < 4 {
		fmt.Fprintln(os.Stderr, "Error: insufficient arguments")
		printHelp()
		os.Exit(1)
	}

	var result interface{}
	var err *mapp.MspecError

	switch module {
	case "template-module":
		model := args[1]
		switch model {
		case "single-model":
			result, err = template_module.CLIParseSingleModel(args)
		default:
			err = &mapp.MspecError{Message: fmt.Sprintf("unknown model type '%s'", model), Code: "unknown_model"}
		}
	default:
		err = &mapp.MspecError{Message: fmt.Sprintf("unknown module '%s'", module), Code: "unknown_module"}
	}

	// Handle errors
	if err != nil {
		jsonBytes, _ := json.MarshalIndent(err, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	// Pretty print result
	jsonBytes, marshalErr := json.MarshalIndent(result, "", "  ")
	if marshalErr != nil {
		errorOutput := mapp.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", marshalErr), Code: "format_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}

//
// help menu
//

func printHelp() {
	fmt.Println(`Usage:
  ./main -h | --help | help
      Displays this global help information.

  ./main <module> help
      Displays help for a specific module.

  ./main <module> <model>
      Displays help for a specific model.

Available modules:
  template-module    Example module with CRUD operations

Examples:
  ./main template-module help
  ./main template-module single-model
  ./main template-module single-model http create '{"single_bool":true,...}'`)
}

func printTemplateModuleHelp() {
	fmt.Println(`Template Module Help

The template-module provides example CRUD operations for data models.

Available models:
  single-model    A model with single-value fields (bool, int, float, string, enum, datetime)

Usage:
  ./main template-module <model>              Show model-specific help
  ./main template-module <model> <command>    Execute a command

Examples:
  ./main template-module single-model         Show single-model help
  ./main template-module single-model help    Show single-model help`)
}
