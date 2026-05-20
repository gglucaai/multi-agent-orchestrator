# AI Startup Studio

A multi-agent orchestration demo that turns a one-line problem statement into a full startup concept report. A central **orchestrator** coordinates six specialized AI agents, and the whole process is streamed live to a React interface where you can watch the agents work, talk to the orchestrator, and revise their output in real time.

The project implements the **orchestrator–workers pattern**: rather than a fixed chain of prompts, a coordinating agent dispatches work to specialists, evaluates what comes back, and (in the Hugging Face version) sends it back for revision if it isn't good enough.

## What it does

Given an input like *"Sustainable agriculture in East Africa"*, the system runs six agents in sequence:

1. **Ideation** — generates startup ideas with target markets and differentiation
2. **Market Research** — estimates market size, competitors, and trends
3. **Validation** — scores feasibility, identifies risks, recommends proceed/pivot/stop
4. **Refinement** — sharpens the idea based on the validation feedback
5. **Business Model** — defines revenue streams, costs, partnerships, unit economics
6. **Report Writer** — synthesizes everything into a markdown report

The final report is saved locally to `backend/reports/` as a timestamped markdown file.

## Three backends

The same frontend works with any of three interchangeable backends. Pick one based on what you have available:

| Backend | File | Cost | Notes |
|---------|------|------|-------|
| Hugging Face | `main_huggingface.py` | Free | Adds the demanding-orchestrator critique loop; uses the HF Inference API |
| Ollama (local) | `main_ollama.py` | Free | Runs entirely offline on your machine; no web search |
| Anthropic Claude | `main.py` | Paid (API usage) | Highest quality; supports web search for market research |

The Hugging Face backend is the most feature-complete: its orchestrator critiques each agent's output against quality criteria and requests up to two revision rounds before accepting the work. Those revision rounds are what the dialogue panel in the UI visualizes.

## Architecture

```
ai-agents-demo/
├── backend/
│   ├── shared.py                     # Shared agent definitions + helpers (single source of truth)
│   ├── main.py                       # Anthropic Claude backend
│   ├── main_huggingface.py           # Hugging Face backend (critique loop)
│   ├── main_ollama.py                # Ollama local backend
│   ├── requirements.txt              # Deps for the Claude backend
│   ├── requirements_huggingface.txt  # Deps for the HF backend
│   ├── requirements_ollama.txt       # Deps for the Ollama backend
│   └── .env.example                  # Backend config template
│
├── frontend/
│   ├── public/images/                # Pixel-art agent characters
│   ├── src/
│   │   ├── App.jsx                   # Main app + SSE handling
│   │   ├── components/
│   │   │   ├── OrchestratorNode.jsx  # Center orchestrator node
│   │   │   ├── AgentNode.jsx         # Agent nodes with revision badges
│   │   │   ├── DialoguePanel.jsx     # Live orchestrator<->agent conversation
│   │   │   ├── ConnectionCanvas.jsx  # Animated connection lines
│   │   │   ├── AgentOutput.jsx       # Click-to-view agent output
│   │   │   └── ReportViewer.jsx      # Final report display + download
│   │   └── styles/index.css
│   ├── .env.example                  # Frontend config template
│   └── package.json
│
├── HUGGINGFACE_GUIDE.md              # Detailed Hugging Face setup
├── OLLAMA_GUIDE.md                   # Detailed Ollama setup
└── README.md
```

The three backends share their agent definitions and helper functions through `shared.py`, so the prompts stay in sync. Each backend keeps only the logic that's genuinely specific to its model provider (how it calls the model, and any provider-specific prompt tweaks).

Communication between backend and frontend uses **Server-Sent Events (SSE)**: the backend streams a sequence of typed events (`agent_start`, `dialogue`, `agent_complete`, `complete`, …) as the orchestration runs, and the frontend updates the visualization as each event arrives.

## Getting started

### Prerequisites

- Python 3.9+
- Node.js 18+
- For the Hugging Face backend: a free Hugging Face account and API token
- For the Ollama backend: [Ollama](https://ollama.com) installed locally
- For the Claude backend: an Anthropic API key

### 1. Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies for your chosen backend
pip install -r requirements_huggingface.txt   # or requirements.txt / requirements_ollama.txt

# Create your local config from the template
cp .env.example .env            # macOS/Linux
# copy .env.example .env        # Windows
```

Then open `.env` and fill in the value(s) you need:

- **Hugging Face**: set `HF_API_TOKEN` (get one at https://huggingface.co/settings/tokens)
- **Claude**: set `ANTHROPIC_API_KEY`
- **Ollama**: no token required

Start the backend:

```bash
python main_huggingface.py      # or main.py / main_ollama.py
```

The backend runs on `http://localhost:8000`. You can confirm it's up by visiting `http://localhost:8000/docs`.

### 2. Frontend

In a separate terminal:

```bash
cd frontend
npm install

# Optional: if your backend isn't on http://localhost:8000, copy the template
# and set VITE_API_BASE_URL accordingly.
cp .env.example .env

npm run dev
```

Open http://localhost:3000 and enter a problem or industry to start an orchestration.

### Convenience scripts

`start.sh` / `start.bat` (Claude), `start_huggingface.sh` / `.bat`, and `start_ollama.sh` / `.bat` start both the backend and frontend together. They still expect you to have created `backend/.env` first.

## Configuration

| Variable | Backend | Required | Purpose |
|----------|---------|----------|---------|
| `HF_API_TOKEN` | Hugging Face | Yes | Authenticates with the HF Inference API |
| `HF_MODEL` | Hugging Face | No | Override the default model (`Qwen/Qwen2.5-72B-Instruct`) |
| `ANTHROPIC_API_KEY` | Claude | Yes | Authenticates with the Anthropic API |
| `VITE_API_BASE_URL` | Frontend | No | Backend URL; defaults to `http://localhost:8000` |

The Ollama backend has no environment variables; edit `OLLAMA_BASE_URL` and `OLLAMA_MODEL` near the top of `main_ollama.py` if your setup differs from the defaults.

> **Note on secrets:** `.env` is gitignored and should never be committed. Only `.env.example` (which contains placeholders) belongs in the repository. The same goes for any API keys or credential files — keep them local.

## The demanding orchestrator (Hugging Face backend)

In the Hugging Face backend, the orchestrator does more than route work. For each agent it:

1. Sets explicit quality criteria
2. Reviews the agent's output against them
3. Approves good work, or rejects weak work with a specific improvement request
4. Allows up to two revision rounds
5. Records every exchange so the UI can display it

For example, if the Market Research agent returns a vague market size, the orchestrator can reject it and ask for a concrete dollar figure with a growth rate, then re-run the agent with that feedback. This critique loop is the most interesting part of the project and is what the dialogue panel visualizes with round numbers and approval/rejection markers.

The Claude and Ollama backends use a simpler single-pass flow (dispatch → collect → continue) without the critique loop.

## Models

- **Hugging Face** defaults to `Qwen/Qwen2.5-72B-Instruct`, a strong open model that needs no gated access. You can switch models via `HF_MODEL`; the code also handles model-loading (503), rate-limit (429), and timeout (504) responses with automatic retries. Llama models work too but require accepting Meta's license on the model page first.
- **Ollama** defaults to `llama3.1:8b`. Pull it first with `ollama pull llama3.1:8b`.
- **Claude** uses `claude-sonnet-4-20250514` and can use web search for the market research step.

## Troubleshooting

- **"Cannot connect to backend"** — make sure the backend is running on port 8000 (or that `VITE_API_BASE_URL` matches wherever it's running).
- **"HF_API_TOKEN not set"** — add your token to `backend/.env`.
- **HF returns 503** — the model is loading; the backend retries automatically after a short wait.
- **HF returns 402** — the free-tier credits are exhausted; try a different model or check your HF billing page.
- **Ollama "Cannot connect"** — make sure `ollama serve` is running and the model is pulled.

See [HUGGINGFACE_GUIDE.md](HUGGINGFACE_GUIDE.md) and [OLLAMA_GUIDE.md](OLLAMA_GUIDE.md) for backend-specific detail.

## What this demonstrates

- The orchestrator–workers multi-agent pattern
- Quality control for LLM output via critique and revision loops
- Real-time streaming of agent activity over Server-Sent Events
- A full-stack setup (FastAPI + React) with a provider-agnostic backend design
- Practical robustness: retries, graceful error events, and a local-save fallback

## Tech stack

**Backend:** Python, FastAPI, Uvicorn, with the Anthropic SDK / Hugging Face Inference API / Ollama depending on the chosen backend.
**Frontend:** React, Vite, Tailwind CSS, lucide-react.
