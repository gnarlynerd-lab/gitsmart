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

# Enable automated memory capture (optional but recommended)
./install-hooks.sh

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

### 🔄 **Automated Capture** 
Install git hooks to automatically document decisions as you code:

```bash
# Install hooks
./install-hooks.sh

# Now every significant commit prompts for documentation
git commit -m "Switch from REST to GraphQL"

🤖 GitSmart detected architectural decision. Save reasoning?
💡 Suggested reasoning: GraphQL chosen for better type safety and reduced over-fetching
[Y/n/edit]: Y

✅ Decision documented automatically
```

## How It Works

GitSmart creates organizational memory in three ways:

### 📊 **Repository Analysis** 
Automatically analyzes your git repository to understand:
- **Commit history and messages** - What changes were made and when
- **File evolution** - How code evolved over time  
- **Developer context** - Who contributed what and when
- **Change patterns** - Frequency and type of modifications

### 🤖 **Automated Documentation**
Optional git hooks capture decisions as they happen:
- **Detects significant commits** (architectural changes, large refactors)
- **AI suggests reasoning** based on commit content and file changes
- **Prompts for confirmation** or manual editing
- **Stores as git notes** that sync with your repository

### 💭 **Team Memory**
All captured knowledge becomes part of your repository:
- **Git notes storage** - Memories sync across the team automatically
- **AI-powered search** - Natural language queries find relevant context
- **Contextual responses** - Answers include both git history and stored decisions

## Installation

```bash
pip install gitsmart
```

### Requirements
- Python 3.8+
- Git repository
- AI provider access:
  - **Public APIs**: DeepSeek, OpenAI
  - **Enterprise**: Azure OpenAI, AWS Bedrock, Google Vertex AI
  - **Local**: Ollama, GitHub Copilot Chat

## Setup

1. **Initialize in your repository:**
   ```bash
   cd your-project
   gitsmart init
   ```

2. **Configure AI provider:**
   ```bash
   # Public APIs
   export DEEPSEEK_API_KEY="your-api-key-here"
   export OPENAI_API_KEY="your-api-key-here"
   
   # Enterprise Azure OpenAI
   export AZURE_OPENAI_API_KEY="your-key"
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   
   # Local/On-premise
   export OLLAMA_BASE_URL="http://localhost:11434"
   ```

3. **(Optional) Install automated memory capture:**
   ```bash
   ./install-hooks.sh
   ```

4. **Start asking questions:**
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

### Automated Documentation

```bash
# Install git hooks for automatic decision capture
./install-hooks.sh

# Analyze any commit manually  
gitsmart analyze-commit HEAD --suggest-only

# Test the automation
git commit -m "Major refactor of authentication system"
# → GitSmart will automatically prompt to document the decision
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
  provider: deepseek    # deepseek, openai, azure, ollama
  model: deepseek-chat  # provider-specific models
  api_key_env: DEEPSEEK_API_KEY

# Enterprise configurations
enterprise:
  azure:
    endpoint: "https://your-resource.openai.azure.com/"
    deployment_name: "gpt-4"
    api_version: "2024-02-15-preview"
  
  ollama:
    base_url: "http://localhost:11434"
    model: "llama2:13b"

output:
  format: plain
  color: true
  
hooks:
  enabled: true
  auto_analyze: true
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
# Manual documentation
gitsmart remember "Chose FastAPI over Flask for better async support"

# Or let automation handle it
git commit -m "Replace Flask with FastAPI for async endpoints"
🤖 GitSmart: Document this architectural decision? [Y/n] Y
✅ Decision captured: FastAPI chosen for non-blocking request handling...

# Later, anyone can ask
gitsmart ask "What web framework decisions have we made?"
```

### 🚨 **Debugging and Maintenance**
```bash
gitsmart ask "What files are related to user authentication?"
gitsmart ask "Who knows the most about the payment system?"
gitsmart explain mysterious_bug_fix.py
```

### 🏢 **Enterprise Deployment**
```bash
# Configure for Azure OpenAI (data stays in your tenant)
gitsmart config set ai.provider azure
gitsmart config set azure.endpoint "https://your-company.openai.azure.com/"

# Or use on-premise Ollama for complete data isolation
gitsmart config set ai.provider ollama
gitsmart config set ollama.base_url "http://internal-llm.company.com:11434"

# Automated decision capture works with any provider
./install-hooks.sh
git commit -m "Implement new compliance requirements"
🤖 GitSmart: Document compliance decision? [Y/n] Y
✅ Stored securely in your enterprise environment
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

⚠️ **What gets sent to AI providers:**
- Commit messages and hashes (but not diff content)
- File paths and names (but not file contents)
- Author names and contributor info
- Repository structure and metadata

✅ **What stays local:**
- Actual source code and file contents
- Database contents, API keys, secrets
- Git objects and repository data

🔒 **Security measures:**
- You control your own AI API keys
- No permanent storage of your data by GitSmart
- Standard HTTPS encryption for API calls
- Local git analysis only

🏢 **Enterprise deployment options:**
- **Azure OpenAI**: Data stays in your Azure tenant
- **AWS Bedrock**: Private VPC deployment available
- **On-premise**: Use Ollama or local LLMs for complete data isolation
- **GitHub Copilot**: Integrate with existing enterprise AI tooling

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Roadmap

**✅ Phase 1 - Core Functionality**
- [x] Git-based team collaboration (git notes storage)
- [x] Automated decision capture (git hooks) 
- [x] Multiple AI provider support (DeepSeek, OpenAI)

**🚀 Phase 2 - Enterprise Integration**  
- [ ] Azure OpenAI integration
- [ ] AWS Bedrock support
- [ ] Local LLM support (Ollama)
- [ ] GitHub Copilot Chat integration
- [ ] SAML/SSO authentication

**📈 Phase 3 - Scale & Integration**
- [ ] Cross-repository analysis  
- [ ] Web dashboard for business users
- [ ] Integration with GitHub/GitLab  
- [ ] VSCode extension
- [ ] Slack/Teams integration
- [ ] JIRA/Linear decision linking

## Support

- **Documentation**: [Full docs](https://docs.gitsmart.dev)
- **Issues**: [GitHub Issues](https://github.com/gitsmart/gitsmart/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gitsmart/gitsmart/discussions)
- **Email**: support@gitsmart.dev

---

**Made with ❤️ for developers who want to understand their code**