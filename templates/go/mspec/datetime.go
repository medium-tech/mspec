package mspec

import (
	"fmt"
	"strings"
	"time"
)

// DateTime wraps time.Time to handle custom datetime format
type DateTime struct {
	time.Time
}

const DatetimeFormat = "2006-01-02T15:04:05"

// UnmarshalJSON implements json.Unmarshaler for DateTime
func (ct *DateTime) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), "\"")
	t, err := time.Parse(DatetimeFormat, s)
	if err != nil {
		return err
	}
	ct.Time = t
	return nil
}

// MarshalJSON implements json.Marshaler for DateTime
func (ct DateTime) MarshalJSON() ([]byte, error) {
	formatted := fmt.Sprintf("\"%s\"", ct.Format(DatetimeFormat))
	return []byte(formatted), nil
}
