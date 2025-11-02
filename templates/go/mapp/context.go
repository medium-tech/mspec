package mapp

import (
	"os"
)

//
// context
//

type Context struct {
	ClientHost string `json:"client_host,omitempty"`
	DBFile     string `json:"db_file,omitempty"`
}

var MappClientHostDefault = "http://localhost:5005"
var MappDBFileDefault = "db.sqlite3"

func ContextFromEnv() *Context {
	clientHost := os.Getenv("MAPP_CLIENT_HOST")
	if clientHost == "" {
		clientHost = MappClientHostDefault
	}
	dbFile := os.Getenv("MAPP_DB_FILE")
	if dbFile == "" {
		dbFile = MappDBFileDefault
	}

	return &Context{
		ClientHost: clientHost,
		DBFile:     dbFile,
	}
}
