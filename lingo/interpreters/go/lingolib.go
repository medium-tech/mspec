package lingolib

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

func ParseFile(path string) (map[string]interface{}, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("cannot read %s: %w", path, err)
	}
	var raw map[string]interface{}
	if err := yaml.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("cannot parse %s: %w", path, err)
	}
	lingo, ok := raw["lingo"].(map[string]interface{})
	if !ok || lingo["spec"] == nil {
		return nil, fmt.Errorf("missing lingo.spec in %s", path)
	}
	return raw, nil
}

func evalExpr(expr interface{}) (string, error) {
	m, ok := expr.(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("unsupported expression type")
	}
	if s, ok := m["str"]; ok {
		return fmt.Sprintf("%v", s), nil
	}
	return "", fmt.Errorf("unsupported expression: %v", m)
}

func ExecuteExe(doc map[string]interface{}) (string, error) {
	main, ok := doc["main"]
	if !ok {
		return "", fmt.Errorf("exe spec missing main")
	}
	return evalExpr(main)
}

func ExecuteFile(path string) (string, error) {
	doc, err := ParseFile(path)
	if err != nil {
		return "", err
	}
	lingo := doc["lingo"].(map[string]interface{})
	spec := fmt.Sprintf("%v", lingo["spec"])
	switch spec {
	case "exe":
		return ExecuteExe(doc)
	default:
		return "", fmt.Errorf("unsupported spec: %s", spec)
	}
}
