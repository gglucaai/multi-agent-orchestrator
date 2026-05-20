# 🤗 Hugging Face Edition - Setup Guide

This is the **most feature-rich version** of the AI Agents Orchestrator with:
- ✅ FREE Hugging Face Inference API (default model: Qwen2.5-72B-Instruct)
- ✅ Demanding orchestrator with critique/revision loops
- ✅ Live dialogue visualization
- ✅ Up to 2 revision rounds per agent

## 🚀 Quick Setup

### 1. Get a Free Hugging Face Token

1. Go to https://huggingface.co/join (free signup)
2. Visit https://huggingface.co/settings/tokens
3. Click "New token"
4. Name it "AI Agents Demo"
5. Select "Read" role
6. Copy the token (starts with `hf_...`)

### 2. Configure Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements_huggingface.txt

# Create .env file
cp .env.example .env

# Edit .env and add your HF token
# HF_API_TOKEN=hf_your_actual_token_here
```

### 3. Start Backend

```bash
python main_huggingface.py
```

You should see:
```
🤗 Starting AI Agents Orchestrator API (Hugging Face)
📍 Server: http://localhost:8000
🤖 Model: Qwen/Qwen2.5-72B-Instruct (default)
🔑 HF Token: ✓ Configured
💬 Mode: Demanding orchestrator with critique loops
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open Browser

Go to http://localhost:3000 and start orchestrating!

## 🤖 Why Llama 3.3 70B?

For our orchestrator-workers demo, we need a model that:

| Requirement | Llama 3.3 70B |
|-------------|---------------|
| **Free on HF** | ✅ Yes |
| **JSON compliance** | ✅ Excellent |
| **Reasoning** | ✅ Strong (matches GPT-4 on many benchmarks) |
| **Speed** | ✅ Fast on HF infrastructure |
| **Open source** | ✅ Yes |
| **Multilingual** | ✅ Yes |

### Alternative Models (if needed)

To change the model, set `HF_MODEL` in `backend/.env`, or edit the `HF_MODEL` default near the top of `main_huggingface.py`:

```python
# Best alternatives:
HF_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # Fast, very capable
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"      # Faster but smaller
HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"             # Strong alternative
```

## 💬 New Features Explained

### 1. Demanding Orchestrator

The orchestrator now CRITIQUES each agent's work using these criteria:

**Ideation Agent must produce:**
- Unique value propositions
- Specific target markets
- Concrete differentiation
- Feasible ideas

**Market Research must produce:**
- Specific dollar TAM figures
- Real competitor names
- Data-backed trends
- Actionable insights

**Validation must produce:**
- Honest feasibility scores
- Specific risks (not generic)
- Testable hypotheses
- Aligned recommendations

If criteria aren't met, the orchestrator REJECTS the work and asks for revisions (up to 2 times).

### 2. Live Dialogue Panel

The right side of the dashboard now shows:
- **Orchestrator messages** (purple, with icon)
- **Agent responses** (colored by agent, with their icon)
- **Revision rounds** (yellow badge: "Round 1", "Round 2")
- **Approvals** (green border, ✓ symbol)
- **Rejections** (red border, ✗ symbol)
- **Data previews** (expandable JSON)

### 3. Report Output

After completion, the final report is saved locally to `backend/reports/` as a
timestamped markdown file (e.g. `startup_report_20260430_190545.md`). You can
also download it directly from the UI.

## 🎨 What You'll See in the Demo

### Phase 1: Initial Dispatch
```
[Orchestrator → Ideation]: "Hi Ideation Agent, I need you to 
generate creative startup ideas. Follow these criteria strictly..."
```

### Phase 2: Agent Works
The Ideation Agent processes (yellow data packets fly out)

### Phase 3: Agent Submits
```
[Ideation → Orchestrator]: "Done! Here's my analysis."
[Data preview available]
```

### Phase 4: Orchestrator Reviews
The orchestrator shows "REVIEWING" badge

### Phase 5a: If Approved
```
[Orchestrator → Ideation]: "✓ Approved. Strong ideas with clear 
differentiation."
```

### Phase 5b: If Rejected
```
[Orchestrator → Ideation]: "✗ Target markets too generic. 
Please provide specific demographic segments..."
[Round 1 badge appears]

[Ideation → Orchestrator]: "Understood. Revising my work..."

[Ideation → Orchestrator]: "Revised version ready."

[Orchestrator → Ideation]: "✓ Approved. Better specificity."
```

## 🐛 Troubleshooting

### "HF API error 503"
**Cause**: Model is loading on Hugging Face's servers

**Solution**: Wait 30 seconds and try again. The retry logic handles this automatically, but cold starts can take 1-2 minutes.

### "HF API error 429"
**Cause**: Rate limit exceeded

**Solution**: Wait a few minutes. Free tier has limits but they reset quickly.

### "HF_API_TOKEN not set"
**Cause**: .env file missing or token not added

**Solution**:
1. Check `.env` exists in `backend/` folder
2. Verify token format: `HF_API_TOKEN=hf_...`
3. Restart the backend server

### Model returns invalid JSON
**Cause**: Smaller models sometimes ignore JSON instructions

**Solution**: 
- Retry logic handles most cases
- If persistent, try a different model via `HF_MODEL` in `backend/.env`

### Critique loop fails
**Cause**: Model can't produce valid JSON for critique

**Solution**: The code has fallback logic - if critique fails, it accepts the agent's work and continues.

## 💰 Cost Comparison

| Method | Per Run | 100 Runs |
|--------|---------|----------|
| **Claude API** | ~$0.10 | $10 |
| **Ollama Local** | $0 | $0 (uses your CPU/GPU) |
| **Hugging Face** | $0 | $0 |

**Hugging Face is ideal because:**
- 100% free (no credit card needed)
- Cloud-based (no local resources used)
- Best quality models
- Fast inference

## 🎯 Demo Tips

### Show Off the Dialogue

When presenting:

> "Watch the right panel - this shows real conversations between the orchestrator and each agent. The orchestrator is demanding - if quality criteria aren't met, it rejects the work and asks for revisions."

### When a revision happens:

> "Look! The orchestrator just rejected the Market Research output because the competitors weren't specific enough. The agent is now revising its work. This shows real quality control in AI systems - not just trusting the first output."

### Technical depth:

> "This implements the orchestrator-workers pattern with quality gates. Each agent has explicit quality criteria, and the orchestrator validates outputs against those criteria. This is how production AI systems handle hallucinations and quality issues."

## 📊 Performance Expectations

| Metric | With Critique | Without Critique |
|--------|---------------|------------------|
| Time per run | 4-6 minutes | 2-3 minutes |
| Quality | Higher | Standard |
| Demo impact | High | Medium |
| API calls | 8-15 | 6-7 |

## 🔧 Customization

### Make orchestrator MORE demanding

Edit `main_huggingface.py`, change `max_revisions`:

```python
# Current: up to 2 revisions
result = await call_agent_with_critique(
    agent_key, context, sse_queue,
    max_revisions=2
)

# More demanding:
result = await call_agent_with_critique(
    agent_key, context, sse_queue,
    max_revisions=3  # Up to 3 revisions
)
```

### Customize quality criteria

Edit each agent's `quality_criteria` in `AGENTS` dict:

```python
"ideation": {
    # ...
    "quality_criteria": [
        "Each idea must address a $1B+ market",  # Stricter
        "Must include AI/ML component",            # Domain-specific
        "Must be doable with <$100k initial capital",  # Constraint
    ]
}
```

### Adjust orchestrator personality

Edit `ORCHESTRATOR_CRITIC_PROMPT` to make orchestrator:
- More strict: "Approve only if work is exceptional..."
- More lenient: "Approve if work is reasonable..."
- More specific: "Focus particularly on quantitative accuracy..."

---

**This version showcases production-grade AI agent patterns: quality control, iterative refinement, and structured dialogue.**
