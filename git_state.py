"""
Git state reporting and analysis utilities
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging


class IssueSeverity(Enum):
    """Severity levels for Git state issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class GitStateIssue:
    """Represents a single issue found in Git state"""
    def __init__(self, severity: IssueSeverity, message: str, suggested_action: Optional[str] = None):
        self.severity = severity
        self.message = message
        self.suggested_action = suggested_action
        
    def __str__(self) -> str:
        result = f"[{self.severity.value.upper()}] {self.message}"
        if self.suggested_action:
            result += f"\n    → Suggested action: {self.suggested_action}"
        return result


class GitStateReport:
    """Comprehensive report of Git repository state with issues and suggested actions"""
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.issues: List[GitStateIssue] = []
        self.logger = logging.getLogger(__name__)
        self._analyze_state()
        
    def _analyze_state(self):
        """Analyze the Git state and identify issues"""
        # Check for special Git states
        if self.state.get("is_in_merge"):
            self.issues.append(GitStateIssue(
                IssueSeverity.ERROR,
                "Repository is in the middle of a merge",
                "Complete the merge with 'git merge --continue' or abort with 'git merge --abort'"
            ))
            
        if self.state.get("is_in_rebase"):
            self.issues.append(GitStateIssue(
                IssueSeverity.ERROR,
                "Repository is in the middle of a rebase",
                "Continue with 'git rebase --continue', skip with 'git rebase --skip', or abort with 'git rebase --abort'"
            ))
            
        if self.state.get("is_in_cherry_pick"):
            self.issues.append(GitStateIssue(
                IssueSeverity.ERROR,
                "Repository is in the middle of a cherry-pick",
                "Continue with 'git cherry-pick --continue' or abort with 'git cherry-pick --abort'"
            ))
            
        if self.state.get("is_in_bisect"):
            self.issues.append(GitStateIssue(
                IssueSeverity.WARNING,
                "Repository is in the middle of a bisect",
                "Complete bisect with 'git bisect reset' when done"
            ))
            
        # Check for conflicted files
        conflicted_files = self.state.get("conflicted_files", [])
        if conflicted_files:
            self.issues.append(GitStateIssue(
                IssueSeverity.ERROR,
                f"Found {len(conflicted_files)} conflicted file(s): {', '.join(conflicted_files[:5])}{'...' if len(conflicted_files) > 5 else ''}",
                "Resolve conflicts, then stage the files with 'git add <file>'"
            ))
            
        # Check for detached HEAD
        if self.state.get("is_detached_head"):
            self.issues.append(GitStateIssue(
                IssueSeverity.WARNING,
                "HEAD is detached",
                "Create a new branch with 'git checkout -b <branch-name>' or checkout an existing branch"
            ))
            
        # Check for uncommitted changes
        if self.state.get("has_uncommitted_changes"):
            staged = len(self.state.get("staged_files", []))
            modified = len(self.state.get("modified_files", []))
            untracked = len(self.state.get("untracked_files", []))
            
            details = []
            if staged:
                details.append(f"{staged} staged")
            if modified:
                details.append(f"{modified} modified")
            if untracked:
                details.append(f"{untracked} untracked")
                
            self.issues.append(GitStateIssue(
                IssueSeverity.WARNING,
                f"Uncommitted changes detected: {', '.join(details)}",
                "Commit changes with 'git commit', stash with 'git stash', or discard with 'git reset --hard'"
            ))
            
        # Check for stashed changes
        stash_count = self.state.get("stash_count", 0)
        if stash_count > 0:
            self.issues.append(GitStateIssue(
                IssueSeverity.INFO,
                f"Found {stash_count} stashed change(s)",
                "View with 'git stash list', apply with 'git stash pop'"
            ))
            
        # Check remote connectivity
        remote_conn = self.state.get("remote_connectivity", {})
        if remote_conn and not remote_conn.get("reachable"):
            error_msg = remote_conn.get("error", "Unknown error")
            self.issues.append(GitStateIssue(
                IssueSeverity.WARNING,
                f"Cannot reach remote repository: {error_msg}",
                "Check network connection and remote URL with 'git remote -v'"
            ))
            
    def has_errors(self) -> bool:
        """Check if there are any error-level issues"""
        return any(issue.severity == IssueSeverity.ERROR for issue in self.issues)
        
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues"""
        return any(issue.severity == IssueSeverity.WARNING for issue in self.issues)
        
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[GitStateIssue]:
        """Get all issues of a specific severity"""
        return [issue for issue in self.issues if issue.severity == severity]
        
    def is_safe_for_operation(self, operation: str) -> Tuple[bool, Optional[str]]:
        """Check if it's safe to perform a specific Git operation"""
        # Define which conditions block which operations
        operation_blockers = {
            "commit": ["is_in_merge", "is_in_rebase", "is_in_cherry_pick", "conflicted_files"],
            "push": ["is_in_merge", "is_in_rebase", "is_in_cherry_pick", "conflicted_files", "is_detached_head"],
            "pull": ["has_uncommitted_changes", "is_in_merge", "is_in_rebase", "is_in_cherry_pick", "conflicted_files"],
            "checkout": ["has_uncommitted_changes", "is_in_merge", "is_in_rebase", "is_in_cherry_pick", "conflicted_files"],
            "merge": ["has_uncommitted_changes", "is_in_merge", "is_in_rebase", "is_in_cherry_pick", "conflicted_files"],
            "rebase": ["has_uncommitted_changes", "is_in_merge", "is_in_rebase", "is_in_cherry_pick", "conflicted_files"]
        }
        
        blockers = operation_blockers.get(operation.lower(), [])
        for blocker in blockers:
            if blocker == "conflicted_files" and self.state.get("conflicted_files"):
                return False, f"Cannot {operation}: repository has conflicted files"
            elif blocker in self.state and self.state.get(blocker):
                return False, f"Cannot {operation}: {blocker.replace('_', ' ')}"
                
        return True, None
        
    def format_report(self, include_state: bool = False) -> str:
        """Format the state report for display"""
        lines = []
        lines.append("=== Git Repository State Report ===")
        lines.append(f"Current branch: {self.state.get('current_branch', 'unknown')}")
        lines.append(f"Repository root: {self.state.get('repo_root', 'unknown')}")
        lines.append("")
        
        # Group issues by severity
        errors = self.get_issues_by_severity(IssueSeverity.ERROR)
        warnings = self.get_issues_by_severity(IssueSeverity.WARNING)
        info = self.get_issues_by_severity(IssueSeverity.INFO)
        
        if errors:
            lines.append("🚨 ERRORS:")
            for issue in errors:
                lines.append(f"  {issue}")
            lines.append("")
            
        if warnings:
            lines.append("⚠️  WARNINGS:")
            for issue in warnings:
                lines.append(f"  {issue}")
            lines.append("")
            
        if info:
            lines.append("ℹ️  INFO:")
            for issue in info:
                lines.append(f"  {issue}")
            lines.append("")
            
        if not self.issues:
            lines.append("✅ No issues found - repository is in a clean state")
            
        # Include full state if requested
        if include_state:
            lines.append("\n=== Full State Details ===")
            for key, value in self.state.items():
                if isinstance(value, list) and len(value) > 10:
                    lines.append(f"{key}: [{len(value)} items]")
                else:
                    lines.append(f"{key}: {value}")
                    
        return "\n".join(lines)