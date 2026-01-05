# Community Chatbot for Mifos Projects

An advanced, extensible chatbot platform designed for seamless integration with Jira, Slack, and GitHub. Built with a FastAPI (Python) backend and a Next.js (React) frontend, it leverages LangChain and OpenAI to provide intelligent, conversational automation and agent-based workflows. The platform features a modern UI, robust authentication, and is easily customizable for a variety of community and project management

This project was completed during Google Summer of Code (GSOC) 

---

## Features

- **Jira Agent**: Query Jira using natural language, generate JQL, and summarize results with LLM fallback.
- **Slack Agent**: Manage conversations and interact with Slack using agent tools to summarize the conversations inside our channel.
- **Github Agent**: Interact with your repo to ask questions related to the project in natural language.
- **Frontend Chatbot UI**: Modern, responsive chat interface built with Next.js and Tailwind CSS.
- **Authentication**: User sign-in and sign-up flows.
- **Extensible UI Components**: Reusable UI library for rapid development.

---

## Directory Structure

```
community-chatbot/
│
├── app/                # Next.js frontend (pages, components, styles)
├── components/         # React UI components (chatbot, UI library)
├── hooks/              # React hooks
├── lib/                # Frontend utility libraries
├── public/             # Static assets
├── scripts/            # FastAPI backend (Jira, Slack, GitHub agents)
├── styles/             # Global styles
└── ...
```

---

## Getting Started

### Prerequisites
- **Python** 3.8+
- **Node.js** 18+

### Backend Setup (FastAPI)

1. **Create and activate a virtual environment**  

   On Unix/macOS:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install Python dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**  
   Create a `.env` file in the project root:

   ```ini
   # Backend
   NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000

   # OpenAI
   OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>

   # Slack
   SLACK_BOT_TOKEN=<YOUR_SLACK_BOT_TOKEN>

   # Jira
   JIRA_API_TOKEN=<YOUR_JIRA_API_TOKEN>
   JIRA_USERNAME=<YOUR_JIRA_USERNAME>
   JIRA_INSTANCE_URL=https://mifosforge.jira.com
   JIRA_CLOUD=True

   # GitHub
   GITHUB_APP_ID=<YOUR_GITHUB_APP_ID>
   GITHUB_REPOSITORY=staru09/Github_analyser
   GITHUB_BRANCH=main
   GITHUB_BASE_BRANCH=main
   GITHUB_APP_PRIVATE_KEY=<YOUR_GITHUB_APP_PRIVATE_KEY>

   # Firebase
   NEXT_PUBLIC_FIREBASE_API_KEY=<YOUR_FIREBASE_API_KEY>
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<YOUR_FIREBASE_AUTH_DOMAIN>
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=<YOUR_FIREBASE_PROJECT_ID>
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=<YOUR_FIREBASE_STORAGE_BUCKET>
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=<YOUR_FIREBASE_MESSAGING_SENDER_ID>
   NEXT_PUBLIC_FIREBASE_APP_ID=<YOUR_FIREBASE_APP_ID>
   NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=<YOUR_FIREBASE_MEASUREMENT_ID>
   ```

   ⚠️ **Note:** In `github_agent.py`, uncomment this line:
   ```python
   os.environ['GITHUB_APP_PRIVATE_KEY']
   ```
   as there is some issue loading it from the `.env` file.

4. **Run FastAPI server**  
   Run this bash command to start the backend server.
   ```bash
   ./scripts/run_backend.sh
   ```

---

### Frontend Setup

**Install Node dependencies**  
1. Installs pnpm globally so you can use pnpm commands for projects that don’t support npm.
   ```bash
   npm install -g pnpm 
   ```

2. Run this bash command in the root directory of the project. 

   ```bash
   pnpm install
   ```

3. **Run Next.js development server**  
   ```bash
   pnpm dev
   ```

---

## To Do

- **Add new agent tools**: Extend `scripts/`
- **UI customization**: Modify components in `components/` and styles in `styles/`.
- **Database Integration**: Add support for a database to store user history.
- **And a lot of code cleanup** 😊
