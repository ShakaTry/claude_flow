"""
Unit tests for Git operations and state checking
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import subprocess
from git_operations import GitOperations
from git_state import GitStateReport, GitStateIssue, IssueSeverity


class TestGitOperations(unittest.TestCase):
    """Test cases for GitOperations class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.git_ops = GitOperations(dry_run=False)
        
    @patch('git_operations.subprocess.run')
    def test_get_current_branch(self, mock_run):
        """Test getting current branch"""
        mock_run.return_value = MagicMock(
            stdout="feature/test-branch\n",
            stderr="",
            returncode=0
        )
        
        branch = self.git_ops.get_current_branch()
        
        self.assertEqual(branch, "feature/test-branch")
        mock_run.assert_called_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        
    @patch('git_operations.subprocess.run')
    def test_has_uncommitted_changes_clean(self, mock_run):
        """Test checking for uncommitted changes when clean"""
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        result = self.git_ops.has_uncommitted_changes()
        
        self.assertFalse(result)
        
    @patch('git_operations.subprocess.run')
    def test_has_uncommitted_changes_dirty(self, mock_run):
        """Test checking for uncommitted changes when dirty"""
        mock_run.return_value = MagicMock(
            stdout=" M file1.py\n?? file2.py\n",
            stderr="",
            returncode=0
        )
        
        result = self.git_ops.has_uncommitted_changes()
        
        self.assertTrue(result)
        
    @patch('git_operations.Path.exists')
    def test_is_in_merge(self, mock_exists):
        """Test checking if in merge state"""
        mock_exists.return_value = True
        result = self.git_ops.is_in_merge()
        self.assertTrue(result)
        
        mock_exists.return_value = False
        result = self.git_ops.is_in_merge()
        self.assertFalse(result)
        
    @patch('git_operations.Path.exists')
    def test_is_in_rebase(self, mock_exists):
        """Test checking if in rebase state"""
        # Test when rebase-merge exists
        mock_exists.side_effect = [True, False]
        result = self.git_ops.is_in_rebase()
        self.assertTrue(result)
        
        # Test when rebase-apply exists
        mock_exists.side_effect = [False, True]
        result = self.git_ops.is_in_rebase()
        self.assertTrue(result)
        
        # Test when neither exists
        mock_exists.side_effect = [False, False]
        result = self.git_ops.is_in_rebase()
        self.assertFalse(result)
        
    @patch('git_operations.subprocess.run')
    def test_is_detached_head(self, mock_run):
        """Test checking if HEAD is detached"""
        # Test when HEAD is detached
        mock_run.return_value = MagicMock(returncode=1)
        result = self.git_ops.is_detached_head()
        self.assertTrue(result)
        
        # Test when HEAD is not detached
        mock_run.return_value = MagicMock(returncode=0)
        result = self.git_ops.is_detached_head()
        self.assertFalse(result)
        
    @patch('git_operations.subprocess.run')
    def test_get_conflicted_files(self, mock_run):
        """Test getting conflicted files"""
        mock_run.return_value = MagicMock(
            stdout="file1.py\nfile2.py\n",
            stderr="",
            returncode=0
        )
        
        files = self.git_ops.get_conflicted_files()
        
        self.assertEqual(files, ["file1.py", "file2.py"])
        
    @patch('git_operations.subprocess.run')
    def test_get_stash_count(self, mock_run):
        """Test getting stash count"""
        # Test with stashes
        mock_run.return_value = MagicMock(
            stdout="stash@{0}: WIP on main\nstash@{1}: Auto-stash\n",
            stderr="",
            returncode=0
        )
        count = self.git_ops.get_stash_count()
        self.assertEqual(count, 2)
        
        # Test without stashes
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        count = self.git_ops.get_stash_count()
        self.assertEqual(count, 0)
        
    @patch('git_operations.subprocess.run')
    def test_check_remote_connectivity_success(self, mock_run):
        """Test checking remote connectivity when successful"""
        # Mock successful responses
        mock_run.side_effect = [
            MagicMock(stdout="https://github.com/user/repo.git\n", returncode=0),  # fetch URL
            MagicMock(stdout="https://github.com/user/repo.git\n", returncode=0),  # push URL
            MagicMock(stdout="refs/heads/main\nrefs/heads/develop\n", returncode=0)  # ls-remote
        ]
        
        result = self.git_ops.check_remote_connectivity()
        
        self.assertTrue(result["reachable"])
        self.assertEqual(result["fetch_url"], "https://github.com/user/repo.git")
        self.assertEqual(result["push_url"], "https://github.com/user/repo.git")
        self.assertIsNone(result["error"])
        
    @patch('git_operations.subprocess.run')
    def test_check_remote_connectivity_failure(self, mock_run):
        """Test checking remote connectivity when failed"""
        # Mock failed ls-remote
        mock_run.side_effect = [
            MagicMock(stdout="https://github.com/user/repo.git\n", returncode=0),
            MagicMock(stdout="https://github.com/user/repo.git\n", returncode=0),
            MagicMock(stderr="fatal: could not read from remote repository", returncode=1)
        ]
        
        result = self.git_ops.check_remote_connectivity()
        
        self.assertFalse(result["reachable"])
        self.assertEqual(result["error"], "fatal: could not read from remote repository")
        
    @patch('git_operations.GitOperations.get_repository_state')
    def test_perform_preflight_checks(self, mock_get_state):
        """Test performing preflight checks"""
        # Mock a clean state
        mock_get_state.return_value = {
            "current_branch": "main",
            "is_detached_head": False,
            "is_in_merge": False,
            "is_in_rebase": False,
            "is_in_cherry_pick": False,
            "is_in_bisect": False,
            "has_uncommitted_changes": False,
            "staged_files": [],
            "modified_files": [],
            "untracked_files": [],
            "conflicted_files": [],
            "stash_count": 0,
            "remote_url": "https://github.com/user/repo.git",
            "remote_connectivity": {"reachable": True},
            "repo_root": "/home/user/repo",
            "is_clean": True
        }
        
        report = self.git_ops.perform_preflight_checks()
        
        self.assertIsInstance(report, GitStateReport)
        self.assertFalse(report.has_errors())
        self.assertFalse(report.has_warnings())
        
    def test_dry_run_mode(self):
        """Test dry run mode prevents write operations"""
        git_ops = GitOperations(dry_run=True)
        
        # Test that write commands return fake results
        with patch('git_operations.subprocess.run') as mock_run:
            result = git_ops._run_git_command(["commit", "-m", "test"])
            # Should not actually run the command
            mock_run.assert_not_called()
            self.assertEqual(result.returncode, 0)
            
    @patch('git_operations.subprocess.run')
    def test_get_repository_state_comprehensive(self, mock_run):
        """Test getting comprehensive repository state"""
        # Mock various command outputs
        responses = [
            # get_current_branch
            MagicMock(stdout="feature/test\n", returncode=0),
            # is_detached_head
            MagicMock(returncode=0),
            # has_uncommitted_changes
            MagicMock(stdout="", returncode=0),
            # get_staged_files
            MagicMock(stdout="", returncode=0),
            # get_modified_files
            MagicMock(stdout="", returncode=0),
            # get_untracked_files
            MagicMock(stdout="", returncode=0),
            # get_conflicted_files
            MagicMock(stdout="", returncode=0),
            # get_stash_count
            MagicMock(stdout="", returncode=0),
            # get_remote_url
            MagicMock(stdout="https://github.com/user/repo.git\n", returncode=0),
            # check_remote_connectivity (3 calls)
            MagicMock(stdout="https://github.com/user/repo.git\n", returncode=0),
            MagicMock(stdout="https://github.com/user/repo.git\n", returncode=0),
            MagicMock(stdout="refs/heads/main\n", returncode=0),
            # _get_repo_root
            MagicMock(stdout="/home/user/repo\n", returncode=0)
        ]
        
        # Also need to mock Path.exists for the state checks
        with patch('git_operations.Path.exists', return_value=False):
            mock_run.side_effect = responses
            state = self.git_ops.get_repository_state()
        
        self.assertEqual(state["current_branch"], "feature/test")
        self.assertFalse(state["is_detached_head"])
        self.assertFalse(state["has_uncommitted_changes"])
        self.assertTrue(state["is_clean"])
        self.assertEqual(state["repo_root"], "/home/user/repo")


class TestGitStateReport(unittest.TestCase):
    """Test cases for GitStateReport class"""
    
    def test_clean_state_report(self):
        """Test report for clean repository state"""
        clean_state = {
            "current_branch": "main",
            "is_detached_head": False,
            "is_in_merge": False,
            "is_in_rebase": False,
            "is_in_cherry_pick": False,
            "is_in_bisect": False,
            "has_uncommitted_changes": False,
            "staged_files": [],
            "modified_files": [],
            "untracked_files": [],
            "conflicted_files": [],
            "stash_count": 0,
            "remote_url": "https://github.com/user/repo.git",
            "remote_connectivity": {"reachable": True},
            "repo_root": "/home/user/repo",
            "is_clean": True
        }
        
        report = GitStateReport(clean_state)
        
        self.assertFalse(report.has_errors())
        self.assertFalse(report.has_warnings())
        self.assertEqual(len(report.issues), 0)
        
    def test_merge_conflict_state_report(self):
        """Test report for merge conflict state"""
        conflict_state = {
            "current_branch": "feature/test",
            "is_detached_head": False,
            "is_in_merge": True,
            "is_in_rebase": False,
            "is_in_cherry_pick": False,
            "is_in_bisect": False,
            "has_uncommitted_changes": True,
            "staged_files": ["file1.py"],
            "modified_files": [],
            "untracked_files": [],
            "conflicted_files": ["file2.py", "file3.py"],
            "stash_count": 0,
            "remote_url": "https://github.com/user/repo.git",
            "remote_connectivity": {"reachable": True},
            "repo_root": "/home/user/repo",
            "is_clean": False
        }
        
        report = GitStateReport(conflict_state)
        
        self.assertTrue(report.has_errors())
        self.assertTrue(report.has_warnings())
        
        errors = report.get_issues_by_severity(IssueSeverity.ERROR)
        self.assertEqual(len(errors), 2)  # merge state + conflicted files
        
    def test_is_safe_for_operation(self):
        """Test checking if operations are safe"""
        # State with uncommitted changes
        dirty_state = {
            "current_branch": "main",
            "is_detached_head": False,
            "is_in_merge": False,
            "is_in_rebase": False,
            "is_in_cherry_pick": False,
            "is_in_bisect": False,
            "has_uncommitted_changes": True,
            "staged_files": ["file1.py"],
            "modified_files": ["file2.py"],
            "untracked_files": [],
            "conflicted_files": [],
            "stash_count": 0,
            "remote_url": "https://github.com/user/repo.git",
            "remote_connectivity": {"reachable": True},
            "repo_root": "/home/user/repo",
            "is_clean": False
        }
        
        report = GitStateReport(dirty_state)
        
        # Should be safe for commit but not for pull
        is_safe, reason = report.is_safe_for_operation("commit")
        self.assertTrue(is_safe)
        
        is_safe, reason = report.is_safe_for_operation("pull")
        self.assertFalse(is_safe)
        self.assertIn("has uncommitted changes", reason)
        
    def test_format_report(self):
        """Test formatting the state report"""
        state_with_issues = {
            "current_branch": "feature/test",
            "is_detached_head": True,
            "is_in_merge": False,
            "is_in_rebase": False,
            "is_in_cherry_pick": False,
            "is_in_bisect": False,
            "has_uncommitted_changes": True,
            "staged_files": ["file1.py"],
            "modified_files": ["file2.py"],
            "untracked_files": ["file3.py"],
            "conflicted_files": [],
            "stash_count": 2,
            "remote_url": None,
            "remote_connectivity": {"reachable": False, "error": "No remote"},
            "repo_root": "/home/user/repo",
            "is_clean": False
        }
        
        report = GitStateReport(state_with_issues)
        formatted = report.format_report()
        
        # Check that key information is included
        self.assertIn("Current branch: feature/test", formatted)
        self.assertIn("WARNINGS", formatted)
        self.assertIn("HEAD is detached", formatted)
        self.assertIn("Uncommitted changes", formatted)
        self.assertIn("INFO", formatted)
        self.assertIn("2 stashed change(s)", formatted)


if __name__ == '__main__':
    unittest.main()