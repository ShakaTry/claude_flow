"""
Validation module for workflow outputs
"""
import json
import logging
import re
from typing import Dict, Any
from jsonschema import validate, ValidationError, Draft7Validator

from schemas import (
    GIT_CONTEXT_SCHEMA,
    FEATURE_ANALYSIS_SCHEMA,
    COMMIT_MESSAGES_SCHEMA,
    PHASE_SCHEMAS
)


class WorkflowValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any], phase_name: str):
        """Validate data against a JSON schema"""
        try:
            validate(instance=data, schema=schema)
            self.logger.info(f"Validation passed for phase: {phase_name}")
        except ValidationError as e:
            self.logger.error(f"Validation failed for phase {phase_name}: {e.message}")
            self.logger.error(f"Failed at path: {' -> '.join(str(p) for p in e.path)}")
            raise ValueError(f"Schema validation failed: {e.message}")
            
    def validate_git_context(self, data: Dict[str, Any]):
        """Validate Git context analysis output"""
        self.validate_schema(data, GIT_CONTEXT_SCHEMA, "git_context")
        
        # Additional validation logic
        if data["has_uncommitted"] and not data.get("warnings"):
            self.logger.warning("Has uncommitted changes but no warnings provided")
            
        if not data["remote_url"] and data["branching_strategy"] == "git-flow":
            raise ValueError("Git-flow strategy requires a remote repository")
            
    def validate_feature_analysis(self, data: Dict[str, Any]):
        """Validate feature analysis output"""
        self.validate_schema(data, FEATURE_ANALYSIS_SCHEMA, "feature_analysis")
        
        # Additional validation logic
        if not data["components"]:
            raise ValueError("At least one component must be specified")
            
        if not data["test_cases"]:
            raise ValueError("At least one test case must be specified")
            
        # Validate file path format
        main_file = data["main_file"]
        if not main_file or main_file.startswith("/") or ".." in main_file:
            raise ValueError(f"Invalid main file path: {main_file}")
            
    def validate_messages(self, data: Dict[str, Any]):
        """Validate commit messages output"""
        self.validate_schema(data, COMMIT_MESSAGES_SCHEMA, "commit_messages")
        
        # Additional validation logic
        commit_msg = data["commit_msg"]
        
        # Check conventional commit format
        conventional_types = [
            "feat", "fix", "docs", "style", "refactor",
            "test", "chore", "perf", "ci", "build"
        ]
        
        # Check format: type(scope)?: description or type: description
        pattern = r'^(' + '|'.join(conventional_types) + r')(\([^)]+\))?:\s.+'
        
        if not re.match(pattern, commit_msg):
            self.logger.warning(f"Commit message doesn't follow conventional format: {commit_msg}")
            
        # Check PR body has some structure
        pr_body = data["pr_body"]
        if len(pr_body) < 50:
            raise ValueError("PR body is too short, should include description and changes")
            
    def get_validation_errors(self, data: Dict[str, Any], schema: Dict[str, Any]) -> list:
        """Get a list of validation errors without raising exceptions"""
        validator = Draft7Validator(schema)
        errors = []
        
        for error in validator.iter_errors(data):
            error_path = " -> ".join(str(p) for p in error.path)
            errors.append({
                "path": error_path,
                "message": error.message,
                "validator": error.validator
            })
            
        return errors
        
    def suggest_fixes(self, phase_name: str, errors: list) -> str:
        """Suggest fixes for common validation errors"""
        suggestions = []
        
        for error in errors:
            if error["validator"] == "required":
                suggestions.append(f"Add missing field: {error['message']}")
            elif error["validator"] == "type":
                suggestions.append(f"Fix type at {error['path']}: {error['message']}")
            elif error["validator"] == "enum":
                suggestions.append(f"Use valid value at {error['path']}: {error['message']}")
                
        if suggestions:
            return "Suggested fixes:\n" + "\n".join(f"  - {s}" for s in suggestions)
        return "Please check the schema requirements for this phase."