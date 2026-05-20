"""
AI AGENTS ORCHESTRATOR - Ollama Local Backend
=============================================
Runs entirely on your machine with Ollama local models.
No API calls, no costs, works offline!

Requirements:
- Ollama installed (https://ollama.com)
- A model pulled (e.g., ollama pull llama3.1:8b)
"""

import json
import asyncio
import re
import requests
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Shared agent definitions and helpers (single source of truth)
from shared import AGENTS, extract_json, format_sse

# Initialize FastAPI app
app = FastAPI(title="AI Agents Orchestrator API (Ollama)")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"  # Change this to your preferred model

# =======================
# AGENT DEFINITIONS
# =======================
# Agents come from shared.py. Ollama runs locally with no web search, so the
# market_research agent is told to estimate from its own knowledge instead of
# searching the web. We override just that one prompt; everything else is shared.

AGENTS["market_research"]["system_prompt"] = """You are a market research analyst. Based on your knowledge, estimate the market for this startup idea.

Analyze:
1. Total Addressable Market (TAM) - provide a realistic estimate
2. Top 3-5 competitors (real or likely competitors)
3. Market trends (growing/declining)
4. Key insights

CRITICAL: Return ONLY valid JSON with no preamble, no explanation, no markdown.
Start your response with { and end with }

Format:
{
  "market_size": "...",
  "competitors": ["...", "..."],
  "trends": "...",
  "insights": "..."
}"""

# =======================
# REQUEST/RESPONSE MODELS
# =======================

class StartupRequest(BaseModel):
    """Request model for starting orchestration"""
    problem: str


# =======================
# OLLAMA HELPER FUNCTIONS
# =======================

def call_ollama(prompt: str, system_prompt: str = "") -> str:
    """
    Call Ollama API to generate text.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
    
    Returns:
        Generated text
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system_prompt}\n\n{prompt}",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Make sure Ollama is running (run 'ollama serve')"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama error: {str(e)}"
        )


async def call_agent(
    agent_key: str, 
    context: Dict[str, Any], 
    retries: int = 2
) -> Dict[str, Any]:
    """
    Call a specialized agent with retry logic using Ollama.
    """
    agent = AGENTS[agent_key]
    last_error = None
    raw_response = ""
    
    for attempt in range(retries + 1):
        try:
            # Build the prompt
            prompt = f"Context:\n{json.dumps(context, indent=2)}"
            
            # Call Ollama (run in thread to not block async)
            raw_response = await asyncio.to_thread(
                call_ollama,
                prompt,
                agent['system_prompt']
            )
            
            print(f"\n[{agent_key}] Raw response preview: {raw_response[:200]}...")
            
            # Parse based on agent type
            if agent_key == "report_writer":
                return {"report": raw_response}
            else:
                return extract_json(raw_response)
                
        except json.JSONDecodeError as e:
            last_error = e
            print(f"JSON parse error in {agent_key} (attempt {attempt + 1}): {e}")
            print(f"Raw response: {raw_response[:500]}")
            if attempt < retries:
                await asyncio.sleep(1)
                continue
        except Exception as e:
            last_error = e
            print(f"Error in {agent_key} (attempt {attempt + 1}): {e}")
            if attempt < retries:
                await asyncio.sleep(1)
                continue
    
    # All retries exhausted
    raise HTTPException(
        status_code=500,
        detail=f"{agent['name']} failed after {retries + 1} attempts: {str(last_error)}"
    )


# =======================
# ORCHESTRATOR
# =======================

async def orchestrate(problem: str) -> AsyncGenerator[str, None]:
    """
    Main orchestrator function.
    Uses Ollama local models instead of Claude API.
    """
    state = {"problem": problem}
    
    try:
        # Send start event
        yield format_sse({
            "type": "start",
            "message": "Orchestrator initiating workflow (using Ollama local model)",
            "timestamp": datetime.now().isoformat()
        })
        
        # PHASE 1: IDEATION
        yield format_sse({
            "type": "agent_start",
            "agent": "ideation",
            "message": "Orchestrator dispatching to Ideation Agent"
        })
        
        ideation_result = await call_agent("ideation", {"problem": problem})
        state["ideation"] = ideation_result
        
        yield format_sse({
            "type": "agent_complete",
            "agent": "ideation",
            "output": ideation_result
        })
        
        # Select first idea
        selected_idea = ideation_result["ideas"][0]
        state["selected_idea"] = selected_idea
        
        yield format_sse({
            "type": "orchestrator_decision",
            "message": f"Orchestrator selected: {selected_idea['name']}",
            "data": selected_idea
        })
        
        # PHASE 2: MARKET RESEARCH (no web search with Ollama)
        yield format_sse({
            "type": "agent_start",
            "agent": "market_research",
            "message": "Orchestrator dispatching to Market Research Agent"
        })
        
        market_result = await call_agent(
            "market_research",
            {"idea": selected_idea, "problem": problem}
        )
        state["market_research"] = market_result
        
        yield format_sse({
            "type": "agent_complete",
            "agent": "market_research",
            "output": market_result
        })
        
        # PHASE 3: VALIDATION
        yield format_sse({
            "type": "agent_start",
            "agent": "validation",
            "message": "Orchestrator dispatching to Validation Agent"
        })
        
        validation_result = await call_agent(
            "validation",
            {"idea": selected_idea, "market_research": market_result}
        )
        state["validation"] = validation_result
        
        yield format_sse({
            "type": "agent_complete",
            "agent": "validation",
            "output": validation_result
        })
        
        # PHASE 4: REFINEMENT
        yield format_sse({
            "type": "agent_start",
            "agent": "refinement",
            "message": "Orchestrator dispatching to Refinement Agent"
        })
        
        refinement_result = await call_agent(
            "refinement",
            {
                "idea": selected_idea,
                "validation": validation_result,
                "market_research": market_result
            }
        )
        state["refinement"] = refinement_result
        
        yield format_sse({
            "type": "agent_complete",
            "agent": "refinement",
            "output": refinement_result
        })
        
        # PHASE 5: BUSINESS MODEL
        yield format_sse({
            "type": "agent_start",
            "agent": "business_model",
            "message": "Orchestrator dispatching to Business Model Agent"
        })
        
        business_result = await call_agent(
            "business_model",
            {
                "refined_idea": refinement_result,
                "market_research": market_result
            }
        )
        state["business_model"] = business_result
        
        yield format_sse({
            "type": "agent_complete",
            "agent": "business_model",
            "output": business_result
        })
        
        # PHASE 6: REPORT WRITING
        yield format_sse({
            "type": "agent_start",
            "agent": "report_writer",
            "message": "Orchestrator dispatching to Report Writer Agent"
        })
        
        report_result = await call_agent("report_writer", state)
        state["report"] = report_result["report"]
        
        yield format_sse({
            "type": "agent_complete",
            "agent": "report_writer",
            "output": report_result
        })
        
        # PHASE 7: SAVE REPORT
        import os
        report_filename = f"startup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = os.path.join("reports", report_filename)
        os.makedirs("reports", exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_result["report"])
        
        yield format_sse({
            "type": "complete",
            "message": "Orchestration complete! (All processing done locally)",
            "report_path": report_path,
            "final_state": state
        })
        
    except Exception as e:
        yield format_sse({
            "type": "error",
            "message": str(e)
        })


# =======================
# API ENDPOINTS
# =======================

@app.get("/")
async def root():
    """Health check endpoint"""
    # Check if Ollama is accessible
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        ollama_status = "connected"
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
    except:
        ollama_status = "disconnected"
        model_names = []
    
    return {
        "status": "running",
        "service": "AI Agents Orchestrator (Ollama)",
        "ollama_status": ollama_status,
        "ollama_model": OLLAMA_MODEL,
        "available_models": model_names,
        "agents": list(AGENTS.keys())
    }


@app.get("/agents")
async def get_agents():
    """Return agent metadata for frontend"""
    return {
        key: {
            "name": agent["name"],
            "character": agent["character"],
            "color": agent["color"],
            "description": agent["description"]
        }
        for key, agent in AGENTS.items()
    }


@app.post("/orchestrate")
async def start_orchestration(request: StartupRequest):
    """
    Start the orchestration process.
    Returns a streaming response with real-time updates.
    """
    return StreamingResponse(
        orchestrate(request.problem),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# =======================
# RUN SERVER
# =======================

if __name__ == "__main__":
    import uvicorn
    print("🦙 Starting AI Agents Orchestrator API (Ollama)")
    print("📍 Server: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print(f"🤖 Using model: {OLLAMA_MODEL}")
    print("\n⚠️  Make sure Ollama is running!")
    print("   Run: ollama serve")
    print(f"   And pull model: ollama pull {OLLAMA_MODEL}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
