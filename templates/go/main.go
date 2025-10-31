package main

import (
    "encoding/json"
    "fmt"
    "os"
    "strconv"
    "strings"
    "time"
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

// SingleEnumType represents valid enum values for single_enum
type SingleEnumType string

const (
	SingleEnumRed   SingleEnumType = "red"
	SingleEnumGreen SingleEnumType = "green"
	SingleEnumBlue  SingleEnumType = "blue"
)

// Valid enum options
var singleEnumOptions = []string{"red", "green", "blue"}

// IsValidSingleEnum checks if a string is a valid enum value
func IsValidSingleEnum(s string) bool {
	for _, v := range singleEnumOptions {
		if s == v {
			return true
		}
	}
	return false
}

// SingleModel represents a data model with various field types
type SingleModel struct {
	ID            *string   `json:"id,omitempty"`
	SingleBool    bool      `json:"single_bool"`
	SingleInt     int       `json:"single_int"`
	SingleFloat   float64   `json:"single_float"`
	SingleString  string    `json:"single_string"`
	SingleEnum    string    `json:"single_enum"`
	SingleDatetime lingoDateTime `json:"single_datetime"`
}

// lingoDateTime wraps time.Time to handle custom datetime format
type lingoDateTime struct {
	time.Time
}

const datetimeFormat = "2006-01-02T15:04:05"

// UnmarshalJSON implements json.Unmarshaler for lingoDateTime
func (ct *lingoDateTime) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), "\"")
	t, err := time.Parse(datetimeFormat, s)
	if err != nil {
		return err
	}
	ct.Time = t
	return nil
}

// MarshalJSON implements json.Marshaler for lingoDateTime
func (ct lingoDateTime) MarshalJSON() ([]byte, error) {
	formatted := fmt.Sprintf("\"%s\"", ct.Format(datetimeFormat))
	return []byte(formatted), nil
}

// SingleModelToJSON serializes the SingleModel to a JSON string
func (m *SingleModel) SingleModelToJSON() (string, error) {
	data, err := json.Marshal(m)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// SingleModelFromJSON deserializes a JSON string into a SingleModel
// All fields except ID are required and will return an error if missing
func SingleModelFromJSON(jsonStr string) (*SingleModel, error) {
	var rawData map[string]interface{}
	err := json.Unmarshal([]byte(jsonStr), &rawData)
	if err != nil {
		return nil, fmt.Errorf("invalid JSON: %w", err)
	}

	// Check required fields
	requiredFields := []string{
		"single_bool",
		"single_int",
		"single_float",
		"single_string",
		"single_enum",
		"single_datetime",
	}

	for _, field := range requiredFields {
		if _, exists := rawData[field]; !exists {
			return nil, fmt.Errorf("missing required field: %s", field)
		}
	}

	// Unmarshal into struct
	var model SingleModel
	err = json.Unmarshal([]byte(jsonStr), &model)
	if err != nil {
		return nil, fmt.Errorf("error parsing fields: %w", err)
	}

	// Validate enum value
	if !IsValidSingleEnum(model.SingleEnum) {
		return nil, fmt.Errorf("invalid enum value for single_enum: %s (must be one of: %v)", model.SingleEnum, singleEnumOptions)
	}

	return &model, nil
}

// SingleModel print to console
func (m *SingleModel) SingleModelPrint() {
	fmt.Printf("SingleModel {\n")
	if m.ID != nil {
		fmt.Printf("  ID: %s\n", *m.ID)
	} else {
		fmt.Printf("  ID: nil\n")
	}
	fmt.Printf("  SingleBool: %t\n", m.SingleBool)
	fmt.Printf("  SingleInt: %d\n", m.SingleInt)
	fmt.Printf("  SingleFloat: %f\n", m.SingleFloat)
	fmt.Printf("  SingleString: %s\n", m.SingleString)
	fmt.Printf("  SingleEnum: %s\n", m.SingleEnum)
	fmt.Printf("  SingleDatetime: %s\n", m.SingleDatetime.Format(datetimeFormat))
	fmt.Printf("}\n")
}


// Placeholder functions for each command

func httpCreateSingleModel(jsonData string) {
    fmt.Printf("httpCreateSingleModel called with JSON: %s\n", jsonData)
	model, err := SingleModelFromJSON(jsonData)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing JSON: %v\n", err)
		return
	}
	model.SingleModelPrint()
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