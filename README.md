# Mifos Community AI

A comprehensive AI-powered toolkit for the Mifos community, featuring intelligent chatbots, automation tools, translation utilities, and voice-driven banking interfaces. This project aims to provide AI-powered self-service support, enhance developer productivity, and simplify access to Mifos ecosystem resources through advanced Generative AI technologies.

## Table of Contents

- [Overview](#overview)
- [Key Components](#key-components)
  - [1. RAG-Based Chatbots](#1-rag-based-chatbots)
  - [2. Community Chatbot Platform](#2-community-chatbot-platform)
  - [3. Translation Tools](#3-translation-tools)
  - [4. Voice-Driven Banking](#4-voice-driven-banking)
  - [5. Data Extraction & Automation](#5-data-extraction--automation)
  - [6. Slack Bot & Pipeline](#6-slack-bot--pipeline)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [Links and Resources](#links-and-resources)

---

## Overview

As the Mifos community and its core products (Mifos X, Payment Hub EE, Mobile Applications, and Mifos Gazelle) continue to grow rapidly, this repository provides a suite of AI-powered tools to support implementors, developers, and new users. The tools simplify finding relevant content across multiple sources, automate repetitive tasks, and enable innovative interfaces for banking applications.

---
## Badges Section
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MPL--2.0-green)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-orange)

## Key Components

### 1. RAG-Based Chatbots

**Retrieval-Augmented Generation (RAG) chatbots** for querying Mifos codebases using natural language.

#### Available Bots

| Bot | Notebook | Vector Storage | Description |
|-----|----------|----------------|-------------|
| **Web App Bot** | `Web-App/web-app_bot.ipynb` | `web_app_vector_storage_metadata/` | Query the Mifos Web Application codebase |
| **Mifos Mobile Bot** | `Mifos-Mobile/mifos-mobile_bot.ipynb` | `mifos-mobile_vector_storage/` | Explore Mifos Mobile app code and features |
| **Android Client Bot** | `Android-Client/android-client_bot.ipynb` | `android-client_vector_storage/` | Navigate the Android Client codebase |
| **Mobile Wallet Bot** | `Mobile-Wallet/mobile-wallet_bot.ipynb` | `mobile_wallet_vector_storage/` | Query Mobile Wallet implementation |

> **Note**: Mifos Mobile also includes an alternative implementation (`mifos-mobile_bot_hf_groq.ipynb`) using Groq LLM and Hugging Face embeddings instead of OpenAI.

#### Deployed Chatbots (No Setup Required!)

Access hosted versions on Hugging Face Spaces:
- [Web App Bot](https://huggingface.co/spaces/MifosBot/Web-App)
- [Mifos Mobile Bot](https://huggingface.co/spaces/MifosBot/Mifos-Mobile)
- [Mobile Wallet Bot](https://huggingface.co/spaces/MifosBot/Mobile-Wallet)
- [Android Client Bot](https://huggingface.co/spaces/MifosBot/Android-Client)

#### How It Works
- Processes and indexes Mifos codebases, creating **vector embeddings** using ChromaDB
- Uses **OpenAI embeddings** (text-embedding-3-large) for semantic search
- Leverages **GPT models** to generate human-like responses based on retrieved code snippets
- Provides insights on file organization, key components, and project architecture

#### Local Setup

```bash
# Clone the repository
git clone https://github.com/openMF/community-ai.git
cd community-ai

# Install dependencies
pip install -r requirements.txt

# Set up API keys in .env file
echo "OPENAI_API_KEY=your_openai_api_key" > .env
# OR
echo "GEMINI_API_KEY=your_gemini_api_key" >> .env

# Launch Jupyter Notebook
jupyter notebook

# Open any bot notebook (e.g., Web-App/web-app_bot.ipynb)
# Run cells and interact via Gradio interface
```

---

### 2. Community Chatbot Platform

**Full-stack chatbot platform** with FastAPI backend and Next.js frontend for integrating with Jira, Slack, and GitHub.

📂 **Location**: `community-chatbot/`

#### Features
- **Jira Agent**: Query Jira issues using natural language, generate JQL, and summarize results
- **Slack Agent**: Manage conversations and summarize Slack channel discussions
- **GitHub Agent**: Interact with repositories and ask questions about project code
- **Modern UI**: React-based chat interface with authentication (Firebase)
- **Agent-Based Workflows**: LangChain-powered intelligent automation

#### Tech Stack
- **Backend**: FastAPI (Python), LangChain, OpenAI
- **Frontend**: Next.js 14, React, Tailwind CSS, shadcn/ui
- **Authentication**: Firebase Auth
- **Database**: Firestore

#### Quick Start

```bash
cd community-chatbot

# Backend setup
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
# Create a .env file with your API keys
# See how_to_get_keys.md for detailed setup instructions
# Add your API keys for OpenAI, Slack, Jira, GitHub, Firebase

# Start backend (from community-chatbot root)
bash scripts/run_backend.sh
# Or run individual agents:
# python scripts/jira.py
# python scripts/slack.py
# python scripts/github_agent.py

# Frontend setup (new terminal, from community-chatbot root)
pnpm install
pnpm dev

# Access at http://localhost:3000
```

---

### 3. Translation Tools

#### A. Multilingual Translation Helper
📂 **Location**: `tools/translation-helper/`

**Gradio-based translation tool** powered by Gemini 2.0 Flash.

**Features**:
- Supports 35+ languages (Arabic, Bengali, Chinese, French, German, Hindi, Japanese, Spanish, etc.)
- Formal/informal tone switching
- Real-time translation with Enter key or button trigger

```bash
cd tools/translation-helper
pip install -r requirements.txt
python app.py
```

#### B. Android XML Localization Translator
📂 **Location**: `Mifos-Mobile Language Translation/`

Translates Android `strings.xml` files using Groq LLM API.

**Features**:
- Parses `values/strings.xml` and generates localized versions
- Handles `<string>` and `<string-array>` elements
- Translation caching to avoid redundant API calls
- Safe XML parsing with pretty-printing

```bash
cd "Mifos-Mobile Language Translation"
python script.py
```

#### C. JSON Translation Utility
📂 **Location**: `WebApp Language Translations/`

CLI utility to translate JSON string values using Groq LLM.

**Features**:
- Walks JSON structure and extracts string leaves
- Persistent caching per target language
- Exponential backoff for API reliability

```bash
cd "WebApp Language Translations"
python Script.py
```

---

### 4. Voice-Driven Banking

📂 **Location**: `Voice-Driven_banking-Lam/`, `voice_driven_banking/`

**End-to-end voice banking assistant** with React frontend and FastAPI backend.

#### Features
- **Multilingual Support**: English, Hindi, Spanish, French, German, and more
- **Core Banking Intents**:
  - Check account balance
  - List recent transactions
  - Transfer money with OTP verification
- **Stateful Conversations**: Context-aware multi-turn dialogues
- **Animated UI**: Real-time feedback for recording, processing, and speaking states
- **AI Pipeline**:
  - **STT**: Whisper (Hugging Face Transformers)
  - **NLU/NLG**: Google Gemini API (Vertex AI)
  - **TTS**: MMS (Hugging Face Transformers)

#### Tech Stack
- **Backend**: FastAPI, Google Gemini, Firestore
- **Frontend**: React, Tailwind CSS
- **Audio Processing**: FFmpeg, Whisper, MMS

```bash
# Backend setup
cd Voice-Driven_banking-Lam/Backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Configure .env file (see Backend README for details)
uvicorn main:app --reload

# Frontend setup (new terminal)
cd Voice-Driven_banking-Lam/Frontend/voicedriven
npm install
npm start
```

#### Testing Framework
📂 **Location**: `voice_driven_banking/`

Automated testing framework for voice banking interfaces.

```bash
cd voice_driven_banking
pip install -r requirements.txt
python voice_banking_test_suite.py
```

---

### 5. Data Extraction & Automation

#### A. Jira/Confluence Data Scraper
📂 **Location**: `Data Scraping/`

Scrapes and extracts data from Mifos Jira/Confluence pages.

```bash
cd "Data Scraping"
jupyter notebook DataExtraction.ipynb
```

#### B. GitHub Repo Automation
📂 **Location**: `Repo Clone Automation/`

Automates cloning and processing of GitHub repositories for RAG applications.

**Features**:
- Selenium-based automated repo download
- Converts repository content to text for vector database ingestion

```bash
cd "Repo Clone Automation"
python repo_cloner.py
jupyter notebook github_repo_rag.ipynb
```

---

### 6. Slack Bot & Pipeline

📂 **Location**: `Slack_scraper_bot/`, `slack_pipeline/`

Tools for extracting, processing, and querying Slack messages.

#### Features
- **Message Extraction**: Convert Slack JSON exports to clean text
- **PII Removal**: Automatically redact personally identifiable information
- **RAG Integration**: Query Slack conversations using vector databases
- **Trustworthy LLM**: Confidence scoring for generated responses

#### Pipeline Components

```bash
# Extract messages from Slack JSON
cd Slack_scraper_bot/scripts
python extract.py

# Remove PII
python pii_removal.py

# Create vector database
cd ../../slack_pipeline
python main.py
```

#### Demo Bot
```bash
cd Slack_scraper_bot/scripts
jupyter notebook demo_bot.ipynb
```

---

## Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 18+** (for Next.js projects)
- **Jupyter Notebook**
- **API Keys**: OpenAI, Gemini, Groq (depending on components used)

### Basic Installation

```bash
# Clone repository
git clone https://github.com/openMF/community-ai.git
cd community-ai

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file and add your API keys
# OPENAI_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here
# GROQ_API_KEY=your_key_here

# Launch Jupyter for chatbots
jupyter notebook

# Or run specific tools (see component sections above)
```

---

## Project Structure

```
community-ai/
├── Android-Client/              # Android Client RAG chatbot
│   ├── android-client_bot.ipynb
│   └── android-client_vector_storage/
|
├── community-chatbot/           # Full-stack chatbot platform
│   ├── app/ 
|   ├── agent/                    # Next.js frontend pages
│   ├── components/             # React UI components
│   ├── scripts/                # FastAPI backend agents
│   └── package.json
├── Data Scraping/              # Jira/Confluence data extraction
│   └── DataExtraction.ipynb
├── Mifos-Mobile/               # Mifos Mobile app chatbot
│   ├── mifos-mobile_bot.ipynb
│   ├── mifos-mobile_bot_hf_groq.ipynb  # Alternative using Groq/HF
│   └── mifos-mobile_vector_storage/
├── Mifos-Mobile Language Translation/  # Android XML translator
│   ├── script.py
│   └── Readme.md
├── Mobile-Wallet/              # Mobile Wallet chatbot
│   ├── mobile-wallet_bot.ipynb
│   └── mobile_wallet_vector_storage/
├── Repo Clone Automation/      # GitHub repo automation
│   ├── repo_cloner.py
│   └── github_repo_rag.ipynb
├── Slack_scraper_bot/          # Slack message extraction & bot
│   ├── scripts/
│   └── data/
├── slack_pipeline/             # Slack vector database pipeline
│   ├── main.py
│   └── vectordb.py
├── tools/
│   └── translation-helper/     # Multilingual translation tool
│       └── app.py
├── Voice-Driven_banking-Lam/   # Voice banking assistant
│   ├── Backend/
│   └── Frontend/
├── voice_driven_banking/       # Voice banking test suite
│   └── voice_banking_test_suite.py
├── Web-App/                    # Web App chatbot
│   ├── web-app_bot.ipynb
│   └── web_app_vector_storage_metadata/
├── WebApp Language Translations/  # JSON translation utility
│   └── Script.py
├── CodeCommentingScript.ipynb  # Code preprocessing utility
├── requirements.txt            # Python dependencies
└── README.md
```

---

## Technologies Used

### AI & Machine Learning
- **LLMs**: OpenAI GPT-4, Google Gemini 2.0 Flash, Groq
- **Embeddings**: OpenAI text-embedding-3-large
- **Frameworks**: LangChain, Hugging Face Transformers
- **Vector Databases**: ChromaDB, Pinecone

### Backend
- **Python**: FastAPI, Flask
- **Data Processing**: BeautifulSoup, Selenium, pandas

### Frontend
- **React/Next.js 14**: Server-side rendering, App Router
- **UI Libraries**: Tailwind CSS, shadcn/ui, Radix UI
- **State Management**: Zustand
- **Forms**: React Hook Form, Zod validation

### Database & Storage
- **Firebase**: Firestore, Firebase Auth
- **Vector Stores**: ChromaDB (persistent), Pinecone

### Voice & Audio
- **STT**: Whisper (Hugging Face)
- **TTS**: MMS (Hugging Face)
- **Processing**: FFmpeg

### Development Tools
- **Notebooks**: Jupyter
- **UI Prototyping**: Gradio
- **Testing**: Jest, Selenium
- **Package Management**: pip, pnpm

---

## Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute
- 🐛 **Report bugs** by opening issues
- 💡 **Suggest new features** or improvements
- 📝 **Improve documentation**
- 🔧 **Submit pull requests** with bug fixes or new features
- 🧪 **Test and provide feedback** on existing tools

### Contribution Workflow

1. **Fork the repository on github** 
    **clone your fork locally** 
   ```bash
   git clone https://github.com/YOUR_USERNAME/community-ai.git
   cd community-ai
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style and conventions
   - Add tests if applicable
   - Update documentation

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a PR on GitHub with a clear description of your changes.

### Development Guidelines
- Use meaningful commit messages (follow [Conventional Commits](https://www.conventionalcommits.org/))
- Ensure code is well-documented with comments
- Test your changes before submitting
- Keep PRs focused on a single feature/fix

---

## Links and Resources

### Mifos Community
- **Website**: [mifos.org](https://mifos.org/)
- **Documentation**: [docs.mifos.org](https://docs.mifos.org/)
- **Jira**: [mifosforge.jira.com](https://mifosforge.jira.com/)
- **Slack**: Join our [AI Working Group](https://join.slack.com/share/enQtOTY2NTIzNDI0MjI5MC02YzhjMzc1NzhhMjM2OTZhNWQ4YWZkYWY0MWFmNTQxNmE4Yjg2ZDM4YWI4YzJmYzczYTQwNzk2NjAzNDgxMTc5)

### Related Projects
- [Mifos X Web App](https://github.com/openMF/web-app)
- [Mifos Mobile](https://github.com/openMF/mifos-mobile)
- [Android Client](https://github.com/openMF/android-client)
- [Mobile Wallet](https://github.com/openMF/mobile-wallet)

### Deployed Chatbots
- [Web App Bot](https://huggingface.co/spaces/MifosBot/Web-App)
- [Mifos Mobile Bot](https://huggingface.co/spaces/MifosBot/Mifos-Mobile)
- [Mobile Wallet Bot](https://huggingface.co/spaces/MifosBot/Mobile-Wallet)
- [Android Client Bot](https://huggingface.co/spaces/MifosBot/Android-Client)

---

## License

This project is licensed under the **MPL-2.0 License** - see the [LICENSE](LICENSE) file for details.

---

## Support

For questions, issues, or feature requests:
- 📧 Open an [issue on GitHub](https://github.com/openMF/community-ai/issues)
- 💬 Join our [Mifos Slack community](https://mifos.slack.com/)
- 📖 Check the [documentation](https://docs.mifos.org/)

---

**Built with ❤️ by the Mifos Community**
