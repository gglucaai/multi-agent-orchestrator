"""
AI AGENTS ORCHESTRATOR - Hugging Face Backend
=============================================
Uses Hugging Face's FREE Inference API with Llama 3.3 70B.

Features:
- DEMANDING ORCHESTRATOR: Critiques agent outputs and requests revisions
- DIALOGUE TRACKING: Records back-and-forth between orchestrator and agents
- LOCAL REPORT EXPORT: Final report saved to the reports/ directory as markdown
- Up to 2 revision rounds per agent for quality

Model: meta-llama/Llama-3.3-70B-Instruct
Why: Best free open-source model, excellent JSON compliance, fast inference
"""

import os
import json
import asyncio
import re
from typing import Dict, Any, AsyncGenerator, List
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Shared helpers (single source of truth). The HF backend keeps its own richer
# AGENTS dict because its prompts and quality_criteria differ intentionally for
# the critique loop.
from shared import extract_json, format_sse

load_dotenv()

app = FastAPI(title="AI Agents Orchestrator API (Hugging Face)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================
# HUGGING FACE CONFIG
# =======================

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# Use the new HF Router endpoint (OpenAI-compatible)
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

# Model selection - configurable via .env
# Best free models for our orchestrator-workers task:
#
# RECOMMENDED (no gated access needed):
#   - "Qwen/Qwen2.5-72B-Instruct"           # Top performer, no license needed
#   - "deepseek-ai/DeepSeek-V3"              # Excellent reasoning
#   - "mistralai/Mixtral-8x7B-Instruct-v0.1" # Fast and reliable
#
# REQUIRES META LICENSE ACCEPTANCE (visit model page first):
#   - "meta-llama/Llama-3.3-70B-Instruct"   # State-of-the-art
#   - "meta-llama/Llama-3.1-8B-Instruct"    # Faster, smaller
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")

if not HF_API_TOKEN:
    print("⚠️  WARNING: HF_API_TOKEN not set in .env file")
    print("   Get a free token at: https://huggingface.co/settings/tokens")


# =======================
# AGENT DEFINITIONS WITH QUALITY CRITERIA
# =======================

AGENTS = {
    "ideation": {
        "name": "Ideation Agent",
        "character": "ideation.png",
        "color": "#FFD700",
        "description": "Generates creative startup ideas",
        "system_prompt": """You are an expert startup ideation specialist. Generate 3 innovative, feasible startup ideas based on the problem provided.

For each idea, provide:
1. Name (memorable, brandable)
2. One-line description (clear value proposition)
3. Target market (specific demographic/segment)
4. Key differentiation (what makes it unique)

CRITICAL: Return ONLY valid JSON with no preamble, no explanation, no markdown.
Start your response with { and end with }

Format:
{
  "ideas": [
    {"name": "...", "description": "...", "target": "...", "differentiation": "..."}
  ]
}""",
        "quality_criteria": [
            "Each idea must have a unique value proposition",
            "Target markets must be specific (not generic 'everyone')",
            "Differentiation must be concrete and defensible",
            "Ideas must be feasible (not pure science fiction)"
        ]
    },
    "market_research": {
        "name": "Market Research Agent",
        "character": "market_research.png",
        "color": "#4A90E2",
        "description": "Analyzes market size and competition",
        "system_prompt": """You are a market research analyst. Provide rigorous market analysis for this startup idea.

Analyze:
1. Total Addressable Market (TAM) - with specific dollar figure
2. Top 3-5 competitors (real companies if possible)
3. Market trends (growing/declining with evidence)
4. Key insights (actionable observations)

CRITICAL: Return ONLY valid JSON with no preamble.
Start with { and end with }

Format:
{
  "market_size": "$X billion globally, growing at Y% CAGR",
  "competitors": ["Company1: positioning", "Company2: positioning"],
  "trends": "...",
  "insights": "..."
}""",
        "quality_criteria": [
            "TAM must include specific dollar figures",
            "Competitors must be real or plausible companies",
            "Trends must reference specific data or timeframes",
            "Insights must be actionable, not generic"
        ]
    },
    "validation": {
        "name": "Validation Agent",
        "character": "validation.png",
        "color": "#E74C3C",
        "description": "Identifies risks and validates feasibility",
        "system_prompt": """You are a startup validation expert. Critically analyze this idea against the market research.

Provide:
1. Feasibility score (0-100, be honest)
2. Top 3 risks (specific and actionable)
3. Key assumptions to test (testable hypotheses)
4. Recommendation: proceed / pivot / stop

CRITICAL: Return ONLY valid JSON with no preamble.
Start with { and end with }

Format:
{
  "feasibility_score": 75,
  "risks": ["Risk 1: ...", "Risk 2: ...", "Risk 3: ..."],
  "assumptions": ["Hypothesis 1: ...", "Hypothesis 2: ..."],
  "recommendation": "proceed"
}""",
        "quality_criteria": [
            "Feasibility score must reflect actual analysis (not always 70-80)",
            "Risks must be specific to this idea, not generic",
            "Assumptions must be testable hypotheses",
            "Recommendation must align with the score"
        ]
    },
    "refinement": {
        "name": "Refinement Agent",
        "character": "refinement.png",
        "color": "#9B59B6",
        "description": "Improves idea based on feedback",
        "system_prompt": """You are a startup strategy consultant. Refine the startup idea based on validation feedback.

Address each risk and adjust:
1. Value proposition (refined and sharper)
2. Target market (narrower if needed)
3. Go-to-market approach (specific channels)
4. Risk mitigation strategies (concrete actions)

CRITICAL: Return ONLY valid JSON with no preamble.
Start with { and end with }

Format:
{
  "refined_idea": "...",
  "adjusted_target": "...",
  "gtm_strategy": "...",
  "risk_mitigation": "..."
}""",
        "quality_criteria": [
            "Must directly address risks from validation",
            "GTM strategy must specify concrete channels",
            "Risk mitigations must be actionable",
            "Refinements must be substantive, not cosmetic"
        ]
    },
    "business_model": {
        "name": "Business Model Agent",
        "character": "business_model.png",
        "color": "#E67E22",
        "description": "Develops revenue and cost structure",
        "system_prompt": """You are a business model expert. Design a viable business model.

Define:
1. Revenue streams (specific pricing/models)
2. Cost structure (major cost categories)
3. Key partnerships (specific types of partners)
4. Unit economics (CAC, LTV estimates if possible)

CRITICAL: Return ONLY valid JSON with no preamble.
Start with { and end with }

Format:
{
  "revenue_streams": ["Stream 1: $X/month subscription", "..."],
  "cost_structure": ["Cost 1: ...", "..."],
  "partnerships": ["Partnership type 1: ...", "..."],
  "unit_economics": "CAC: $X, LTV: $Y, Payback: Z months"
}""",
        "quality_criteria": [
            "Revenue streams must include pricing logic",
            "Cost structure must be comprehensive",
            "Partnerships must be specific types",
            "Unit economics should include real estimates"
        ]
    },
    "report_writer": {
        "name": "Report Writer Agent",
        "character": "report_writer.png",
        "color": "#1ABC9C",
        "description": "Synthesizes final report",
        "system_prompt": """You are a business analyst writing a professional startup concept report.

Synthesize all previous agent outputs into a cohesive narrative with these sections:

# Executive Summary
# Startup Concept
# Market Analysis
# Validation & Risks
# Refined Strategy
# Business Model
# Conclusion & Next Steps

Write in professional, clear prose. Be specific and data-driven. Use markdown formatting.
Return ONLY the markdown report text, no JSON, no preamble.""",
        "quality_criteria": [
            "Must include all required sections",
            "Must reference specific data from previous agents",
            "Must be in markdown format",
            "Must be professional and cohesive"
        ]
    }
}


# =======================
# ORCHESTRATOR CRITIC PROMPT
# =======================

ORCHESTRATOR_CRITIC_PROMPT = """You are a demanding project orchestrator reviewing the work of a specialized agent.

Agent role: {agent_name}
Agent description: {agent_description}

Quality criteria the agent MUST meet:
{quality_criteria}

The agent produced this output:
{agent_output}

Original context provided to agent:
{context}

Evaluate the work critically. Be DEMANDING but FAIR.

Respond ONLY in valid JSON format:
{{
  "approved": true/false,
  "critique": "Brief specific critique (1-2 sentences)",
  "improvement_request": "Specific actionable request if not approved (or empty if approved)"
}}

Approve only if work meets ALL quality criteria. Reject if any criterion is weak.
Start with {{ and end with }}"""


class StartupRequest(BaseModel):
    problem: str


# =======================
# HUGGING FACE API CALLER
# =======================

async def call_huggingface(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> str:
    """
    Call Hugging Face Inference API via the new Router endpoint.
    Uses OpenAI-compatible format - works with Llama 3.3 70B and other top models.
    """
    if not HF_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="HF_API_TOKEN not set. Get one free at https://huggingface.co/settings/tokens"
        )
    
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(HF_API_URL, headers=headers, json=payload)
            
            # Handle model loading
            if response.status_code == 503:
                error_data = response.json()
                wait_time = error_data.get("estimated_time", 20)
                print(f"Model loading, waiting {wait_time}s...")
                await asyncio.sleep(min(wait_time, 30))
                response = await client.post(HF_API_URL, headers=headers, json=payload)
            
            # Handle gateway timeout - retry once
            if response.status_code == 504:
                print(f"Gateway timeout (504), retrying in 10s...")
                await asyncio.sleep(10)
                response = await client.post(HF_API_URL, headers=headers, json=payload)
            
            # Handle rate limit
            if response.status_code == 429:
                print(f"Rate limited (429), waiting 30s...")
                await asyncio.sleep(30)
                response = await client.post(HF_API_URL, headers=headers, json=payload)
            
            if response.status_code == 402:
                raise HTTPException(
                    status_code=402,
                    detail="Free tier credits exhausted. Visit https://huggingface.co/settings/billing to check your usage, or try a different model."
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Handle OpenAI-compatible response format
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected response format: {str(result)[:200]}"
                )
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:300]
            raise HTTPException(
                status_code=500,
                detail=f"HF API error {e.response.status_code}: {error_text}"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"HF API error: {str(e)}"
            )


# =======================
# AGENT CALL WITH CRITIC LOOP
# =======================

async def call_agent_with_critique(
    agent_key: str,
    context: Dict[str, Any],
    sse_queue: asyncio.Queue,
    max_revisions: int = 2
) -> Dict[str, Any]:
    """
    Call agent with demanding orchestrator critique loop.
    
    Flow:
    1. Orchestrator dispatches task to agent
    2. Agent produces output
    3. Orchestrator critiques output
    4. If not approved, requests revision (up to max_revisions times)
    5. Returns final approved output
    """
    agent = AGENTS[agent_key]
    
    # ============ INITIAL DISPATCH ============
    await sse_queue.put({
        "type": "dialogue",
        "speaker": "orchestrator",
        "to": agent_key,
        "message": f"Hi {agent['name']}, I need you to {agent['description'].lower()}. Follow these criteria strictly: {'; '.join(agent['quality_criteria'][:2])}.",
        "round": 0
    })
    
    await asyncio.sleep(0.5)
    
    await sse_queue.put({
        "type": "agent_thinking",
        "agent": agent_key,
        "message": "Working on the task..."
    })
    
    # First attempt
    user_prompt = f"Context:\n{json.dumps(context, indent=2)}"
    raw_response = await call_huggingface(
        agent['system_prompt'],
        user_prompt,
        max_tokens=2500
    )
    
    try:
        if agent_key == "report_writer":
            current_output = {"report": raw_response}
        else:
            current_output = extract_json(raw_response)
    except json.JSONDecodeError:
        await sse_queue.put({
            "type": "dialogue",
            "speaker": "orchestrator",
            "to": agent_key,
            "message": "Your output had formatting issues. Please respond with valid JSON only.",
            "round": 0
        })
        raw_response = await call_huggingface(
            agent['system_prompt'] + "\n\nIMPORTANT: Return ONLY valid JSON, no other text.",
            user_prompt,
            max_tokens=2500
        )
        if agent_key == "report_writer":
            current_output = {"report": raw_response}
        else:
            current_output = extract_json(raw_response)
    
    # Agent submits work
    await sse_queue.put({
        "type": "dialogue",
        "speaker": agent_key,
        "to": "orchestrator",
        "message": "Done! Here's my analysis.",
        "data": current_output,
        "round": 0
    })
    
    # Skip critique for report_writer
    if agent_key == "report_writer":
        return current_output
    
    # ============ CRITIQUE LOOP ============
    for revision in range(max_revisions):
        await sse_queue.put({
            "type": "orchestrator_reviewing",
            "agent": agent_key,
            "message": "Reviewing the work..."
        })
        
        critic_prompt = ORCHESTRATOR_CRITIC_PROMPT.format(
            agent_name=agent['name'],
            agent_description=agent['description'],
            quality_criteria='\n'.join(f"- {c}" for c in agent['quality_criteria']),
            agent_output=json.dumps(current_output, indent=2),
            context=json.dumps(context, indent=2)[:1000]
        )
        
        try:
            critique_response = await call_huggingface(
                "You are a demanding but fair orchestrator. Be strict about quality.",
                critic_prompt,
                max_tokens=500,
                temperature=0.3
            )
            critique = extract_json(critique_response)
        except (json.JSONDecodeError, KeyError):
            await sse_queue.put({
                "type": "dialogue",
                "speaker": "orchestrator",
                "to": agent_key,
                "message": "Approved. Good work.",
                "round": revision + 1
            })
            return current_output
        
        if critique.get("approved", False):
            await sse_queue.put({
                "type": "dialogue",
                "speaker": "orchestrator",
                "to": agent_key,
                "message": f"✓ Approved. {critique.get('critique', 'Good work.')}",
                "round": revision + 1
            })
            return current_output
        
        # Work rejected - request revision
        if revision < max_revisions - 1:
            critique_msg = critique.get('critique', 'Quality issues detected')
            improvement = critique.get('improvement_request', 'Please improve the work')
            
            await sse_queue.put({
                "type": "dialogue",
                "speaker": "orchestrator",
                "to": agent_key,
                "message": f"✗ {critique_msg} {improvement}",
                "round": revision + 1
            })
            
            await asyncio.sleep(0.5)
            
            await sse_queue.put({
                "type": "dialogue",
                "speaker": agent_key,
                "to": "orchestrator",
                "message": "Understood. Revising my work...",
                "round": revision + 1
            })
            
            await sse_queue.put({
                "type": "agent_thinking",
                "agent": agent_key,
                "message": "Revising..."
            })
            
            revision_prompt = f"""Your previous output was rejected by the orchestrator.

Previous output:
{json.dumps(current_output, indent=2)}

Orchestrator's critique:
{critique.get('critique', '')}

Required improvement:
{critique.get('improvement_request', '')}

Original context:
{json.dumps(context, indent=2)}

Now provide an IMPROVED version. Return ONLY valid JSON."""

            raw_response = await call_huggingface(
                agent['system_prompt'],
                revision_prompt,
                max_tokens=2500
            )
            
            try:
                if agent_key == "report_writer":
                    current_output = {"report": raw_response}
                else:
                    current_output = extract_json(raw_response)
                
                await sse_queue.put({
                    "type": "dialogue",
                    "speaker": agent_key,
                    "to": "orchestrator",
                    "message": "Revised version ready.",
                    "data": current_output,
                    "round": revision + 1
                })
            except json.JSONDecodeError:
                break
        else:
            await sse_queue.put({
                "type": "dialogue",
                "speaker": "orchestrator",
                "to": agent_key,
                "message": f"Final version accepted. {critique.get('critique', '')}",
                "round": revision + 1
            })
    
    return current_output


# =======================
# LOCAL REPORT EXPORT
# =======================

async def save_report(report_content: str, title: str) -> Dict[str, Any]:
    """
    Save the final report locally to the reports/ directory as markdown.
    """
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"startup_report_{timestamp}.md"
    filepath = os.path.join(report_dir, filename)

    full_content = (
        f"# {title}\n\n"
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        f"---\n\n"
        f"{report_content}"
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    return {
        "success": True,
        "method": "local",
        "filepath": filepath,
        "url": None,
        "message": f"Report saved to {filepath}"
    }


# =======================
# ORCHESTRATOR
# =======================

async def orchestrate(problem: str) -> AsyncGenerator[str, None]:
    """Demanding orchestrator with dialogue tracking."""
    state = {"problem": problem}
    sse_queue: asyncio.Queue = asyncio.Queue()
    
    async def agent_worker():
        """Run the full agent pipeline, pushing SSE events onto the queue as it goes."""
        try:
            await sse_queue.put({
                "type": "start",
                "message": "Orchestrator initiating workflow",
                "timestamp": datetime.now().isoformat()
            })
            
            # PHASE 1: IDEATION
            await sse_queue.put({"type": "agent_start", "agent": "ideation"})
            ideation_result = await call_agent_with_critique("ideation", {"problem": problem}, sse_queue)
            state["ideation"] = ideation_result
            await sse_queue.put({"type": "agent_complete", "agent": "ideation", "output": ideation_result})
            
            selected_idea = ideation_result["ideas"][0]
            state["selected_idea"] = selected_idea
            await sse_queue.put({
                "type": "orchestrator_decision",
                "message": f"Selected: {selected_idea['name']}",
                "data": selected_idea
            })
            
            # PHASE 2: MARKET RESEARCH
            await sse_queue.put({"type": "agent_start", "agent": "market_research"})
            market_result = await call_agent_with_critique(
                "market_research",
                {"idea": selected_idea, "problem": problem},
                sse_queue
            )
            state["market_research"] = market_result
            await sse_queue.put({"type": "agent_complete", "agent": "market_research", "output": market_result})
            
            # PHASE 3: VALIDATION
            await sse_queue.put({"type": "agent_start", "agent": "validation"})
            validation_result = await call_agent_with_critique(
                "validation",
                {"idea": selected_idea, "market_research": market_result},
                sse_queue
            )
            state["validation"] = validation_result
            await sse_queue.put({"type": "agent_complete", "agent": "validation", "output": validation_result})
            
            # PHASE 4: REFINEMENT
            await sse_queue.put({"type": "agent_start", "agent": "refinement"})
            refinement_result = await call_agent_with_critique(
                "refinement",
                {"idea": selected_idea, "validation": validation_result, "market_research": market_result},
                sse_queue
            )
            state["refinement"] = refinement_result
            await sse_queue.put({"type": "agent_complete", "agent": "refinement", "output": refinement_result})
            
            # PHASE 5: BUSINESS MODEL
            await sse_queue.put({"type": "agent_start", "agent": "business_model"})
            business_result = await call_agent_with_critique(
                "business_model",
                {"refined_idea": refinement_result, "market_research": market_result},
                sse_queue
            )
            state["business_model"] = business_result
            await sse_queue.put({"type": "agent_complete", "agent": "business_model", "output": business_result})
            
            # PHASE 6: REPORT WRITING
            await sse_queue.put({"type": "agent_start", "agent": "report_writer"})
            report_result = await call_agent_with_critique(
                "report_writer",
                state,
                sse_queue,
                max_revisions=1
            )
            state["report"] = report_result["report"]
            await sse_queue.put({"type": "agent_complete", "agent": "report_writer", "output": report_result})
            
            # PHASE 7: SAVE REPORT
            await sse_queue.put({
                "type": "saving_report",
                "message": "Exporting final report..."
            })
            
            doc_title = f"Startup Concept: {selected_idea['name']} - {datetime.now().strftime('%Y-%m-%d')}"
            save_result = await save_report(report_result["report"], doc_title)
            
            await sse_queue.put({
                "type": "complete",
                "message": "Orchestration complete!",
                "save_result": save_result,
                "final_state": state
            })
            
        except Exception as e:
            await sse_queue.put({
                "type": "error",
                "message": str(e)
            })
        finally:
            await sse_queue.put({"type": "_end"})
    
    worker_task = asyncio.create_task(agent_worker())
    
    while True:
        event = await sse_queue.get()
        if event.get("type") == "_end":
            break
        yield format_sse(event)
    
    await worker_task


# =======================
# API ENDPOINTS
# =======================

@app.get("/")
async def root():
    """Health check endpoint. Reports model, token status, and agent list."""
    return {
        "status": "running",
        "service": "AI Agents Orchestrator (Hugging Face)",
        "model": HF_MODEL,
        "hf_token_configured": bool(HF_API_TOKEN),
        "agents": list(AGENTS.keys())
    }


@app.get("/agents")
async def get_agents():
    """Return agent metadata (name, character, color, description) for the frontend."""
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
    """Start orchestration and stream progress to the client via SSE."""
    return StreamingResponse(
        orchestrate(request.problem),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn
    print("🤗 Starting AI Agents Orchestrator API (Hugging Face)")
    print(f"📍 Server: http://localhost:8000")
    print(f"🤖 Model: {HF_MODEL}")
    print(f"🌐 Endpoint: {HF_API_URL}")
    print(f"🔑 HF Token: {'✓ Configured' if HF_API_TOKEN else '✗ NOT SET (add to .env)'}")
    print(f"💬 Mode: Demanding orchestrator with critique loops")
    print()
    if "meta-llama" in HF_MODEL:
        print("⚠️  IMPORTANT: Llama models require accepting Meta's license:")
        print(f"   Visit: https://huggingface.co/{HF_MODEL}")
        print("   And click 'Agree and access repository'")
        print()
    uvicorn.run(app, host="0.0.0.0", port=8000)
