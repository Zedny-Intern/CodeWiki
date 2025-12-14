# AI-Powered Code Wiki System

An intelligent documentation platform that automatically clones, analyzes, and documents GitHub repositories with AI-powered Q&A capabilities.

## What It Does

This system creates a living, searchable knowledge base from your codebases by:
- **Automatically cloning** public/private GitHub repositories
- **Analyzing code** to understand architecture and relationships
- **Generating documentation** and diagrams automatically
- **Answering questions** about your code using AI
- **Staying synced** with repository changes in real-time

## Quick Start

### Prerequisites
- Python 3.8+
- Git installed
- GitHub Personal Access Token (PAT)
- Groq API key (free tier available)

### Installation

```bash
# Clone this repo
git clone <your-repo-url>
cd code-wiki-system

# Install dependencies
pip install crewai requests pydantic

# Configure (edit CONFIG in the script)
# Add your tokens:
# - GROQ_API_KEY
# - GITHUB_PAT
```

### Configuration

Edit the `CONFIG` dictionary in the script:

```python
CONFIG = {
    "GROQ_API_KEY": "your-groq-api-key",
    "GITHUB_PAT": "your-github-token",
    "REPO_TYPE": "private",  # or "public"
    "CLONE_BASE_PATH": "./cloned_repos",
    # ... other settings
}
```

For **public repos**, add:
```python
CONFIG["PUBLIC_REPO_URL"] = "https://github.com/owner/repo"
```

### Run

```bash
python main.py
```

## How It Works

### For Private Repositories
1. **Monitor** - Checks GitHub notifications for collaboration invites
2. **Accept** - Automatically accepts repository invitations
3. **Clone** - Clones the repository with authentication
4. **Analyze** - (Future) Parses code and generates docs

### For Public Repositories
1. **Validate** - Checks if repository exists and is accessible
2. **Clone** - Clones the repository
3. **Analyze** - (Future) Processes code for documentation

## Agent System

The system uses 4 specialized AI agents:

| Agent | Role |
|-------|------|
| **Notification Monitor** | Watches for GitHub invitations |
| **Invitation Handler** | Accepts collaboration invites |
| **Repository Cloner** | Clones repos with proper auth |
| **Workflow Coordinator** | Orchestrates the entire process |

## Repository Access Methods

### Recommended: Deploy Keys (SSH)
- Repo-specific, read-only
- Most secure for automation
- See full documentation for setup

### Personal Access Token (PAT)
- Quick setup for testing
- Works for multiple repos
- Used in current implementation

## Security Best Practices

✅ **DO:**
- Store tokens in environment variables or secrets manager
- Use read-only access when possible
- Rotate credentials every 90 days
- Enable 2FA on GitHub accounts

❌ **DON'T:**
- Commit tokens to repositories
- Use write access unless necessary
- Share agent credentials
- Log sensitive information

## Architecture Overview

```
User Query → Q&A Engine → Vector DB → AI Analysis
                ↑              ↑           ↑
                └──────────────┴───────────┘
                          ↑
                    Sync Engine
                          ↑
                   Local Repository
                          ↑
                    Clone Agent
                          ↑
                    GitHub Repo
```

## Technology Stack

- **AI Models:** Llama 3.3 70B (via Groq), GPT-4, Claude
- **Code Analysis:** tree-sitter, AST parsing
- **Embeddings:** OpenAI, Cohere, Sentence-BERT
- **Vector DB:** FAISS, Pinecone, Weaviate
- **Diagrams:** Graphviz, Mermaid, PlantUML
- **Agent Framework:** CrewAI

## Roadmap

**Current (v1.0):**
- ✅ Repository cloning (public/private)
- ✅ GitHub API integration
- ✅ Multi-agent orchestration

**Next Phase (v1.1):**
- 🔄 Code parsing and analysis
- 🔄 Documentation generation
- 🔄 Embedding creation and indexing

**Future (v2.0):**
- ⏳ Semantic search
- ⏳ AI-powered Q&A
- ⏳ Real-time sync engine
- ⏳ Web UI dashboard

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16-32 GB |
| Storage | 100 GB SSD | 500 GB+ NVMe |
| GPU | Not required* | RTX 3060+* |

*GPU only needed for local LLM inference

## Troubleshooting

**Clone fails with authentication error:**
- Verify your PAT has `repo` scope
- Check token hasn't expired
- Ensure you're added as collaborator for private repos

**No invitations found:**
- Verify invitation was sent to agent account
- Check GitHub notifications manually
- Try `get_repository_invitations_tool` directly

**Import errors:**
- Install missing packages: `pip install <package-name>`
- Verify Python version: `python --version` (needs 3.8+)

## Resources

- [Full Documentation](CODE_WIKI_DOC.md)
- [GitHub Deploy Keys Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
- [CrewAI Documentation](https://docs.crewai.com)
- [Groq API](https://groq.com)

## Contributing

This is a production system in active development. For questions or issues, refer to the complete documentation.

## License

See LICENSE file for details.

---

**Built with:** CrewAI + Groq + GitHub API  
**Version:** 1.0  
**Last Updated:** December 2025