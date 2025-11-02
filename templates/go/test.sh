#!/bin/bash

set -e

echo "=== Running Go Tests ==="

# Check if port 5005 is already in use
if lsof -Pi :5005 -sTCP:LISTEN -t >/dev/null 2>&1; then
    lsof -Pi :5005 -sTCP:LISTEN
    echo -e "\nError: Port 5005 is already in use"
    echo "Please stop the server running on port 5005 before running tests"
    exit 1
fi

echo "Port 5005 is available"

# Build the server
echo ""
echo "Building Go binary for testing..."
go build -o main_test main.go

# Start the Go server in the background
echo ""
echo "Starting Go server on port 5005..."
MAPP_SERVER_PORT=5005 ./main_test server > /tmp/go-test-server.log 2>&1 &
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping Go server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    rm -f /tmp/go-test-server.log
    rm -f ./main_test
}

# Register cleanup function to run on script exit
trap cleanup EXIT INT TERM

# Wait for server to start
echo "Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5005/api/template-module/single-model > /dev/null 2>&1; then
        echo "Go server is running"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: Server failed to start within 30 seconds"
        cat /tmp/go-test-server.log
        exit 1
    fi
    sleep 0.1
done

# Run unit tests
echo ""
echo "Running unit tests..."
go test -v ./template_module -run "^(TestFromJSON|TestToJSON|TestIsValidSingleEnum)"

# Run HTTP integration tests
echo ""
echo "Running HTTP integration tests (using Go server)..."
go test -v ./template_module -run "^TestHttp"

# Run CLI tests
echo ""
echo "Running CLI tests..."
go test -v . -run "^TestCLI"

echo ""
echo "=== All tests passed! ==="
