package template_module

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"

	"github.com/medium-tech/mspec/templates/go/mapp"
)

//
// data model
//

type SingleEnumType string

const (
	SingleEnumRed   SingleEnumType = "red"
	SingleEnumGreen SingleEnumType = "green"
	SingleEnumBlue  SingleEnumType = "blue"
)

var singleEnumOptions = []string{"red", "green", "blue"}

func IsValidSingleEnum(s string) bool {
	for _, v := range singleEnumOptions {
		if s == v {
			return true
		}
	}
	return false
}

type SingleModel struct {
	ID             *string       `json:"id,omitempty"`
	SingleBool     bool          `json:"single_bool"`
	SingleInt      int           `json:"single_int"`
	SingleFloat    float64       `json:"single_float"`
	SingleString   string        `json:"single_string"`
	SingleEnum     string        `json:"single_enum"`
	SingleDatetime mapp.DateTime `json:"single_datetime"`
}

func (m *SingleModel) ToJSON() (string, error) {
	data, err := json.Marshal(m)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

//
// json
//

func FromJSON(jsonStr string) (*SingleModel, error) {
	var rawData map[string]interface{}
	err := json.Unmarshal([]byte(jsonStr), &rawData)
	if err != nil {
		return nil, fmt.Errorf("invalid JSON: %w", err)
	}

	// Check required fields //

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

	// Unmarshal into struct //

	var model SingleModel
	err = json.Unmarshal([]byte(jsonStr), &model)
	if err != nil {
		return nil, fmt.Errorf("error parsing fields: %w", err)
	}

	// Validate enum value //

	if !IsValidSingleEnum(model.SingleEnum) {
		return nil, fmt.Errorf("invalid enum value for single_enum: %s (must be one of: %v)", model.SingleEnum, singleEnumOptions)
	}

	return &model, nil
}

//
// http client
//

func HttpCreateSingleModel(ctx *mapp.Context, model *SingleModel) (*SingleModel, *mapp.MspecError) {
	// Convert to JSON for request //

	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error marshaling JSON: %v", err), Code: "marshal_error"}
	}

	// Make HTTP request //

	url := ctx.ClientHost + "/api/template-module/single-model"
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error creating single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	createdModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return createdModel, nil
}

func HttpReadSingleModel(ctx *mapp.Context, modelID string) (*SingleModel, *mapp.MspecError) {
	url := ctx.ClientHost + "/api/template-module/single-model/" + modelID

	resp, err := http.Get(url)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error reading single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	model, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return model, nil
}

func HttpUpdateSingleModel(ctx *mapp.Context, modelID string, model *SingleModel) (*SingleModel, *mapp.MspecError) {
	// Set the ID if not already set //

	if model.ID == nil {
		model.ID = &modelID
	}

	// Convert to JSON for request //

	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error marshaling JSON: %v", err), Code: "marshal_error"}
	}

	// Make HTTP request //

	url := ctx.ClientHost + "/api/template-module/single-model/" + modelID
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error creating request: %v", err), Code: "request_error"}
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error updating single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	updatedModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return updatedModel, nil
}

func HttpDeleteSingleModel(ctx *mapp.Context, modelID string) *mapp.MspecError {
	url := ctx.ClientHost + "/api/template-module/single-model/" + modelID

	req, err := http.NewRequest("DELETE", url, nil)
	if err != nil {
		return &mapp.MspecError{Message: fmt.Sprintf("error creating request: %v", err), Code: "request_error"}
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return &mapp.MspecError{Message: fmt.Sprintf("error deleting single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return &mapp.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return &mapp.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return &mapp.MspecError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return &mapp.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	return nil
}

type ListSingleModelResponse struct {
	Total int           `json:"total"`
	Items []SingleModel `json:"items"`
}

func HttpListSingleModel(ctx *mapp.Context, offset int, limit int) (*ListSingleModelResponse, *mapp.MspecError) {
	url := fmt.Sprintf("%s/api/template-module/single-model?offset=%d&limit=%d", ctx.ClientHost, offset, limit)

	resp, err := http.Get(url)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error listing single models: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	var listResponse ListSingleModelResponse
	err = json.Unmarshal(responseBody, &listResponse)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return &listResponse, nil
}

//
// database operations (placeholder)
//

func DBCreateTableSingleModel() (map[string]string, *mapp.MspecError) {
	// Placeholder: This will create the SQLite table
	response := map[string]string{
		"message": "table single_model created (placeholder)",
		"status":  "success",
	}
	return response, nil
}

func DBCreateSingleModel(model *SingleModel) (*SingleModel, *mapp.MspecError) {
	// Placeholder: This will insert into SQLite
	// For now, just return the model with a placeholder ID
	id := "placeholder-id-123"
	model.ID = &id
	return model, nil
}

func DBReadSingleModel(modelID string) (*SingleModel, *mapp.MspecError) {
	// Placeholder: This will query SQLite
	model := &SingleModel{
		ID:             &modelID,
		SingleBool:     true,
		SingleInt:      42,
		SingleFloat:    3.14,
		SingleString:   "placeholder data from db",
		SingleEnum:     "blue",
		SingleDatetime: mapp.DateTime{},
	}
	return model, nil
}

func DBUpdateSingleModel(modelID string, model *SingleModel) (*SingleModel, *mapp.MspecError) {
	// Placeholder: This will update in SQLite
	if model.ID == nil {
		model.ID = &modelID
	}
	return model, nil
}

func DBDeleteSingleModel(modelID string) *mapp.MspecError {
	// Placeholder: This will delete from SQLite
	return nil
}

func DBListSingleModel(offset int, limit int) (*ListSingleModelResponse, *mapp.MspecError) {
	// Placeholder: This will query SQLite with pagination
	items := []SingleModel{}
	for i := 0; i < 3; i++ {
		id := fmt.Sprintf("placeholder-id-%d", offset+i+1)
		item := SingleModel{
			ID:             &id,
			SingleBool:     i%2 == 0,
			SingleInt:      100 + i,
			SingleFloat:    1.5 * float64(i),
			SingleString:   fmt.Sprintf("placeholder item %d", i+1),
			SingleEnum:     "green",
			SingleDatetime: mapp.DateTime{},
		}
		items = append(items, item)
	}

	response := &ListSingleModelResponse{
		Total: 100, // placeholder total
		Items: items,
	}
	return response, nil
}

//
// cli
//

func CLIParseSingleModel(args []string) (interface{}, *mapp.MspecError) {

	command := args[2]
	action := args[3]

	ctx := mapp.ContextFromEnv()

	switch command {
	case "http", "db":
		// Validate command is supported
	default:
		return nil, &mapp.MspecError{Message: fmt.Sprintf("unknown command '%s'", command), Code: "unknown_command"}
	}

	switch action {
	case "create-table":
		if command != "db" {
			return nil, &mapp.MspecError{Message: "create-table is only available for db command", Code: "invalid_action"}
		}
		return CLIDbCreateTableSingleModel()
	case "create":
		if len(args) < 5 {
			return nil, &mapp.MspecError{Message: "missing JSON string for create", Code: "missing_argument"}
		}
		return CLICreateSingleModel(command, ctx, args[4])
	case "read":
		if len(args) < 5 {
			return nil, &mapp.MspecError{Message: "missing model ID for read", Code: "missing_argument"}
		}
		return CLIReadSingleModel(command, ctx, args[4])
	case "update":
		if len(args) < 6 {
			return nil, &mapp.MspecError{Message: "missing model ID or JSON string for update", Code: "missing_argument"}
		}
		return CLIUpdateSingleModel(command, ctx, args[4], args[5])
	case "delete":
		if len(args) < 5 {
			return nil, &mapp.MspecError{Message: "missing model ID for delete", Code: "missing_argument"}
		}
		return CLIDeleteSingleModel(command, ctx, args[4])
	case "list":
		offset := 0
		limit := 50

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
		return CLIListSingleModel(command, ctx, offset, limit)
	default:
		return nil, &mapp.MspecError{Message: fmt.Sprintf("unknown action '%s'", action), Code: "unknown_action"}
	}
}

// cli crud wrappers //

func CLICreateSingleModel(command string, ctx *mapp.Context, jsonData string) (*SingleModel, *mapp.MspecError) {
	model, err := FromJSON(jsonData)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error parsing JSON: %v", err), Code: "parse_error"}
	}

	var createdModel *SingleModel
	var mspecErr *mapp.MspecError

	if command == "http" {
		createdModel, mspecErr = HttpCreateSingleModel(ctx, model)
	} else {
		createdModel, mspecErr = DBCreateSingleModel(model)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return createdModel, nil
}

func CLIReadSingleModel(command string, ctx *mapp.Context, modelID string) (*SingleModel, *mapp.MspecError) {
	var model *SingleModel
	var mspecErr *mapp.MspecError

	if command == "http" {
		model, mspecErr = HttpReadSingleModel(ctx, modelID)
	} else {
		model, mspecErr = DBReadSingleModel(modelID)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return model, nil
}

func CLIUpdateSingleModel(command string, ctx *mapp.Context, modelID string, jsonData string) (*SingleModel, *mapp.MspecError) {
	model, err := FromJSON(jsonData)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error parsing JSON: %v", err), Code: "parse_error"}
	}

	var updatedModel *SingleModel
	var mspecErr *mapp.MspecError

	if command == "http" {
		updatedModel, mspecErr = HttpUpdateSingleModel(ctx, modelID, model)
	} else {
		updatedModel, mspecErr = DBUpdateSingleModel(modelID, model)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return updatedModel, nil
}

func CLIDeleteSingleModel(command string, ctx *mapp.Context, modelID string) (map[string]string, *mapp.MspecError) {
	var mspecErr *mapp.MspecError

	if command == "http" {
		mspecErr = HttpDeleteSingleModel(ctx, modelID)
	} else {
		mspecErr = DBDeleteSingleModel(modelID)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	response := map[string]string{
		"message": fmt.Sprintf("deleted single model %s", modelID),
		"id":      modelID,
	}
	return response, nil
}

func CLIListSingleModel(command string, ctx *mapp.Context, offset int, limit int) (*ListSingleModelResponse, *mapp.MspecError) {
	var listResponse *ListSingleModelResponse
	var mspecErr *mapp.MspecError

	if command == "http" {
		listResponse, mspecErr = HttpListSingleModel(ctx, offset, limit)
	} else {
		listResponse, mspecErr = DBListSingleModel(offset, limit)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return listResponse, nil
}

//
// DB-specific CLI wrappers
//

func CLIDbCreateTableSingleModel() (map[string]string, *mapp.MspecError) {
	response, mspecErr := DBCreateTableSingleModel()
	if mspecErr != nil {
		return nil, mspecErr
	}

	return response, nil
}

//
// help menu
//

func PrintSingleModelHelp() {
	fmt.Println(`Single Model Help

The single-model supports CRUD operations via HTTP or database commands.

Available commands:
  http    Interact with the model via HTTP API
  db      Interact with the model via local SQLite database

Usage:
  ./main template-module single-model <command> <action> [args]

HTTP Commands:
  ./main template-module single-model http create <json>
      Creates a single model on the remote server via HTTP.

  ./main template-module single-model http read <model_id>
      Reads a single model from the remote server via HTTP.

  ./main template-module single-model http update <model_id> <json>
      Updates a single model on the remote server via HTTP.

  ./main template-module single-model http delete <model_id>
      Deletes a single model from the remote server via HTTP.

  ./main template-module single-model http list [--offset=N] [--limit=N]
      Lists models from the remote server via HTTP with optional pagination.

Database Commands:
  ./main template-module single-model db create-table
      Creates the single_model table in the local SQLite database.

  ./main template-module single-model db create <json>
      Creates a single model in the local SQLite database.

  ./main template-module single-model db read <model_id>
      Reads a single model from the local SQLite database.

  ./main template-module single-model db update <model_id> <json>
      Updates a single model in the local SQLite database.

  ./main template-module single-model db delete <model_id>
      Deletes a single model from the local SQLite database.

  ./main template-module single-model db list [--offset=N] [--limit=N]
      Lists models from the local SQLite database with optional pagination.

Model JSON Format:
  {
    "single_bool": true,
    "single_int": 42,
    "single_float": 3.14,
    "single_string": "example text",
    "single_enum": "red|green|blue",
    "single_datetime": "2000-01-11T12:34:56"
  }

Examples:
  ./main template-module single-model http create '{"single_bool":true,"single_int":42,"single_float":3.14,"single_string":"test","single_enum":"red","single_datetime":"2024-01-01T10:00:00"}'
  ./main template-module single-model http read 123
  ./main template-module single-model http list --offset=0 --limit=10
  ./main template-module single-model db create-table
  ./main template-module single-model db list`)
}
