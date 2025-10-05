# Contributing to IELTS AI Coach

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ielts-ai-coach.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Add your API keys to .env

# Run the application
./startup.sh
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Write docstrings for functions

## Testing

Before submitting:
- Test all functionality works
- Check both frontend and backend
- Verify with different LLM providers
- Test on your target OS

## Pull Request Process

1. Update documentation if needed
2. Test your changes thoroughly
3. Update CHANGELOG.md if applicable
4. Submit PR with clear description
5. Link any related issues

## Bug Reports

Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Error messages/logs

## Feature Requests

- Explain the use case
- Describe expected behavior
- Consider implementation approach
- Discuss alternatives

## Questions?

Open a [Discussion](https://github.com/MdRasheduz-zaman/ielts-ai-coach/discussions) for questions.

Thank you for contributing! 🙏
