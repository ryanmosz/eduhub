# Quality Gates Configuration

This document defines the quality gates enforced by the EduHub CI/CD pipeline to ensure code quality, security, and reliability.

## Overview

Quality gates are automated checks that must pass before code can be merged or deployed. They are divided into **Core Gates** (mandatory) and **Optional Gates** (advisory).

## Core Quality Gates (Must Pass)

These gates must pass for the pipeline to succeed:

### 1. Code Quality Gate
- **Tools**: Black, isort, MyPy
- **Requirements**:
  - Code must be formatted with Black (line length: 88)
  - Imports must be sorted with isort
  - MyPy type checking (warnings allowed, not errors)
- **Failure Impact**: Blocks merge/deployment
- **Fix Strategy**: Run `black src tests && isort src tests` locally

### 2. Unit Testing Gate  
- **Coverage Threshold**: 60% minimum
- **Python Versions**: 3.9, 3.11 (matrix testing)
- **Requirements**:
  - All tests must pass
  - Coverage above minimum threshold
  - No test failures on either Python version
- **Failure Impact**: Blocks merge/deployment
- **Fix Strategy**: Add tests or fix failing tests

### 3. Integration Testing Gate
- **Components**: Plone-FastAPI bridge tests
- **Requirements**:
  - All integration tests pass
  - Mock external dependencies work correctly
  - API endpoints respond correctly
- **Failure Impact**: Blocks merge/deployment
- **Fix Strategy**: Fix integration issues or update tests

### 4. Build Validation Gate
- **Components**: Python package build
- **Requirements**:
  - Package builds successfully
  - Twine validation passes
  - No build warnings or errors
- **Failure Impact**: Blocks merge/deployment
- **Fix Strategy**: Fix package configuration issues

## Optional Quality Gates (Advisory)

These gates provide warnings but don't block the pipeline:

### 5. Security Scanning Gate
- **Tools**: Safety (dependency vulnerabilities), Bandit (security linting)
- **Requirements**:
  - No high-severity vulnerabilities in dependencies
  - No security anti-patterns in code
- **Failure Impact**: Warning only, doesn't block
- **Fix Strategy**: Update dependencies, fix security issues

### 6. Docker Build Gate
- **Components**: Container build and test
- **Requirements**:
  - Docker image builds successfully
  - Container starts and responds to health checks
  - Image pushes to registry (if secrets available)
- **Failure Impact**: Warning only, doesn't block
- **Fix Strategy**: Fix Dockerfile, container configuration

## Quality Standards

### Code Quality Standards
```yaml
black:
  line-length: 88
  target-version: py39

isort:
  profile: black
  multi_line_output: 3

mypy:
  python_version: 3.9
  warn_return_any: true
  warn_unused_configs: true
  ignore_missing_imports: true
```

### Testing Standards
```yaml
pytest:
  minimum_coverage: 60%
  fail_under: 60%
  python_versions: [3.9, 3.11]
  
coverage:
  exclude_lines:
    - "pragma: no cover"
    - "def __repr__"
    - "raise NotImplementedError"
```

### Security Standards
```yaml
safety:
  ignore_vulnerabilities: []
  
bandit:
  severity: medium
  confidence: medium
  exclude_paths: [tests/]
```

## Threshold Configuration

### Current Thresholds
- **Test Coverage**: 60% (target: increase to 80%)
- **MyPy**: Warnings allowed (target: strict mode)
- **Security**: Medium+ severity (target: all levels)

### Progressive Enhancement Plan
1. **Phase 1** (Current): 60% coverage, MyPy warnings
2. **Phase 2**: 70% coverage, MyPy strict on new code
3. **Phase 3**: 80% coverage, full MyPy strict mode

## Gate Evaluation Logic

### Success Criteria
```bash
CORE_GATES_PASSED = (
    lint_job == "success" &&
    test_job == "success" &&
    integration_job == "success" &&
    build_job == "success"
)

PIPELINE_SUCCESS = CORE_GATES_PASSED
# Optional gates don't affect overall success
```

### Failure Handling
- **Core Gate Failure**: Pipeline fails, blocks merge
- **Optional Gate Failure**: Warning logged, pipeline continues
- **Partial Failure**: If any core gate fails, entire pipeline fails

## Overrides and Exceptions

### Emergency Overrides
In exceptional circumstances, quality gates can be bypassed:

1. **Security Hotfix**: Use `[skip-quality-gates]` in commit message
2. **Infrastructure Issues**: Override via GitHub branch protection
3. **False Positives**: Temporary ignore rules in tool configs

### Override Process
1. Document reason in PR description
2. Get approval from tech lead
3. Create follow-up issue to address
4. Remove override after fix

## Monitoring and Metrics

### Pipeline Metrics
- **Gate Success Rate**: % of pipelines passing all gates
- **Coverage Trend**: Coverage percentage over time
- **Security Issues**: Count of vulnerabilities found
- **Build Time**: Time to complete all gates

### Quality Trends
- **Code Quality**: Black/isort violations over time
- **Test Reliability**: Flaky test detection
- **Security Posture**: Vulnerability introduction rate

## Local Development

### Pre-commit Setup
Run quality checks locally before pushing:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run all checks manually
pre-commit run --all-files
```

### Quality Check Commands
```bash
# Code formatting
black src tests
isort src tests

# Type checking  
mypy src

# Testing with coverage
pytest --cov=src --cov-fail-under=60

# Security scanning
safety check
bandit -r src/
```

## Troubleshooting

### Common Issues

**Coverage Below Threshold**:
- Add tests for uncovered code
- Remove dead/unreachable code
- Update coverage configuration

**MyPy Type Errors**:
- Add type annotations
- Use `# type: ignore` for false positives
- Update mypy configuration

**Security Vulnerabilities**:
- Update affected dependencies
- Add security exceptions if false positive
- Implement security fixes

**Docker Build Failures**:
- Check Dockerfile syntax
- Verify base image availability
- Fix application startup issues

## Configuration Files

- **Workflow**: `.github/workflows/ci.yml`
- **Secrets**: `.github/SECRETS.md`
- **PyProject**: `pyproject.toml` (tool configurations)
- **Coverage**: `.coveragerc` (if needed)

This quality gates system ensures consistent code quality while allowing for iterative improvement and emergency procedures when needed. 