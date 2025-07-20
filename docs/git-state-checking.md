# Git Safe State Checking

## Overview

The Git safe state checking utilities provide comprehensive pre-flight checks to ensure Git operations can be performed safely. This prevents common errors and provides clear guidance when the repository is in an invalid state.

## Features

### State Detection
- **Merge State**: Detects if repository is in the middle of a merge
- **Rebase State**: Detects if repository is in the middle of a rebase
- **Cherry-pick State**: Detects if repository is in the middle of a cherry-pick
- **Bisect State**: Detects if repository is in the middle of a bisect
- **Detached HEAD**: Detects if HEAD is detached from a branch
- **Uncommitted Changes**: Tracks staged, modified, and untracked files
- **Merge Conflicts**: Identifies files with unresolved conflicts
- **Stash Count**: Reports number of stashed changes
- **Remote Connectivity**: Verifies remote repository is reachable

### Pre-flight Checks
The `perform_preflight_checks()` method runs comprehensive checks and returns a `GitStateReport` containing:
- Categorized issues (errors, warnings, info)
- Suggested actions for each issue
- Operation-specific safety checks

### Operation Safety
The system validates if specific Git operations are safe to perform:
- **commit**: Blocked by merge/rebase/cherry-pick states or conflicts
- **push**: Blocked by special states, conflicts, or detached HEAD
- **pull**: Blocked by uncommitted changes or special states
- **checkout**: Blocked by uncommitted changes or special states
- **merge**: Blocked by uncommitted changes or special states
- **rebase**: Blocked by uncommitted changes or special states

## Usage Examples

### Basic State Check
```python
from git_operations import GitOperations

git_ops = GitOperations()

# Get comprehensive state
state = git_ops.get_repository_state()
print(f"Current branch: {state['current_branch']}")
print(f"Is clean: {state['is_clean']}")
```

### Pre-flight Checks
```python
# General pre-flight check
report = git_ops.perform_preflight_checks()

if report.has_errors():
    print("Errors found:")
    print(report.format_report())
else:
    print("Repository is ready for operations")

# Operation-specific check
push_report = git_ops.perform_preflight_checks("push")
is_safe, reason = push_report.is_safe_for_operation("push")

if not is_safe:
    print(f"Cannot push: {reason}")
```

### Integration with Existing Operations
The following GitOperations methods now use pre-flight checks automatically:
- `create_feature_branch()`: Ensures clean state before creating branches
- `commit()`: Validates repository state before committing
- `push()`: Checks state and remote connectivity before pushing

### Error Handling
```python
try:
    git_ops.commit("My commit message")
except RuntimeError as e:
    # Pre-flight check failed
    print(f"Commit failed: {e}")
    # Get detailed report
    report = git_ops.perform_preflight_checks("commit")
    print(report.format_report())
```

## GitStateReport Class

The `GitStateReport` class provides:
- Issue categorization by severity
- Human-readable formatting
- Operation safety validation
- Suggested actions for resolution

### Report Format Example
```
=== Git Repository State Report ===
Current branch: feature/test
Repository root: /home/user/project

🚨 ERRORS:
  [ERROR] Repository is in the middle of a merge
    → Suggested action: Complete the merge with 'git merge --continue' or abort with 'git merge --abort'

⚠️  WARNINGS:
  [WARNING] Uncommitted changes detected: 2 staged, 1 modified, 3 untracked
    → Suggested action: Commit changes with 'git commit', stash with 'git stash', or discard with 'git reset --hard'

ℹ️  INFO:
  [INFO] Found 2 stashed change(s)
    → Suggested action: View with 'git stash list', apply with 'git stash pop'
```

## Testing

Comprehensive unit tests are provided in `tests/test_git_operations.py`:
```bash
python -m unittest tests.test_git_operations -v
```

## Schema Validation

Two new schemas are available for validation:
- `GIT_STATE_SCHEMA`: Validates comprehensive repository state
- `PREFLIGHT_CHECK_SCHEMA`: Validates pre-flight check results

These can be used with the existing `WorkflowValidator` class.