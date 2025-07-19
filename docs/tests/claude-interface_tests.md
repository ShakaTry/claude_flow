# Test Documentation for claude-interface

## Overview
This test suite validates the Claude interface module, which provides Python integration with the Claude CLI tool. The tests ensure reliable command execution, JSON response parsing, retry mechanisms, and error handling for various edge cases that may occur during Claude CLI interactions.

## Test Cases

### test_execute_raw
- **Description**: Validates successful raw command execution with valid Claude response
- **Expected behavior**: Executes Claude CLI command and returns raw string output without modification
- **Test data/setup required**: Mock subprocess.run to return successful response with stdout containing Claude's output

### test_extract_json_from_output
- **Description**: Tests JSON extraction from various output formats including code blocks, plain JSON, and mixed text
- **Expected behavior**: Successfully extracts valid JSON from different formatting contexts (markdown code blocks, plain text, mixed content)
- **Test data/setup required**: Sample outputs with JSON in various formats: ```json blocks, plain JSON objects, JSON mixed with explanatory text

### test_execute_json
- **Description**: Tests the combined execution and JSON parsing workflow
- **Expected behavior**: Executes Claude command and returns parsed JSON object, handling various response formats
- **Test data/setup required**: Mock Claude responses containing JSON in different formats

### test_execute_with_retry
- **Description**: Validates retry mechanism with progressive error recovery
- **Expected behavior**: Retries failed requests with exponential backoff, applies validator function, and recovers from transient failures
- **Test data/setup required**: Mock failing responses followed by successful response, custom validator functions

### test_make_prompt_more_explicit
- **Description**: Tests prompt enhancement functionality for clearer Claude instructions
- **Expected behavior**: Transforms user prompts into more explicit instructions for better Claude comprehension
- **Test data/setup required**: Sample prompts and expected enhanced versions

### test_connection
- **Description**: Validates connection validation with Claude CLI
- **Expected behavior**: Verifies Claude CLI is installed and accessible, returns connection status
- **Test data/setup required**: Mock subprocess calls to simulate Claude CLI presence/absence

### test_error_handling_invalid_json
- **Description**: Tests error handling for invalid JSON responses
- **Expected behavior**: Gracefully handles malformed JSON with appropriate error messages and fallback behavior
- **Test data/setup required**: Various malformed JSON samples (missing brackets, invalid syntax, truncated responses)

### test_validator_function_integration
- **Description**: Tests validator function integration in retry logic
- **Expected behavior**: Applies custom validation logic during retries, only accepting responses that pass validation
- **Test data/setup required**: Custom validator functions, responses that pass/fail validation

### test_timeout_handling
- **Description**: Tests timeout handling for long-running Claude executions
- **Expected behavior**: Terminates long-running processes gracefully, returns timeout error
- **Test data/setup required**: Mock subprocess with delayed response, timeout configuration

## Edge Cases

### Claude CLI not installed or not in PATH
- **Scenario description**: System lacks Claude CLI installation or PATH configuration
- **How to test**: Mock subprocess.run to raise FileNotFoundError or return command not found error
- **Expected handling**: Clear error message indicating Claude CLI is not available with installation instructions

### Malformed JSON with nested objects and special characters
- **Scenario description**: Response contains complex JSON with escape sequences, Unicode, nested structures
- **How to test**: Provide JSON with escaped quotes, newlines, Unicode characters, deeply nested objects
- **Expected handling**: Successful parsing of valid but complex JSON structures

### Partial JSON responses due to output truncation
- **Scenario description**: Claude's response is cut off mid-JSON due to output limits
- **How to test**: Provide incomplete JSON strings missing closing brackets or truncated mid-value
- **Expected handling**: Error with indication that response was truncated, retry mechanism activation

### Concurrent execution conflicts
- **Scenario description**: Multiple Claude interface calls executing simultaneously
- **How to test**: Launch multiple parallel executions, test resource contention
- **Expected handling**: Each execution completes independently without interference

### Network timeouts and subprocess communication errors
- **Scenario description**: Claude CLI hangs or network issues cause communication failures
- **How to test**: Mock subprocess to hang indefinitely or raise timeout exceptions
- **Expected handling**: Timeout after configured duration, clean process termination, appropriate error message

### Empty or null responses from Claude
- **Scenario description**: Claude returns empty string or null output
- **How to test**: Mock subprocess to return empty stdout or None
- **Expected handling**: Specific error for empty responses, differentiated from other errors

### JSON embedded in markdown or other formatting
- **Scenario description**: JSON is wrapped in markdown code blocks, HTML, or other formatting
- **How to test**: Provide responses with JSON in triple backticks, HTML pre tags, or mixed with explanatory text
- **Expected handling**: Successfully extracts JSON regardless of surrounding formatting

## Dependencies

### pytest
Core testing framework providing test discovery, fixtures, and assertions

### pytest-mock
Provides enhanced mocking capabilities for simulating subprocess and system calls

### pytest-timeout
Enables timeout configuration for individual tests to prevent hanging

### pytest-asyncio
Supports asynchronous test execution for concurrent operation testing

## Test Execution

Run all tests:
```bash
pytest tests/test_claude_interface.py -v
```

Run specific test:
```bash
pytest tests/test_claude_interface.py::test_execute_raw -v
```

Run with coverage:
```bash
pytest tests/test_claude_interface.py --cov=claude_interface --cov-report=html
```

Run with timeout monitoring:
```bash
pytest tests/test_claude_interface.py --timeout=30
```

Run edge case tests only:
```bash
pytest tests/test_claude_interface.py -k "edge" -v
```
