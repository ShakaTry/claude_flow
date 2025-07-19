# Claude Flow Orchestrator - Architecture Documentation

## System Architecture

The Claude Flow Orchestrator implements a phase-based workflow system that separates intelligent decision-making (Claude) from deterministic execution (Python scripts).

### Core Principles

1. **Separation of Concerns**: Claude handles intelligence, scripts handle execution
2. **Deterministic Workflows**: Git operations are predictable and repeatable
3. **Full Traceability**: Every phase produces auditable outputs
4. **Error Recovery**: State persistence enables workflow resumption
5. **Validation First**: All outputs are validated before proceeding

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      orchestrator.py                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                  WorkflowOrchestrator                │  │
│  │  - Manages workflow lifecycle                        │  │
│  │  - Coordinates phases                               │  │
│  │  - Handles state persistence                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌──────────────┬──────────┴────────┬─────────────────┐  │
│  ▼              ▼                   ▼                  ▼  │
│ ┌─────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────┐│
│ │ Claude  │ │     Git     │ │  Validators  │ │  State   ││
│ │Interface│ │ Operations  │ │   & Schema   │ │ Manager  ││
│ └─────────┘ └─────────────┘ └──────────────┘ └──────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Module Descriptions

### orchestrator.py
The main orchestration engine that:
- Initializes workflow environment
- Executes phases in sequence
- Manages state between phases
- Handles error recovery
- Provides CLI interface

### claude_interface.py
Manages all Claude CLI interactions:
- Executes prompts via subprocess
- Extracts JSON from Claude outputs
- Implements retry logic with enhanced prompts
- Handles timeouts and errors

### git_operations.py
Handles all Git-related operations:
- Repository state analysis
- Branch creation and management
- Commit and push operations
- Pull request creation (via gh CLI)
- Dry-run support for testing

### validators.py & schemas.py
Provides JSON validation:
- Defines schemas for each phase output
- Validates Claude responses
- Provides helpful error messages
- Suggests fixes for validation failures

### prompts.py
Contains all prompt templates:
- Structured prompts for each phase
- Error recovery prompts
- Project-type specific variations
- Prompt enhancement utilities

## Workflow Phases

### Phase 0: Git Context Analysis
```python
Input: Current directory, git status
Output: {
    "current_branch": "main",
    "has_uncommitted": false,
    "remote_url": "github.com/user/repo",
    "branching_strategy": "feature-branch",
    "base_branch": "main",
    "warnings": []
}
```

### Phase 1: Feature Analysis
```python
Input: Git context, feature name
Output: {
    "feature_name": "user-auth",
    "main_file": "src/auth/login.py",
    "components": ["LoginForm", "AuthService"],
    "test_cases": ["valid login", "invalid password"],
    "dependencies": ["bcrypt", "jwt"],
    "edge_cases": ["concurrent login"]
}
```

### Phase 2: Documentation Generation
```python
Input: Feature analysis
Output: Markdown test documentation
File: docs/tests/{feature}_tests.md
```

### Phase 3: Commit Messages
```python
Input: Git changes
Output: {
    "commit_msg": "feat(auth): add user authentication",
    "pr_title": "Add user authentication feature",
    "pr_body": "## Description\n..."
}
```

## State Management

### Workflow State Directory
```
.claude-workflow/
├── state.json              # Current workflow state
├── phase_outputs/          # JSON outputs from each phase
│   ├── git-context.json
│   ├── analysis.json
│   └── messages.json
├── logs/                   # Detailed execution logs
│   └── workflow-{timestamp}.log
└── .gitignore             # Ensures directory isn't committed
```

### State Persistence
- Each phase saves its state before and after execution
- Enables resumption from any point
- Tracks success/failure status
- Maintains phase outputs for debugging

## Error Handling Strategy

### Validation Errors
1. First attempt with standard prompt
2. Retry with enhanced prompt including error details
3. Final retry with most explicit instructions
4. Fallback to manual intervention

### Git Operation Errors
- Check for uncommitted changes
- Verify branch doesn't already exist
- Handle merge conflicts
- Provide recovery instructions

### Claude Execution Errors
- Timeout handling (configurable)
- JSON parsing fallbacks
- Connection verification
- Graceful degradation

## Configuration System

### Configuration Hierarchy
1. Default values in code
2. config.yaml overrides
3. Command-line arguments
4. Environment variables (future)

### Key Configuration Areas
- Claude CLI settings
- Git behavior preferences
- Workflow options
- Validation strictness
- Logging preferences

## Extension Points

### Custom Prompts
- Override default templates
- Add project-specific prompts
- Support multiple languages
- Template variables

### Workflow Hooks
- Pre-workflow validation
- Post-phase processing
- Error handlers
- Completion notifications

### Custom Validators
- Add business logic validation
- Project-specific rules
- Cross-phase validation
- Output transformations

## Performance Considerations

### Caching Strategy
- Phase outputs are cached by default
- Cache invalidation on parameter changes
- Optional cache bypass flags
- Configurable cache lifetime

### Parallel Execution
- Currently sequential (by design)
- Future: parallel independent phases
- Dependency graph analysis
- Resource optimization

## Security Considerations

### Input Validation
- Sanitize feature names
- Validate file paths
- Prevent command injection
- Limit resource usage

### Credential Management
- No credentials in code
- Use Git credential helpers
- Environment variable support
- Secure prompt handling

## Future Architecture Enhancements

### Planned Features
1. **Workflow Definition Language**: YAML/JSON workflow definitions
2. **Plugin System**: Extensible phase types
3. **Web UI**: Real-time workflow monitoring
4. **Distributed Execution**: Run phases on different machines
5. **Integration APIs**: Webhook support for CI/CD

### Scalability Considerations
- Stateless phase execution
- Horizontal scaling potential
- Message queue integration
- Database state backend

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock Claude responses
- Mock Git operations
- Validate all schemas

### Integration Tests
- End-to-end workflow tests
- Error recovery scenarios
- State persistence tests
- Configuration tests

### Performance Tests
- Measure phase execution times
- Test timeout handling
- Cache effectiveness
- Resource usage

## Deployment Considerations

### Installation Methods
- pip package (future)
- Docker container
- Git clone + pip install
- System package managers

### Monitoring
- Structured logging
- Metrics collection hooks
- Performance tracking
- Error rate monitoring