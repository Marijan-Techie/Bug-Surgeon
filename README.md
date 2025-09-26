# Claude Code Bug Surgeon 🤖🔧

An AI-powered debugging agent that performs systematic root cause analysis using Claude's reasoning capabilities, integrated with GitHub Actions for automated bug triage and analysis.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or create the project
cd claude-bug-surgeon

# Create virtual environment (MacOS/Linux)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the template and add your keys:
```bash
cp .env.template .env
```

Edit `.env` and add:
- `ANTHROPIC_API_KEY`: Get from [Anthropic Console](https://console.anthropic.com/)
- `GITHUB_TOKEN`: Personal access token from GitHub
- `GITHUB_REPOSITORY`: Format `username/repo-name`

### 3. Test Locally

```bash
# Basic functionality test
python test_local.py

# GitHub integration test  
python test_github.py
```

## 🏗️ Architecture

The Bug Surgeon uses a **ReAct (Reason + Act) framework** with these components:

- **System Prompt**: Defines the AI's role as a Senior Debugging Specialist
- **Reasoning Engine**: Uses `<thinking>` tags for transparent analysis
- **Tool Integration**: Reads files from local filesystem or GitHub repos
- **GitHub Actions**: Automated workflow triggered by issue labels

## 🔍 How It Works

1. **Issue Analysis**: ReAct cycle analyzes bug reports systematically
2. **Context Gathering**: Reads relevant code files based on error traces
3. **Root Cause Identification**: Forms hypotheses and validates with evidence  
4. **Solution Generation**: Provides fixes addressing underlying causes
5. **PR Creation**: Automated pull requests with detailed analysis

## 📁 Project Structure

```
claude-bug-surgeon/
├── debug_orchestrator.py      # Main Bug Surgeon implementation
├── requirements.txt           # Python dependencies
├── .env.template             # Environment variables template
├── test_local.py             # Local functionality test
├── test_github.py            # GitHub integration test
├── examples/
│   └── auth.py              # Example buggy file for testing
└── .github/
    └── workflows/
        └── bug-surgeon.yml   # GitHub Actions workflow
```

## 🤖 GitHub Actions Integration

### Setup:

1. **Add to your repository:**
   - Copy `bug-surgeon.yml` to `.github/workflows/`
   - Copy `debug_orchestrator.py` and `requirements.txt` to repo root

2. **Configure Secrets:**
   - Go to Repository Settings → Secrets and Variables → Actions
   - Add `ANTHROPIC_API_KEY` with your Claude API key

3. **Usage:**
   - **Automatic**: Label any issue with `bug-surgeon` 
   - **Manual**: Go to Actions → Claude Bug Surgeon → Run workflow

### What Happens:
- ✅ Analyzes the issue description
- ✅ Reads relevant code files from your repository  
- ✅ Creates pull request with detailed bug analysis
- ✅ Comments on the original issue with results

## 🧪 Testing Examples

### Local Test with Built-in Example:

```python
from debug_orchestrator import BugSurgeon

surgeon = BugSurgeon()
bug_report = """
Getting AttributeError: 'NoneType' object has no attribute 'id'
in auth.py line 42 when users try to log in.
"""

analysis = surgeon.analyze_bug(bug_report)
print(f"Root Cause: {analysis.root_cause}")
```

### Test with GitHub Repository:

```python
# Set environment variables first
import os
os.environ['GITHUB_REPOSITORY'] = 'your-username/your-repo'
os.environ['GITHUB_TOKEN'] = 'your-token'

# Now test with real repo files
surgeon = BugSurgeon()  # Will connect to GitHub
analysis = surgeon.analyze_bug(bug_report)
```

## 🎯 Key Features

- **Systematic Analysis**: Uses ReAct framework for methodical debugging
- **Transparent Reasoning**: `<thinking>` tags show the AI's thought process
- **Context-Aware**: Reads actual code files to understand issues
- **Production Ready**: Full error handling, logging, and GitHub integration
- **Adaptable**: Works locally for development and in CI/CD for automation

## 🔧 Development Workflow

1. **Local Development**: Test changes with `test_local.py`
2. **GitHub Integration**: Validate with `test_github.py`  
3. **Repository Testing**: Create test issues and apply `bug-surgeon` label
4. **Production Deployment**: Enable workflow in your production repositories

## 📋 Requirements

- Python 3.8+
- Anthropic API key
- GitHub Personal Access Token (for repository integration)

## 🤝 Contributing

This implementation provides a complete foundation for AI-powered debugging. Key areas for extension:

- **Multi-language Support**: Extend beyond Python
- **Integration Hooks**: Slack notifications, Jira tickets
- **Learning Loops**: Collect feedback to improve prompts
- **Advanced Analysis**: Static analysis tool integration

## 📖 Learn More

This Bug Surgeon demonstrates advanced prompt engineering techniques for building production AI agents:

- **Structured Reasoning**: How to design prompts for systematic analysis
- **ReAct Framework**: Implementing reason-act cycles in practice  
- **GitHub Integration**: Real-world CI/CD deployment patterns
- **Error Handling**: Production-ready robustness techniques

Perfect for teams wanting to understand both the theory and practice of building intelligent debugging agents.

---

*Built with Claude 3.5 Sonnet - Demonstrating the power of systematic prompt engineering for AI agents*
