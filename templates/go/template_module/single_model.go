package template_module

import (
	"encoding/json"
	"os"
	"fmt"

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

func HttpCreateSingleModel(jsonData string) {
	model, err := FromJSON(jsonData)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing JSON: %v\n", err)
		return
	}
	model.Print()
	// TODO: Implement HTTP create logic
}

func HttpReadSingleModel(modelID string) {
	fmt.Printf("HttpReadSingleModel called with ID: %s\n", modelID)
	// TODO: Implement HTTP read logic
}

func HttpUpdateSingleModel(modelID string, jsonData string) {
	fmt.Printf("HttpUpdateSingleModel called with ID: %s and JSON: %s\n", modelID, jsonData)
	// TODO: Implement HTTP update logic
}

func HttpDeleteSingleModel(modelID string) {
	fmt.Printf("HttpDeleteSingleModel called with ID: %s\n", modelID)
	// TODO: Implement HTTP delete logic
}

func HttpListSingleModel(offset int, limit int) {
	fmt.Printf("HttpListSingleModel called with offset: %d, limit: %d\n", offset, limit)
	// TODO: Implement HTTP list logic
}