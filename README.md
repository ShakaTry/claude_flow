# Claude Flow Orchestrator

An external orchestration system for Claude Code that manages complex workflows by breaking them into discrete, validated phases.

## Overview

Instead of having Claude orchestrate everything internally, this system uses a master Python script that:

1. Launches Claude for specific tasks with structured prompts
2. Captures and validates JSON outputs from each phase
3. Executes deterministic actions (Git operations, file creation)
4. Maintains workflow state and provides full traceability

## Architecture

```
orchestrator.py
    ├── Phase 0: Git Context Analysis
    ├── Phase 1: Feature Analysis  
    ├── Phase 2: Documentation Generation
    └── Phase 3: Commit Message Generation
```

Each phase produces structured JSON outputs that are validated and passed to subsequent phases.

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd claude_flow

# Install dependencies
pip install -r requirements.txt

# Ensure Claude CLI is installed and accessible
claude --version
```

## Usage

### Basic Usage

```bash
# Run a complete workflow for a new feature
python orchestrator.py user-authentication

# Dry run mode (no Git changes)
python orchestrator.py user-authentication --dry-run

# Resume from last saved state
python orchestrator.py user-authentication --resume

# Clean up workflow files
python orchestrator.py user-authentication --cleanup
```

### Workflow Phases

1. **Git Context Analysis**: Analyzes current repository state
2. **Feature Analysis**: Determines components, tests, and dependencies
3. **Documentation Generation**: Creates test documentation
4. **Commit Messages**: Generates commit and PR messages

### Configuration

Edit `config.yaml` to customize:

- Claude CLI settings (timeout, retries)
- Git preferences (branching strategy, auto-push)
- Workflow behavior (caching, cleanup)
- Logging preferences

### Example Workflow

```bash
# Start a new feature workflow
$ python orchestrator.py payment-integration

Starting workflow for feature: payment-integration
Phase 0: Analyzing Git context...
Phase 1: Analyzing feature requirements...
Creating feature branch: feature-payment-integration
Phase 2: Generating documentation...
Documentation written to: docs/tests/payment-integration_tests.md
Phase 3: Generating commit messages...
Staging all changes...
Creating commit...
Pushing branch: feature-payment-integration
Created PR: https://github.com/user/repo/pull/123
Workflow completed successfully!
```

## Project Structure

```
claude_flow/
├── orchestrator.py          # Main orchestration script
├── claude_interface.py      # Claude CLI interaction
├── git_operations.py        # Git operations
├── validators.py           # JSON validation logic
├── schemas.py              # JSON schemas for phases
├── prompts.py              # Prompt templates
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
└── .claude-workflow/       # Temporary workflow files (gitignored)
    ├── state.json
    ├── phase_outputs/
    └── logs/
```

## Advanced Features

### Custom Prompts

Create custom prompt templates by:

1. Adding them to `prompts.py`
2. Or creating a custom prompts directory and setting it in `config.yaml`

### Validation

The system validates all Claude outputs against JSON schemas. Failed validations trigger retries with enhanced prompts.

### Error Recovery

- Automatic retry with enhanced prompts on validation failure
- State persistence allows resuming interrupted workflows
- Detailed logging for debugging

### Dry Run Mode

Test workflows without making actual changes:

```bash
python orchestrator.py feature-name --dry-run
```

## Troubleshooting

### Common Issues

1. **Claude command not found**
   - Ensure Claude CLI is installed: `pip install claude-code`
   - Check PATH or update `claude.command` in config.yaml

2. **JSON parsing errors**
   - Check logs in `.claude-workflow/logs/`
   - The system will retry with clearer prompts

3. **Git operation failures**
   - Ensure you have no uncommitted changes
   - Check remote repository access

### Debug Mode

Enable debug logging in `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## Future Enhancements

- [ ] Support for custom workflow definitions (YAML/JSON)
- [ ] Integration with CI/CD pipelines  
- [ ] Web UI for workflow monitoring
- [ ] Plugin system for custom phases
- [ ] Multi-language project support

## License

MIT License - see LICENSE file for details