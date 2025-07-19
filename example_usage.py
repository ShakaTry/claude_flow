#!/usr/bin/env python3
"""
Example usage of the Claude Flow Orchestrator
"""

from orchestrator import WorkflowOrchestrator
import logging
import sys


def run_simple_workflow():
    """Run a simple workflow with default settings"""
    print("Running simple workflow example...")
    
    # Create orchestrator for a feature
    orchestrator = WorkflowOrchestrator(
        feature_name="user-authentication",
        dry_run=True  # Use dry run for example
    )
    
    # Run the workflow
    success = orchestrator.run_workflow()
    
    if success:
        print("✓ Workflow completed successfully!")
    else:
        print("✗ Workflow failed. Check logs for details.")
        
    return success


def run_custom_workflow():
    """Example of running a workflow with custom configuration"""
    print("\nRunning custom workflow example...")
    
    # You could load custom config here
    # config = load_config("custom_config.yaml")
    
    orchestrator = WorkflowOrchestrator(
        feature_name="payment-integration",
        dry_run=True
    )
    
    # You could also run individual phases
    try:
        # Phase 0: Git analysis
        git_context = orchestrator._phase_git_analysis()
        print(f"Git context: {git_context}")
        
        # Phase 1: Feature analysis
        analysis = orchestrator._phase_feature_analysis(git_context)
        print(f"Feature analysis: {analysis}")
        
        # Continue with other phases...
        
    except Exception as e:
        print(f"Error during workflow: {e}")
        return False
        
    return True


def demonstrate_error_handling():
    """Demonstrate error handling and recovery"""
    print("\nDemonstrating error handling...")
    
    orchestrator = WorkflowOrchestrator(
        feature_name="test-feature",
        dry_run=True
    )
    
    # Check saved state
    state = orchestrator._load_state()
    if state:
        print(f"Found saved state from phase: {state['current_phase']}")
        print(f"Status: {state['status']}")
        
        if state['status'] == 'failed':
            print("Previous run failed. Would you like to retry? (y/n)")
            # In real usage, you'd handle the retry logic
            
    return True


def main():
    """Main example execution"""
    print("Claude Flow Orchestrator - Example Usage\n")
    
    # Set up logging for examples
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run examples
    examples = [
        ("Simple Workflow", run_simple_workflow),
        ("Custom Workflow", run_custom_workflow),
        ("Error Handling", demonstrate_error_handling)
    ]
    
    for name, func in examples:
        print(f"\n{'='*50}")
        print(f"Example: {name}")
        print(f"{'='*50}")
        
        try:
            success = func()
            if not success:
                print(f"Example '{name}' completed with issues.")
        except Exception as e:
            print(f"Example '{name}' failed: {e}")
            logging.exception("Example failed")
            
    print("\n" + "="*50)
    print("Examples completed!")
    print("\nTo run a real workflow:")
    print("  python orchestrator.py <feature-name>")
    print("\nFor more options:")
    print("  python orchestrator.py --help")


if __name__ == "__main__":
    main()