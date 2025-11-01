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

// Print outputs the SingleModel to console
func (m *SingleModel) Print() {
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
	fmt.Printf("  SingleDatetime: %s\n", m.SingleDatetime.Format(mspec.DatetimeFormat))
	fmt.Printf("}\n")
}

//
// http client
//

const DefaultHost = "http://localhost:5005"

func HttpCreateSingleModel(jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing JSON: %v\n", err)
		os.Exit(1)
	}

	// Convert to JSON for request
	requestBody, err := json.Marshal(model)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling JSON: %v\n", err)
		os.Exit(1)
	}

	// Make HTTP request
	url := DefaultHost + "/api/template-module/single-model"
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating single model: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		fmt.Fprintf(os.Stderr, "Error creating single model: authentication error\n")
		os.Exit(1)
	} else if resp.StatusCode == 403 {
		fmt.Fprintf(os.Stderr, "Error creating single model: forbidden\n")
		os.Exit(1)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		fmt.Fprintf(os.Stderr, "Error creating single model: HTTP %d: %s\n", resp.StatusCode, string(body))
		os.Exit(1)
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading response: %v\n", err)
		os.Exit(1)
	}

	createdModel, err := FromJSON(string(responseBody))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing response: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Created:")
	createdModel.Print()
}

func HttpReadSingleModel(modelID string) {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

	resp, err := http.Get(url)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading single model: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		fmt.Fprintf(os.Stderr, "Error reading single model: authentication error\n")
		os.Exit(1)
	} else if resp.StatusCode == 403 {
		fmt.Fprintf(os.Stderr, "Error reading single model: forbidden\n")
		os.Exit(1)
	} else if resp.StatusCode == 404 {
		fmt.Fprintf(os.Stderr, "Error: single model %s not found\n", modelID)
		os.Exit(1)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		fmt.Fprintf(os.Stderr, "Error reading single model: HTTP %d: %s\n", resp.StatusCode, string(body))
		os.Exit(1)
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading response: %v\n", err)
		os.Exit(1)
	}

	model, err := FromJSON(string(responseBody))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing response: %v\n", err)
		os.Exit(1)
	}

	model.Print()
}

func HttpUpdateSingleModel(modelID string, jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing JSON: %v\n", err)
		os.Exit(1)
	}

	// Set the ID if not already set
	if model.ID == nil {
		model.ID = &modelID
	}

	// Convert to JSON for request
	requestBody, err := json.Marshal(model)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling JSON: %v\n", err)
		os.Exit(1)
	}

	// Make HTTP request
	url := DefaultHost + "/api/template-module/single-model/" + modelID
	req, err := http.NewRequest("PUT", url, bytes.NewBuffer(requestBody))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating request: %v\n", err)
		os.Exit(1)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error updating single model: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		fmt.Fprintf(os.Stderr, "Error updating single model: authentication error\n")
		os.Exit(1)
	} else if resp.StatusCode == 403 {
		fmt.Fprintf(os.Stderr, "Error updating single model: forbidden\n")
		os.Exit(1)
	} else if resp.StatusCode == 404 {
		fmt.Fprintf(os.Stderr, "Error: single model %s not found\n", modelID)
		os.Exit(1)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		fmt.Fprintf(os.Stderr, "Error updating single model: HTTP %d: %s\n", resp.StatusCode, string(body))
		os.Exit(1)
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading response: %v\n", err)
		os.Exit(1)
	}

	updatedModel, err := FromJSON(string(responseBody))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing response: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Updated:")
	updatedModel.Print()
}

func HttpDeleteSingleModel(modelID string) {
	url := DefaultHost + "/api/template-module/single-model/" + modelID

	req, err := http.NewRequest("DELETE", url, nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating request: %v\n", err)
		os.Exit(1)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error deleting single model: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		fmt.Fprintf(os.Stderr, "Error deleting single model: authentication error\n")
		os.Exit(1)
	} else if resp.StatusCode == 403 {
		fmt.Fprintf(os.Stderr, "Error deleting single model: forbidden\n")
		os.Exit(1)
	} else if resp.StatusCode == 404 {
		fmt.Fprintf(os.Stderr, "Error: single model %s not found\n", modelID)
		os.Exit(1)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		fmt.Fprintf(os.Stderr, "Error deleting single model: HTTP %d: %s\n", resp.StatusCode, string(body))
		os.Exit(1)
	}

	fmt.Printf("Deleted single model %s\n", modelID)
}

func HttpListSingleModel(offset int, limit int) {
	url := fmt.Sprintf("%s/api/template-module/single-model?offset=%d&limit=%d", DefaultHost, offset, limit)

	resp, err := http.Get(url)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error listing single models: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	// Handle HTTP errors
	if resp.StatusCode == 401 {
		fmt.Fprintf(os.Stderr, "Error listing single models: authentication error\n")
		os.Exit(1)
	} else if resp.StatusCode == 403 {
		fmt.Fprintf(os.Stderr, "Error listing single models: forbidden\n")
		os.Exit(1)
	} else if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		fmt.Fprintf(os.Stderr, "Error listing single models: HTTP %d: %s\n", resp.StatusCode, string(body))
		os.Exit(1)
	}

	// Parse response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading response: %v\n", err)
		os.Exit(1)
	}

	var listResponse struct {
		Total int           `json:"total"`
		Items []SingleModel `json:"items"`
	}

	err = json.Unmarshal(responseBody, &listResponse)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing response: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Total: %d\n", listResponse.Total)
	fmt.Printf("Showing %d items:\n", len(listResponse.Items))
	for i, model := range listResponse.Items {
		fmt.Printf("\n[%d] ", i+1)
		model.Print()
	}
}
