package template_module

import (
	"strings"
	"testing"
	"time"

	"github.com/medium-tech/mspec/templates/go/mapp"
)

//
// JSON parsing tests
//

func TestFromJSON_Valid(t *testing.T) {
	jsonStr := `{
		"single_bool": true,
		"single_int": 42,
		"single_float": 3.14,
		"single_string": "test",
		"single_enum": "red",
		"single_datetime": "2000-01-11T12:34:56"
	}`

	model, err := FromJSON(jsonStr)
	if err != nil {
		t.Fatalf("FromJSON failed: %v", err)
	}

	if model.SingleBool != true {
		t.Errorf("Expected SingleBool=true, got %v", model.SingleBool)
	}
	if model.SingleInt != 42 {
		t.Errorf("Expected SingleInt=42, got %d", model.SingleInt)
	}
	if model.SingleFloat != 3.14 {
		t.Errorf("Expected SingleFloat=3.14, got %f", model.SingleFloat)
	}
	if model.SingleString != "test" {
		t.Errorf("Expected SingleString=test, got %s", model.SingleString)
	}
	if model.SingleEnum != "red" {
		t.Errorf("Expected SingleEnum=red, got %s", model.SingleEnum)
	}
}

func TestFromJSON_RequiredFields(t *testing.T) {
	testCases := []struct {
		name     string
		json     string
		expected string
	}{
		{
			name:     "missing single_bool",
			json:     `{"single_int":42,"single_float":3.14,"single_string":"test","single_enum":"red","single_datetime":"2000-01-11T12:34:56"}`,
			expected: "missing required field: single_bool",
		},
		{
			name:     "missing single_int",
			json:     `{"single_bool":true,"single_float":3.14,"single_string":"test","single_enum":"red","single_datetime":"2000-01-11T12:34:56"}`,
			expected: "missing required field: single_int",
		},
		{
			name:     "missing single_datetime",
			json:     `{"single_bool":true,"single_int":42,"single_float":3.14,"single_string":"test","single_enum":"red"}`,
			expected: "missing required field: single_datetime",
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := FromJSON(tc.json)
			if err == nil {
				t.Error("Expected error for missing required field")
			}
			if !strings.Contains(err.Error(), tc.expected) {
				t.Errorf("Expected error to contain '%s', got: %v", tc.expected, err)
			}
		})
	}
}

func TestFromJSON_ExtraFields(t *testing.T) {
	jsonStr := `{
		"single_bool": true,
		"single_int": 42,
		"single_float": 3.14,
		"single_string": "test",
		"single_enum": "red",
		"single_datetime": "2000-01-11T12:34:56",
		"extra_field": "not allowed"
	}`

	_, err := FromJSON(jsonStr)
	if err == nil {
		t.Error("Expected error for extra field")
	}
	if !strings.Contains(err.Error(), "extra field found: extra_field") {
		t.Errorf("Expected 'extra field found' error, got: %v", err)
	}
}

func TestFromJSON_InvalidEnum(t *testing.T) {
	jsonStr := `{
		"single_bool": true,
		"single_int": 42,
		"single_float": 3.14,
		"single_string": "test",
		"single_enum": "purple",
		"single_datetime": "2000-01-11T12:34:56"
	}`

	_, err := FromJSON(jsonStr)
	if err == nil {
		t.Error("Expected error for invalid enum value")
	}
	if !strings.Contains(err.Error(), "invalid enum value") {
		t.Errorf("Expected 'invalid enum value' error, got: %v", err)
	}
}

func TestFromJSON_InvalidDatetime(t *testing.T) {
	jsonStr := `{
		"single_bool": true,
		"single_int": 42,
		"single_float": 3.14,
		"single_string": "test",
		"single_enum": "red",
		"single_datetime": "invalid-date"
	}`

	_, err := FromJSON(jsonStr)
	if err == nil {
		t.Error("Expected error for invalid datetime")
	}
}

//
// ToJSON tests
//

func TestToJSON(t *testing.T) {
	id := "test123"
	model := &SingleModel{
		ID:           &id,
		SingleBool:   true,
		SingleInt:    42,
		SingleFloat:  3.14,
		SingleString: "test",
		SingleEnum:   "red",
		SingleDatetime: mapp.DateTime{
			Time: time.Date(2000, 1, 11, 12, 34, 56, 0, time.UTC),
		},
	}

	jsonStr, err := model.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}

	if !strings.Contains(jsonStr, `"id":"test123"`) {
		t.Error("JSON doesn't contain expected id")
	}
	if !strings.Contains(jsonStr, `"single_int":42`) {
		t.Error("JSON doesn't contain expected single_int")
	}
	if !strings.Contains(jsonStr, `"single_enum":"red"`) {
		t.Error("JSON doesn't contain expected single_enum")
	}
	if !strings.Contains(jsonStr, `"single_datetime":"2000-01-11T12:34:56"`) {
		t.Error("JSON doesn't contain expected single_datetime")
	}
}

//
// Enum validation tests
//

func TestIsValidSingleEnum(t *testing.T) {
	validEnums := []string{"red", "green", "blue"}
	for _, enum := range validEnums {
		if !IsValidSingleEnum(enum) {
			t.Errorf("Expected %s to be valid", enum)
		}
	}

	invalidEnums := []string{"purple", "yellow", "", "RED"}
	for _, enum := range invalidEnums {
		if IsValidSingleEnum(enum) {
			t.Errorf("Expected %s to be invalid", enum)
		}
	}
}
