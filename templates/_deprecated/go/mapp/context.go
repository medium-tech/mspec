package mapp

import (
	"os"
	"strconv"
)

//
// context
//

type Context struct {
	ServerPort int    `json:"server_port,omitempty"`
	ClientHost string `json:"client_host,omitempty"`
	DBFile     string `json:"db_file,omitempty"`
}

var MappServerPortDefault = 5005
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
	serverPort := os.Getenv("MAPP_SERVER_PORT")
	if serverPort == "" {
		serverPort = strconv.Itoa(MappServerPortDefault)
	}
	port, err := strconv.Atoi(serverPort)
	if err != nil {
		port = MappServerPortDefault
	}
	return &Context{
		ClientHost: clientHost,
		DBFile:     dbFile,
		ServerPort: port,
	}
}
