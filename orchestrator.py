#!/usr/bin/env python3
"""
Claude Code Orchestrator - External orchestration for Claude Code workflows
"""
import json
import os
import sys
import subprocess
import datetime
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
import logging

from claude_interface import ClaudeInterface
from git_operations import GitOperations
from validators import WorkflowValidator
from prompts import PROMPT_TEMPLATES


class WorkflowOrchestrator:
    def __init__(self, feature_name: str, feature_description: str = "", dry_run: bool = False, force_refresh: bool = False):
        self.feature_name = feature_name
        self.feature_description = feature_description
        self.dry_run = dry_run
        self.force_refresh = force_refresh
        self.workflow_dir = Path(".claude-workflow")
        self.phase_outputs_dir = self.workflow_dir / "phase_outputs"
        self.logs_dir = self.workflow_dir / "logs"
        self.state_file = self.workflow_dir / "state.json"
        
        self.claude = ClaudeInterface()
        self.git = GitOperations(dry_run=dry_run)
        self.validator = WorkflowValidator()
        
        self._setup_workflow_directory()
        self._setup_logging()
        
    def _setup_workflow_directory(self):
        """Initialize the workflow directory structure"""
        self.workflow_dir.mkdir(exist_ok=True)
        self.phase_outputs_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create .gitignore if it doesn't exist
        gitignore_path = self.workflow_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("*\n")
            
    def _setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"workflow-{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _save_state(self, phase: str, status: str, data: Dict[str, Any]):
        """Save the current workflow state"""
        state = {
            "feature_name": self.feature_name,
            "current_phase": phase,
            "status": status,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data
        }
        self.state_file.write_text(json.dumps(state, indent=2))
        self.logger.info(f"Saved state for phase: {phase}")
        
    def _load_state(self) -> Optional[Dict[str, Any]]:
        """Load the saved workflow state"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return None
        
    def _save_phase_output(self, phase: str, data: Dict[str, Any]):
        """Save the output of a phase"""
        output_file = self.phase_outputs_dir / f"{phase}.json"
        output_file.write_text(json.dumps(data, indent=2))
        self.logger.info(f"Saved output for phase: {phase}")
        
    def _load_phase_output(self, phase: str) -> Optional[Dict[str, Any]]:
        """Load the output of a previous phase"""
        output_file = self.phase_outputs_dir / f"{phase}.json"
        if output_file.exists():
            return json.loads(output_file.read_text())
        return None
        
    def run_workflow(self):
        """Execute the complete workflow"""
        try:
            self.logger.info(f"Starting workflow for feature: {self.feature_name}")
            
            # Phase 0: Claude Session - Git Context Analysis
            git_context = self._phase_git_analysis()
            
            # Script Phase: Validate Git Context
            if not self._script_validate_git_context(git_context):
                return False
                
            # Phase 1: Claude Session - Feature Analysis
            analysis = self._phase_feature_analysis(git_context)
            
            # Script Phase: Apply Git Workflow Part 1
            self._script_git_workflow_part1(git_context)
                
            # Phase 2: Claude Session - Documentation Generation
            self._phase_documentation_generation(analysis)
            
            # Script Phase: Validate Documentation
            self._script_validate_documentation()
            
            # Phase 3: Claude Session - Commit Message Generation
            messages = self._phase_commit_messages()
            
            # Script Phase: Finalize Git Workflow Part 2
            self._script_git_workflow_part2(messages)
                
            self.logger.info("Workflow completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}", exc_info=True)
            self._save_state("error", "failed", {"error": str(e)})
            return False
            
    def _get_feature_cache_key(self) -> str:
        """Generate a unique cache key based on feature name and description"""
        import hashlib
        content = f"{self.feature_name}:{self.feature_description}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
        
    def _phase_git_analysis(self) -> Dict[str, Any]:
        """Phase 0: Analyze Git repository state"""
        self.logger.info("Phase 0: Analyzing Git context...")
        
        # Check if we have a cached result
        cached = self._load_phase_output("git-context")
        if cached:
            self.logger.info("Using cached Git context")
            return cached
            
        # Get Git status
        git_status = self.git.get_status()
        cwd = os.getcwd()
        
        # Prepare prompt
        prompt = PROMPT_TEMPLATES["git_analysis"].format(
            cwd=cwd,
            git_status=git_status
        )
        
        # Execute Claude
        result = self.claude.execute_with_retry(
            "git_analysis",
            prompt,
            self.validator.validate_git_context
        )
        
        # Save output
        self._save_phase_output("git-context", result)
        self._save_state("git_analysis", "completed", result)
        
        return result
        
    def _script_validate_git_context(self, git_context: Dict[str, Any]) -> bool:
        """Script Phase: Validate the Git context is suitable for workflow"""
        self.logger.info("Script: Validating Git context...")
        
        # Check for critical issues
        if git_context.get("has_uncommitted"):
            self.logger.warning("Repository has uncommitted changes")
            if not self.dry_run:
                response = input("Continue with uncommitted changes? (y/n): ")
                if response.lower() != 'y':
                    self.logger.info("Workflow cancelled by user due to uncommitted changes")
                    return False
                    
        # Check for remote repository
        if not git_context.get("remote_url"):
            self.logger.warning("No remote repository configured")
            if not self.dry_run:
                response = input("Continue without remote repository? (y/n): ")
                if response.lower() != 'y':
                    return False
                    
        warnings = git_context.get("warnings", [])
        if warnings:
            self.logger.warning(f"Git warnings: {warnings}")
            
        self.logger.info("Git context validation passed")
        self._save_state("git_validation", "completed", {"validated": True})
        return True
        
    def _script_git_workflow_part1(self, git_context: Dict[str, Any]):
        """Script Phase: Apply Git workflow part 1 - Create branch"""
        self.logger.info("Script: Applying Git workflow (Part 1)...")
        
        if not self.dry_run:
            # Read git context and apply branching strategy
            self.logger.info("Creating feature branch based on strategy...")
            self.git.create_feature_branch(self.feature_name, git_context)
            self.logger.info("Feature branch created successfully")
        else:
            self.logger.info("[DRY RUN] Would create feature branch")
            
        self._save_state("git_workflow_part1", "completed", {
            "branch_created": True,
            "feature_name": self.feature_name
        })
        
    def _script_validate_documentation(self):
        """Script Phase: Validate generated documentation"""
        self.logger.info("Script: Validating documentation...")
        
        doc_path = Path(f"docs/tests/{self.feature_name}_tests.md")
        
        if not self.dry_run and doc_path.exists():
            # Check file exists and has content
            content = doc_path.read_text()
            
            # Validate required sections
            required_sections = ["## Overview", "## Test Cases", "## Edge Cases", "## Dependencies"]
            missing_sections = []
            
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
                    
            if missing_sections:
                self.logger.warning(f"Documentation missing sections: {missing_sections}")
            else:
                self.logger.info("Documentation validation passed")
                
            # Check minimum length
            if len(content) < 200:
                self.logger.warning("Documentation seems too short")
                
        self._save_state("doc_validation", "completed", {"validated": True})
        
    def _script_git_workflow_part2(self, messages: Dict[str, Any]):
        """Script Phase: Finalize Git workflow part 2 - Commit, push, PR"""
        self.logger.info("Script: Finalizing Git workflow (Part 2)...")
        
        if not self.dry_run:
            # Stage all changes
            self.logger.info("Staging all changes...")
            self.git.stage_all_changes()
            
            # Commit with generated message
            self.logger.info("Creating commit...")
            commit_msg = messages.get("commit_msg", "feat: update feature")
            self.git.commit(commit_msg)
            
            # Push to remote
            self.logger.info("Pushing to remote...")
            self.git.push()
            
            # Create PR if possible (to the base branch from git context)
            self.logger.info("Creating pull request...")
            pr_title = messages.get("pr_title", "New feature")
            pr_body = messages.get("pr_body", "Feature implementation")
            
            # Always use develop as base branch for PRs
            base_branch = "develop"
            
            pr_url = self.git.create_pull_request(pr_title, pr_body, base_branch)
            
            if pr_url:
                self.logger.info(f"Pull request created: {pr_url}")
        else:
            self.logger.info("[DRY RUN] Would stage, commit, push and create PR")
            
        self._save_state("git_workflow_part2", "completed", {
            "committed": True,
            "pushed": True,
            "pr_created": True
        })
        
    def _phase_feature_analysis(self, git_context: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Analyze the feature requirements"""
        self.logger.info("Phase 1: Analyzing feature requirements...")
        
        # Check cache with feature-specific key
        cache_key = self._get_feature_cache_key()
        cached = self._load_phase_output(f"analysis_{cache_key}")
        if cached and not self.force_refresh:
            # Verify cache is for the same feature
            if cached.get("feature_name") == self.feature_name:
                self.logger.info("Using cached feature analysis")
                return cached
            else:
                self.logger.info("Cache mismatch, regenerating analysis...")
            
        # Prepare prompt
        feature_desc = f"\nDescription: {self.feature_description}" if self.feature_description else ""
        prompt = PROMPT_TEMPLATES["feature_analysis"].format(
            git_context=json.dumps(git_context, indent=2),
            feature_name=self.feature_name,
            feature_description=feature_desc
        )
        
        # Execute Claude
        result = self.claude.execute_with_retry(
            "feature_analysis",
            prompt,
            self.validator.validate_feature_analysis
        )
        
        # Save output with feature-specific key
        cache_key = self._get_feature_cache_key()
        self._save_phase_output(f"analysis_{cache_key}", result)
        # Also save as generic for backward compatibility
        self._save_phase_output("analysis", result)
        self._save_state("feature_analysis", "completed", result)
        
        return result
        
    def _phase_documentation_generation(self, analysis: Dict[str, Any]):
        """Phase 2: Generate test documentation"""
        self.logger.info("Phase 2: Generating documentation...")
        
        # Prepare prompt
        prompt = PROMPT_TEMPLATES["doc_generation"].format(
            analysis=json.dumps(analysis, indent=2),
            feature_name=self.feature_name
        )
        
        # Execute Claude for documentation
        doc_content = self.claude.execute_raw(prompt)
        
        # Save documentation file
        doc_path = Path(f"docs/tests/{self.feature_name}_tests.md")
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to phase outputs for inspection even in dry-run
        self._save_phase_output("documentation", {
            "content": doc_content,
            "target_path": str(doc_path)
        })
        
        if not self.dry_run:
            doc_path.write_text(doc_content)
            self.logger.info(f"Documentation written to: {doc_path}")
        else:
            self.logger.info(f"[DRY RUN] Would write documentation to: {doc_path}")
            
        self._save_state("documentation", "completed", {"path": str(doc_path)})
        
    def _phase_commit_messages(self) -> Dict[str, Any]:
        """Phase 3: Generate commit and PR messages"""
        self.logger.info("Phase 3: Generating commit messages...")
        
        # Get changes
        changes = self.git.get_changes()
        
        # Prepare prompt
        prompt = PROMPT_TEMPLATES["commit_messages"].format(
            changes=changes
        )
        
        # Execute Claude
        result = self.claude.execute_with_retry(
            "commit_messages",
            prompt,
            self.validator.validate_messages
        )
        
        # Save output
        self._save_phase_output("messages", result)
        self._save_state("commit_messages", "completed", result)
        
        return result
        
    def cleanup(self):
        """Clean up the workflow directory"""
        if self.workflow_dir.exists():
            shutil.rmtree(self.workflow_dir)
            self.logger.info("Cleaned up workflow directory")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Orchestrator - External orchestration for Claude Code workflows",
        epilog="""
Examples:
  python orchestrator.py auth --dry-run
  python orchestrator.py user-login -d "Add login with email and password" --dry-run
  python orchestrator.py payment -d "Stripe integration for subscriptions"
  
Note: The feature name can be approximate. Claude will understand variations like:
  'auth', 'authentication', 'user-auth', 'login-system' → User authentication feature
  'payment', 'payments', 'billing' → Payment processing feature
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "feature_name",
        help="Name of the feature to implement (e.g., 'user-auth', 'payment-integration')"
    )
    parser.add_argument(
        "--description",
        "-d",
        help="Detailed description of what the feature should do",
        default=""
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making actual changes"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last saved state"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up workflow directory and exit"
    )
    parser.add_argument(
        "--force-refresh",
        "-f",
        action="store_true",
        help="Force regeneration of all analyses (ignore cache)"
    )
    
    args = parser.parse_args()
    
    orchestrator = WorkflowOrchestrator(
        args.feature_name, 
        feature_description=args.description,
        dry_run=args.dry_run,
        force_refresh=args.force_refresh
    )
    
    if args.cleanup:
        orchestrator.cleanup()
        return
        
    # Run the workflow
    success = orchestrator.run_workflow()
    
    if success and not args.dry_run:
        # Optionally cleanup after successful run
        response = input("Workflow completed. Clean up temporary files? (y/n): ")
        if response.lower() == 'y':
            orchestrator.cleanup()


if __name__ == "__main__":
    main()