package mapp

import (
	"database/sql"
	"os"
	"path/filepath"
	"sync"

	_ "modernc.org/sqlite"
)

var (
	db     *sql.DB
	dbOnce sync.Once
	dbErr  error
)

// GetDB returns a singleton SQLite database connection
func GetDB() (*sql.DB, error) {
	dbOnce.Do(func() {
		// Get database path from environment or use default
		dbPath := os.Getenv("MSPEC_DB_PATH")
		if dbPath == "" {
			// Default to ./data/app.db
			dbPath = filepath.Join("data", "app.db")
		}

		// Ensure the directory exists
		dir := filepath.Dir(dbPath)
		if err := os.MkdirAll(dir, 0755); err != nil {
			dbErr = err
			return
		}

		// Open database connection
		db, dbErr = sql.Open("sqlite", dbPath)
		if dbErr != nil {
			return
		}

		// Enable foreign keys
		_, dbErr = db.Exec("PRAGMA foreign_keys = ON")
	})

	return db, dbErr
}
