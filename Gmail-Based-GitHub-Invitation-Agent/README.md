# 🤖 Gmail-Based GitHub Invitation Agent

An intelligent automation system that monitors Gmail for GitHub repository invitations, automatically accepts them via browser automation, and clones repositories locally using AI-powered multi-agent architecture.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.28.8-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ Features

- 📬 **Gmail Integration** - Monitors inbox via Gmail API for GitHub invitations
- 🌐 **Browser Automation** - Selenium-based invitation acceptance
- 🧠 **Local LLM** - Ollama with Qwen 2.5 for intelligent reasoning (optional)
- 🤖 **Multi-Agent System** - CrewAI orchestration with 4 specialized agents
- 💰 **Zero API Costs** - All processing done locally
- 📊 **Structured Reports** - JSON workflow reports

---

## 📁 Project Structure

```
project/
├── agent_system.py           # Main agent script
├── cloned_repos/             # Cloned repositories (auto-created)
├── reports/                  # Workflow reports (auto-created)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/gmail-github-agent.git
cd gmail-github-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
```

### 5. Set Up Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Gmail API** (APIs & Services → Library)
4. Create OAuth 2.0 credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - Download JSON → Save as `credentials.json` in project root
5. Add your email as a test user in OAuth consent screen

### 6. Install Ollama (Optional but Recommended)

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Pull the reasoning model
ollama pull qwen2.5:7b-instruct
```

### 7. Run the Agent

```bash
python agent_system.py
```

On first run, a browser will open for Gmail authentication. Grant permissions and the token will be saved.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_USERNAME` | Your GitHub username | `myuser` |
| `GITHUB_PASSWORD` | GitHub password or token | `ghp_xxxx` |
| `GITHUB_EMAIL` | Your email address | `user@example.com` |
| `LLM_MODEL` | Ollama model name | `qwen2.5:7b-instruct` |
| `LLM_ENABLED` | Enable/disable LLM | `true` or `false` |
| `HEADLESS_BROWSER` | Hide browser window | `true` or `false` |
| `CLONE_BASE_PATH` | Where to clone repos | `./cloned_repos` |

> ⚠️ **Never commit your `.env` file!** It contains sensitive credentials.

---

## 🔄 How It Works

The system uses four specialized agents:

1. **Email Monitor Agent** - Scans Gmail for GitHub invitation emails
2. **Invitation Acceptor Agent** - Logs into GitHub and accepts invitations via Selenium
3. **Repository Cloner Agent** - Clones accepted repositories locally
4. **Workflow Coordinator Agent** - Generates comprehensive JSON reports

```
Gmail → Parse Invitations → Accept via Browser → Clone Repos → Generate Report
```

---

## 📋 Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Chrome/Chromium | Latest |
| ChromeDriver | Matching Chrome version |
| Git | Any recent version |
| Ollama (optional) | Latest |

---

## 🛠️ Troubleshooting

### Gmail Authentication Failed
```bash
# Delete old token and re-authenticate
rm token.json
python agent_system.py
```

### Ollama Not Running
```bash
# Check status
ollama list

# Pull model if missing
ollama pull qwen2.5:7b-instruct
```

### Selenium Button Not Found
Set `HEADLESS_BROWSER=false` in `.env` to watch browser actions and debug.

### ChromeDriver Issues
Ensure ChromeDriver version matches your Chrome browser version.

---

## 📊 Sample Output

```
================================================================================
🤖 GMAIL-BASED GITHUB INVITATION AGENT
================================================================================

📧 Checking Gmail for GitHub invitations...
   ✅ Found: owner/repository-name

🌐 Accepting invitation...
   ✅ Successfully accepted!

📦 Cloning repository...
   ✅ Clone successful!

📄 Report saved: reports/workflow_report_20251219_120000.json
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [CrewAI](https://docs.crewai.com) - Multi-agent orchestration
- [Ollama](https://ollama.com) - Local LLM inference
- [Selenium](https://selenium-python.readthedocs.io/) - Browser automation
- [Gmail API](https://developers.google.com/gmail/api) - Email access
