package mapp

import (
	"fmt"
	"strings"
	"time"
)

//
// custom error
//

type MappError struct {
	Message string `json:"message"`
	Code    string `json:"code,omitempty"`
}

func (e *MappError) Error() string {
	return fmt.Sprintf("MappError :: %s :: %s", e.Code, e.Message)
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
