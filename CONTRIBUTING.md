# Contributing to ZTA Behavioral Monitoring System

We love your input! We want to make contributing to the ZTA Behavioral Monitoring System as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🚀 Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## 🔄 Pull Requests

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## 🔧 Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/zta-behavioral-monitoring.git
   cd zta-behavioral-monitoring
   ```

2. **Set up development environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Run tests**
   ```bash
   python -m pytest tests/
   ```

4. **Start development server**
   ```bash
   python3 main.py
   ```

## 🐛 Bug Reports

We use GitHub issues to track public bugs. Report a bug by opening a new issue.

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## 💡 Feature Requests

We use GitHub issues to track feature requests. When filing an issue, make sure to answer these questions:

1. What feature would you like to see?
2. Why do you want this feature?
3. How should it work?
4. Are there any alternatives you've considered?

## 🔍 Code Style

* Follow PEP 8 Python style guidelines
* Use type hints where possible
* Write descriptive variable and function names
* Add docstrings to all functions and classes
* Keep functions small and focused
* Use meaningful commit messages

### Code Formatting

We use the following tools for code formatting:

```bash
# Install formatting tools
pip install black isort flake8

# Format code
black .
isort .

# Check for issues
flake8 .
```

## 🧪 Testing

All code changes should include appropriate tests:

* **Unit tests** for individual functions
* **Integration tests** for API endpoints
* **End-to-end tests** for critical workflows

Run tests with:
```bash
python -m pytest tests/ -v
```

## 📝 Documentation

When adding new features:

1. Update docstrings for any new functions/classes
2. Update the README.md if necessary
3. Update API documentation in the code
4. Consider updating the USER_GUIDE.md

## 🏗️ Project Structure

Please maintain the existing project structure:

```
zta-behavioral-monitoring/
├── src/                     # Source code
│   ├── api/                 # FastAPI backend
│   ├── core/                # Core business logic
│   ├── ml/                  # Machine learning models
│   └── monitoring/          # Event collection
├── tests/                   # Test files
├── config/                  # Configuration files
├── docs/                    # Additional documentation
└── scripts/                 # Utility scripts
```

## 🔒 Security

If you find a security vulnerability, please do NOT open a public issue. Instead, email the maintainers directly.

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- The project README
- Release notes for versions containing their contributions
- The project's contributor list

## 📚 Resources

* [Python PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [Scikit-learn Documentation](https://scikit-learn.org/)
* [pytest Documentation](https://docs.pytest.org/)

## 💬 Questions?

Don't hesitate to ask questions! Open an issue with the label "question" or reach out to the maintainers.

---

Thank you for contributing to ZTA Behavioral Monitoring System! 🛡️
