# 🌐 Public Repository Clone Agent

A multi-agent system for cloning public GitHub repositories directly, using AI-powered reasoning with local LLM (Ollama).

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.28.8-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ Features

- 🌐 **Direct Clone** - Clone public repositories directly from URL
- 🧠 **Local LLM** - Ollama with Qwen 2.5 for intelligent reasoning
- 🤖 **Multi-Agent System** - CrewAI orchestration with 3 specialized agents
- 💰 **Zero API Costs** - All processing done locally
- 📊 **Structured Reports** - JSON workflow reports
- ⚡ **Lightweight** - No Gmail API or Selenium required

---

## 📁 Project Structure

```
update/
├── agent_system_public.py    # Main agent script for public repos
├── cloned_repos/             # Cloned repositories (auto-created)
├── reports/                  # Workflow reports (auto-created)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies (simplified)
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd update
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Repository URL

Edit `agent_system_public.py` and set your target repository:

```python
PUBLIC_REPO_CONFIG = {
    "PUBLIC_REPO_URL": "https://github.com/owner/repo",  # <-- Set your URL here
    ...
}
```

### 3. Install Ollama (Recommended)

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Pull the reasoning model
ollama pull qwen2.5:7b-instruct
```

### 4. Run the Agent

```bash
python agent_system_public.py
```

---

## 🔄 How It Works

The system uses three specialized agents:

1. **URL Validator Agent** - Validates GitHub URL format and verifies repository exists
2. **Repository Cloner Agent** - Clones the repository to local storage
3. **Workflow Report Agent** - Generates comprehensive JSON reports

```
Configure URL → Validate → Clone → Generate Report
```

---

## ⚙️ Configuration

### In-Code Configuration

Edit `PUBLIC_REPO_CONFIG` in `agent_system_public.py`:

| Variable | Description | Example |
|----------|-------------|---------|
| `PUBLIC_REPO_URL` | Target repository URL | `https://github.com/microsoft/vscode` |
| `CLONE_BASE_PATH` | Where to clone repos | `./cloned_repos` |
| `LLM_MODEL` | Ollama model name | `qwen2.5:7b-instruct` |
| `LLM_ENABLED` | Enable/disable LLM | `True` or `False` |

### Environment Variables (Optional)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Environment variables override the in-code defaults for LLM settings.

---

## 📋 Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Git | Any recent version |
| Ollama (optional) | Latest |

---

## 🆚 Comparison with Private Agent

| Feature | agent_system.py (Private) | agent_system_public.py (Public) |
|---------|---------------------------|----------------------------------|
| Input | Gmail inbox | Configured URL |
| Dependencies | Gmail API, Selenium | Git only |
| Agents | 4 | 3 |
| Authentication | Required | None |
| Use Case | Private repos via invitation | Public repos |

---

## 📊 Sample Output

```
================================================================================
🌐 PUBLIC REPOSITORY CLONE AGENT - LOCAL LLM EDITION
================================================================================

📋 Configuration:
   Repository URL: https://github.com/crewAIInc/crewAI
   Clone Path: ./cloned_repos
   LLM Model: qwen2.5:7b-instruct
   LLM Status: ✅ Active

🚀 Starting public repository workflow...

🔍 Validating GitHub URL...
   ✅ Valid public repository: crewAIInc/crewAI

📦 Cloning repository...
   ✅ Clone successful!

================================================================================
✅ WORKFLOW COMPLETED
================================================================================

📄 Report saved: reports/workflow_report_20251219_224500.json
```

---

## 🛠️ Troubleshooting

### Ollama Not Running
```bash
ollama list
ollama pull qwen2.5:7b-instruct
```

### Repository Not Found
Ensure the URL is correct and the repository is public.

### Git Not Installed
Install Git from https://git-scm.com/downloads

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🔗 Related

- [agent_system.py](../agent_system.py) - Private repository agent (Gmail + Selenium)
- [CrewAI](https://docs.crewai.com) - Multi-agent orchestration
- [Ollama](https://ollama.com) - Local LLM inference
