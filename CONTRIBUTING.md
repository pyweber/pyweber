
# Contributing to PyWeber

Thank you for your interest in contributing to PyWeber! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful, inclusive, and considerate in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- pip

### Setting Up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/pyweber/pyweber.git
   cd pyweber
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Branching Strategy

- `main` - Stable release branch
- `dev` - Development branch for upcoming releases
- Feature branches should be created from `dev` and named descriptively:
  - `feature/new-feature-name`
  - `bugfix/issue-description`
  - `docs/documentation-update`

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: description of the changes"
   ```

3. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request against the `dev` branch of the main repository

### Coding Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions, classes, and methods
- Keep functions and methods focused on a single responsibility
- Use descriptive variable and function names

### Testing

Before submitting a pull request, ensure that:

1. All existing tests pass:
   ```bash
   pytest
   ```

2. You've added tests for new functionality
3. Your code passes linting:
   ```bash
   flake8 pyweber
   ```

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the CHANGELOG.md with details of changes
3. The PR should work with Python 3.10 and above
4. Ensure all tests pass and code quality checks succeed
5. Request review from maintainers

## Documentation

- Update documentation for any new features or changes to existing functionality
- Follow the existing documentation style
- Use clear, concise language
- Include code examples where appropriate

## Reporting Bugs

When reporting bugs, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. PyWeber version
6. Python version
7. Operating system
8. Any relevant error messages or screenshots

## Feature Requests

Feature requests are welcome! Please provide:

1. A clear description of the feature
2. The motivation for the feature
3. Examples of how the feature would be used
4. Any relevant references or examples from other frameworks

## Community

- Join our discussions on GitHub Issues
- Ask questions and share ideas
- Help others who are getting started with PyWeber

## Release Process

For maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. Publish to PyPI:
   ```bash
   python -m build
   twine upload dist/*
   ```

## License

By contributing to PyWeber, you agree that your contributions will be licensed under the project's MIT License.

## Contact

If you have questions or need help, you can:

- Open an issue on GitHub
- Contact the maintainers directly
- Join our community channels

Thank you for contributing to PyWeber!