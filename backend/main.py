"""
AI AGENTS ORCHESTRATOR - Python Backend
========================================
FastAPI server that handles agent orchestration logic.
Streams real-time updates to the frontend via Server-Sent Events (SSE).

Architecture:
- FastAPI: Web framework for building APIs
- Anthropic SDK: Official Python client for Claude
- SSE: Server-Sent Events for real-time updates
- CORS: Allows frontend to communicate with backend
"""

import os
import json
import asyncio
import re
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv

# Shared agent definitions and helpers (single source of truth)
from shared import AGENTS, extract_json, format_sse

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Agents Orchestrator API")

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# =======================
# REQUEST/RESPONSE MODELS
# =======================

class StartupRequest(BaseModel):
    """Request model for starting orchestration"""
    problem: str


# =======================
# HELPER FUNCTIONS
# =======================

async def call_agent(
    agent_key: str, 
    context: Dict[str, Any], 
    use_web_search: bool = False,
    retries: int = 2
) -> Dict[str, Any]:
    """
    Call a specialized agent with retry logic.
    
    Args:
        agent_key: Which agent to call (e.g., 'ideation')
        context: Data to pass to the agent
        use_web_search: Whether to enable web search tool
        retries: Number of retry attempts on failure
    
    Returns:
        Parsed agent output
    """
    agent = AGENTS[agent_key]
    last_error = None
    raw_response = ""
    
    for attempt in range(retries + 1):
        try:
            # Build the request
            messages = [{
                "role": "user",
                "content": f"{agent['system_prompt']}\n\nContext:\n{json.dumps(context, indent=2)}"
            }]
            
            kwargs = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4000,
                "messages": messages
            }
            
            # Add web search if needed
            if use_web_search:
                kwargs["tools"] = [{
                    "type": "web_search_20250305",
                    "name": "web_search"
                }]
            
            # Make the API call (run in thread to not block async)
            response = await asyncio.to_thread(
                client.messages.create,
                **kwargs
            )
            
            # Extract text from response
            raw_response = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    raw_response += block.text
            
            # Parse based on agent type
            if agent_key == "report_writer":
                return {"report": raw_response}
            else:
                return extract_json(raw_response)
                
        except json.JSONDecodeError as e:
            last_error = e
            print(f"JSON parse error in {agent_key} (attempt {attempt + 1}): {e}")
            print(f"Raw response: {raw_response[:200]}")
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
    Coordinates all agents and streams updates to frontend.
    
    This is the heart of the orchestrator-workers pattern:
    - Sequences agent calls
    - Passes context between agents
    - Streams progress updates
    - Handles errors gracefully
    """
    state = {"problem": problem}
    
    try:
        # Send start event
        yield format_sse({
            "type": "start",
            "message": "Orchestrator initiating workflow",
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
        
        # Select first idea (orchestrator decision)
        selected_idea = ideation_result["ideas"][0]
        state["selected_idea"] = selected_idea
        
        yield format_sse({
            "type": "orchestrator_decision",
            "message": f"Orchestrator selected: {selected_idea['name']}",
            "data": selected_idea
        })
        
        # PHASE 2: MARKET RESEARCH (with web search)
        yield format_sse({
            "type": "agent_start",
            "agent": "market_research",
            "message": "Orchestrator dispatching to Market Research Agent (with web search)"
        })
        
        market_result = await call_agent(
            "market_research",
            {"idea": selected_idea, "problem": problem},
            use_web_search=True
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
        
        # PHASE 7: SAVE REPORT (saved locally to reports/)
        report_filename = f"startup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = os.path.join("reports", report_filename)
        os.makedirs("reports", exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_result["report"])
        
        yield format_sse({
            "type": "complete",
            "message": "Orchestration complete!",
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
    return {
        "status": "running",
        "service": "AI Agents Orchestrator",
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
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# =======================
# RUN SERVER
# =======================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Agents Orchestrator API")
    print("📍 Server: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
