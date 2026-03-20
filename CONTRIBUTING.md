Ok # Contributing to MeshCloud

Thank you for your interest in contributing to MeshCloud! We welcome contributions from the community. This document provides guidelines and information for contributors.

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## How to Contribute

### 1. Find an Issue

- Check the [Issues](https://github.com/yourusername/meshcloud/issues) page for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Development Setup

1. **Fork and Clone**:
```bash
git clone https://github.com/yourusername/meshcloud.git
cd meshcloud
```

2. **Create Virtual Environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Install Development Dependencies**:
```bash
pip install black ruff mypy pytest pytest-cov pre-commit
```

5. **Initialize Database**:
```bash
python -c "from app.db import init_db; init_db()"
```

6. **Set up Pre-commit Hooks**:
```bash
pre-commit install
```

### 3. Create a Branch

Create a feature branch for your changes:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 4. Make Changes

- Write clear, concise commit messages
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 5. Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov=utils --cov-report=html
```

### 6. Code Quality

Format your code:
```bash
black .
```

Check for linting issues:
```bash
flake8 .
```

Type checking:
```bash
mypy .
```

### 7. Commit and Push

```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 8. Create a Pull Request

1. Go to the original repository
2. Click "New Pull Request"
3. Select your branch
4. Fill out the pull request template
5. Submit for review

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use `black` for code formatting
- Use type hints where appropriate
- Write descriptive variable and function names
- Keep functions small and focused

### Testing

- Write unit tests for all new functionality
- Aim for >80% code coverage
- Test edge cases and error conditions
- Use descriptive test names

### Documentation

- Update README.md for significant changes
- Add docstrings to new functions
- Update API documentation for endpoint changes
- Keep examples current

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

## Architecture Guidelines

### API Design

- Use RESTful conventions
- Return appropriate HTTP status codes
- Provide meaningful error messages
- Version APIs when making breaking changes

### Database

- Use migrations for schema changes
- Avoid raw SQL when possible
- Handle database errors gracefully
- Consider performance implications

### Security

- Validate all inputs
- Use parameterized queries
- Implement proper authentication
- Follow security best practices

## Areas for Contribution

### High Priority

- **Testing**: Add comprehensive test coverage
- **Documentation**: Improve API docs and guides
- **Security**: Implement authentication and authorization
- **Performance**: Optimize chunking and replication

### Medium Priority

- **UI/UX**: Improve dashboard and CLI
- **Monitoring**: Add metrics and logging
- **Deployment**: Docker and Kubernetes support
- **Database**: PostgreSQL support

### Future Enhancements

- **Encryption**: End-to-end encryption
- **Plugins**: Extensible storage backends
- **Multi-region**: Geographic replication
- **Web UI**: Full web management interface

## Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Join community discussions
- **Documentation**: Check the README and docs first

## Recognition

Contributors will be:
- Listed in CHANGELOG.md for releases
- Recognized in release notes
- Added to a future contributors file

Thank you for contributing to MeshCloud! 🎉