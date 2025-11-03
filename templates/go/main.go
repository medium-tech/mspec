package main

import (
	"encoding/json"
	"fmt"
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
	var model string
	num_args := len(args)

	var result interface{}
	var cliErr *mapp.MappError

	switch module {
	// for :: {% for module in modules %} :: {"template-module": "module.name.kebab_case"}
	case "template-module":

		if num_args < 2 {
			cliErr = &mapp.MappError{Message: "missing command argument", Code: "missing_argument"}
			break
		} else {
			model = args[1]
		}
		switch model {
		// for :: {% for model in module.models %} :: {"single-model": "model.name.kebab_case"}
		case "single-model":
			result, cliErr = template_module.CLIParseSingleModel(args, num_args)
		// end for ::
		case "help", "--help", "-h":
			printTemplateModuleHelp()
			os.Exit(0)
		default:
			cliErr = &mapp.MappError{Message: fmt.Sprintf("unknown model type '%s'", model), Code: "unknown_model"}
		}
	// end for ::
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

var availableModules = []string{
	// for :: {% for module in modules %} :: {"template-module": "module.name.kebab_case"}
	"template-module",
	// end for ::
}

func availableModulesList() string {
	result := ""
	for _, module := range availableModules {
		result += fmt.Sprintf("  %s\n", module)
	}
	return result
}

func printHelp() {
	fmt.Printf(`Usage:
  ./main -h | --help | help
      Displays this global help information.

  ./main server
      Starts a hello world web server on the port specified by MAPP_SERVER_PORT environment variable.

  ./main <module> help
      Displays help for a specific module.

  ./main <module> <model> help
      Displays help for a specific model.

Available modules:
%s
Environment variables:
  MAPP_SERVER_PORT    The server port (default: %d)
  MAPP_CLIENT_HOST    The client host URL (default: %s)
  MAPP_DB_FILE       The database file path (default: %s)`,
		availableModulesList(), mapp.MappServerPortDefault, mapp.MappClientHostDefault, mapp.MappDBFileDefault)
}

// for :: {% for module in modules %} :: {"template-module": "module.name.kebab_case", "TemplateModule": "module.name.pascal_case"}
func printTemplateModuleHelp() {
	helpText := "TemplateModule Help\n\n"
	helpText += "The template-module provides example CRUD operations for data models.\n\n"
	helpText += "Available models:\n"

	// for :: {% for model in module.models %} :: {"single-model": "model.name.kebab_case"}
	helpText += fmt.Sprintf("  %s\n", "single-model")
	// end for ::

	helpText += "\nUsage:\n"
	helpText += "  ./main template-module <model> help         Show model-specific help\n"
	helpText += "  ./main template-module <model> <command>    Execute a command\n"

	fmt.Println(helpText)
}

//
// web server
//

func startServer(ctx *mapp.Context) {

	template_module.ServerRegisterRoutesSingleModel(ctx)

	http.HandleFunc("/", notFoundHandler)

	if ctx.ServerPort < 1 || ctx.ServerPort > 65535 {
		fmt.Fprintf(os.Stderr, "Error: invalid port '%d' (must be 1-65535)\n", ctx.ServerPort)
		os.Exit(1)
	}

	addr := fmt.Sprintf(":%d", ctx.ServerPort)
	fmt.Printf("Starting server on http://localhost%s\n", addr)

	err := http.ListenAndServe(addr, nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: failed to start server on port %d: %v\n", ctx.ServerPort, err)
		os.Exit(1)
	}
}

func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	fmt.Printf("NOT FOUND %s\n", r.URL.Path)

	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{"error": "not found"})
}
