package main

import (
	"encoding/json"
	"os/exec"
	"strings"
	"testing"
)

// These tests build the binary and test the CLI interface
// They require the Python server to be running at http://localhost:5005

func buildBinary(t *testing.T) {
	cmd := exec.Command("go", "build", "-o", "main_test", "main.go")
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("Failed to build binary: %v\n%s", err, string(output))
	}
}

func runCLI(t *testing.T, args ...string) (string, int) {
	cmdArgs := append([]string{"./main_test"}, args...)
	cmd := exec.Command(cmdArgs[0], cmdArgs[1:]...)
	output, err := cmd.CombinedOutput()

	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			t.Fatalf("Failed to run command: %v", err)
		}
	}

	return string(output), exitCode
}

func TestCLI_Help(t *testing.T) {
	buildBinary(t)

	output, exitCode := runCLI(t, "--help")

	if exitCode != 0 {
		t.Errorf("Expected exit code 0, got %d", exitCode)
	}
	if !strings.Contains(output, "Usage:") {
		t.Error("Help output doesn't contain 'Usage:'")
	}
	if !strings.Contains(output, "template-module single-model http create") {
		t.Error("Help output doesn't contain 'template-module single-model http create'")
	}
}

func TestCLI_InvalidCommand(t *testing.T) {
	buildBinary(t)

	output, exitCode := runCLI(t, "invalid-command")

	if exitCode == 0 {
		t.Error("Expected non-zero exit code for invalid command")
	}
	if !strings.Contains(output, "Error") {
		t.Error("Expected error message")
	}
}

func TestCLI_CreateSingleModel(t *testing.T) {
	buildBinary(t)

	jsonInput := `{"single_bool":false,"single_int":42,"single_float":3.14,"single_string":"cli test","single_enum":"red","single_datetime":"2000-01-11T12:34:56"}`

	output, exitCode := runCLI(t, "template-module", "single-model", "http", "create", jsonInput)

	if exitCode != 0 {
		t.Errorf("Expected exit code 0, got %d. Output: %s", exitCode, output)
	}

	// Parse JSON output
	var result map[string]interface{}
	err := json.Unmarshal([]byte(output), &result)
	if err != nil {
		t.Fatalf("Failed to parse JSON output: %v\nOutput: %s", err, output)
	}

	// Verify structure
	if _, ok := result["id"]; !ok {
		t.Error("Output doesn't contain 'id' field")
	}
	if result["single_int"] != float64(42) {
		t.Errorf("Expected single_int=42, got %v", result["single_int"])
	}
	if result["single_string"] != "cli test" {
		t.Errorf("Expected single_string='cli test', got %v", result["single_string"])
	}
	if result["single_enum"] != "red" {
		t.Errorf("Expected single_enum='red', got %v", result["single_enum"])
	}
}

func TestCLI_CreateSingleModel_InvalidJSON(t *testing.T) {
	buildBinary(t)

	output, exitCode := runCLI(t, "template-module", "single-model", "http", "create", "{invalid json}")

	if exitCode == 0 {
		t.Error("Expected non-zero exit code for invalid JSON")
	}

	// Parse error JSON output
	var errorResult map[string]interface{}
	err := json.Unmarshal([]byte(output), &errorResult)
	if err != nil {
		t.Fatalf("Failed to parse error JSON output: %v\nOutput: %s", err, output)
	}

	// Verify error structure
	if _, ok := errorResult["message"]; !ok {
		t.Error("Error output doesn't contain 'message' field")
	}
	if _, ok := errorResult["code"]; !ok {
		t.Error("Error output doesn't contain 'code' field")
	}
	if errorResult["code"] != "parse_error" {
		t.Errorf("Expected code='parse_error', got %v", errorResult["code"])
	}
}

func TestCLI_CreateSingleModel_MissingRequiredField(t *testing.T) {
	buildBinary(t)

	jsonInput := `{"single_int":42}` // missing required fields

	output, exitCode := runCLI(t, "template-module", "single-model", "http", "create", jsonInput)

	if exitCode == 0 {
		t.Error("Expected non-zero exit code for missing required fields")
	}

	// Parse error JSON output
	var errorResult map[string]interface{}
	err := json.Unmarshal([]byte(output), &errorResult)
	if err != nil {
		t.Fatalf("Failed to parse error JSON output: %v\nOutput: %s", err, output)
	}

	if errorResult["code"] != "parse_error" {
		t.Errorf("Expected code='parse_error', got %v", errorResult["code"])
	}
}

func TestCLI_ReadSingleModel_NotFound(t *testing.T) {
	buildBinary(t)

	output, exitCode := runCLI(t, "template-module", "single-model", "http", "read", "nonexistent-id-99999")

	if exitCode == 0 {
		t.Error("Expected non-zero exit code for not found")
	}

	// Parse error JSON output
	var errorResult map[string]interface{}
	err := json.Unmarshal([]byte(output), &errorResult)
	if err != nil {
		t.Fatalf("Failed to parse error JSON output: %v\nOutput: %s", err, output)
	}

	if errorResult["code"] != "not_found" {
		t.Errorf("Expected code='not_found', got %v", errorResult["code"])
	}
	if !strings.Contains(errorResult["message"].(string), "not found") {
		t.Error("Error message doesn't contain 'not found'")
	}
}

func TestCLI_ListSingleModel(t *testing.T) {
	buildBinary(t)

	output, exitCode := runCLI(t, "template-module", "single-model", "http", "list", "--offset=0", "--limit=5")

	if exitCode != 0 {
		t.Errorf("Expected exit code 0, got %d. Output: %s", exitCode, output)
	}

	// Parse JSON output
	var result map[string]interface{}
	err := json.Unmarshal([]byte(output), &result)
	if err != nil {
		t.Fatalf("Failed to parse JSON output: %v\nOutput: %s", err, output)
	}

	// Verify structure
	if _, ok := result["total"]; !ok {
		t.Error("Output doesn't contain 'total' field")
	}
	if _, ok := result["items"]; !ok {
		t.Error("Output doesn't contain 'items' field")
	}

	items, ok := result["items"].([]interface{})
	if !ok {
		t.Error("'items' field is not an array")
	}

	if len(items) > 5 {
		t.Errorf("Expected at most 5 items with limit=5, got %d", len(items))
	}
}

func TestCLI_DeleteSingleModel(t *testing.T) {
	buildBinary(t)

	// First create a model to delete
	jsonInput := `{"single_bool":true,"single_int":999,"single_float":1.1,"single_string":"delete me","single_enum":"blue","single_datetime":"2000-01-11T12:34:56"}`
	createOutput, exitCode := runCLI(t, "template-module", "single-model", "http", "create", jsonInput)

	if exitCode != 0 {
		t.Fatalf("Failed to create model: %s", createOutput)
	}

	var created map[string]interface{}
	json.Unmarshal([]byte(createOutput), &created)
	modelID := created["id"].(string)

	// Delete it
	output, exitCode := runCLI(t, "template-module", "single-model", "http", "delete", modelID)

	if exitCode != 0 {
		t.Errorf("Expected exit code 0, got %d. Output: %s", exitCode, output)
	}

	// Parse JSON output
	var result map[string]interface{}
	err := json.Unmarshal([]byte(output), &result)
	if err != nil {
		t.Fatalf("Failed to parse JSON output: %v\nOutput: %s", err, output)
	}

	// Verify delete response structure
	if _, ok := result["message"]; !ok {
		t.Error("Output doesn't contain 'message' field")
	}
	if _, ok := result["id"]; !ok {
		t.Error("Output doesn't contain 'id' field")
	}
	if result["id"] != modelID {
		t.Errorf("Expected id='%s', got %v", modelID, result["id"])
	}
}

func TestCLI_UpdateSingleModel(t *testing.T) {
	buildBinary(t)

	// First create a model to update
	jsonInput := `{"single_bool":true,"single_int":100,"single_float":2.2,"single_string":"original","single_enum":"green","single_datetime":"2000-01-11T12:34:56"}`
	createOutput, exitCode := runCLI(t, "template-module", "single-model", "http", "create", jsonInput)

	if exitCode != 0 {
		t.Fatalf("Failed to create model: %s", createOutput)
	}

	var created map[string]interface{}
	json.Unmarshal([]byte(createOutput), &created)
	modelID := created["id"].(string)

	// Update it
	updateInput := `{"single_bool":false,"single_int":200,"single_float":3.3,"single_string":"updated","single_enum":"red","single_datetime":"2000-01-11T12:34:56"}`
	output, exitCode := runCLI(t, "template-module", "single-model", "http", "update", modelID, updateInput)

	if exitCode != 0 {
		t.Errorf("Expected exit code 0, got %d. Output: %s", exitCode, output)
	}

	// Parse JSON output
	var result map[string]interface{}
	err := json.Unmarshal([]byte(output), &result)
	if err != nil {
		t.Fatalf("Failed to parse JSON output: %v\nOutput: %s", err, output)
	}

	// Verify updated values
	if result["single_int"] != float64(200) {
		t.Errorf("Expected single_int=200, got %v", result["single_int"])
	}
	if result["single_string"] != "updated" {
		t.Errorf("Expected single_string='updated', got %v", result["single_string"])
	}
	if result["single_enum"] != "red" {
		t.Errorf("Expected single_enum='red', got %v", result["single_enum"])
	}
}
