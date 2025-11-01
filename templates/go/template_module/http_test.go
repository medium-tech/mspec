package template_module

import (
	"testing"
	"time"

	"github.com/medium-tech/mspec/templates/go/mapp"
)

// These tests require the Python server to be running at http://localhost:5005

func TestHttpCreateSingleModel(t *testing.T) {
	model := &SingleModel{
		SingleBool:   false,
		SingleInt:    42,
		SingleFloat:  3.14,
		SingleString: "test create",
		SingleEnum:   "red",
		SingleDatetime: mapp.DateTime{
			Time: time.Date(2000, 1, 11, 12, 34, 56, 0, time.UTC),
		},
	}

	result, err := HttpCreateSingleModel(model)
	if err != nil {
		t.Fatalf("HttpCreateSingleModel failed: %v", err)
	}

	if result.ID == nil {
		t.Error("Expected ID to be set")
	}
	if result.SingleInt != 42 {
		t.Errorf("Expected SingleInt=42, got %d", result.SingleInt)
	}
	if result.SingleEnum != "red" {
		t.Errorf("Expected SingleEnum=red, got %s", result.SingleEnum)
	}
}

func TestHttpReadSingleModel(t *testing.T) {
	// First create a model
	model := &SingleModel{
		SingleBool:   true,
		SingleInt:    99,
		SingleFloat:  2.71,
		SingleString: "test read",
		SingleEnum:   "blue",
		SingleDatetime: mapp.DateTime{
			Time: time.Date(2000, 1, 11, 12, 34, 56, 0, time.UTC),
		},
	}

	created, err := HttpCreateSingleModel(model)
	if err != nil {
		t.Fatalf("HttpCreateSingleModel failed: %v", err)
	}

	if created.ID == nil {
		t.Fatal("Created model has no ID")
	}

	// Now read it back
	result, err := HttpReadSingleModel(*created.ID)
	if err != nil {
		t.Fatalf("HttpReadSingleModel failed: %v", err)
	}

	if result.ID == nil || *result.ID != *created.ID {
		t.Error("Read model ID doesn't match created ID")
	}
	if result.SingleInt != 99 {
		t.Errorf("Expected SingleInt=99, got %d", result.SingleInt)
	}
	if result.SingleEnum != "blue" {
		t.Errorf("Expected SingleEnum=blue, got %s", result.SingleEnum)
	}
}

func TestHttpReadSingleModel_NotFound(t *testing.T) {
	_, err := HttpReadSingleModel("nonexistent-id-12345")
	if err == nil {
		t.Error("Expected error for non-existent model")
	}
	if err.Code != "not_found" {
		t.Errorf("Expected error code 'not_found', got '%s'", err.Code)
	}
}

func TestHttpUpdateSingleModel(t *testing.T) {
	// First create a model
	model := &SingleModel{
		SingleBool:   true,
		SingleInt:    100,
		SingleFloat:  1.23,
		SingleString: "test update original",
		SingleEnum:   "green",
		SingleDatetime: mapp.DateTime{
			Time: time.Date(2000, 1, 11, 12, 34, 56, 0, time.UTC),
		},
	}

	created, err := HttpCreateSingleModel(model)
	if err != nil {
		t.Fatalf("HttpCreateSingleModel failed: %v", err)
	}

	if created.ID == nil {
		t.Fatal("Created model has no ID")
	}

	// Update it
	created.SingleString = "test update modified"
	created.SingleInt = 200

	result, err := HttpUpdateSingleModel(*created.ID, created)
	if err != nil {
		t.Fatalf("HttpUpdateSingleModel failed: %v", err)
	}

	if result.SingleString != "test update modified" {
		t.Errorf("Expected SingleString='test update modified', got '%s'", result.SingleString)
	}
	if result.SingleInt != 200 {
		t.Errorf("Expected SingleInt=200, got %d", result.SingleInt)
	}
}

func TestHttpDeleteSingleModel(t *testing.T) {
	// First create a model
	model := &SingleModel{
		SingleBool:   false,
		SingleInt:    77,
		SingleFloat:  9.99,
		SingleString: "test delete",
		SingleEnum:   "red",
		SingleDatetime: mapp.DateTime{
			Time: time.Date(2000, 1, 11, 12, 34, 56, 0, time.UTC),
		},
	}

	created, err := HttpCreateSingleModel(model)
	if err != nil {
		t.Fatalf("HttpCreateSingleModel failed: %v", err)
	}

	if created.ID == nil {
		t.Fatal("Created model has no ID")
	}

	// Delete it
	err = HttpDeleteSingleModel(*created.ID)
	if err != nil {
		t.Fatalf("HttpDeleteSingleModel failed: %v", err)
	}

	// Verify it's gone
	_, err = HttpReadSingleModel(*created.ID)
	if err == nil {
		t.Error("Expected error when reading deleted model")
	}
	if err.Code != "not_found" {
		t.Errorf("Expected error code 'not_found', got '%s'", err.Code)
	}
}

func TestHttpListSingleModel(t *testing.T) {
	// Create a few models first
	for i := 0; i < 3; i++ {
		model := &SingleModel{
			SingleBool:   i%2 == 0,
			SingleInt:    i,
			SingleFloat:  1.5,
			SingleString: "test list",
			SingleEnum:   "red",
			SingleDatetime: mapp.DateTime{
				Time: time.Date(2000, 1, 11, 12, 34, 56, 0, time.UTC),
			},
		}
		_, err := HttpCreateSingleModel(model)
		if err != nil {
			t.Fatalf("HttpCreateSingleModel failed: %v", err)
		}
	}

	// List models
	result, err := HttpListSingleModel(0, 10)
	if err != nil {
		t.Fatalf("HttpListSingleModel failed: %v", err)
	}

	if result.Total < 3 {
		t.Errorf("Expected at least 3 models, got %d", result.Total)
	}
	if len(result.Items) == 0 {
		t.Error("Expected items in response")
	}
}

func TestHttpListSingleModel_Pagination(t *testing.T) {
	result, err := HttpListSingleModel(0, 2)
	if err != nil {
		t.Fatalf("HttpListSingleModel failed: %v", err)
	}

	if len(result.Items) > 2 {
		t.Errorf("Expected at most 2 items with limit=2, got %d", len(result.Items))
	}
}
