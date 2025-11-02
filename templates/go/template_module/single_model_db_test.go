package template_module

import (
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/medium-tech/mspec/templates/go/mapp"
)

// Helper to create a test context with a unique DB file for each test
func createTestContext(t *testing.T) *mapp.Context {
	dbFile := fmt.Sprintf("test_%s.db", t.Name())
	return &mapp.Context{
		ClientHost: "http://localhost:5005",
		DBFile:     dbFile,
	}
}

// Helper to cleanup test database
func cleanupTestDB(t *testing.T, ctx *mapp.Context) {
	mapp.ResetDB()
	dbPath := fmt.Sprintf("data/%s", ctx.DBFile)
	os.Remove(dbPath)
}

func TestDBCreateTableSingleModel(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	response, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if response["status"] != "success" {
		t.Errorf("Expected status=success, got %s", response["status"])
	}

	// Creating table again should not error (IF NOT EXISTS)
	response2, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Expected no error on second create, got %v", err)
	}
	if response2["status"] != "success" {
		t.Errorf("Expected status=success on second create, got %s", response2["status"])
	}
}

func TestDBCreateSingleModel(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Create table first
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	// Create a model
	model := &SingleModel{
		SingleBool:     true,
		SingleInt:      42,
		SingleFloat:    3.14,
		SingleString:   "test string",
		SingleEnum:     "red",
		SingleDatetime: mapp.DateTime{Time: time.Date(2024, 1, 1, 10, 0, 0, 0, time.UTC)},
	}

	created, mspecErr := DBCreateSingleModel(ctx, model)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}

	// Verify ID was assigned
	if created.ID == nil {
		t.Error("Expected ID to be assigned")
	} else if *created.ID != "1" {
		t.Errorf("Expected ID=1, got %s", *created.ID)
	}

	// Verify all fields are preserved
	if created.SingleBool != true {
		t.Error("SingleBool not preserved")
	}
	if created.SingleInt != 42 {
		t.Error("SingleInt not preserved")
	}
	if created.SingleFloat != 3.14 {
		t.Error("SingleFloat not preserved")
	}
	if created.SingleString != "test string" {
		t.Error("SingleString not preserved")
	}
	if created.SingleEnum != "red" {
		t.Error("SingleEnum not preserved")
	}
}

func TestDBReadSingleModel(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table and insert a record
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	model := &SingleModel{
		SingleBool:     false,
		SingleInt:      99,
		SingleFloat:    2.71,
		SingleString:   "read test",
		SingleEnum:     "green",
		SingleDatetime: mapp.DateTime{Time: time.Date(2024, 6, 15, 14, 30, 0, 0, time.UTC)},
	}
	created, _ := DBCreateSingleModel(ctx, model)

	// Test reading the record
	read, mspecErr := DBReadSingleModel(ctx, *created.ID)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}

	// Verify all fields match
	if *read.ID != *created.ID {
		t.Errorf("Expected ID=%s, got %s", *created.ID, *read.ID)
	}
	if read.SingleBool != false {
		t.Error("SingleBool mismatch")
	}
	if read.SingleInt != 99 {
		t.Error("SingleInt mismatch")
	}
	if read.SingleFloat != 2.71 {
		t.Error("SingleFloat mismatch")
	}
	if read.SingleString != "read test" {
		t.Error("SingleString mismatch")
	}
	if read.SingleEnum != "green" {
		t.Error("SingleEnum mismatch")
	}
}

func TestDBReadSingleModel_NotFound(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table but don't insert any records
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	// Try to read non-existent record
	_, mspecErr := DBReadSingleModel(ctx, "999")
	if mspecErr == nil {
		t.Fatal("Expected error for non-existent record")
	}
	if mspecErr.Code != "not_found" {
		t.Errorf("Expected code=not_found, got %s", mspecErr.Code)
	}
}

func TestDBUpdateSingleModel(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table and insert a record
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	original := &SingleModel{
		SingleBool:     true,
		SingleInt:      100,
		SingleFloat:    1.0,
		SingleString:   "original",
		SingleEnum:     "red",
		SingleDatetime: mapp.DateTime{Time: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)},
	}
	created, _ := DBCreateSingleModel(ctx, original)

	// Update the record
	updated := &SingleModel{
		SingleBool:     false,
		SingleInt:      200,
		SingleFloat:    2.0,
		SingleString:   "updated",
		SingleEnum:     "blue",
		SingleDatetime: mapp.DateTime{Time: time.Date(2024, 12, 31, 23, 59, 59, 0, time.UTC)},
	}

	result, mspecErr := DBUpdateSingleModel(ctx, *created.ID, updated)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}

	// Verify update result
	if *result.ID != *created.ID {
		t.Errorf("Expected ID=%s, got %s", *created.ID, *result.ID)
	}

	// Read back and verify all fields were updated
	read, _ := DBReadSingleModel(ctx, *created.ID)
	if read.SingleBool != false {
		t.Error("SingleBool not updated")
	}
	if read.SingleInt != 200 {
		t.Error("SingleInt not updated")
	}
	if read.SingleFloat != 2.0 {
		t.Error("SingleFloat not updated")
	}
	if read.SingleString != "updated" {
		t.Error("SingleString not updated")
	}
	if read.SingleEnum != "blue" {
		t.Error("SingleEnum not updated")
	}
}

func TestDBUpdateSingleModel_NotFound(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table but don't insert any records
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	model := &SingleModel{
		SingleBool:     true,
		SingleInt:      1,
		SingleFloat:    1.0,
		SingleString:   "test",
		SingleEnum:     "red",
		SingleDatetime: mapp.DateTime{Time: time.Now()},
	}

	// Try to update non-existent record
	_, mspecErr := DBUpdateSingleModel(ctx, "999", model)
	if mspecErr == nil {
		t.Fatal("Expected error for non-existent record")
	}
	if mspecErr.Code != "not_found" {
		t.Errorf("Expected code=not_found, got %s", mspecErr.Code)
	}
}

func TestDBDeleteSingleModel(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table and insert a record
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	model := &SingleModel{
		SingleBool:     true,
		SingleInt:      42,
		SingleFloat:    3.14,
		SingleString:   "to be deleted",
		SingleEnum:     "red",
		SingleDatetime: mapp.DateTime{Time: time.Now()},
	}
	created, _ := DBCreateSingleModel(ctx, model)

	// Delete the record
	mspecErr := DBDeleteSingleModel(ctx, *created.ID)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}

	// Verify it's gone
	_, readErr := DBReadSingleModel(ctx, *created.ID)
	if readErr == nil {
		t.Error("Expected record to be deleted")
	} else if readErr.Code != "not_found" {
		t.Errorf("Expected code=not_found, got %s", readErr.Code)
	}
}

func TestDBDeleteSingleModel_NotFound(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table but don't insert any records
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	// Deleting non-existent record should succeed (idempotent)
	mspecErr := DBDeleteSingleModel(ctx, "999")
	if mspecErr != nil {
		t.Fatalf("Expected no error for deleting non-existent record (idempotent), got %v", mspecErr)
	}
}

func TestDBListSingleModel(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	// Test empty list
	emptyList, mspecErr := DBListSingleModel(ctx, 0, 50)
	if mspecErr != nil {
		t.Fatalf("Expected no error for empty list, got %v", mspecErr)
	}
	if emptyList.Total != 0 {
		t.Errorf("Expected total=0 for empty list, got %d", emptyList.Total)
	}
	if len(emptyList.Items) != 0 {
		t.Errorf("Expected 0 items, got %d", len(emptyList.Items))
	}

	// Insert test records
	for i := 1; i <= 5; i++ {
		model := &SingleModel{
			SingleBool:     i%2 == 0,
			SingleInt:      i * 10,
			SingleFloat:    float64(i) * 1.1,
			SingleString:   fmt.Sprintf("item %d", i),
			SingleEnum:     []string{"red", "green", "blue"}[i%3],
			SingleDatetime: mapp.DateTime{Time: time.Date(2024, time.Month(i), 1, 0, 0, 0, 0, time.UTC)},
		}
		DBCreateSingleModel(ctx, model)
	}

	// Test listing all
	allList, mspecErr := DBListSingleModel(ctx, 0, 50)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}
	if allList.Total != 5 {
		t.Errorf("Expected total=5, got %d", allList.Total)
	}
	if len(allList.Items) != 5 {
		t.Errorf("Expected 5 items, got %d", len(allList.Items))
	}

	// Verify items are in order
	for i, item := range allList.Items {
		expectedID := fmt.Sprintf("%d", i+1)
		if *item.ID != expectedID {
			t.Errorf("Expected item %d to have ID=%s, got %s", i, expectedID, *item.ID)
		}
	}
}

func TestDBListSingleModel_Pagination(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Setup: create table and insert records
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	// Insert 10 records
	for i := 1; i <= 10; i++ {
		model := &SingleModel{
			SingleBool:     true,
			SingleInt:      i,
			SingleFloat:    float64(i),
			SingleString:   fmt.Sprintf("item %d", i),
			SingleEnum:     "red",
			SingleDatetime: mapp.DateTime{Time: time.Now()},
		}
		DBCreateSingleModel(ctx, model)
	}

	// Test first page
	page1, mspecErr := DBListSingleModel(ctx, 0, 3)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}
	if page1.Total != 10 {
		t.Errorf("Expected total=10, got %d", page1.Total)
	}
	if len(page1.Items) != 3 {
		t.Errorf("Expected 3 items on page 1, got %d", len(page1.Items))
	}
	if *page1.Items[0].ID != "1" {
		t.Errorf("Expected first item ID=1, got %s", *page1.Items[0].ID)
	}

	// Test second page
	page2, mspecErr := DBListSingleModel(ctx, 3, 3)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}
	if len(page2.Items) != 3 {
		t.Errorf("Expected 3 items on page 2, got %d", len(page2.Items))
	}
	if *page2.Items[0].ID != "4" {
		t.Errorf("Expected first item on page 2 ID=4, got %s", *page2.Items[0].ID)
	}

	// Test last page (partial)
	page4, mspecErr := DBListSingleModel(ctx, 9, 3)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}
	if len(page4.Items) != 1 {
		t.Errorf("Expected 1 item on last page, got %d", len(page4.Items))
	}
	if *page4.Items[0].ID != "10" {
		t.Errorf("Expected last item ID=10, got %s", *page4.Items[0].ID)
	}

	// Test beyond last page
	page5, mspecErr := DBListSingleModel(ctx, 20, 3)
	if mspecErr != nil {
		t.Fatalf("Expected no error, got %v", mspecErr)
	}
	if len(page5.Items) != 0 {
		t.Errorf("Expected 0 items beyond last page, got %d", len(page5.Items))
	}
	if page5.Total != 10 {
		t.Errorf("Expected total=10 even beyond last page, got %d", page5.Total)
	}
}

func TestDBFullCRUDCycle(t *testing.T) {
	ctx := createTestContext(t)
	defer cleanupTestDB(t, ctx)

	// Create table
	_, err := DBCreateTableSingleModel(ctx)
	if err != nil {
		t.Fatalf("Failed to create table: %v", err)
	}

	// Create
	original := &SingleModel{
		SingleBool:     true,
		SingleInt:      42,
		SingleFloat:    3.14159,
		SingleString:   "full cycle test",
		SingleEnum:     "green",
		SingleDatetime: mapp.DateTime{Time: time.Date(2024, 7, 4, 12, 0, 0, 0, time.UTC)},
	}
	created, mspecErr := DBCreateSingleModel(ctx, original)
	if mspecErr != nil {
		t.Fatalf("Create failed: %v", mspecErr)
	}
	modelID := *created.ID

	// Read
	read, mspecErr := DBReadSingleModel(ctx, modelID)
	if mspecErr != nil {
		t.Fatalf("Read failed: %v", mspecErr)
	}
	if read.SingleString != "full cycle test" {
		t.Error("Read returned wrong data")
	}

	// Update
	updated := &SingleModel{
		SingleBool:     false,
		SingleInt:      100,
		SingleFloat:    2.71828,
		SingleString:   "updated cycle test",
		SingleEnum:     "blue",
		SingleDatetime: mapp.DateTime{Time: time.Date(2024, 12, 25, 0, 0, 0, 0, time.UTC)},
	}
	_, mspecErr = DBUpdateSingleModel(ctx, modelID, updated)
	if mspecErr != nil {
		t.Fatalf("Update failed: %v", mspecErr)
	}

	// Read again to verify update
	readAfterUpdate, mspecErr := DBReadSingleModel(ctx, modelID)
	if mspecErr != nil {
		t.Fatalf("Read after update failed: %v", mspecErr)
	}
	if readAfterUpdate.SingleString != "updated cycle test" {
		t.Error("Update didn't persist")
	}
	if readAfterUpdate.SingleInt != 100 {
		t.Error("Update didn't persist all fields")
	}

	// List
	list, mspecErr := DBListSingleModel(ctx, 0, 50)
	if mspecErr != nil {
		t.Fatalf("List failed: %v", mspecErr)
	}
	if list.Total != 1 {
		t.Errorf("Expected 1 record in list, got %d", list.Total)
	}

	// Delete
	mspecErr = DBDeleteSingleModel(ctx, modelID)
	if mspecErr != nil {
		t.Fatalf("Delete failed: %v", mspecErr)
	}

	// Verify deletion
	_, mspecErr = DBReadSingleModel(ctx, modelID)
	if mspecErr == nil {
		t.Error("Record should be deleted")
	} else if mspecErr.Code != "not_found" {
		t.Errorf("Expected not_found after delete, got %s", mspecErr.Code)
	}

	// List should be empty
	emptyList, mspecErr := DBListSingleModel(ctx, 0, 50)
	if mspecErr != nil {
		t.Fatalf("List after delete failed: %v", mspecErr)
	}
	if emptyList.Total != 0 {
		t.Errorf("Expected 0 records after delete, got %d", emptyList.Total)
	}
}
