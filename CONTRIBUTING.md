# Contributing to EduHub

Thank you for your interest in contributing to EduHub! This guide will help you get started with our development workflow and contribution standards.

## 🚀 Quick Start for Contributors

### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/eduhub.git
cd eduhub

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/eduhub.git
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Create Feature Branch
```bash
# Get latest changes
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

## 📋 Development Workflow

### Code Quality Standards

Our CI/CD pipeline enforces strict quality standards that must be met before merge:

#### **Formatting & Style**
- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting with Black profile
- **PEP 8**: Python style guidelines

#### **Type Safety**
- **MyPy**: Static type checking required
- **Type hints**: All functions must have type annotations
- **Return types**: Explicit return type annotations

#### **Testing**
- **Coverage**: Minimum 60% test coverage (target: 80%)
- **Pytest**: All tests must pass
- **Integration tests**: Include tests for new integrations

#### **Security**
- **Safety**: No known vulnerabilities in dependencies
- **Bandit**: Security linting for code patterns
- **Secrets**: No hardcoded secrets or credentials

### Local Development Commands

```bash
# Format code
black src tests
isort src tests

# Type checking
mypy src

# Run tests with coverage
pytest --cov=src --cov-fail-under=60

# Run all quality checks
pre-commit run --all-files

# Security scanning
safety check
bandit -r src/
```

### Docker Development

```bash
# Start development stack
docker-compose up -d

# Run tests in container
docker-compose exec api pytest

# View logs
docker-compose logs -f api

# Shell access
docker-compose exec api bash
```

## 🎯 Contribution Types

### Bug Fixes
1. **Search existing issues** before creating new ones
2. **Create issue** if bug doesn't exist
3. **Reference issue** in commit and PR
4. **Include tests** that reproduce the bug
5. **Verify fix** doesn't break existing functionality

### New Features
1. **Open discussion** via GitHub Discussions or issue
2. **Wait for approval** before implementing large features
3. **Follow TDD**: Write tests first when possible
4. **Update documentation** as needed
5. **Consider backward compatibility**

### Documentation
1. **Clear and concise** writing
2. **Include code examples** when relevant
3. **Test documentation** links and commands
4. **Update README** if adding user-facing features

### Performance Improvements
1. **Benchmark before/after** with evidence
2. **Profile code** to identify bottlenecks
3. **Consider memory usage** alongside speed
4. **Avoid premature optimization**

## 📝 Commit Standards

### Conventional Commits
We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### **Types**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semi colons, etc)
- `refactor`: Code refactoring without feature changes
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Build process or auxiliary tool changes
- `ci`: Continuous integration changes

#### **Examples**
```bash
feat: add user authentication system
fix: resolve Plone connection timeout issue
docs: update API endpoint documentation
test: add integration tests for content CRUD
refactor: optimize database query performance
ci: add Docker build caching
```

#### **Scope Examples**
```bash
feat(auth): implement JWT token validation
fix(plone): handle connection retry logic
docs(api): add OpenAPI schema examples
test(integration): add Plone bridge tests
```

### Commit Best Practices
- **Atomic commits**: One logical change per commit
- **Clear descriptions**: Explain what and why, not how
- **Reference issues**: Include issue numbers when relevant
- **Imperative mood**: "Add feature" not "Added feature"

## 🔄 Pull Request Process

### Before Creating PR
1. **Rebase on latest main**: `git rebase upstream/main`
2. **Run all quality checks**: `pre-commit run --all-files`
3. **Test thoroughly**: Ensure all tests pass
4. **Update documentation**: If adding features
5. **Self-review**: Check your own diff first

### PR Requirements
- **Clear title**: Follow conventional commit format
- **Detailed description**: What, why, and how
- **Link related issues**: Use "Closes #123" or "Fixes #456"
- **Screenshots/demos**: For UI changes
- **Breaking changes**: Clearly documented

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or documented)
```

### Review Process
1. **Automated checks**: CI must pass
2. **Code review**: At least one approval required
3. **Testing**: Reviewer should test changes
4. **Merge strategy**: Squash and merge preferred

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_auth.py
│   └── test_plone_client.py
├── integration/             # Integration tests
│   ├── test_api_endpoints.py
│   └── test_plone_bridge.py
├── fixtures/               # Test data and fixtures
└── conftest.py            # Test configuration
```

### Writing Tests
```python
# Good test example
def test_plone_client_authentication_success():
    """Test successful authentication with valid credentials."""
    # Arrange
    client = PloneClient(config=valid_config)
    
    # Act
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"token": "valid-token"}
        
        # Assert
        assert client.authenticate() is True
        assert client.token == "valid-token"
```

### Test Categories
- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **API tests**: Test HTTP endpoints
- **Performance tests**: Benchmark critical paths

### Test Best Practices
- **Descriptive names**: Clear test purpose
- **AAA pattern**: Arrange, Act, Assert
- **Independent tests**: No test dependencies
- **Mock external services**: Use mocks for APIs, databases
- **Test edge cases**: Error conditions, boundary values

## 🏗️ Architecture Guidelines

### Code Organization
```
src/
├── eduhub/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── core/                # Core business logic
│   │   ├── auth.py
│   │   └── config.py
│   ├── api/                 # API routes
│   │   ├── endpoints/
│   │   └── dependencies.py
│   ├── models/              # Data models
│   ├── services/            # Business services
│   └── integrations/        # External integrations
│       └── plone.py
```

### Design Principles
1. **Separation of concerns**: Clear module responsibilities
2. **Dependency injection**: Use FastAPI dependencies
3. **Error handling**: Consistent error responses
4. **Async/await**: Use async where beneficial
5. **Type safety**: Comprehensive type hints

### API Design
- **RESTful endpoints**: Follow REST conventions
- **Consistent responses**: Standard JSON format
- **Error handling**: HTTP status codes + error details
- **Documentation**: OpenAPI/Swagger integration
- **Versioning**: Consider API versioning strategy

## 🔒 Security Guidelines

### Code Security
- **Input validation**: Validate all user inputs
- **SQL injection**: Use parameterized queries
- **Authentication**: Secure token handling
- **Authorization**: Role-based access control
- **Secrets management**: Environment variables only

### Dependency Security
- **Regular updates**: Keep dependencies current
- **Vulnerability scanning**: Safety and Bandit checks
- **License compliance**: Check license compatibility

### Data Protection
- **Sensitive data**: Never log passwords or tokens
- **Encryption**: Use HTTPS in production
- **Privacy**: Follow data protection regulations

## 📚 Documentation Standards

### Code Documentation
```python
def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password.
    
    Args:
        username: User's username or email
        password: User's plain text password
        
    Returns:
        User object if authentication successful, None otherwise
        
    Raises:
        AuthenticationError: If authentication service unavailable
        
    Example:
        >>> user = authenticate_user("john@example.com", "secret123")
        >>> print(user.name if user else "Authentication failed")
    """
```

### API Documentation
- **OpenAPI schemas**: Complete parameter documentation
- **Examples**: Request/response examples
- **Error codes**: Document all possible errors
- **Rate limiting**: Document any limits

### README Updates
- **Feature additions**: Update feature list
- **Breaking changes**: Update migration guide
- **Dependencies**: Update requirements
- **Installation**: Keep setup instructions current

## 🎉 Recognition

### Contributors
We recognize contributions in several ways:
- **Contributors file**: Listed in CONTRIBUTORS.md
- **Release notes**: Mentioned in CHANGELOG.md
- **GitHub releases**: Tagged in release descriptions

### Types of Contributions
- Code contributions
- Documentation improvements  
- Bug reports and testing
- Community support
- Translations
- Design and UX improvements

## 📞 Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Request Comments**: Code-specific discussions

### Code of Conduct
We expect all contributors to follow our code of conduct:
- **Be respectful**: Treat everyone with respect
- **Be inclusive**: Welcome newcomers and diverse perspectives
- **Be collaborative**: Work together constructively
- **Be professional**: Keep discussions focused and productive

### Development Support
- **Setup issues**: Tag with `help wanted`
- **Architecture questions**: Start GitHub Discussion
- **Bug help**: Provide minimal reproduction case

## 🚀 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Workflow
1. **Update CHANGELOG.md**: Document all changes
2. **Version bump**: Update version in pyproject.toml
3. **Create release PR**: For review
4. **Tag release**: After merge to main
5. **Deploy**: Automated via CI/CD

---

Thank you for contributing to EduHub! Together we're building the future of education technology. 🎓✨ 