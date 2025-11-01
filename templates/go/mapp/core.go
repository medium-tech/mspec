package mapp

import (
	"fmt"
	"os"
	"strings"
	"time"
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

//
// custom error
//

type MspecError struct {
	Message string `json:"message"`
	Code    string `json:"code,omitempty"`
}

func (e *MspecError) Error() string {
	return fmt.Sprintf("MspecError :: %s :: %s", e.Code, e.Message)
}

//
// custom datetime format
//

type DateTime struct {
	time.Time
}

const DatetimeFormat = "2006-01-02T15:04:05"

func (ct *DateTime) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), "\"")
	t, err := time.Parse(DatetimeFormat, s)
	if err != nil {
		return err
	}
	ct.Time = t
	return nil
}

func (ct DateTime) MarshalJSON() ([]byte, error) {
	formatted := fmt.Sprintf("\"%s\"", ct.Format(DatetimeFormat))
	return []byte(formatted), nil
}
