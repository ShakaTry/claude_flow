"""
Prompt templates for Claude interactions
"""

PROMPT_TEMPLATES = {
    "git_analysis": """You are analyzing a Git repository state. Return ONLY a JSON object with:
- current_branch: string (the current Git branch name)
- has_uncommitted: boolean (whether there are uncommitted changes)
- remote_url: string or null (the remote repository URL, null if no remote)
- branching_strategy: "feature-branch" or "git-flow" (infer from branch names and structure)
- base_branch: string (the main/master branch name)
- warnings: array of strings (any warnings about the Git state)

Current directory: {cwd}
Git status output:
{git_status}

Analyze the repository and return ONLY the JSON object, no other text.""",
    
    "feature_analysis": """Given this Git context: {git_context}

Analyze the feature: {feature_name}

Based on common patterns and best practices, return ONLY a JSON object with:
- feature_name: string (the feature name provided)
- main_file: string (suggested main file path for this feature)
- components: array of component names (logical components needed)
- test_cases: array of test descriptions (key test scenarios)
- dependencies: array of package names (likely dependencies needed)
- edge_cases: array of edge case descriptions (important edge cases to consider)

Consider the project structure and naming conventions. Return ONLY the JSON object.""",

    "doc_generation": """Given this feature analysis: {analysis}

Generate comprehensive test documentation in Markdown format. Include:

# Test Documentation for {feature_name}

## Overview
Brief description of what is being tested and why.

## Test Cases
List each test case from the analysis with:
- Test name
- Description
- Expected behavior
- Test data/setup required

## Edge Cases
Detail each edge case with:
- Scenario description
- How to test
- Expected handling

## Dependencies
List all dependencies and their purpose.

## Test Execution
Instructions for running the tests.

Generate ONLY the markdown content, no other text or code blocks.""",

    "commit_messages": """Given these changes:
{changes}

Generate ONLY a JSON object with:
- commit_msg: string (conventional commit format - e.g., "feat(scope): description")
- pr_title: string (clear and concise pull request title)
- pr_body: string (markdown formatted PR description with these sections:
  ## Description
  Brief description of changes
  
  ## Changes
  - List of specific changes
  
  ## Testing
  How the changes were tested
  
  ## Related Issues
  Any related issue numbers)

Follow conventional commit format. Return ONLY the JSON object.""",

    # Additional utility prompts
    "error_recovery": """The previous attempt failed with this error:
{error}

Please provide a corrected response that addresses the error.
Original request: {original_prompt}

Return ONLY the requested format (JSON or markdown), no explanatory text.""",

    "validate_branch_name": """Given this feature name: {feature_name}
And this branching strategy: {strategy}

Return ONLY a JSON object with:
- branch_name: string (the properly formatted branch name)
- is_valid: boolean (whether the name follows conventions)
- suggestions: array of strings (alternative names if not valid)""",

    "analyze_test_requirements": """Given this feature: {feature_name}
And these components: {components}

Return ONLY a JSON object with:
- unit_tests: array of unit test descriptions
- integration_tests: array of integration test descriptions  
- e2e_tests: array of end-to-end test descriptions
- performance_tests: array of performance test descriptions (if applicable)
- security_tests: array of security test descriptions (if applicable)""",
}

# Prompt enhancement helpers
def enhance_prompt_with_examples(prompt: str, examples: list) -> str:
    """Add examples to a prompt for better clarity"""
    if not examples:
        return prompt
        
    examples_text = "\n\nExamples:\n" + "\n".join(examples)
    return prompt + examples_text

def create_retry_prompt(original_prompt: str, error: str, attempt: int) -> str:
    """Create a retry prompt with error context"""
    retry_template = f"""Attempt {attempt} failed with error: {error}

Please provide a valid response following the exact format requested.
Be especially careful about:
- JSON syntax (proper quotes, commas, brackets)
- Including all required fields
- Using the correct data types

Original request:
{original_prompt}

Return ONLY the requested format with no additional text."""
    
    return retry_template

# Specialized prompts for different project types
PROJECT_TYPE_PROMPTS = {
    "python": {
        "structure": "src/{feature_name}/",
        "test_structure": "tests/{feature_name}/",
        "conventions": "PEP 8 naming, pytest for testing"
    },
    "javascript": {
        "structure": "src/features/{feature_name}/",  
        "test_structure": "src/features/{feature_name}/__tests__/",
        "conventions": "camelCase naming, Jest for testing"
    },
    "typescript": {
        "structure": "src/features/{feature_name}/",
        "test_structure": "src/features/{feature_name}/__tests__/",
        "conventions": "camelCase naming, Jest/Vitest for testing, strict typing"
    }
}