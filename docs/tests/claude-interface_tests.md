# Test Documentation for claude-interface

## Overview
This test suite validates the ClaudeInterface module, which handles interactions with the Claude CLI tool. The tests ensure reliable command execution, JSON response parsing, error handling, retry mechanisms, and connection validation. The module is critical for integrating Claude's capabilities into the application workflow.

## Test Cases

### Test successful Claude CLI execution with valid prompt
- **Description**: Verifies that the Claude CLI can be invoked successfully with a valid prompt and returns expected output
- **Expected behavior**: Claude CLI executes without errors and returns a valid response
- **Test data/setup required**: Valid Claude CLI installation, sample prompt text, mock subprocess response

### Test JSON extraction from various output formats (code blocks, inline, mixed text)
- **Description**: Validates the JSONExtractor component's ability to parse JSON from different response formats
- **Expected behavior**: JSON is correctly extracted from markdown code blocks, inline JSON, and mixed text responses
- **Test data/setup required**: Sample responses with JSON in various formats: ```json blocks, inline `{...}`, and embedded in prose

### Test retry mechanism with different error types (JSONDecodeError, ValueError)
- **Description**: Ensures the RetryHandler properly attempts to recover from parsing errors
- **Expected behavior**: System retries with enhanced prompts when JSON parsing fails, up to configured retry limit
- **Test data/setup required**: Mock responses that trigger JSONDecodeError and ValueError, retry configuration settings

### Test timeout handling for long-running Claude operations
- **Description**: Validates proper handling when Claude operations exceed the configured timeout
- **Expected behavior**: Operation terminates gracefully after timeout, appropriate error is raised
- **Test data/setup required**: Mock subprocess that simulates long-running operation, timeout configuration

### Test connection validation with Claude CLI
- **Description**: Verifies the ConnectionValidator can detect if Claude CLI is properly installed and accessible
- **Expected behavior**: Returns true when Claude CLI is available, false when not found or misconfigured
- **Test data/setup required**: Mock PATH configurations, subprocess responses for version checks

### Test prompt enhancement after failed attempts
- **Description**: Validates that prompts are properly enhanced with additional instructions after parsing failures
- **Expected behavior**: Subsequent attempts include clearer JSON formatting instructions
- **Test data/setup required**: Initial prompt, expected enhanced prompt format, retry counter

### Test validator integration during execution
- **Description**: Ensures validators are properly invoked during the execution pipeline
- **Expected behavior**: Validators run before/after Claude execution, validation failures prevent execution
- **Test data/setup required**: Mock validator implementations, valid and invalid validation scenarios

## Edge Cases

### Claude CLI not installed or not in PATH
- **Scenario description**: System attempts to execute Claude when CLI tool is not available
- **How to test**: Remove Claude from PATH or mock subprocess to return command not found error
- **Expected handling**: Clear error message indicating Claude CLI is not installed, no retries attempted

### Malformed JSON embedded in natural language response
- **Scenario description**: Claude returns JSON-like content that is syntactically incorrect
- **How to test**: Provide responses with missing quotes, trailing commas, or unclosed brackets
- **Expected handling**: JSONExtractor attempts multiple parsing strategies, triggers retry mechanism if all fail

### Nested JSON objects with complex structures
- **Scenario description**: Response contains deeply nested JSON with arrays and objects
- **How to test**: Generate responses with 3+ levels of nesting, mixed arrays and objects
- **Expected handling**: Successful parsing regardless of depth, maintains structure integrity

### Multiple JSON objects in single response
- **Scenario description**: Claude returns multiple separate JSON objects in one response
- **How to test**: Create responses with multiple JSON blocks or objects
- **Expected handling**: Extract and return all valid JSON objects, or the most relevant one based on context

### Empty or null responses from Claude
- **Scenario description**: Claude returns empty string or null value
- **How to test**: Mock subprocess to return empty stdout
- **Expected handling**: Appropriate error raised, no parsing attempted on empty content

### Network interruptions during subprocess execution
- **Scenario description**: Connection loss while Claude CLI is processing
- **How to test**: Simulate subprocess interruption or network timeout
- **Expected handling**: Graceful error handling, subprocess cleanup, appropriate error message

### Partial JSON due to output truncation
- **Scenario description**: Large responses get truncated mid-JSON structure
- **How to test**: Mock responses that end abruptly within JSON content
- **Expected handling**: Detection of incomplete JSON, retry with request for smaller response

### Unicode characters in JSON responses
- **Scenario description**: JSON contains special Unicode characters or emojis
- **How to test**: Include various Unicode ranges in JSON strings
- **Expected handling**: Proper encoding/decoding, no data loss or corruption

## Dependencies

- **subprocess**: Core Python module for executing Claude CLI commands
- **json**: Standard library for parsing and validating JSON responses
- **re**: Regular expressions for extracting JSON from mixed content
- **logging**: Structured logging for debugging and error tracking
- **pytest**: Testing framework for organizing and running tests
- **pytest-timeout**: Plugin for setting test execution timeouts
- **pytest-mock**: Mocking framework for simulating external dependencies

## Test Execution

Run all tests:
```bash
pytest tests/test_claude_interface.py -v
```

Run specific test categories:
```bash
# Only connection tests
pytest tests/test_claude_interface.py::TestConnectionValidator -v

# Only JSON extraction tests
pytest tests/test_claude_interface.py::TestJSONExtractor -v

# With timeout settings
pytest tests/test_claude_interface.py --timeout=30
```

Run with coverage:
```bash
pytest tests/test_claude_interface.py --cov=claude_interface --cov-report=html
```

Run edge case tests:
```bash
pytest tests/test_claude_interface.py -k "edge_case" -v
```
