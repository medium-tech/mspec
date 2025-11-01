#!/bin/bash

set -e

echo "=== Running Go Tests ==="

# Check if Python server is running
if ! curl -s http://localhost:5005/api/template-module/single-model > /dev/null 2>&1; then
    echo "Error: Python server is not running at http://localhost:5005"
    echo "Please start the server with: cd ../py && ./server.sh"
    exit 1
fi

echo "✓ Python server is running"

# Run unit tests
echo ""
echo "Running unit tests..."
go test -v ./template_module -run "^(TestFromJSON|TestToJSON|TestIsValidSingleEnum)"

# Run HTTP integration tests
echo ""
echo "Running HTTP integration tests (requires Python server)..."
go test -v ./template_module -run "^TestHttp"

# Run CLI tests
echo ""
echo "Running CLI tests..."
go test -v . -run "^TestCLI"

# Clean up test binary
if [ -f "./main_test" ]; then
    rm ./main_test
fi

echo ""
echo "=== All tests passed! ==="
