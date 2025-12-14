# AI-Powered Code Wiki System — Complete Documentation

**Filename:** `CODE_WIKI_DOC.md`  
**Version:** 1.0  
**Last Updated:** December 2025

---

## 1. Executive Summary

This project builds an AI-powered documentation platform similar to Google Code Wiki. It automatically connects to public/private repositories, maintains synchronized local copies, analyzes codebases, and generates an interactive, always-up-to-date knowledge base with Q&A capabilities.

**Key Features:**
- Automatic repository cloning and sync (via AI agent)
- Deep code analysis and architecture understanding
- Auto-generated documentation and diagrams
- Semantic search and embeddings-based Q&A
- Real-time sync engine to reflect code changes

**Agent Role (Critical):** The AI agent ONLY clones and updates repositories. All analysis, documentation generation, diagramming, indexing, and Q&A are handled by the Code Wiki system itself.

---

## 2. Technology Overview

**Core Technologies (Beginner-Friendly Explanation):**

- **AI Code Understanding:** Models (e.g., CodeBERT, StarCoder) parse syntax, extract functions/classes, infer relationships, and understand code semantics without executing it.
- **Repository Integration:** Uses Git protocols (HTTPS/SSH) to clone repos; agent handles credentials securely.
- **Embeddings:** Convert code chunks into numeric vectors for semantic search (models: OpenAI Ada, Sentence-BERT, Cohere).
- **Indexing:** Vector databases (Pinecone, Weaviate, FAISS) store embeddings for fast retrieval.
- **Diagram Generation:** Tools like Graphviz, Mermaid, or PlantUML auto-create architecture/flow diagrams from code structure.
- **Search & Q&A:** RAG (Retrieval-Augmented Generation) fetches relevant code snippets, feeds them to LLMs (GPT-4, Claude) for answers.
- **Background Sync:** Periodic polling (webhooks or cron jobs) detects repo changes, triggers re-analysis.
- **Local Storage:** Repos cloned locally; embeddings stored in vector DB; metadata in SQL/NoSQL DB.

---

## 3. Available Tools and Models

**Code Parsing:** tree-sitter, ctags, Language Server Protocol (LSP) clients  
**Summarization Models:** GPT-4, Claude Sonnet, Llama 3, Mistral  
**Embedding Models:** OpenAI text-embedding-3, Cohere embed-v3, all-MiniLM-L6-v2 (local)  
**Agent Frameworks (Repo Cloning Only):** LangChain agents, AutoGPT, custom Git automation scripts. *Agent role: authenticate + clone + sync repos; no analysis.*  
**Diagram Tools:** Graphviz, Mermaid CLI, PlantUML, D2  
**Search/RAG:** FAISS (local), Pinecone (cloud), Weaviate, Qdrant  
**UI Frameworks:** React, Next.js, Streamlit, Gradio  

*No code required for setup — tools have CLI/API interfaces.*

---

## 4. Hardware Requirements

| **Spec**          | **Minimum**                     | **Recommended**                  |
|-------------------|---------------------------------|----------------------------------|
| **CPU**           | 4 cores                         | 8+ cores                         |
| **RAM**           | 8 GB                            | 16–32 GB (for large repos)       |
| **GPU**           | Not required (API models)       | Optional: RTX 3060+ for local LLMs |
| **Disk**          | 100 GB SSD                      | 500 GB+ NVMe (repos + embeddings) |
| **Network**       | Stable broadband                | High-speed for large repo clones |

**When GPU Needed:** Local LLM inference (Llama, Mistral). API-based models (OpenAI, Anthropic) don't need GPU.  
**Disk Notes:** Large repos (e.g., Linux kernel: ~3 GB) + embeddings (can be GBs) require ample storage.

---

## 5. Model & Tool Comparison Matrix

| **Tool/Model**       | **Pros**                          | **Cons**                     | **Cost**       | **Use Case**                  |
|----------------------|-----------------------------------|------------------------------|----------------|-------------------------------|
| GPT-4                | Best reasoning, Q&A quality       | API costs add up             | $$$ (API)      | Production Q&A, summaries     |
| Claude Sonnet        | Long context, accurate            | API-only                     | $$ (API)       | Deep code analysis            |
| Llama 3 (local)      | Free, private                     | Needs GPU, slower            | Free           | Privacy-first deployments     |
| OpenAI Embeddings    | High quality, scalable            | API costs                    | $ (API)        | Semantic search               |
| all-MiniLM (local)   | Free, fast                        | Lower quality vs. OpenAI     | Free           | Budget/local deployments      |
| FAISS                | Fast, local, no API               | Manual scaling               | Free           | Small-medium repos            |
| Pinecone             | Managed, scalable                 | Subscription fees            | $$ (SaaS)      | Large-scale production        |
| tree-sitter          | Universal parser, fast            | Requires grammar setup       | Free           | Multi-language parsing        |

---

## 6. Analysis

**Feasibility:** Highly feasible. All components (Git automation, static analysis, LLMs, vector DBs) are mature and production-ready.

**Architectural Decisions:**
- **Separation of Concerns:** Agent handles repo access; Wiki system handles analysis. Keeps security boundaries clear.
- **Modular Pipeline:** Ingestion → Analysis → Embedding → Indexing → UI. Each stage can be optimized independently.

**Security Implications:**
- Agent credentials must be isolated (secrets management: Vault, AWS Secrets Manager).
- Use read-only tokens/collaborator roles where possible.
- Rotate credentials regularly.
- Never commit secrets to repos.

**Repo Access Tradeoffs:**
- Personal Access Tokens (PAT): Easy but tied to user account.
- Deploy Keys: Repo-specific, read-only — ideal for automation.
- GitHub App: Best for org-wide access, granular permissions.

**Sync Challenges:**
- Large repos: Incremental updates (fetch diffs) instead of full re-clones.
- Webhooks: Real-time but require exposed endpoints.
- Polling: Simpler but less efficient.

**Scaling:**
- Horizontal: Multiple agents for parallel repo processing.
- Vector DB sharding for >10M embeddings.
- Cache LLM responses for repeated queries.

**Handling Large Repos:**
- Chunk files (e.g., 500 lines/chunk) for embeddings.
- Prioritize high-value files (exclude binaries, vendor deps).

**Multi-Language Support:** Use tree-sitter (supports 40+ languages) or language-agnostic embeddings.

**Keeping Docs Updated:**
- Webhook triggers on `push` events.
- Scheduled polling (e.g., every hour).
- Diff-based re-indexing (only changed files).

---

## 7. Development Tools & Libraries

**Backend:** Python (FastAPI, Flask), Node.js (Express)  
**Frontend:** React, Next.js, Vue.js  
**Storage:** PostgreSQL (metadata), Redis (cache), S3 (repo backups)  
**Repo Integration:** GitPython, libgit2 (pygit2), simple-git (Node)  
**AI Pipelines:** LangChain, LlamaIndex, Haystack  
**Diagram Generation:** Graphviz Python bindings, mermaid-cli  
**Q&A System:** OpenAI/Anthropic API clients, Hugging Face Transformers  
**UI Frameworks:** Streamlit (rapid prototyping), Gradio  

*Keep conceptual — these are interface layers, not implementation details.*

---

## 8. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  USER INTERFACE (Web App)                                   │
│  - Browse Docs  - Search Code  - Ask Questions             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Q&A CHAT ENGINE (RAG)                                      │
│  - Retrieve context from Vector DB                          │
│  - Generate answers via LLM                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  SEARCH & INDEXING LAYER                                    │
│  - Vector DB (embeddings)  - Metadata DB (files, tags)     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  DOCUMENT & DIAGRAM GENERATOR                               │
│  - Auto-generate markdown docs  - Create architecture diagrams│
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  AI ANALYSIS MODULE                                         │
│  - Code understanding (LLM)  - Extract structure, functions │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  STATIC ANALYSIS INGESTION                                  │
│  - Parse code (tree-sitter)  - Extract AST, dependencies    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  SYNC ENGINE (Background Worker)                            │
│  - Detect repo changes (webhooks/polling)                   │
│  - Trigger re-analysis for updated files                    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  AGENT ACCESS LAYER (Repo Clone Only)                       │
│  - Clone repo (public/private)  - Keep local copy synced    │
│  - Uses: PAT, Deploy Key, SSH, or GitHub App                │
└─────────────────────────────────────────────────────────────┘
                     │
                  [GITHUB REPO]
```

**Data Flow:**
1. Agent clones repo locally.
2. Ingestion parses files → extracts structure.
3. AI analysis → understands architecture.
4. Doc/diagram generators → create artifacts.
5. Embeddings → stored in vector DB.
6. Sync engine → monitors changes → repeats steps 2–5 for diffs.
7. UI queries vector DB → RAG generates answers.

---

## 9. Implementation Guide (No Code — Only Plan & Design)

### 9.1 Setting Up the AI Agent GitHub Account

1. **Create Dedicated GitHub Account:**  
   - Sign up for a new GitHub account (e.g., `my-org-wiki-bot`).
   - Use organization email if available (e.g., `wiki-bot@company.com`).
   - Enable 2FA for security.

2. **Purpose:** This account represents the agent and isolates permissions from personal accounts.

---

### 9.2 Agent Access to Private GitHub Repos (Complete Guide)

**What is the Agent User?**  
A dedicated GitHub account or bot used solely for automated repo access. It separates automation credentials from personal accounts, enabling fine-grained permission control and auditability.

---

#### **8 Official Methods to Grant Repository Access**

| **Method**                     | **Steps**                                                                 | **Pros**                          | **Cons**                          | **Security Risk** | **Difficulty** | **When to Use**                     |
|--------------------------------|---------------------------------------------------------------------------|-----------------------------------|-----------------------------------|-------------------|----------------|-------------------------------------|
| **1. Repository Collaborator** | Settings → Collaborators → Add agent account with Read/Write             | Simple, direct                    | Tied to repo, manual per-repo     | Medium            | Easy           | Small teams, few repos              |
| **2. Personal Access Token (Classic)** | Agent account → Settings → Developer → PAT → Generate (repo scope) | Quick setup                       | Broad access, no expiration options (classic) | High if leaked    | Easy           | Quick prototyping                   |
| **3. Fine-Grained PAT**        | Agent account → PAT (beta) → Repo-specific, read-only, expiration        | Granular, expires automatically   | Newer feature, limited adoption   | Low (if read-only)| Medium         | Production, single-repo automation  |
| **4. Deploy Key (SSH)**        | Repo Settings → Deploy Keys → Add agent's public SSH key                 | Repo-specific, read-only default  | One key per repo                  | Low               | Medium         | **Recommended for automation**      |
| **5. GitHub App**              | Create GitHub App → Install on org/repos → Generate JWT + installation token | Best permissions, scalable       | Complex setup                     | Low               | Hard           | Enterprise, multi-repo, org-wide    |
| **6. OAuth App**               | Create OAuth App → User authorizes → Access token                        | User-controlled                   | Requires user interaction         | Medium            | Medium         | User-facing integrations            |
| **7. Organization Member**     | Invite agent account → Assign team with repo access                      | Centralized management            | Agent counts as user seat         | Medium            | Easy           | Orgs with seat capacity             |
| **8. SSH Key (Personal)**      | Agent account → Settings → SSH Keys → Add public key                     | Works across all accessible repos | Tied to agent account             | Medium            | Easy           | Multi-repo access for single agent  |

---

#### **Detailed Breakdown**

**1. Repository Collaborator**
- **How:** Add agent account as collaborator with Read or Write access.
- **Best For:** Small teams (1–5 repos).
- **Security:** Revoke access via repo settings. Use least privilege (Read if possible).

**2. Personal Access Token (Classic)**
- **How:** Agent account generates PAT with `repo` scope. Use in Git URLs: `https://<TOKEN>@github.com/owner/repo.git`.
- **Risks:** No expiration, broad access if scopes are too wide.
- **Mitigation:** Rotate regularly, store in secrets manager (Vault, AWS Secrets).

**3. Fine-Grained PAT (Recommended for Single Repos)**
- **How:** Generate PAT (beta) with specific repo, read-only, expiration (90 days).
- **Why Better:** Automatic expiration, minimal scope.
- **Example:** Read-only access to `my-org/private-repo` for 90 days.

**4. Deploy Key (SSH) — RECOMMENDED**
- **How:**  
  - Generate SSH key pair: `ssh-keygen -t ed25519 -C "wiki-agent"`
  - Add public key to repo: Settings → Deploy Keys → Paste → Check "Read-only" (default).
  - Agent uses private key to clone: `git clone git@github.com:owner/repo.git`
- **Why Best:** Repo-specific, read-only, no broad account permissions.
- **Drawback:** One key per repo (manageable with automation).

**5. GitHub App (Best for Orgs)**
- **How:** Create app, install on org, use JWT to request installation tokens.
- **Pros:** Granular permissions, works across repos, audit logs.
- **Complexity:** Requires server to generate JWTs, handle webhooks.
- **Use Case:** Enterprises, SaaS platforms.

**6. OAuth App**
- **How:** User authorizes app, agent uses access token.
- **Not Ideal:** Requires user interaction (not fully automated).

**7. Organization Member**
- **How:** Invite agent account, assign to team with repo access.
- **Cost:** Consumes a seat (paid orgs).
- **Use Case:** When seat cost is acceptable, centralized role management needed.

**8. SSH Key (Personal)**
- **How:** Add agent's SSH public key to its GitHub account (not deploy key).
- **Access:** All repos agent account can access.
- **Security:** Higher risk if key leaks (access to all repos).

---

#### **Recommended Method: Deploy Keys (SSH)**

**Why?**
- Read-only by default (can't push changes).
- Repo-specific (compromise doesn't affect other repos).
- No account-level permissions needed.
- Free, simple, secure.

**Setup Cheat Sheet:**
```bash
# 1. Generate key
ssh-keygen -t ed25519 -f ~/.ssh/wiki_agent_key -N ""

# 2. Add public key to GitHub
cat ~/.ssh/wiki_agent_key.pub
# Copy output → Repo Settings → Deploy Keys → Add

# 3. Clone repo
GIT_SSH_COMMAND="ssh -i ~/.ssh/wiki_agent_key" git clone git@github.com:owner/repo.git

# 4. Configure Git to use key
cd repo
git config core.sshCommand "ssh -i ~/.ssh/wiki_agent_key"
```

**For Multiple Repos:** Use SSH config file:
```
# ~/.ssh/config
Host github-wiki-agent
  HostName github.com
  User git
  IdentityFile ~/.ssh/wiki_agent_key
```
Then clone: `git clone git@github-wiki-agent:owner/repo.git`

---

#### **Security Best Practices**

- **Least Privilege:** Grant read-only access unless writes are required.
- **Rotate Credentials:** Refresh tokens/keys every 90 days.
- **Secrets Management:** Store keys/tokens in Vault, AWS Secrets Manager, or encrypted env vars.
- **Audit Logs:** Monitor agent activity (GitHub provides access logs).
- **Network Security:** Run agent in isolated environment (container, VM).
- **Backup Keys:** Store key backups securely (encrypted).

---

#### **Comparison: Collaborator vs. Tokens vs. Org Access**

| **Aspect**          | **Collaborator**       | **Fine-Grained PAT**   | **Deploy Key**         | **GitHub App**         |
|---------------------|------------------------|------------------------|------------------------|------------------------|
| **Scope**           | Single repo            | Single/multi repo      | Single repo            | Org-wide               |
| **Permissions**     | Read/Write/Admin       | Granular               | Read-only (default)    | Fully customizable     |
| **Revocation**      | Manual                 | Token expiration       | Remove key             | Uninstall app          |
| **Audit Trail**     | Limited                | Limited                | Limited                | Excellent              |
| **Cost**            | Free                   | Free                   | Free                   | Free (dev), paid (SaaS)|

---

#### **How Agent Maintains Local Repo Clone Safely**

1. **Clone:** Agent uses chosen method (Deploy Key, PAT) to clone repo to local disk.
2. **Isolation:** Store repos in dedicated directory (`/opt/wiki-agent/repos/`).
3. **Sync:** Periodic `git fetch` + `git pull` (or webhooks trigger pulls).
4. **Cleanup:** Old branches/tags pruned to save space.
5. **Security:** Private keys never committed; stored in secrets manager.
6. **Monitoring:** Log all Git operations for auditing.

**Example Workflow:**
```
Agent starts → Reads config (repo URL, credentials) →
Clones repo → Stores in /data/repos/owner_repo/ →
Background job (cron/webhook) → Checks for updates (git fetch) →
If changes detected → Pull → Trigger Wiki system re-analysis.
```

---

### 9.3 Repo Cloning Workflow

1. **Read Configuration:** Load repo URL, credentials (from secrets).
2. **Clone:** Execute `git clone` with appropriate auth (SSH key, HTTPS token).
3. **Verify:** Check clone success (repo exists locally, `.git` folder present).
4. **Store Metadata:** Record repo path, last commit hash in DB.

---

### 9.4 Code Ingestion and Analysis Pipeline

1. **Scan Repository:** Recursively list files, filter by extensions (`.py`, `.js`, `.java`, etc.).
2. **Parse Code:** Use tree-sitter to extract AST (functions, classes, imports).
3. **Chunk Files:** Split large files into ~500-line chunks for embedding.
4. **Generate Metadata:** Extract file paths, languages, dependencies.

---

### 9.5 Architecture Understanding

1. **Dependency Graph:** Parse imports/includes → build graph (networkx, Graphviz).
2. **LLM Analysis:** Send code snippets to LLM with prompts:
   - "Summarize this module's purpose."
   - "Identify design patterns used."
3. **Store Insights:** Save summaries, relationships in metadata DB.

---

### 9.6 Documentation Generation Workflow

1. **Template Selection:** Choose format (Markdown, HTML).
2. **Auto-Generate Docs:**
   - Per-file: Function signatures, docstrings, usage examples.
   - Per-module: High-level summaries, architecture notes.
   - Global: README-style overview, getting-started guide.
3. **Markdown Rendering:** Convert to HTML for UI display.

---

### 9.7 Diagram Generation

1. **Extract Structure:** Use AST to get class hierarchies, call graphs.
2. **Generate Diagram Code:** Create Graphviz DOT or Mermaid syntax.
3. **Render:** Convert to SVG/PNG via CLI (`dot -Tsvg`, `mmdc`).
4. **Embed in Docs:** Link diagrams to relevant doc sections.

---

### 9.8 Indexing + Embeddings

1. **Generate Embeddings:** Send code chunks to embedding model (OpenAI, Cohere).
2. **Store in Vector DB:** Insert embeddings with metadata (file path, line numbers).
3. **Index Metadata:** Store file names, tags in relational DB for fast filtering.

---

### 9.9 Q&A Chat Engine

1. **User Query:** "How does authentication work?"
2. **Retrieve Context:** Query vector DB for top-k similar code chunks.
3. **Augment Prompt:** Combine retrieved code + user query.
4. **Generate Answer:** Send to LLM (GPT-4, Claude) → return response.
5. **Cite Sources:** Include file paths, line numbers in answer.

---

### 9.10 Sync Engine for Automatic Updates

**Webhook Approach (Real-Time):**
1. Configure GitHub webhook (Settings → Webhooks → `push` event).
2. Expose endpoint (e.g., `/webhook/github`).
3. On push → Agent pulls latest changes → Trigger re-analysis (only changed files).

**Polling Approach (Simpler):**
1. Cron job every hour: `git fetch` → compare commit hashes.
2. If new commits → pull → re-analyze diffs.

**Optimization:** Use `git diff` to identify changed files, only re-embed those.

---

### 9.11 Deployment Considerations

- **Containerization:** Docker for agent, Wiki app, vector DB.
- **Orchestration:** Kubernetes for scaling, self-healing.
- **Secrets:** Use Docker secrets, Kubernetes secrets, or cloud services.
- **Monitoring:** Log agent activity, API usage, embedding generation times.
- **Backup:** Regularly backup vector DB, metadata DB, local repos.

---

## 10. Recommendations

**Best Agent Access Method:**  
**Deploy Keys (SSH)** for production. Read-only, repo-specific, secure. For org-wide needs, use GitHub App.

**Best Model Choices:**
- **Q&A:** GPT-4 or Claude Sonnet (accuracy over cost).
- **Embeddings:** OpenAI text-embedding-3 (quality) or all-MiniLM-L6-v2 (cost).
- **Parsing:** tree-sitter (universal, fast).

**Scaling Tips:**
- Horizontal scaling: Multiple agents for parallel repo processing.
- Cache embeddings: Store precomputed vectors, invalidate on file changes.
- Incremental updates: Only re-process changed files.

**Security Practices:**
- Rotate credentials every 90 days.
- Use secrets managers (Vault, AWS).
- Never log tokens/keys.
- Enable GitHub audit logs.
- Run agent in isolated environment (container, VM).

**Maintaining Accuracy:**
- Webhooks for real-time updates (preferred).
- Scheduled polling as fallback.
- Diff-based re-indexing (avoid full re-clones).
- Version control docs (Git repo for generated docs).

**Performance Optimizations:**
- Filter files: Exclude binaries, vendor dependencies.
- Batch embeddings: Send multiple chunks per API call.
- Use local models for embeddings if API costs are high.
- Cache LLM responses for repeated queries.

---

## 11. Resources

**Official Documentation:**
- [GitHub Deploy Keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub Apps](https://docs.github.com/en/apps)
- [tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [LangChain](https://python.langchain.com/docs/get_started/introduction)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Pinecone](https://docs.pinecone.io/)

**AI Models:**
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [Anthropic Claude](https://docs.anthropic.com/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)

**Diagram Tools:**
- [Graphviz](https://graphviz.org/)
- [Mermaid](https://mermaid.js.org/)
- [PlantUML](https://plantuml.com/)

**Articles & Tutorials:**
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [Code Embeddings Guide](https://huggingface.co/blog/code-embeddings)
- [Automating GitHub with SSH](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2)

**Security:**
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

---

**End of Documentation**  
For deeper detail on any topic, refer to the linked resources above.