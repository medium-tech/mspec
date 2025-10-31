package main

import (
    "fmt"
    "os"
    "strconv"
    "strings"
)

func main() {
    args := os.Args[1:]

    if len(args) == 0 || args[0] == "--help" {
        printHelp()
        return
    }

    if args[0] != "http" {
        fmt.Fprintf(os.Stderr, "Error: unknown command '%s'\n", args[0])
        printHelp()
        os.Exit(1)
    }

    if len(args) < 3 {
        fmt.Fprintln(os.Stderr, "Error: insufficient arguments")
        printHelp()
        os.Exit(1)
    }

    action := args[1]
    model := args[2]

    if model != "single-model" {
        fmt.Fprintf(os.Stderr, "Error: unknown model type '%s'\n", model)
        os.Exit(1)
    }

    switch action {
		case "create":
			if len(args) < 4 {
				fmt.Fprintln(os.Stderr, "Error: missing JSON string for create")
				os.Exit(1)
			}
			httpCreateSingleModel(args[3])
		case "read":
			if len(args) < 4 {
				fmt.Fprintln(os.Stderr, "Error: missing model ID for read")
				os.Exit(1)
			}
			httpReadSingleModel(args[3])
		case "update":
			if len(args) < 5 {
				fmt.Fprintln(os.Stderr, "Error: missing model ID or JSON string for update")
				os.Exit(1)
			}
			httpUpdateSingleModel(args[3], args[4])
		case "delete":
			if len(args) < 4 {
				fmt.Fprintln(os.Stderr, "Error: missing model ID for delete")
				os.Exit(1)
			}
			httpDeleteSingleModel(args[3])
		case "list":
			offset := 0
			limit := 50
			// Parse optional flags
			for i := 3; i < len(args); i++ {
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
			httpListSingleModel(offset, limit)
		default:
			fmt.Fprintf(os.Stderr, "Error: unknown action '%s'\n", action)
			printHelp()
			os.Exit(1)
    }
}

func printHelp() {
    fmt.Println(`Usage:
  ./main --help
      Displays the help information.

  ./main http create single-model [<json string of model>]
      Creates a single model based on the provided JSON string on remote server via HTTP.

  ./main http read single-model [<model id>]
      Reads a single model based on the provided model ID from remote server via HTTP.

  ./main http update single-model [<model id>] [<json string of updated model>]
      Updates a single model based on the provided model ID and JSON string on remote server via HTTP.

  ./main http delete single-model [<model id>]
      Deletes a single model based on the provided model ID from remote server via HTTP.

  ./main http list single-model [--offset=<offset> default:0] [--limit=<limit> default:50]
      Lists models with optional pagination parameters.`)
}

// Placeholder functions for each command

func httpCreateSingleModel(jsonData string) {
    fmt.Printf("httpCreateSingleModel called with JSON: %s\n", jsonData)
    // TODO: Implement HTTP create logic
}

func httpReadSingleModel(modelID string) {
    fmt.Printf("httpReadSingleModel called with ID: %s\n", modelID)
    // TODO: Implement HTTP read logic
}

func httpUpdateSingleModel(modelID string, jsonData string) {
    fmt.Printf("httpUpdateSingleModel called with ID: %s and JSON: %s\n", modelID, jsonData)
    // TODO: Implement HTTP update logic
}

func httpDeleteSingleModel(modelID string) {
    fmt.Printf("httpDeleteSingleModel called with ID: %s\n", modelID)
    // TODO: Implement HTTP delete logic
}

func httpListSingleModel(offset int, limit int) {
    fmt.Printf("httpListSingleModel called with offset: %d, limit: %d\n", offset, limit)
    // TODO: Implement HTTP list logic
}