# Contributing to AuthLib

Thank you for your interest in contributing to AuthLib! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and inclusive. We're building this for the community.

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/authlib.git
   cd authlib
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Follow PEP 8 style guidelines
   - Add type hints

3. **Write tests**
   - Add tests in `tests/` directory
   - Run tests: `pytest tests/`
   - Aim for >85% coverage: `pytest --cov=authlib tests/`

4. **Format code**
   ```bash
   black authlib/
   isort authlib/
   ```

5. **Lint code**
   ```bash
   flake8 authlib/
   mypy authlib/
   ```

6. **Commit changes**
   ```bash
   git commit -m "Brief description of changes"
   ```

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**
   - Write a clear description
   - Reference related issues
   - Ensure CI passes

## Coding Standards

- **Type Hints**: All functions must have type hints
- **Docstrings**: Use Google-style docstrings
- **Tests**: Write tests for all functionality
- **Comments**: Use comments for complex logic
- **Naming**: Use clear, descriptive names

### Example Function

```python
def create_user(
    email: str,
    password: str,
    first_name: Optional[str] = None,
) -> User:
    """
    Create a new user.

    Args:
        email: User email address
        password: Plain text password
        first_name: User's first name (optional)

    Returns:
        Created User object

    Raises:
        ValidationError: If email or password is invalid
        UserAlreadyExists: If user with email already exists
    """
    # Implementation...
```

## Testing Guidelines

- Write unit tests for utilities
- Write integration tests for services
- Use fixtures for shared test data
- Test error cases
- Test edge cases

```python
def test_create_user(test_db_session, test_user_data):
    """Test creating a new user."""
    user_service = UserService(test_db_session)
    
    user = user_service.create_user(
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    
    assert user.id is not None
    assert user.email == test_user_data["email"]
```

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design changes
- Write docstrings for all public functions
- Add examples for new features

## Pull Request Process

1. Update documentation
2. Add/update tests
3. Ensure all tests pass
4. Request review from maintainers
5. Address feedback
6. Maintain clean commit history

## Issue Reporting

- Use clear title describing the issue
- Include steps to reproduce
- Provide expected vs actual behavior
- Include environment info (Python version, OS, etc.)

## Release Process

Maintainers will handle releases following semantic versioning:
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

## Questions?

- Open an issue with [QUESTION] tag
- Start a discussion on GitHub Discussions
- Email: support@authlib.dev

---

Thank you for contributing! 🎉
