"""
JSON schemas for workflow phase outputs
"""

# Schema for Git context analysis output
GIT_CONTEXT_SCHEMA = {
    "type": "object",
    "required": ["current_branch", "has_uncommitted", "remote_url", "branching_strategy", "base_branch", "warnings"],
    "properties": {
        "current_branch": {
            "type": "string",
            "description": "The current Git branch"
        },
        "has_uncommitted": {
            "type": "boolean",
            "description": "Whether there are uncommitted changes"
        },
        "remote_url": {
            "type": ["string", "null"],
            "description": "The remote repository URL"
        },
        "branching_strategy": {
            "type": "string",
            "enum": ["feature-branch", "git-flow"],
            "description": "The branching strategy used"
        },
        "base_branch": {
            "type": "string",
            "description": "The base branch for features"
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Any warnings about the Git state"
        }
    }
}

# Schema for feature analysis output
FEATURE_ANALYSIS_SCHEMA = {
    "type": "object",
    "required": ["feature_name", "main_file", "components", "test_cases", "dependencies", "edge_cases"],
    "properties": {
        "feature_name": {
            "type": "string",
            "description": "The name of the feature"
        },
        "main_file": {
            "type": "string",
            "description": "The main file path for the feature"
        },
        "components": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of components to create"
        },
        "test_cases": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of test case descriptions"
        },
        "dependencies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of package dependencies"
        },
        "edge_cases": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of edge cases to consider"
        }
    }
}

# Schema for commit messages output
COMMIT_MESSAGES_SCHEMA = {
    "type": "object",
    "required": ["commit_msg", "pr_title", "pr_body"],
    "properties": {
        "commit_msg": {
            "type": "string",
            "description": "The commit message in conventional format"
        },
        "pr_title": {
            "type": "string",
            "description": "The pull request title"
        },
        "pr_body": {
            "type": "string",
            "description": "The pull request body in markdown"
        }
    }
}

# Map phase names to schemas
PHASE_SCHEMAS = {
    "git_analysis": GIT_CONTEXT_SCHEMA,
    "feature_analysis": FEATURE_ANALYSIS_SCHEMA,
    "commit_messages": COMMIT_MESSAGES_SCHEMA
}