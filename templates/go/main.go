package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
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

	// Web server command
	if args[0] == "server" {

		ctx := mapp.ContextFromEnv()

		startServer(ctx)
		return
	}

	module := args[0]

	// Require at least 3 args for actual commands
	if len(args) < 3 {
		fmt.Fprintln(os.Stderr, "Error: insufficient arguments")
		printHelp()
		os.Exit(1)
	}

	var result interface{}
	var cliErr *mapp.MappError

	switch module {
	case "template-module":
		model := args[1]
		switch model {
		case "single-model":
			result, cliErr = template_module.CLIParseSingleModel(args)
		case "help":
			printTemplateModuleHelp()
			os.Exit(0)
		default:
			cliErr = &mapp.MappError{Message: fmt.Sprintf("unknown model type '%s'", model), Code: "unknown_model"}
		}
	default:
		cliErr = &mapp.MappError{Message: fmt.Sprintf("unknown module '%s'", module), Code: "unknown_module"}
	}

	// Handle errors
	if cliErr != nil {
		jsonBytes, _ := json.MarshalIndent(cliErr, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	// Pretty print result
	if result != nil {
		jsonBytes, marshalErr := json.MarshalIndent(result, "", "  ")
		if marshalErr != nil {
			errorOutput := mapp.MappError{Message: fmt.Sprintf("error formatting JSON: %v", marshalErr), Code: "format_error"}
			jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
			fmt.Println(string(jsonBytes))
			os.Exit(1)
		}
		fmt.Println(string(jsonBytes))
	}
}

//
// help menu
//

func printHelp() {
	fmt.Printf(`Usage:
  ./main -h | --help | help
      Displays this global help information.

  ./main server
      Starts a hello world web server on the port specified by MAPP_SERVER_PORT environment variable.

  ./main <module> help
      Displays help for a specific module.

  ./main <module> <model>
      Displays help for a specific model.

Available modules:
  template-module    Example module with CRUD operations

Environment variables:
  MAPP_SERVER_PORT    The server port (default: %d)
  MAPP_CLIENT_HOST    The client host URL (default: %s)
  MAPP_DB_FILE       The database file path (default: %s)

Examples:
  ./main server 8080
  ./main template-module help
  ./main template-module single-model
  ./main template-module single-model http create '{"single_bool":true,...}'`, mapp.MappServerPortDefault, mapp.MappClientHostDefault, mapp.MappDBFileDefault)
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

//
// web server
//

func startServer(ctx *mapp.Context) {
	http.HandleFunc("/", helloHandler)

	if ctx.ServerPort < 1 || ctx.ServerPort > 65535 {
		fmt.Fprintf(os.Stderr, "Error: invalid port '%d' (must be 1-65535)\n", ctx.ServerPort)
		os.Exit(1)
	}

	addr := fmt.Sprintf(":%d", ctx.ServerPort)
	fmt.Printf("Starting server on http://localhost%s\n", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}

func helloHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	fmt.Fprintf(w, "hello.world\n")
}
