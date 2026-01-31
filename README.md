# GitSmart

> Your git repository's memory made searchable

GitSmart transforms your git repository into an intelligent knowledge base. Ask questions about your codebase in natural language and get answers based on your actual git history, file evolution, and development decisions.

## Quick Start

```bash
# Install
pip install gitsmart

# Initialize in your repo
cd your-project
gitsmart init

# Ask questions
gitsmart ask "Why do we use Redis?"
gitsmart ask "What is this repository about?"
gitsmart ask "When was authentication added?"

# Explain files
gitsmart explain app.py
gitsmart explain src/components/

# Remember decisions  
gitsmart remember "Decided to use PostgreSQL for better ACID compliance"
```

## Features

### 🔍 **Natural Language Queries**
Ask questions about your codebase and get intelligent answers based on git history:

```bash
gitsmart ask "Why is this authentication code so complex?"
```

### 📖 **File Evolution Understanding**  
Understand why files exist and how they evolved over time:

```bash
gitsmart explain weird_legacy_file.py
```

### 🧠 **Decision Memory**
Store and retrieve decisions with full context:

```bash
gitsmart remember "Switched to JWT for stateless auth"
gitsmart ask "Why did we choose JWT?"
```

## How It Works

GitSmart analyzes your git repository to understand:
- **Commit history and messages** - What changes were made and why
- **File evolution** - How code evolved over time  
- **Developer context** - Who wrote what and when
- **Decision patterns** - Why technical choices were made

It then uses AI to make this information searchable through natural language.

## Installation

```bash
pip install gitsmart
```

### Requirements
- Python 3.8+
- Git repository
- OpenAI API key (get one at [platform.openai.com](https://platform.openai.com/api-keys))

## Setup

1. **Initialize in your repository:**
   ```bash
   cd your-project
   gitsmart init
   ```

2. **Provide your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Start asking questions:**
   ```bash
   gitsmart ask "What is this repository about?"
   ```

## Commands

### `gitsmart ask <question>`
Query your repository with natural language:

```bash
gitsmart ask "What database do we use?"
gitsmart ask "Who wrote the payment system?"
gitsmart ask "What was the biggest change last month?"
gitsmart ask "How does authentication work?"
```

### `gitsmart explain <path>`
Explain why files or directories exist:

```bash
gitsmart explain app.py                    # Single file
gitsmart explain src/components/           # Directory
gitsmart explain .                         # Entire repository
```

### `gitsmart remember <note>`
Store decisions and notes with git context:

```bash
gitsmart remember "Decided to use Redis for session storage"
gitsmart remember "Bug in payment flow - investigate timeout issues"
gitsmart remember "Team agreed to use TypeScript for new features"
```

### Utility Commands

```bash
gitsmart status          # Show GitSmart status and statistics
gitsmart config          # Manage configuration
gitsmart --help          # Show help
```

## Configuration

GitSmart stores configuration in `.gitsmart/config.yml`:

```yaml
ai:
  provider: openai
  model: gpt-4
  api_key_env: OPENAI_API_KEY

output:
  format: plain
  color: true
```

## Use Cases

### 🏗️ **Understanding Legacy Code**
```bash
gitsmart explain legacy_auth_module.py
gitsmart ask "Why is this validation logic so complex?"
```

### 👋 **Onboarding New Developers**
```bash
gitsmart ask "What should I know about this codebase?"
gitsmart ask "How is the project structured?"
gitsmart ask "What are the main components?"
```

### 🔍 **Code Archaeology**
```bash
gitsmart ask "Why did we switch from MySQL to PostgreSQL?"
gitsmart ask "When was the API redesigned?"
gitsmart ask "What was the original reason for this weird hack?"
```

### 📋 **Decision Documentation**
```bash
gitsmart remember "Chose FastAPI over Flask for better async support"
gitsmart ask "What web framework decisions have we made?"
```

### 🚨 **Debugging and Maintenance**
```bash
gitsmart ask "What files are related to user authentication?"
gitsmart ask "Who knows the most about the payment system?"
gitsmart explain mysterious_bug_fix.py
```

## Examples

### Real Repository Analysis

```bash
$ gitsmart ask "What is this repository?"
🔍 Analyzing repository history...

This is a Python web application with 342 commits over 14 months. 
The main components are:
- FastAPI backend (app/) handling REST API
- React frontend (frontend/) with TypeScript  
- PostgreSQL database with SQLAlchemy ORM
- Redis for caching and session storage

Recent activity focuses on user authentication and payment processing.

$ gitsmart explain app/auth/jwt_handler.py
📄 Analyzing app/auth/jwt_handler.py...

## Purpose
JWT token handling utilities created to implement stateless authentication.

## History
• Created: 2023-09-15 (commit a1b2c3d)
  Reason: Replace session-based auth for API scalability
  
• Major changes:
  - 2023-10-01: Added token refresh mechanism
  - 2023-11-12: Enhanced security with rotating secrets
  - 2024-01-05: Added multi-audience support for mobile app

## Usage
• app/api/auth.py (token generation and validation)
• app/middleware/auth.py (request authentication)
• tests/test_jwt.py (comprehensive test coverage)

💡 Use `gitsmart ask "How does JWT auth work?"` for implementation details.
```

## Privacy and Security

- **Local Processing**: Git analysis happens locally on your machine
- **API Calls**: Only processed content is sent to AI providers  
- **No Code Storage**: Your code never leaves your machine permanently
- **API Key Control**: You control and provide your own AI API keys

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Roadmap

- [ ] Multiple AI provider support (Claude, local models)
- [ ] Cross-repository analysis  
- [ ] Team collaboration features
- [ ] Web dashboard for business users
- [ ] Integration with GitHub/GitLab
- [ ] VSCode extension

## Support

- **Documentation**: [Full docs](https://docs.gitsmart.dev)
- **Issues**: [GitHub Issues](https://github.com/gitsmart/gitsmart/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gitsmart/gitsmart/discussions)
- **Email**: support@gitsmart.dev

---

**Made with ❤️ for developers who want to understand their code**