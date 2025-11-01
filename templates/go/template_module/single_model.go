package template_module

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
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

const DefaultHost = "http://localhost:5005"

func HttpCreateSingleModel(model *SingleModel) (*SingleModel, *mapp.MspecError) {
	// Convert to JSON for request //

	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, &mapp.MspecError{Message: fmt.Sprintf("error marshaling JSON: %v", err), Code: "marshal_error"}
	}

	// Make HTTP request //

	url := DefaultHost + "/api/template-module/single-model"
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

func HttpReadSingleModel(modelID string) (*SingleModel, *mapp.MspecError) {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

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

func HttpUpdateSingleModel(modelID string, model *SingleModel) (*SingleModel, *mapp.MspecError) {
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

	url := DefaultHost + "/api/template-module/single-model/" + modelID
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

func HttpDeleteSingleModel(modelID string) *mapp.MspecError {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

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

func HttpListSingleModel(offset int, limit int) (*ListSingleModelResponse, *mapp.MspecError) {
	url := fmt.Sprintf("%s/api/template-module/single-model?offset=%d&limit=%d", DefaultHost, offset, limit)

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
// cli wrappers
//

func CLIParseSingleModel(args []string) *mapp.MspecError {

	command := args[2]

	switch command {
	case "http":
		return CLIParseSingleModelHttp(args)
	default:
		fmt.Fprintf(os.Stderr, "Error: unknown command '%s'\n", command)
		os.Exit(1)
	}

	return nil
}

func CLIParseSingleModelHttp(args []string) *mapp.MspecError {
	action := args[3]

	switch action {
	case "create":
		if len(args) < 5 {
			fmt.Fprintln(os.Stderr, "Error: missing JSON string for create")
			os.Exit(1)
		}
		CLICreateSingleModel(args[4])
	case "read":
		if len(args) < 5 {
			fmt.Fprintln(os.Stderr, "Error: missing model ID for read")
			os.Exit(1)
		}
		CLIReadSingleModel(args[4])
	case "update":
		if len(args) < 6 {
			fmt.Fprintln(os.Stderr, "Error: missing model ID or JSON string for update")
			os.Exit(1)
		}
		CLIUpdateSingleModel(args[4], args[5])
	case "delete":
		if len(args) < 5 {
			fmt.Fprintln(os.Stderr, "Error: missing model ID for delete")
			os.Exit(1)
		}
		CLIDeleteSingleModel(args[4])
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
		CLIListSingleModel(offset, limit)
	default:
		fmt.Fprintf(os.Stderr, "Error: unknown action '%s'\n", action)
		os.Exit(1)
	}

	return nil
}

func CLICreateSingleModel(jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		errorOutput := mapp.MspecError{Message: fmt.Sprintf("error parsing JSON: %v", err), Code: "parse_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	createdModel, mspecErr := HttpCreateSingleModel(model)
	if mspecErr != nil {
		jsonBytes, _ := json.MarshalIndent(mspecErr, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	jsonBytes, err := json.MarshalIndent(createdModel, "", "  ")
	if err != nil {
		errorOutput := mapp.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}

func CLIReadSingleModel(modelID string) {
	model, mspecErr := HttpReadSingleModel(modelID)
	if mspecErr != nil {
		jsonBytes, _ := json.MarshalIndent(mspecErr, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	jsonBytes, err := json.MarshalIndent(model, "", "  ")
	if err != nil {
		errorOutput := mapp.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}

func CLIUpdateSingleModel(modelID string, jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		errorOutput := mapp.MspecError{Message: fmt.Sprintf("error parsing JSON: %v", err), Code: "parse_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	updatedModel, mspecErr := HttpUpdateSingleModel(modelID, model)
	if mspecErr != nil {
		jsonBytes, _ := json.MarshalIndent(mspecErr, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	jsonBytes, err := json.MarshalIndent(updatedModel, "", "  ")
	if err != nil {
		errorOutput := mapp.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}

func CLIDeleteSingleModel(modelID string) {
	mspecErr := HttpDeleteSingleModel(modelID)
	if mspecErr != nil {
		jsonBytes, _ := json.MarshalIndent(mspecErr, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	response := map[string]string{
		"message": fmt.Sprintf("deleted single model %s", modelID),
		"id":      modelID,
	}
	jsonBytes, _ := json.MarshalIndent(response, "", "  ")
	fmt.Println(string(jsonBytes))
}

func CLIListSingleModel(offset int, limit int) {
	listResponse, mspecErr := HttpListSingleModel(offset, limit)
	if mspecErr != nil {
		jsonBytes, _ := json.MarshalIndent(mspecErr, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}

	jsonBytes, err := json.MarshalIndent(listResponse, "", "  ")
	if err != nil {
		errorOutput := mapp.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}
