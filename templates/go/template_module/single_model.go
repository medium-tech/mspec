// mtemplate :: {"module": "template module", "model": "single model"}
package template_module

import (
	"bytes"
	_ "embed"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"slices"
	"strconv"
	"strings"
	"time"

	"github.com/medium-tech/mspec/templates/go/mapp"
)

//
// data model
//

// for :: {% for field in model.enum_fields %} ::{"SingleEnum": "field.name.pascal_case", "singleEnum": "field.name.camel_case"}
type SingleEnumType string

const (
	// for :: {% for value in field.enum %} :: {"red": "value"}
	SingleEnumRed SingleEnumType = "red"
	// end for ::
	// ignore ::
	SingleEnumGreen SingleEnumType = "green"
	SingleEnumBlue  SingleEnumType = "blue"
	// end ignore
)

var singleEnumOptions = []string{
	// for :: {% for value in field.enum %} :: {"red": "value"}
	"red",
	// end for ::
	// ignore ::
	"green",
	"blue",
	// end ignore
}

func IsValidSingleEnum(s string) bool {
	return slices.Contains(singleEnumOptions, s)
}

// end for ::

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
		value, exists := rawData[field]
		if !exists {
			return nil, fmt.Errorf("missing required field: %s", field)
		}
		if value == nil {
			return nil, fmt.Errorf("field %s cannot be null", field)
		}
	}

	// Check for extra fields //
	allowedFields := []string{
		"id",
		"single_bool",
		"single_int",
		"single_float",
		"single_string",
		"single_enum",
		"single_datetime",
	}

	for field := range rawData {
		if !slices.Contains(allowedFields, field) {
			return nil, fmt.Errorf("extra field found: %s", field)
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

func HttpCreateSingleModel(ctx *mapp.Context, model *SingleModel) (*SingleModel, *mapp.MappError) {
	// Convert to JSON for request //

	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error marshaling JSON: %v", err), Code: "marshal_error"}
	}

	// Make HTTP request //

	url := ctx.ClientHost + "/api/template-module/single-model"
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error creating single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MappError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MappError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MappError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	createdModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return createdModel, nil
}

func HttpReadSingleModel(ctx *mapp.Context, modelID string) (*SingleModel, *mapp.MappError) {
	url := ctx.ClientHost + "/api/template-module/single-model/" + modelID

	resp, err := http.Get(url)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error reading single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MappError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MappError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return nil, &mapp.MappError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MappError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	model, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return model, nil
}

func HttpUpdateSingleModel(ctx *mapp.Context, modelID string, model *SingleModel) (*SingleModel, *mapp.MappError) {
	// Set the ID if not already set //

	if model.ID == nil {
		model.ID = &modelID
	}

	// Convert to JSON for request //

	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error marshaling JSON: %v", err), Code: "marshal_error"}
	}

	// Make HTTP request //

	url := ctx.ClientHost + "/api/template-module/single-model/" + modelID
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error creating request: %v", err), Code: "request_error"}
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error updating single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MappError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MappError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return nil, &mapp.MappError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MappError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	updatedModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return updatedModel, nil
}

func HttpDeleteSingleModel(ctx *mapp.Context, modelID string) *mapp.MappError {
	url := ctx.ClientHost + "/api/template-module/single-model/" + modelID

	req, err := http.NewRequest("DELETE", url, nil)
	if err != nil {
		return &mapp.MappError{Message: fmt.Sprintf("error creating request: %v", err), Code: "request_error"}
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return &mapp.MappError{Message: fmt.Sprintf("error deleting single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return &mapp.MappError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return &mapp.MappError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return &mapp.MappError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return &mapp.MappError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	return nil
}

type ListSingleModelResponse struct {
	Total int           `json:"total"`
	Items []SingleModel `json:"items"`
}

func HttpListSingleModel(ctx *mapp.Context, offset int, limit int) (*ListSingleModelResponse, *mapp.MappError) {
	url := fmt.Sprintf("%s/api/template-module/single-model?offset=%d&limit=%d", ctx.ClientHost, offset, limit)

	resp, err := http.Get(url)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error listing single models: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors //

	if resp.StatusCode == 401 {
		return nil, &mapp.MappError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mapp.MappError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mapp.MappError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response //

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	var listResponse ListSingleModelResponse
	err = json.Unmarshal(responseBody, &listResponse)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return &listResponse, nil
}

//
// database operations
//

//go:embed sql/single_model_create_table.sql
var createTableSQL string

//go:embed sql/single_model_insert.sql
var insertSQL string

//go:embed sql/single_model_select_by_id.sql
var selectByIDSQL string

//go:embed sql/single_model_update.sql
var updateSQL string

//go:embed sql/single_model_delete.sql
var deleteSQL string

//go:embed sql/single_model_count.sql
var countSQL string

//go:embed sql/single_model_list.sql
var listSQL string

func DBCreateTableSingleModel(ctx *mapp.Context) (map[string]string, *mapp.MappError) {
	db, err := mapp.GetDB(ctx)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error connecting to database: %v", err), Code: "db_error"}
	}

	// Use embedded SQL
	_, err = db.Exec(createTableSQL)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error creating table: %v", err), Code: "db_error"}
	}

	response := map[string]string{
		"message": "table single_model created successfully",
		"status":  "success",
	}
	return response, nil
}

func DBCreateSingleModel(ctx *mapp.Context, model *SingleModel) (*SingleModel, *mapp.MappError) {
	db, err := mapp.GetDB(ctx)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error connecting to database: %v", err), Code: "db_error"}
	}

	// Format datetime as RFC3339 for SQLite storage
	datetimeStr := model.SingleDatetime.Time.Format(time.RFC3339)

	// Use embedded SQL
	result, err := db.Exec(insertSQL,
		model.SingleBool,
		model.SingleInt,
		model.SingleFloat,
		model.SingleString,
		model.SingleEnum,
		datetimeStr,
	)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error creating single model: %v", err), Code: "db_error"}
	}

	// Get the inserted ID
	id, err := result.LastInsertId()
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error getting inserted ID: %v", err), Code: "db_error"}
	}

	// Convert ID to string and set it on the model
	idStr := fmt.Sprintf("%d", id)
	model.ID = &idStr

	return model, nil
}

func DBReadSingleModel(ctx *mapp.Context, modelID string) (*SingleModel, *mapp.MappError) {
	db, err := mapp.GetDB(ctx)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error connecting to database: %v", err), Code: "db_error"}
	}

	var model SingleModel
	var id int
	var singleBool int
	var datetimeStr string

	// Use embedded SQL
	err = db.QueryRow(selectByIDSQL, modelID).Scan(
		&id,
		&singleBool,
		&model.SingleInt,
		&model.SingleFloat,
		&model.SingleString,
		&model.SingleEnum,
		&datetimeStr,
	)
	if err != nil {
		if err.Error() == "sql: no rows in result set" {
			return nil, &mapp.MappError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
		}
		return nil, &mapp.MappError{Message: fmt.Sprintf("error reading single model: %v", err), Code: "db_error"}
	}

	// Convert ID to string
	idStr := fmt.Sprintf("%d", id)
	model.ID = &idStr

	// Convert SQLite integer to bool
	model.SingleBool = singleBool != 0

	// Parse datetime
	parsedTime, err := time.Parse(time.RFC3339, datetimeStr)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error parsing datetime: %v", err), Code: "parse_error"}
	}
	model.SingleDatetime = mapp.DateTime{Time: parsedTime}

	return &model, nil
}

func DBUpdateSingleModel(ctx *mapp.Context, modelID string, model *SingleModel) (*SingleModel, *mapp.MappError) {
	db, err := mapp.GetDB(ctx)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error connecting to database: %v", err), Code: "db_error"}
	}

	// Format datetime as RFC3339 for SQLite storage
	datetimeStr := model.SingleDatetime.Time.Format(time.RFC3339)

	// Use embedded SQL
	result, err := db.Exec(updateSQL,
		model.SingleBool,
		model.SingleInt,
		model.SingleFloat,
		model.SingleString,
		model.SingleEnum,
		datetimeStr,
		modelID,
	)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error updating single model: %v", err), Code: "db_error"}
	}

	// Check if any rows were affected
	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error checking rows affected: %v", err), Code: "db_error"}
	}
	if rowsAffected == 0 {
		return nil, &mapp.MappError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	}

	// Set the ID on the model
	if model.ID == nil {
		model.ID = &modelID
	}

	return model, nil
}

func DBDeleteSingleModel(ctx *mapp.Context, modelID string) *mapp.MappError {
	db, err := mapp.GetDB(ctx)
	if err != nil {
		return &mapp.MappError{Message: fmt.Sprintf("error connecting to database: %v", err), Code: "db_error"}
	}

	// Use embedded SQL
	_, err = db.Exec(deleteSQL, modelID)
	if err != nil {
		return &mapp.MappError{Message: fmt.Sprintf("error deleting single model: %v", err), Code: "db_error"}
	}

	// Idempotent: successful even if record doesn't exist
	return nil
}

func DBListSingleModel(ctx *mapp.Context, offset int, limit int) (*ListSingleModelResponse, *mapp.MappError) {
	db, err := mapp.GetDB(ctx)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error connecting to database: %v", err), Code: "db_error"}
	}

	// Get total count using embedded SQL
	var total int
	err = db.QueryRow(countSQL).Scan(&total)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error counting single models: %v", err), Code: "db_error"}
	}

	// Get paginated items using embedded SQL
	rows, err := db.Query(listSQL, limit, offset)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error listing single models: %v", err), Code: "db_error"}
	}
	defer rows.Close()

	items := []SingleModel{}
	for rows.Next() {
		var model SingleModel
		var id int
		var singleBool int
		var datetimeStr string

		err = rows.Scan(
			&id,
			&singleBool,
			&model.SingleInt,
			&model.SingleFloat,
			&model.SingleString,
			&model.SingleEnum,
			&datetimeStr,
		)
		if err != nil {
			return nil, &mapp.MappError{Message: fmt.Sprintf("error scanning row: %v", err), Code: "db_error"}
		}

		// Convert ID to string
		idStr := fmt.Sprintf("%d", id)
		model.ID = &idStr

		// Convert SQLite integer to bool
		model.SingleBool = singleBool != 0

		// Parse datetime
		parsedTime, err := time.Parse(time.RFC3339, datetimeStr)
		if err != nil {
			return nil, &mapp.MappError{Message: fmt.Sprintf("error parsing datetime: %v", err), Code: "parse_error"}
		}
		model.SingleDatetime = mapp.DateTime{Time: parsedTime}

		items = append(items, model)
	}

	// Check for errors from iterating over rows
	if err = rows.Err(); err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("error iterating rows: %v", err), Code: "db_error"}
	}

	response := &ListSingleModelResponse{
		Total: total,
		Items: items,
	}
	return response, nil
}

//
// cli
//

func CLIParseSingleModel(args []string, num_args int) (interface{}, *mapp.MappError) {
	if num_args < 3 {
		return nil, &mapp.MappError{Message: "missing command argument", Code: "missing_argument"}
	}

	command := args[2]

	ctx := mapp.ContextFromEnv()

	switch command {
	case "http", "db":
		// Validate command is supported
	case "help", "--help", "-h":
		printSingleModelHelp()
		return nil, nil
	default:
		return nil, &mapp.MappError{Message: fmt.Sprintf("unknown command '%s'", command), Code: "unknown_command"}
	}

	if num_args < 4 {
		return nil, &mapp.MappError{Message: "missing action argument", Code: "missing_argument"}
	}

	action := args[3]

	switch action {
	case "create-table":
		if command != "db" {
			return nil, &mapp.MappError{Message: "create-table is only available for db command", Code: "invalid_action"}
		}
		return CLIDbCreateTableSingleModel(ctx)
	case "create":
		if num_args < 5 {
			return nil, &mapp.MappError{Message: "missing JSON string for create", Code: "missing_argument"}
		}
		return CLICreateSingleModel(command, ctx, args[4])
	case "read":
		if num_args < 5 {
			return nil, &mapp.MappError{Message: "missing model ID for read", Code: "missing_argument"}
		}
		return CLIReadSingleModel(command, ctx, args[4])
	case "update":
		if num_args < 6 {
			return nil, &mapp.MappError{Message: "missing model ID or JSON string for update", Code: "missing_argument"}
		}
		return CLIUpdateSingleModel(command, ctx, args[4], args[5])
	case "delete":
		if num_args < 5 {
			return nil, &mapp.MappError{Message: "missing model ID for delete", Code: "missing_argument"}
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
		return nil, &mapp.MappError{Message: fmt.Sprintf("unknown action '%s'", action), Code: "unknown_action"}
	}
}

// cli crud wrappers //

func CLICreateSingleModel(command string, ctx *mapp.Context, jsonData string) (*SingleModel, *mapp.MappError) {
	model, err := FromJSON(jsonData)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("Validation Error: %v", err), Code: "validation_error"}
	}

	var createdModel *SingleModel
	var mspecErr *mapp.MappError

	if command == "http" {
		createdModel, mspecErr = HttpCreateSingleModel(ctx, model)
	} else {
		createdModel, mspecErr = DBCreateSingleModel(ctx, model)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return createdModel, nil
}

func CLIReadSingleModel(command string, ctx *mapp.Context, modelID string) (*SingleModel, *mapp.MappError) {
	var model *SingleModel
	var mspecErr *mapp.MappError

	if command == "http" {
		model, mspecErr = HttpReadSingleModel(ctx, modelID)
	} else {
		model, mspecErr = DBReadSingleModel(ctx, modelID)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return model, nil
}

func CLIUpdateSingleModel(command string, ctx *mapp.Context, modelID string, jsonData string) (*SingleModel, *mapp.MappError) {
	model, err := FromJSON(jsonData)
	if err != nil {
		return nil, &mapp.MappError{Message: fmt.Sprintf("Validation Error: %v", err), Code: "validation_error"}
	}

	var updatedModel *SingleModel
	var mspecErr *mapp.MappError

	if command == "http" {
		updatedModel, mspecErr = HttpUpdateSingleModel(ctx, modelID, model)
	} else {
		updatedModel, mspecErr = DBUpdateSingleModel(ctx, modelID, model)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return updatedModel, nil
}

func CLIDeleteSingleModel(command string, ctx *mapp.Context, modelID string) (map[string]string, *mapp.MappError) {
	var mspecErr *mapp.MappError

	if command == "http" {
		mspecErr = HttpDeleteSingleModel(ctx, modelID)
	} else {
		mspecErr = DBDeleteSingleModel(ctx, modelID)
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

func CLIListSingleModel(command string, ctx *mapp.Context, offset int, limit int) (*ListSingleModelResponse, *mapp.MappError) {
	var listResponse *ListSingleModelResponse
	var mspecErr *mapp.MappError

	if command == "http" {
		listResponse, mspecErr = HttpListSingleModel(ctx, offset, limit)
	} else {
		listResponse, mspecErr = DBListSingleModel(ctx, offset, limit)
	}

	if mspecErr != nil {
		return nil, mspecErr
	}

	return listResponse, nil
}

// other cli commands //

func CLIDbCreateTableSingleModel(ctx *mapp.Context) (map[string]string, *mapp.MappError) {
	response, mspecErr := DBCreateTableSingleModel(ctx)
	if mspecErr != nil {
		return nil, mspecErr
	}

	return response, nil
}

func printSingleModelHelp() {
	fmt.Println(`SingleModel Help

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

//
// server
//

// ServerCreateSingleModel handles POST /api/template-module/single-model
func ServerCreateSingleModel(ctx *mapp.Context, w http.ResponseWriter, r *http.Request) {
	// Read request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "failed to read request body"})
		return
	}

	// Parse JSON into model
	model, parseErr := FromJSON(string(body))
	if parseErr != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{
			"message": "Validation Error: " + parseErr.Error(),
			"code":    "validation_error",
		})
		return
	}

	// Create in database
	created, mappErr := DBCreateSingleModel(ctx, model)
	if mappErr != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": mappErr.Message})
		return
	}

	// Log and respond
	fmt.Printf("POST template-module.single-model - id: %s\n", *created.ID)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(created)
}

// ServerReadSingleModel handles GET /api/template-module/single-model/{id}
func ServerReadSingleModel(ctx *mapp.Context, w http.ResponseWriter, r *http.Request, modelID string) {
	// Read from database
	model, mappErr := DBReadSingleModel(ctx, modelID)
	if mappErr != nil {
		if mappErr.Code == "not_found" {
			fmt.Printf("GET template-module.single-model/%s - Not Found\n", modelID)
			w.WriteHeader(http.StatusNotFound)
			json.NewEncoder(w).Encode(map[string]string{
				"error": fmt.Sprintf("single model %s not found", modelID),
				"code":  "not_found",
			})
			return
		}
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": mappErr.Message})
		return
	}

	// Log and respond
	fmt.Printf("GET template-module.single-model/%s\n", modelID)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(model)
}

// ServerUpdateSingleModel handles PUT /api/template-module/single-model/{id}
func ServerUpdateSingleModel(ctx *mapp.Context, w http.ResponseWriter, r *http.Request, modelID string) {
	// Read request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "failed to read request body"})
		return
	}

	// Parse JSON into model
	model, parseErr := FromJSON(string(body))
	if parseErr != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{
			"message": "Validation Error: " + parseErr.Error(),
			"code":    "validation_error",
		})
		return
	}

	// Verify ID matches
	if model.ID != nil && *model.ID != modelID {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "single model id mismatch"})
		return
	}

	// Update in database
	updated, mappErr := DBUpdateSingleModel(ctx, modelID, model)
	if mappErr != nil {
		if mappErr.Code == "not_found" {
			fmt.Printf("PUT template-module.single-model/%s - Not Found\n", modelID)
			w.WriteHeader(http.StatusNotFound)
			json.NewEncoder(w).Encode(map[string]string{"error": "not found"})
			return
		}
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": mappErr.Message})
		return
	}

	// Log and respond
	fmt.Printf("PUT template-module.single-model/%s\n", modelID)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(updated)
}

// ServerDeleteSingleModel handles DELETE /api/template-module/single-model/{id}
func ServerDeleteSingleModel(ctx *mapp.Context, w http.ResponseWriter, r *http.Request, modelID string) {
	// Delete from database
	mappErr := DBDeleteSingleModel(ctx, modelID)
	if mappErr != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": mappErr.Message})
		return
	}

	// Log and respond
	fmt.Printf("DELETE template-module.single-model/%s\n", modelID)
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]bool{"acknowledged": true})
}

// ServerListSingleModel handles GET /api/template-module/single-model
func ServerListSingleModel(ctx *mapp.Context, w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	offset := 0
	limit := 25

	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if val, err := strconv.Atoi(offsetStr); err == nil {
			offset = val
		}
	}

	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if val, err := strconv.Atoi(limitStr); err == nil {
			limit = val
		}
	}

	// List from database
	result, mappErr := DBListSingleModel(ctx, offset, limit)
	if mappErr != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": mappErr.Message})
		return
	}

	// Log and respond
	fmt.Printf("GET template-module.single-model\n")
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(result)
}

// ServerRegisterRoutesSingleModel registers all single-model routes
func ServerRegisterRoutesSingleModel(ctx *mapp.Context) {
	// Model routes - /api/template-module/single-model
	http.HandleFunc("/api/template-module/single-model", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			ServerCreateSingleModel(ctx, w, r)
		case http.MethodGet:
			ServerListSingleModel(ctx, w, r)
		default:
			fmt.Printf("ERROR 405 template-module.single-model\n")
			w.WriteHeader(http.StatusMethodNotAllowed)
			json.NewEncoder(w).Encode(map[string]string{"error": "invalid request method"})
		}
	})

	// Instance routes - /api/template-module/single-model/{id}
	http.HandleFunc("/api/template-module/single-model/", func(w http.ResponseWriter, r *http.Request) {
		// Extract ID from path
		path := strings.TrimPrefix(r.URL.Path, "/api/template-module/single-model/")
		if path == "" {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		modelID := path

		switch r.Method {
		case http.MethodGet:
			ServerReadSingleModel(ctx, w, r, modelID)
		case http.MethodPut:
			ServerUpdateSingleModel(ctx, w, r, modelID)
		case http.MethodDelete:
			ServerDeleteSingleModel(ctx, w, r, modelID)
		default:
			fmt.Printf("ERROR 405 template-module.single-model/%s\n", modelID)
			w.WriteHeader(http.StatusMethodNotAllowed)
			json.NewEncoder(w).Encode(map[string]string{"error": "invalid request method"})
		}
	})
}
