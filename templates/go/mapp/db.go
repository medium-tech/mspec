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

// GetDB returns a singleton SQLite database connection using the path from context
func GetDB(ctx *Context) (*sql.DB, error) {
	dbOnce.Do(func() {
		// Get database path from context
		dbPath := ctx.DBFile

		// If it's a relative path, put it in the data directory
		if !filepath.IsAbs(dbPath) {
			dbPath = filepath.Join("data", dbPath)
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
