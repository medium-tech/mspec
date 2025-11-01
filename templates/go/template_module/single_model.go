package template_module

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/medium-tech/mspec/templates/go/mspec"
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
	ID             *string        `json:"id,omitempty"`
	SingleBool     bool           `json:"single_bool"`
	SingleInt      int            `json:"single_int"`
	SingleFloat    float64        `json:"single_float"`
	SingleString   string         `json:"single_string"`
	SingleEnum     string         `json:"single_enum"`
	SingleDatetime mspec.DateTime `json:"single_datetime"`
}

// ToJSON serializes the SingleModel to a JSON string
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

//
// http client
//

const DefaultHost = "http://localhost:5005"

func HttpCreateSingleModel(model *SingleModel) (*SingleModel, *mspec.MspecError) {
	// Convert to JSON for request
	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error marshaling JSON: %v", err), Code: "marshal_error"}
	}

	// Make HTTP request
	url := DefaultHost + "/api/template-module/single-model"
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error creating single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, &mspec.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mspec.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mspec.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	createdModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return createdModel, nil
}

func HttpReadSingleModel(modelID string) (*SingleModel, *mspec.MspecError) {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

	resp, err := http.Get(url)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error reading single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, &mspec.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mspec.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mspec.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	model, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return model, nil
}

func HttpUpdateSingleModel(modelID string, model *SingleModel) (*SingleModel, *mspec.MspecError) {
	// Set the ID if not already set
	if model.ID == nil {
		model.ID = &modelID
	}

	// Convert to JSON for request
	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error marshaling JSON: %v", err), Code: "marshal_error"}
	}

	// Make HTTP request
	url := DefaultHost + "/api/template-module/single-model/" + modelID
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error creating request: %v", err), Code: "request_error"}
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error updating single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, &mspec.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mspec.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mspec.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	updatedModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return updatedModel, nil
}

func HttpDeleteSingleModel(modelID string) *mspec.MspecError {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

	req, err := http.NewRequest("DELETE", url, nil)
	if err != nil {
		return &mspec.MspecError{Message: fmt.Sprintf("error creating request: %v", err), Code: "request_error"}
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return &mspec.MspecError{Message: fmt.Sprintf("error deleting single model: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return &mspec.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return &mspec.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode == 404 {
		return &mspec.MspecError{Message: fmt.Sprintf("single model %s not found", modelID), Code: "not_found"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return &mspec.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	return nil
}

type ListSingleModelResponse struct {
	Total int           `json:"total"`
	Items []SingleModel `json:"items"`
}

func HttpListSingleModel(offset int, limit int) (*ListSingleModelResponse, *mspec.MspecError) {
	url := fmt.Sprintf("%s/api/template-module/single-model?offset=%d&limit=%d", DefaultHost, offset, limit)

	resp, err := http.Get(url)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error listing single models: %v", err), Code: "http_error"}
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, &mspec.MspecError{Message: "authentication error", Code: "authentication_error"}
	} else if resp.StatusCode == 403 {
		return nil, &mspec.MspecError{Message: "forbidden", Code: "forbidden"}
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, &mspec.MspecError{Message: string(body), Code: fmt.Sprintf("http_%d", resp.StatusCode)}
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error reading response: %v", err), Code: "read_error"}
	}

	var listResponse ListSingleModelResponse
	err = json.Unmarshal(responseBody, &listResponse)
	if err != nil {
		return nil, &mspec.MspecError{Message: fmt.Sprintf("error parsing response: %v", err), Code: "parse_error"}
	}

	return &listResponse, nil
}

//
// cli wrappers
//

func CLICreateSingleModel(jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		errorOutput := mspec.MspecError{Message: fmt.Sprintf("error parsing JSON: %v", err), Code: "parse_error"}
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

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(createdModel, "", "  ")
	if err != nil {
		errorOutput := mspec.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
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

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(model, "", "  ")
	if err != nil {
		errorOutput := mspec.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}

func CLIUpdateSingleModel(modelID string, jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		errorOutput := mspec.MspecError{Message: fmt.Sprintf("error parsing JSON: %v", err), Code: "parse_error"}
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

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(updatedModel, "", "  ")
	if err != nil {
		errorOutput := mspec.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
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

	// Print success message as JSON
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

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(listResponse, "", "  ")
	if err != nil {
		errorOutput := mspec.MspecError{Message: fmt.Sprintf("error formatting JSON: %v", err), Code: "format_error"}
		jsonBytes, _ := json.MarshalIndent(errorOutput, "", "  ")
		fmt.Println(string(jsonBytes))
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}
