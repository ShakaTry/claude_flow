# Test Documentation for claude-interface

## Overview
This test suite validates the Claude CLI interface functionality, focusing on command execution, JSON extraction from various output formats, retry logic with validation, error handling, and timeout management. The tests ensure reliable integration with Claude's command-line interface for automated workflows.

## Test Cases

### Test successful execution of Claude CLI commands
- **Test name**: `test_successful_execution`
- **Description**: Validates that Claude CLI commands execute successfully and return expected output
- **Expected behavior**: Command executes with exit code 0 and returns valid response data
- **Test data/setup required**: Mock subprocess to return successful execution with sample output

### Test JSON extraction from markdown code blocks
- **Test name**: `test_json_extraction_markdown`
- **Description**: Verifies extraction of JSON data embedded within markdown code blocks (```json...```)
- **Expected behavior**: JSON is correctly parsed from markdown formatting and returned as Python dict
- **Test data/setup required**: Sample markdown output containing JSON code blocks

### Test JSON extraction from plain JSON output
- **Test name**: `test_json_extraction_plain`
- **Description**: Tests extraction of JSON from plain text output without markdown formatting
- **Expected behavior**: Direct JSON output is parsed and returned as Python dict
- **Test data/setup required**: Raw JSON string output from Claude

### Test retry logic with validation failures
- **Test name**: `test_retry_validation_failures`
- **Description**: Ensures retry mechanism works when initial responses fail validation
- **Expected behavior**: System retries up to configured limit, eventually succeeding or raising final error
- **Test data/setup required**: Mock responses that fail initial validations but succeed on retry

### Test subprocess errors and exception handling
- **Test name**: `test_subprocess_errors`
- **Description**: Validates handling of subprocess failures and non-zero exit codes
- **Expected behavior**: Appropriate exceptions raised with meaningful error messages
- **Test data/setup required**: Mock subprocess to raise CalledProcessError or other exceptions

### Test timeout handling for long-running commands
- **Test name**: `test_timeout_handling`
- **Description**: Verifies commands that exceed timeout limits are properly terminated
- **Expected behavior**: TimeoutExpired exception raised after configured timeout period
- **Test data/setup required**: Mock subprocess that simulates long-running command

### Test validation with custom validators
- **Test name**: `test_custom_validators`
- **Description**: Tests integration with custom validation functions/schemas
- **Expected behavior**: Custom validators are applied correctly to extracted JSON
- **Test data/setup required**: Custom validator functions and test data that passes/fails validation

### Test logging of command execution and retries
- **Test name**: `test_execution_logging`
- **Description**: Ensures proper logging of command execution, retries, and errors
- **Expected behavior**: Log entries created for each execution attempt with appropriate detail levels
- **Test data/setup required**: Mock logger to capture and verify log messages

## Edge Cases

### Claude returns invalid JSON that cannot be parsed
- **Scenario description**: Output contains malformed JSON that fails parsing
- **How to test**: Provide output with syntax errors, missing quotes, or invalid structures
- **Expected handling**: JSONDecodeError raised with details about parsing failure

### Claude returns empty or null output
- **Scenario description**: Command executes but returns empty string or null
- **How to test**: Mock subprocess to return empty stdout
- **Expected handling**: Appropriate error indicating no valid output received

### Subprocess command fails with non-zero exit code
- **Scenario description**: Claude CLI returns error exit code (1, 2, etc.)
- **How to test**: Mock subprocess.run to return non-zero returncode
- **Expected handling**: CalledProcessError with exit code and stderr content

### Command times out during execution
- **Scenario description**: Claude takes longer than timeout threshold to respond
- **How to test**: Mock subprocess to simulate delay beyond timeout
- **Expected handling**: TimeoutExpired exception with command details

### Multiple JSON blocks in Claude's output
- **Scenario description**: Output contains multiple JSON code blocks or objects
- **How to test**: Provide markdown with multiple ```json``` blocks
- **Expected handling**: Extract first valid JSON block or handle according to configuration

### Nested or escaped JSON in markdown
- **Scenario description**: JSON contains escaped characters or is nested in complex markdown
- **How to test**: Use JSON with escaped quotes, newlines, or nested markdown formatting
- **Expected handling**: Correctly unescape and parse the JSON structure

### Validation fails on all retry attempts
- **Scenario description**: Response never passes validation despite retries
- **How to test**: Mock all retry attempts to fail validation
- **Expected handling**: Final validation error raised after exhausting retry limit

### Claude CLI is not available or misconfigured
- **Scenario description**: Claude executable not found or improperly configured
- **How to test**: Mock subprocess to raise FileNotFoundError or similar
- **Expected handling**: Clear error message indicating CLI configuration issue

## Dependencies

### pytest
Core testing framework providing test discovery, fixtures, and assertions

### pytest-mock
Mocking functionality for simulating subprocess calls and external dependencies

### jsonschema
JSON schema validation for verifying Claude's output structure and content

## Test Execution

Run all tests:
```bash
pytest tests/test_claude_interface.py -v
```

Run specific test class:
```bash
pytest tests/test_claude_interface.py::TestClaudeInterface -v
```

Run with coverage:
```bash
pytest tests/test_claude_interface.py --cov=claude_interface --cov-report=html
```

Run specific test case:
```bash
pytest tests/test_claude_interface.py::TestClaudeInterface::test_successful_execution -v
```
