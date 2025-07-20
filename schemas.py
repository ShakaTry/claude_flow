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

# Schema for comprehensive Git state
GIT_STATE_SCHEMA = {
    "type": "object",
    "required": [
        "current_branch", "is_detached_head", "is_in_merge", "is_in_rebase", 
        "is_in_cherry_pick", "is_in_bisect", "has_uncommitted_changes",
        "staged_files", "modified_files", "untracked_files", "conflicted_files",
        "stash_count", "remote_url", "remote_connectivity", "repo_root", "is_clean"
    ],
    "properties": {
        "current_branch": {
            "type": "string",
            "description": "Current Git branch name"
        },
        "is_detached_head": {
            "type": "boolean",
            "description": "Whether HEAD is detached"
        },
        "is_in_merge": {
            "type": "boolean",
            "description": "Whether repository is in merge state"
        },
        "is_in_rebase": {
            "type": "boolean",
            "description": "Whether repository is in rebase state"
        },
        "is_in_cherry_pick": {
            "type": "boolean",
            "description": "Whether repository is in cherry-pick state"
        },
        "is_in_bisect": {
            "type": "boolean",
            "description": "Whether repository is in bisect state"
        },
        "has_uncommitted_changes": {
            "type": "boolean",
            "description": "Whether there are uncommitted changes"
        },
        "staged_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of staged files"
        },
        "modified_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of modified but unstaged files"
        },
        "untracked_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of untracked files"
        },
        "conflicted_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of files with merge conflicts"
        },
        "stash_count": {
            "type": "integer",
            "minimum": 0,
            "description": "Number of stashed changes"
        },
        "remote_url": {
            "type": ["string", "null"],
            "description": "Remote repository URL"
        },
        "remote_connectivity": {
            "type": "object",
            "properties": {
                "reachable": {"type": "boolean"},
                "fetch_url": {"type": ["string", "null"]},
                "push_url": {"type": ["string", "null"]},
                "error": {"type": ["string", "null"]}
            },
            "description": "Remote connectivity status"
        },
        "repo_root": {
            "type": ["string", "null"],
            "description": "Git repository root directory"
        },
        "is_clean": {
            "type": "boolean",
            "description": "Whether working directory is clean"
        }
    }
}

# Schema for preflight check results
PREFLIGHT_CHECK_SCHEMA = {
    "type": "object",
    "required": ["has_errors", "has_warnings", "issues", "state"],
    "properties": {
        "has_errors": {
            "type": "boolean",
            "description": "Whether any error-level issues were found"
        },
        "has_warnings": {
            "type": "boolean",
            "description": "Whether any warning-level issues were found"
        },
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["severity", "message"],
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["error", "warning", "info"]
                    },
                    "message": {
                        "type": "string"
                    },
                    "suggested_action": {
                        "type": ["string", "null"]
                    }
                }
            },
            "description": "List of issues found"
        },
        "state": GIT_STATE_SCHEMA
    }
}

# Map phase names to schemas
PHASE_SCHEMAS = {
    "git_analysis": GIT_CONTEXT_SCHEMA,
    "feature_analysis": FEATURE_ANALYSIS_SCHEMA,
    "commit_messages": COMMIT_MESSAGES_SCHEMA,
    "git_state": GIT_STATE_SCHEMA,
    "preflight_check": PREFLIGHT_CHECK_SCHEMA
}