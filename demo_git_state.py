#!/usr/bin/env python3
"""
Demonstration of Git safe state checking utilities
"""
import logging
from git_operations import GitOperations


def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create GitOperations instance
    git_ops = GitOperations()
    
    print("=== Git Safe State Checking Demo ===\n")
    
    # 1. Get comprehensive repository state
    print("1. Getting comprehensive repository state...")
    state = git_ops.get_repository_state()
    
    print(f"   Current branch: {state['current_branch']}")
    print(f"   Has uncommitted changes: {state['has_uncommitted_changes']}")
    print(f"   Is repository clean: {state['is_clean']}")
    print(f"   Remote reachable: {state['remote_connectivity'].get('reachable', 'Unknown')}")
    print()
    
    # 2. Perform preflight checks
    print("2. Performing general preflight checks...")
    report = git_ops.perform_preflight_checks()
    
    if report.has_errors():
        print("   ❌ Found errors that must be resolved:")
    elif report.has_warnings():
        print("   ⚠️  Found warnings to consider:")
    else:
        print("   ✅ Repository is in a clean state!")
    
    # Print the formatted report
    print("\n" + report.format_report())
    print()
    
    # 3. Check if specific operations are safe
    print("3. Checking if specific operations are safe...")
    operations = ["commit", "push", "pull", "checkout", "merge", "rebase"]
    
    for op in operations:
        is_safe, reason = report.is_safe_for_operation(op)
        if is_safe:
            print(f"   ✅ {op}: Safe to perform")
        else:
            print(f"   ❌ {op}: Not safe - {reason}")
    
    print()
    
    # 4. Demonstrate operation-specific preflight checks
    print("4. Operation-specific preflight check example...")
    
    # Example: Check before pushing
    push_report = git_ops.perform_preflight_checks("push")
    is_safe, reason = push_report.is_safe_for_operation("push")
    
    if is_safe:
        print("   Push operation is safe to perform!")
        # git_ops.push() would be called here in real usage
    else:
        print(f"   Cannot push: {reason}")
        print("   Please resolve the following issues first:")
        for issue in push_report.issues:
            print(f"     - {issue}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()