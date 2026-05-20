# 🦙 Running with Ollama (Local Models - Zero Cost)

This guide shows you how to run the entire demo **completely offline** using Ollama local models.

## ✅ Benefits

- **💰 Zero cost** - No API charges ever
- **🔒 Private** - All data stays on your machine
- **⚡ No rate limits** - Run unlimited demos
- **📡 Offline** - Works without internet
- **🎓 Learn more** - Understand how LLMs work locally

## 📋 Setup Steps

### 1. Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
- Download from: https://ollama.com/download
- Run the installer
- Ollama will start automatically

### 2. Pull a Model

Choose based on your RAM:

**Recommended for most laptops (8-16GB RAM):**
```bash
ollama pull llama3.1:8b
```

**For powerful machines (32GB+ RAM):**
```bash
ollama pull llama3.1:70b
```

**Alternative smaller model (6GB RAM):**
```bash
ollama pull mistral:7b
```

### 3. Verify Ollama is Running

```bash
# Check if Ollama is running
ollama list

# You should see your pulled model listed
```

If Ollama isn't running:
```bash
ollama serve
```

### 4. Update Backend Configuration

In `backend/main_ollama.py`, change the model if needed:

```python
# Line 26
OLLAMA_MODEL = "llama3.1:8b"  # Change to your model
```

### 5. Install Python Dependencies

```bash
cd backend
pip install -r requirements_ollama.txt
```

### 6. Run the Backend

Instead of `main.py`, use `main_ollama.py`:

```bash
python main_ollama.py
```

You should see:
```
🦙 Starting AI Agents Orchestrator API (Ollama)
📍 Server: http://localhost:8000
🤖 Using model: llama3.1:8b
```

### 7. Run Frontend (Same as Before)

```bash
cd frontend
npm install
npm run dev
```

### 8. Test It!

Go to http://localhost:3000 and run a demo!

## 🆚 Ollama vs Claude API Comparison

| Feature | Claude API | Ollama Local |
|---------|-----------|--------------|
| **Cost** | ~$0.10/run | $0 forever |
| **Speed** | 2-3 min/run | 3-5 min/run* |
| **Quality** | Excellent | Very Good |
| **Internet** | Required | Not required |
| **Setup** | API key only | Install + download model |
| **Privacy** | Data sent to Anthropic | 100% local |
| **Rate Limits** | Yes (50/min) | None |

*Speed depends on your CPU/GPU

## ⚙️ Model Recommendations

### For Your Demo Presentation

**Best Quality (if you have RAM):**
```bash
ollama pull llama3.1:70b
# Requires: 40GB+ RAM
# Quality: Closest to Claude
# Speed: Slower (1-2 min per agent)
```

**Best Balance:**
```bash
ollama pull llama3.1:8b
# Requires: 8GB RAM
# Quality: Very good
# Speed: Fast (10-20 sec per agent)
```

**Fastest:**
```bash
ollama pull mistral:7b
# Requires: 6GB RAM
# Quality: Good
# Speed: Very fast (5-10 sec per agent)
```

## 🐛 Troubleshooting

### "Cannot connect to Ollama"

**Solution 1: Start Ollama**
```bash
ollama serve
```

**Solution 2: Check if running**
```bash
# Should return list of models
curl http://localhost:11434/api/tags
```

### "Model not found"

Make sure you pulled the model:
```bash
ollama list  # Check available models
ollama pull llama3.1:8b  # Pull if missing
```

### Slow Performance

**If using CPU only:**
- Smaller model helps: `ollama pull mistral:7b`
- Close other applications
- Give Ollama more RAM

**If you have NVIDIA GPU:**
- Ollama auto-detects and uses GPU
- Should be much faster

### JSON Parsing Errors

Local models sometimes add more preamble than Claude. If you get errors:

1. Check `backend/main_ollama.py` line ~200 (extract_json function)
2. The retry logic should handle it
3. Try running again (models can be inconsistent)

## 🎯 Best Practices for Demo

### Strategy 1: Hybrid Approach
- **Practice runs**: Use Ollama (free, unlimited)
- **Final demo**: Use Claude API (better quality)

### Strategy 2: Full Local
- Run everything with Ollama
- Mention: "This runs entirely on my laptop - no cloud APIs"
- Great talking point about local AI deployment

### Strategy 3: Comparison Demo
- Show both versions side-by-side
- Compare quality, speed, costs
- Educational for audience

## 🔧 Advanced: GPU Acceleration

If you have an NVIDIA GPU:

**Check GPU usage:**
```bash
nvidia-smi  # Should show ollama process
```

**Models automatically use GPU** - no configuration needed!

**Expected speedup:**
- CPU: ~30-60 seconds per agent
- GPU: ~5-15 seconds per agent

## 📊 What to Expect

### Quality Comparison

**Claude Sonnet 4 (API):**
- Best structured output
- Most consistent JSON formatting
- Highest quality insights
- Sometimes overly verbose

**Llama 3.1 70B (Local):**
- Comparable quality to Claude
- Occasionally needs retry for JSON
- Great insights
- Good for demo

**Llama 3.1 8B (Local):**
- Good quality
- Sometimes simpler insights
- Faster
- Reliable JSON with retry logic

**Mistral 7B (Local):**
- Decent quality
- More concise
- Very fast
- Good for testing

## 💡 Why This is Great for Learning

Running locally teaches you:
- How LLMs actually work (not just API calls)
- Resource requirements (RAM, CPU, GPU)
- Trade-offs between model size and quality
- Local deployment strategies
- Cost optimization for production

## 🎓 For Your Presentation

**Talking points:**

> "I implemented this with both Claude API and local Ollama models. The local version runs entirely on my laptop with zero API costs, though Claude provides slightly better output quality. This flexibility shows understanding of deployment trade-offs."

> "For production, you'd consider: API for best quality and zero infrastructure, or local models for privacy, cost at scale, and offline capability."

**If asked about costs:**
> "The API version costs about $0.10 per full run. But I also built a local version with Ollama that's completely free - I can switch between them depending on requirements."

## 🚀 Next Steps

1. **Test both versions** - See the quality difference
2. **Compare speeds** - Time each approach
3. **Practice your demo** - Unlimited runs with Ollama
4. **Decide for presentation** - API for quality, or local for "wow factor"

---

**Questions? Issues?**
- Ollama Docs: https://ollama.com/library
- Models: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
