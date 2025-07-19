# Test Documentation for claude-interface

## Overview
This test suite validates the Claude CLI interface functionality, ensuring reliable command execution, proper error handling, response parsing, and retry mechanisms. The tests verify that the system can successfully communicate with Claude CLI, handle various failure scenarios, and maintain data integrity throughout the process.

## Test Cases

### Test successful Claude command execution
- **Description**: Verifies that Claude commands execute correctly and return expected results
- **Expected behavior**: Command executes without errors, returns valid response within timeout period
- **Test data/setup required**: Mock Claude CLI executable, sample command strings, expected response formats

### Test retry mechanism with transient failures
- **Description**: Validates automatic retry logic when encountering temporary failures
- **Expected behavior**: System retries failed commands according to configured retry policy, eventually succeeds or fails gracefully
- **Test data/setup required**: Mock failures with different error codes, retry configuration settings, success on nth attempt scenarios

### Test JSON extraction from Claude responses
- **Description**: Ensures correct parsing of JSON data from Claude's text responses
- **Expected behavior**: Successfully extracts valid JSON objects from mixed text/JSON responses
- **Test data/setup required**: Sample Claude responses with embedded JSON, various JSON formats and structures

### Test timeout handling for long-running commands
- **Description**: Verifies proper handling when Claude commands exceed configured timeout
- **Expected behavior**: Command terminates gracefully after timeout, appropriate error is raised
- **Test data/setup required**: Long-running command simulations, timeout configurations, partial response scenarios

### Test error parsing and exception handling
- **Description**: Validates parsing of error messages and proper exception propagation
- **Expected behavior**: Error messages are correctly extracted, appropriate exceptions raised with context
- **Test data/setup required**: Various error response formats, stderr outputs, exit codes

### Test response validation against JSON schema
- **Description**: Ensures Claude responses conform to expected JSON schemas
- **Expected behavior**: Valid responses pass schema validation, invalid responses are rejected with clear errors
- **Test data/setup required**: JSON schemas for different response types, valid and invalid response samples

### Test command formatting and escaping
- **Description**: Verifies proper formatting and escaping of commands sent to Claude
- **Expected behavior**: Special characters are properly escaped, commands are formatted correctly for subprocess execution
- **Test data/setup required**: Commands with special characters, quotes, newlines, and other escape sequences

### Test subprocess communication and buffering
- **Description**: Validates reliable communication between Python process and Claude subprocess
- **Expected behavior**: Data flows correctly through stdin/stdout/stderr, no buffer overflows or data loss
- **Test data/setup required**: Large payloads, streaming responses, various buffer sizes

## Edge Cases

### Claude CLI not installed or not in PATH
- **Scenario description**: System attempts to execute Claude commands when CLI is missing
- **How to test**: Remove Claude from PATH or rename executable
- **Expected handling**: Clear error message indicating Claude CLI is not found, suggestions for installation

### Malformed JSON in Claude response
- **Scenario description**: Claude returns invalid JSON that cannot be parsed
- **How to test**: Mock responses with syntax errors, truncated JSON, mixed formats
- **Expected handling**: Graceful degradation, attempt to extract partial data, clear error reporting

### Partial JSON response due to timeout
- **Scenario description**: Timeout occurs mid-JSON response, resulting in incomplete data
- **How to test**: Simulate timeout during JSON streaming
- **Expected handling**: Attempt to parse partial JSON, return available data with warning

### Unicode and special characters in responses
- **Scenario description**: Claude returns responses containing unicode, emojis, or special characters
- **How to test**: Mock responses with various character encodings and special symbols
- **Expected handling**: Proper encoding/decoding, no data corruption or crashes

### Concurrent Claude processes interfering
- **Scenario description**: Multiple Claude processes running simultaneously cause conflicts
- **How to test**: Launch multiple test instances in parallel
- **Expected handling**: Process isolation, no shared state conflicts, proper resource cleanup

### Rate limiting from Claude API
- **Scenario description**: Claude API enforces rate limits, rejecting requests
- **How to test**: Simulate rate limit responses, rapid request sequences
- **Expected handling**: Exponential backoff, queuing mechanism, clear rate limit error messages

### Memory issues with large responses
- **Scenario description**: Claude returns extremely large responses that strain memory
- **How to test**: Mock very large response payloads
- **Expected handling**: Streaming processing, memory-efficient parsing, graceful OOM handling

### Network interruptions during execution
- **Scenario description**: Network connection drops while Claude command is executing
- **How to test**: Simulate network failures at various points
- **Expected handling**: Appropriate timeout, retry logic for recoverable failures, clear network error messages

## Dependencies

- **pytest**: Core testing framework for organizing and running tests
- **pytest-mock**: Provides advanced mocking capabilities for simulating Claude CLI behavior
- **pytest-cov**: Generates code coverage reports to ensure comprehensive testing
- **pytest-timeout**: Prevents tests from hanging by enforcing time limits
- **jsonschema**: Validates JSON responses against defined schemas

## Test Execution

Run all tests:
```bash
pytest tests/test_claude_interface.py -v
```

Run with coverage:
```bash
pytest tests/test_claude_interface.py --cov=claude_interface --cov-report=html
```

Run specific test class:
```bash
pytest tests/test_claude_interface.py::ClaudeInterfaceUnitTests -v
```

Run with timeout enforcement:
```bash
pytest tests/test_claude_interface.py --timeout=30
```

Run in parallel:
```bash
pytest tests/test_claude_interface.py -n auto
```
