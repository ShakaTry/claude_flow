"""
Git operations module - Handles all Git-related operations
"""
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path


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
        strategy = git_context.get("branching_strategy", "feature-branch")
        base_branch = git_context.get("base_branch", "main")
        
        # Determine branch name based on strategy
        if strategy == "git-flow":
            branch_name = f"feature/{feature_name}"
        else:
            branch_name = f"feature-{feature_name}"
            
        self.logger.info(f"Creating feature branch: {branch_name}")
        
        # Ensure we're on the base branch
        current = self.get_current_branch()
        if current != base_branch:
            self._run_git_command(["checkout", base_branch])
            
        # Pull latest changes
        if git_context.get("remote_url"):
            self._run_git_command(["pull", "origin", base_branch])
            
        # Create and checkout new branch
        self._run_git_command(["checkout", "-b", branch_name])
        
    def stage_all_changes(self):
        """Stage all changes for commit"""
        self.logger.info("Staging all changes...")
        self._run_git_command(["add", "-A"])
        
    def commit(self, message: str):
        """Create a commit with the given message"""
        self.logger.info(f"Creating commit...")
        self._run_git_command(["commit", "-m", message])
        
    def push(self, branch: Optional[str] = None, set_upstream: bool = True):
        """Push the current branch to remote"""
        if not branch:
            branch = self.get_current_branch()
            
        self.logger.info(f"Pushing branch: {branch}")
        
        args = ["push"]
        if set_upstream:
            args.extend(["-u", "origin", branch])
        else:
            args.extend(["origin", branch])
            
        self._run_git_command(args)
        
    def create_pull_request(self, title: str, body: str) -> Optional[str]:
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
            result = subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", body],
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
            
    def finalize_workflow(self, messages: Dict[str, Any]):
        """Finalize the Git workflow with commit and optional PR"""
        # Stage all changes
        self.stage_all_changes()
        
        # Commit with generated message
        commit_msg = messages.get("commit_msg", "feat: update feature")
        self.commit(commit_msg)
        
        # Push to remote
        self.push()
        
        # Create PR if possible
        pr_title = messages.get("pr_title", "New feature")
        pr_body = messages.get("pr_body", "Feature implementation")
        self.create_pull_request(pr_title, pr_body)
        
    def get_recent_commits(self, limit: int = 10) -> str:
        """Get recent commit messages for style reference"""
        result = self._run_git_command(["log", f"--oneline", f"-{limit}"])
        return result.stdout