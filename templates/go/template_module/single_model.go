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

func HttpCreateSingleModel(model *SingleModel) (*SingleModel, error) {
	// Convert to JSON for request
	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, fmt.Errorf("error marshaling JSON: %w", err)
	}

	// Make HTTP request
	url := DefaultHost + "/api/template-module/single-model"
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, fmt.Errorf("error creating single model: %w", err)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, fmt.Errorf("authentication error")
	} else if resp.StatusCode == 403 {
		return nil, fmt.Errorf("forbidden")
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %w", err)
	}

	createdModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, fmt.Errorf("error parsing response: %w", err)
	}

	return createdModel, nil
}

func HttpReadSingleModel(modelID string) (*SingleModel, error) {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("error reading single model: %w", err)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, fmt.Errorf("authentication error")
	} else if resp.StatusCode == 403 {
		return nil, fmt.Errorf("forbidden")
	} else if resp.StatusCode == 404 {
		return nil, fmt.Errorf("single model %s not found", modelID)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %w", err)
	}

	model, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, fmt.Errorf("error parsing response: %w", err)
	}

	return model, nil
}

func HttpUpdateSingleModel(modelID string, model *SingleModel) (*SingleModel, error) {
	// Set the ID if not already set
	if model.ID == nil {
		model.ID = &modelID
	}

	// Convert to JSON for request
	requestBody, err := json.Marshal(model)
	if err != nil {
		return nil, fmt.Errorf("error marshaling JSON: %w", err)
	}

	// Make HTTP request
	url := DefaultHost + "/api/template-module/single-model/" + modelID
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error updating single model: %w", err)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, fmt.Errorf("authentication error")
	} else if resp.StatusCode == 403 {
		return nil, fmt.Errorf("forbidden")
	} else if resp.StatusCode == 404 {
		return nil, fmt.Errorf("single model %s not found", modelID)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %w", err)
	}

	updatedModel, err := FromJSON(string(responseBody))
	if err != nil {
		return nil, fmt.Errorf("error parsing response: %w", err)
	}

	return updatedModel, nil
}

func HttpDeleteSingleModel(modelID string) error {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

	req, err := http.NewRequest("DELETE", url, nil)
	if err != nil {
		return fmt.Errorf("error creating request: %w", err)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("error deleting single model: %w", err)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return fmt.Errorf("authentication error")
	} else if resp.StatusCode == 403 {
		return fmt.Errorf("forbidden")
	} else if resp.StatusCode == 404 {
		return fmt.Errorf("single model %s not found", modelID)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

type ListSingleModelResponse struct {
	Total int           `json:"total"`
	Items []SingleModel `json:"items"`
}

func HttpListSingleModel(offset int, limit int) (*ListSingleModelResponse, error) {
	url := fmt.Sprintf("%s/api/template-module/single-model?offset=%d&limit=%d", DefaultHost, offset, limit)

	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("error listing single models: %w", err)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		return nil, fmt.Errorf("authentication error")
	} else if resp.StatusCode == 403 {
		return nil, fmt.Errorf("forbidden")
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %w", err)
	}

	var listResponse ListSingleModelResponse
	err = json.Unmarshal(responseBody, &listResponse)
	if err != nil {
		return nil, fmt.Errorf("error parsing response: %w", err)
	}

	return &listResponse, nil
}

//
// cli wrappers
//

func CLICreateSingleModel(jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing JSON: %v\n", err)
		os.Exit(1)
	}

	createdModel, err := HttpCreateSingleModel(model)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating single model: %v\n", err)
		os.Exit(1)
	}

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(createdModel, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error formatting JSON: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Created:")
	fmt.Println(string(jsonBytes))
}

func CLIReadSingleModel(modelID string) {
	model, err := HttpReadSingleModel(modelID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading single model: %v\n", err)
		os.Exit(1)
	}

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(model, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error formatting JSON: %v\n", err)
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}

func CLIUpdateSingleModel(modelID string, jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing JSON: %v\n", err)
		os.Exit(1)
	}

	updatedModel, err := HttpUpdateSingleModel(modelID, model)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error updating single model: %v\n", err)
		os.Exit(1)
	}

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(updatedModel, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error formatting JSON: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Updated:")
	fmt.Println(string(jsonBytes))
}

func CLIDeleteSingleModel(modelID string) {
	err := HttpDeleteSingleModel(modelID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error deleting single model: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Deleted single model %s\n", modelID)
}

func CLIListSingleModel(offset int, limit int) {
	listResponse, err := HttpListSingleModel(offset, limit)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error listing single models: %v\n", err)
		os.Exit(1)
	}

	// Pretty print JSON
	jsonBytes, err := json.MarshalIndent(listResponse, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error formatting JSON: %v\n", err)
		os.Exit(1)
	}
	fmt.Println(string(jsonBytes))
}
