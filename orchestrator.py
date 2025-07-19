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
    def __init__(self, feature_name: str, dry_run: bool = False):
        self.feature_name = feature_name
        self.dry_run = dry_run
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
            
            # Phase 0: Git Context Analysis
            git_context = self._phase_git_analysis()
            
            # Validation: Check Git context
            if not self._validate_git_context(git_context):
                return False
                
            # Phase 1: Feature Analysis
            analysis = self._phase_feature_analysis(git_context)
            
            # Git Operation: Create feature branch
            if not self.dry_run:
                self.git.create_feature_branch(self.feature_name, git_context)
                
            # Phase 2: Documentation Generation
            self._phase_documentation_generation(analysis)
            
            # Phase 3: Commit Message Generation
            messages = self._phase_commit_messages()
            
            # Git Operation: Finalize workflow
            if not self.dry_run:
                self.git.finalize_workflow(messages)
                
            self.logger.info("Workflow completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}", exc_info=True)
            self._save_state("error", "failed", {"error": str(e)})
            return False
            
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
        
    def _validate_git_context(self, git_context: Dict[str, Any]) -> bool:
        """Validate the Git context is suitable for workflow"""
        if git_context.get("has_uncommitted"):
            self.logger.warning("Repository has uncommitted changes")
            if not self.dry_run:
                response = input("Continue with uncommitted changes? (y/n): ")
                if response.lower() != 'y':
                    return False
                    
        warnings = git_context.get("warnings", [])
        if warnings:
            self.logger.warning(f"Git warnings: {warnings}")
            
        return True
        
    def _phase_feature_analysis(self, git_context: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Analyze the feature requirements"""
        self.logger.info("Phase 1: Analyzing feature requirements...")
        
        # Check cache
        cached = self._load_phase_output("analysis")
        if cached:
            self.logger.info("Using cached feature analysis")
            return cached
            
        # Prepare prompt
        prompt = PROMPT_TEMPLATES["feature_analysis"].format(
            git_context=json.dumps(git_context, indent=2),
            feature_name=self.feature_name
        )
        
        # Execute Claude
        result = self.claude.execute_with_retry(
            "feature_analysis",
            prompt,
            self.validator.validate_feature_analysis
        )
        
        # Save output
        self._save_phase_output("analysis", result)
        self._save_state("feature_analysis", "completed", result)
        
        return result
        
    def _phase_documentation_generation(self, analysis: Dict[str, Any]):
        """Phase 2: Generate test documentation"""
        self.logger.info("Phase 2: Generating documentation...")
        
        # Prepare prompt
        prompt = PROMPT_TEMPLATES["doc_generation"].format(
            analysis=json.dumps(analysis, indent=2)
        )
        
        # Execute Claude for documentation
        doc_content = self.claude.execute_raw(prompt)
        
        # Save documentation file
        doc_path = Path(f"docs/tests/{self.feature_name}_tests.md")
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
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
        description="Claude Code Orchestrator - External orchestration for Claude Code workflows"
    )
    parser.add_argument(
        "feature_name",
        help="Name of the feature to implement"
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
    
    args = parser.parse_args()
    
    orchestrator = WorkflowOrchestrator(args.feature_name, dry_run=args.dry_run)
    
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