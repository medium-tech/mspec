package mapp

import (
	"database/sql"
	"os"
	"path/filepath"
	"sync"

	_ "modernc.org/sqlite"
)

var (
	db      *sql.DB
	dbOnce  sync.Once
	dbErr   error
	dbPath  string
	dbMutex sync.Mutex
)

// ResetDB closes the current database connection and resets the singleton
// This is primarily for testing purposes
func ResetDB() {
	dbMutex.Lock()
	defer dbMutex.Unlock()

	if db != nil {
		db.Close()
	}
	db = nil
	dbErr = nil
	dbPath = ""
	dbOnce = sync.Once{}
}

// GetDB returns a singleton SQLite database connection using the path from context
func GetDB(ctx *Context) (*sql.DB, error) {
	dbMutex.Lock()
	defer dbMutex.Unlock()

	// Get database path from context
	contextDBPath := ctx.DBFile
	if !filepath.IsAbs(contextDBPath) {
		contextDBPath = filepath.Join("data", contextDBPath)
	}

	// If we already have a connection to a different database, reset
	if db != nil && dbPath != contextDBPath {
		db.Close()
		db = nil
		dbErr = nil
		dbOnce = sync.Once{}
	}

	dbOnce.Do(func() {
		dbPath = contextDBPath

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
