"""
Git operations module - Handles all Git-related operations
"""
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from git_state import GitStateReport, IssueSeverity


class GitOperations:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
    def _run_git_command(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command and return the result"""
        cmd = ["git"] + args
        self.logger.debug(f"Running git command: {' '.join(cmd)}")
        
        if self.dry_run and self._is_write_command(args):
            self.logger.info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            # Return a fake successful result
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git command failed: {e.stderr}")
            raise
            
    def _is_write_command(self, args: List[str]) -> bool:
        """Check if a git command modifies the repository"""
        write_commands = {
            "add", "commit", "push", "checkout", "branch",
            "merge", "rebase", "reset", "rm", "mv"
        }
        return len(args) > 0 and args[0] in write_commands
        
    def get_status(self) -> str:
        """Get the current git status"""
        result = self._run_git_command(["status", "--porcelain", "-b"])
        return result.stdout
        
    def get_current_branch(self) -> str:
        """Get the current branch name"""
        result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        return result.stdout.strip()
        
    def get_remote_url(self) -> Optional[str]:
        """Get the remote URL for origin"""
        result = self._run_git_command(["remote", "get-url", "origin"], check=False)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
        
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        result = self._run_git_command(["status", "--porcelain"])
        return bool(result.stdout.strip())
        
    def get_changes(self) -> str:
        """Get a summary of current changes"""
        # Get staged changes
        staged = self._run_git_command(["diff", "--staged", "--stat"]).stdout
        
        # Get unstaged changes
        unstaged = self._run_git_command(["diff", "--stat"]).stdout
        
        # Get untracked files
        untracked_result = self._run_git_command(["ls-files", "--others", "--exclude-standard"])
        untracked = untracked_result.stdout.strip().split('\n') if untracked_result.stdout.strip() else []
        
        changes = []
        if staged:
            changes.append(f"Staged changes:\n{staged}")
        if unstaged:
            changes.append(f"Unstaged changes:\n{unstaged}")
        if untracked:
            changes.append(f"Untracked files:\n" + "\n".join(f"  - {f}" for f in untracked))
            
        return "\n\n".join(changes) if changes else "No changes detected"
        
    def create_feature_branch(self, feature_name: str, git_context: Dict[str, Any]):
        """Create a feature branch based on the branching strategy"""
        # Run preflight checks
        report = self.perform_preflight_checks("checkout")
        
        # Always use develop as base branch for now
        base_branch = "develop"
        
        # Since we're creating test documentation, use docs/ prefix
        branch_name = f"docs/{feature_name}"
            
        self.logger.info(f"Creating feature branch: {branch_name} from {base_branch}")
        
        # Check for issues that would prevent branch creation
        stashed = False
        if report.has_errors():
            self.logger.error("Cannot create branch due to repository state issues:")
            self.logger.error(report.format_report())
            raise RuntimeError("Repository is in an invalid state for branch creation")
            
        # Handle uncommitted changes by stashing
        if self.has_uncommitted_changes():
            self.logger.warning("Uncommitted changes detected. Stashing changes before creating branch...")
            # Stash changes with a descriptive message
            stash_result = self._run_git_command(["stash", "push", "-m", f"Auto-stash before creating branch {branch_name}"])
            stashed = "No local changes to save" not in stash_result.stdout
        
        # Ensure we're on develop
        current = self.get_current_branch()
        if current != base_branch:
            self._run_git_command(["checkout", base_branch])
            
        # Pull latest changes
        if git_context.get("remote_url"):
            self._run_git_command(["pull", "origin", base_branch])
            
        # Create and checkout new branch
        self._run_git_command(["checkout", "-b", branch_name])
        
        # If we stashed changes, pop them back
        if stashed:
            self.logger.info("Restoring stashed changes...")
            self._run_git_command(["stash", "pop"])
        
    def stage_all_changes(self):
        """Stage all changes for commit"""
        self.logger.info("Staging all changes...")
        self._run_git_command(["add", "-A"])
        
    def commit(self, message: str):
        """Create a commit with the given message"""
        # Run preflight checks
        report = self.perform_preflight_checks("commit")
        
        if report.has_errors():
            self.logger.error("Cannot commit due to repository state issues:")
            self.logger.error(report.format_report())
            raise RuntimeError("Repository is in an invalid state for committing")
            
        self.logger.info(f"Creating commit...")
        self._run_git_command(["commit", "-m", message])
        
    def push(self, branch: Optional[str] = None, set_upstream: bool = True):
        """Push the current branch to remote"""
        # Run preflight checks
        report = self.perform_preflight_checks("push")
        
        if report.has_errors():
            self.logger.error("Cannot push due to repository state issues:")
            self.logger.error(report.format_report())
            raise RuntimeError("Repository is in an invalid state for pushing")
            
        # Check remote connectivity specifically
        if not report.state.get("remote_connectivity", {}).get("reachable", False):
            self.logger.error("Cannot push: remote repository is not reachable")
            raise RuntimeError("Remote repository is not reachable")
            
        if not branch:
            branch = self.get_current_branch()
            
        self.logger.info(f"Pushing branch: {branch}")
        
        args = ["push"]
        if set_upstream:
            args.extend(["-u", "origin", branch])
        else:
            args.extend(["origin", branch])
            
        self._run_git_command(args)
        
    def create_pull_request(self, title: str, body: str, base_branch: Optional[str] = None) -> Optional[str]:
        """Create a pull request using gh CLI if available"""
        try:
            # Check if gh CLI is available
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("GitHub CLI (gh) not found. Skipping PR creation.")
            return None
            
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create PR with title: {title}")
            return None
            
        try:
            # Build command with base branch if specified
            cmd = ["gh", "pr", "create", "--title", title, "--body", body]
            if base_branch:
                cmd.extend(["--base", base_branch])
                
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            pr_url = result.stdout.strip()
            self.logger.info(f"Created PR: {pr_url}")
            return pr_url
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create PR: {e.stderr}")
            return None
            
    def merge_pull_request(self, pr_number: str, delete_branch: bool = True) -> bool:
        """Merge a pull request and optionally delete the branch"""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would merge PR #{pr_number} and delete branch")
            return True
            
        try:
            # Merge the PR and delete the branch in one command
            self.logger.info(f"Merging PR #{pr_number}...")
            merge_cmd = ["gh", "pr", "merge", pr_number, "--merge"]
            if delete_branch:
                merge_cmd.append("--delete-branch")
                self.logger.info("Will delete branch after merge")
            
            merge_result = subprocess.run(
                merge_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            self.logger.info(f"PR #{pr_number} merged successfully")
            if delete_branch:
                self.logger.info("Remote branch deleted successfully")
                    
                # Also delete local branch
                current_branch = self.get_current_branch()
                if current_branch.startswith("docs/"):
                    # Switch to develop before deleting current branch
                    self._run_git_command(["checkout", "develop"])
                    # Delete the local branch
                    self._run_git_command(["branch", "-D", current_branch])
                    self.logger.info(f"Local branch {current_branch} deleted")
                    
                # Prune remote references to keep IDE in sync
                self._run_git_command(["remote", "prune", "origin"])
                self.logger.info("Pruned remote references")
                    
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to merge PR: {e.stderr}")
            return False
        
    def get_recent_commits(self, limit: int = 10) -> str:
        """Get recent commit messages for style reference"""
        result = self._run_git_command(["log", f"--oneline", f"-{limit}"])
        return result.stdout
        
    def is_in_merge(self) -> bool:
        """Check if repository is in the middle of a merge"""
        merge_head = Path(".git/MERGE_HEAD")
        return merge_head.exists()
        
    def is_in_rebase(self) -> bool:
        """Check if repository is in the middle of a rebase"""
        rebase_merge = Path(".git/rebase-merge")
        rebase_apply = Path(".git/rebase-apply")
        return rebase_merge.exists() or rebase_apply.exists()
        
    def is_in_cherry_pick(self) -> bool:
        """Check if repository is in the middle of a cherry-pick"""
        cherry_pick_head = Path(".git/CHERRY_PICK_HEAD")
        return cherry_pick_head.exists()
        
    def is_in_bisect(self) -> bool:
        """Check if repository is in the middle of a bisect"""
        bisect_log = Path(".git/BISECT_LOG")
        return bisect_log.exists()
        
    def is_detached_head(self) -> bool:
        """Check if HEAD is detached"""
        result = self._run_git_command(["symbolic-ref", "-q", "HEAD"], check=False)
        return result.returncode != 0
        
    def get_conflicted_files(self) -> List[str]:
        """Get list of files with merge conflicts"""
        result = self._run_git_command(["diff", "--name-only", "--diff-filter=U"])
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
        
    def get_stash_count(self) -> int:
        """Get number of stashed changes"""
        result = self._run_git_command(["stash", "list"])
        if result.stdout.strip():
            return len(result.stdout.strip().split('\n'))
        return 0
        
    def check_remote_connectivity(self, remote: str = "origin") -> Dict[str, Any]:
        """Check if remote is reachable and get fetch/push URLs"""
        connectivity = {
            "reachable": False,
            "fetch_url": None,
            "push_url": None,
            "error": None
        }
        
        # Get remote URLs
        fetch_result = self._run_git_command(["remote", "get-url", remote], check=False)
        if fetch_result.returncode == 0:
            connectivity["fetch_url"] = fetch_result.stdout.strip()
            
        push_result = self._run_git_command(["remote", "get-url", "--push", remote], check=False)
        if push_result.returncode == 0:
            connectivity["push_url"] = push_result.stdout.strip()
            
        # Test connectivity with ls-remote (lightweight operation)
        test_result = self._run_git_command(["ls-remote", "--heads", remote], check=False)
        if test_result.returncode == 0:
            connectivity["reachable"] = True
        else:
            connectivity["error"] = test_result.stderr.strip()
            
        return connectivity
        
    def get_untracked_files(self) -> List[str]:
        """Get list of untracked files"""
        result = self._run_git_command(["ls-files", "--others", "--exclude-standard"])
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
        
    def get_staged_files(self) -> List[str]:
        """Get list of staged files"""
        result = self._run_git_command(["diff", "--name-only", "--cached"])
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
        
    def get_modified_files(self) -> List[str]:
        """Get list of modified but unstaged files"""
        result = self._run_git_command(["diff", "--name-only"])
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
        
    def get_repository_state(self) -> Dict[str, Any]:
        """Get comprehensive repository state information"""
        state = {
            # Basic info
            "current_branch": self.get_current_branch(),
            "is_detached_head": self.is_detached_head(),
            
            # Special states
            "is_in_merge": self.is_in_merge(),
            "is_in_rebase": self.is_in_rebase(),
            "is_in_cherry_pick": self.is_in_cherry_pick(),
            "is_in_bisect": self.is_in_bisect(),
            
            # File states
            "has_uncommitted_changes": self.has_uncommitted_changes(),
            "staged_files": self.get_staged_files(),
            "modified_files": self.get_modified_files(),
            "untracked_files": self.get_untracked_files(),
            "conflicted_files": self.get_conflicted_files(),
            
            # Stash info
            "stash_count": self.get_stash_count(),
            
            # Remote info
            "remote_url": self.get_remote_url(),
            "remote_connectivity": self.check_remote_connectivity(),
            
            # Repository root
            "repo_root": self._get_repo_root(),
            
            # Clean working directory check
            "is_clean": False
        }
        
        # Determine if working directory is clean
        state["is_clean"] = (
            not state["has_uncommitted_changes"] and
            not state["is_in_merge"] and
            not state["is_in_rebase"] and
            not state["is_in_cherry_pick"] and
            not state["is_in_bisect"] and
            len(state["conflicted_files"]) == 0
        )
        
        return state
        
    def _get_repo_root(self) -> Optional[str]:
        """Get the root directory of the git repository"""
        try:
            result = self._run_git_command(["rev-parse", "--show-toplevel"])
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
            
    def perform_preflight_checks(self, operation: Optional[str] = None) -> GitStateReport:
        """
        Perform comprehensive pre-flight checks before Git operations
        
        Args:
            operation: Optional specific operation to check for (e.g., 'commit', 'push', 'pull')
            
        Returns:
            GitStateReport with issues and suggested actions
        """
        self.logger.info("Performing Git pre-flight checks...")
        
        # Get comprehensive repository state
        state = self.get_repository_state()
        
        # Create state report
        report = GitStateReport(state)
        
        # Check if specific operation is safe
        if operation:
            is_safe, reason = report.is_safe_for_operation(operation)
            if not is_safe:
                self.logger.warning(f"Operation '{operation}' is not safe: {reason}")
                
        # Log summary
        if report.has_errors():
            self.logger.error(f"Pre-flight check found {len(report.get_issues_by_severity(IssueSeverity.ERROR))} error(s)")
        elif report.has_warnings():
            self.logger.warning(f"Pre-flight check found {len(report.get_issues_by_severity(IssueSeverity.WARNING))} warning(s)")
        else:
            self.logger.info("Pre-flight check passed - repository is in a clean state")
            
        return report