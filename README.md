# Mifos Community AI Chatbot

A lightweight developer-focused chatbot that helps Mifos / Fineract implementors and contributors find relevant code and docs quickly using vector search + generative models. This repository contains prototype tooling to index selected code & docs into vector embeddings and a small Gradio notebook for interactive exploration.

---

## Table of Contents

- [Project purpose & scope](#project-purpose--scope)
- [Quick start (run locally)](#quick-start-run-locally)
- [Usage](#usage)
  - [Run locally (Jupyter Notebook)](#run-locally-jupyter-notebook)
  - [Use deployed chatbots (no setup)](#use-deployed-chatbots-no-setup)
- [Project structure](#project-structure)
- [How it works (short)](#how-it-works-short)
- [Features](#features)
- [Tests & CI (notes)](#tests--ci-notes)
- [Known limitations](#known-limitations)
- [Contributing](#contributing)
- [Contact & resources](#contact--resources)

---

## Project purpose & scope

**Purpose:** Provide concise, contextual answers about Mifos/Fineract source code and documentation by combining retrieval (vector embeddings) with an LLM (OpenAI / Gemini). Use cases: onboarding, quick code lookup, documentation discovery and small translation helper tasks.

**In scope**
- Tools to extract text from code and docs and build embeddings.
- A local Gradio notebook (`web-app_bot.ipynb`) for experimentation.
- Lightweight utilities (translation helper, preprocessing scripts).

**Out of scope**
- Production-scale serving or managed vector DB hosting (this repo is a prototype/experiment).
- Authoritative replacement for official docs — the assistant aids discovery, not canonical documentation.

---

## Quick start (run locally)

> Requires **Python 3.8+**. Work in a virtual environment.

1. Clone the Repository:
```bash
git clone https://github.com/<your-username>/community-ai.git
cd community-ai
````

2. Create & activate a virtual environment:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

3. Install Dependencies:

```bash
pip install -r requirements.txt        # optional if heavy; see CI notes
pip install pytest
```

4. Add API keys in `.env` (create file in repo root):

```
OPENAI_API_KEY=sk-...
# or for Gemini:
GEMINI_API_KEY=your-gemini-key
```

5. Run the notebook:

```bash
jupyter notebook
# open web-app_bot.ipynb and run the cells (follow the cell instructions)
```

**Note about pre-processing / embeddings:**
`CodeCommentingScript.py` is the script used to extract and prepare text for embeddings. If it exposes a CLI in this repo, the typical invocation we recommend is:

```bash
python CodeCommentingScript.py --source web-app --out web_app_vector_storage_metadata --batch 64 --model <EMBEDDING_MODEL>
```

If the script does not have CLI flags, open the file and follow the top comments / main function. If you need help adding a small CLI wrapper, open an issue or I can draft a follow-up PR.

---

## Usage

### Run locally (Jupyter Notebook)

* Launch `web-app_bot.ipynb`.
* Run cells to load embeddings (or generate them first with the preprocessor).
* Use the Gradio interface to ask questions and inspect the retrieved snippets.

### Use deployed chatbots (no setup)

* Web App Bot: [https://huggingface.co/spaces/MifosBot/Web-App](https://huggingface.co/spaces/MifosBot/Web-App)
* Mifos Mobile Bot: [https://huggingface.co/spaces/MifosBot/Mifos-Mobile](https://huggingface.co/spaces/MifosBot/Mifos-Mobile)
* Mobile Wallet Bot: [https://huggingface.co/spaces/MifosBot/Mobile-Wallet](https://huggingface.co/spaces/MifosBot/Mobile-Wallet)
* Android Client Bot: [https://huggingface.co/spaces/MifosBot/Android-Client](https://huggingface.co/spaces/MifosBot/Android-Client)

---

## Project structure (top-level)

```
├── web-app/                          # source files analyzed by the Web App bot
├── web-app_bot.ipynb                 # notebook to run the demo locally
├── web_app_vector_storage_metadata/  # generated embeddings & metadata (gitignored)
├── tools/
│   └── translation-helper/           # Gemini-powered translation helper tool
├── requirements.txt                  # Python dependencies (optional heavy)
├── CodeCommentingScript.py           # preprocessing script for creating embeddings
├── tests/                            # pytest tests (added by contributors)
└── .github/workflows/                # CI workflows (lint/test)
```

---

## How it works (short)

1. **Preprocess**: extract text from source files (script: `CodeCommentingScript.py`).
2. **Embed**: convert text chunks to vector embeddings (local or managed vector store).
3. **Retrieve**: on query, perform nearest-neighbour retrieval to get relevant chunks.
4. **Answer**: feed retrieved chunks plus the query to an LLM (OpenAI/Gemini) to generate a concise answer.

---

## Features

* Vector retrieval over code & docs.
* Notebook + Gradio demo for interactive testing.
* Optional translation helper tool.
* Extensible to different vector stores (FAISS/Chroma/Pinecone/Weaviate).

---

## Tests & CI (notes / recommended)

**Current status:** limited automated tests. We recommend a small starter test-suite that validates the repo layout and core scripts.

**What to add now (safe, low friction):**

* `tests/test_files_exist.py` — checks essential files/folders exist.
* `tests/test_readme_headers.py` — smoke check for README content.

**CI workflow (minimal):** Add `.github/workflows/python-tests.yml` that:

* checks out code,
* sets up Python 3.8+,
* installs `pytest`,
* runs `pytest`.

This avoids installing heavy runtime dependencies in CI while ensuring PRs include the basic checks.

---

## Known limitations

* Prototype/demo code with limited formal testing.
* Local embeddings stored in repo folder — not suitable for production (move to managed vector DB).
* Notebook-driven UX is for experimentation, not production serving.

---

## Contributing

We welcome all contributions. Best first steps:

1. Fork the repo and create a focused branch:

```bash
git checkout -b docs/readme-overhaul
```

2. Make one small change per PR (docs, then tests, then CI).
3. Run the small test-suite locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest
pytest -q
```

4. Push and open a PR:

* Title example: `docs: clarify README scope & file structure`
* PR body: link `#34` and paste a short note about local testing.

**PR checklist**

* [ ] I ran the basic tests locally.
* [ ] This PR is small & focused.
* [ ] Linked to issue: `#34`

---

## Link & Resources

* Repo: [https://github.com/openMF/community-ai](https://github.com/openMF/community-ai)
* Mifos: [https://mifos.org/](https://mifos.org/)

---


