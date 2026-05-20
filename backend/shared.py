"""
AI AGENTS ORCHESTRATOR - Shared Definitions
===========================================
Single source of truth for the pieces every backend uses:

- AGENTS:        the six specialized agent definitions (metadata + system prompts)
- extract_json:  robust JSON extraction from LLM responses
- format_sse:    Server-Sent Event formatter

Each backend (main.py / main_huggingface.py / main_ollama.py) imports from here
so the agent prompts and helpers never drift out of sync. Backends that need a
model-specific tweak (e.g. Ollama has no web search) override individual fields
after import rather than copying the whole dictionary.
"""

import re
import json
from typing import Dict, Any


# =======================
# AGENT DEFINITIONS
# =======================
# Canonical definitions. The market_research prompt assumes a web-search-capable
# model; backends without web search override it (see main_ollama.py).

AGENTS: Dict[str, Dict[str, Any]] = {
    "ideation": {
        "name": "Ideation Agent",
        "character": "ideation.png",
        "color": "#FFD700",
        "description": "Generates creative startup ideas",
        "system_prompt": """You are an expert startup ideation specialist. Generate 3 innovative, feasible startup ideas based on the problem or industry provided.

For each idea, provide:
1. Name
2. One-line description
3. Target market
4. Key differentiation

CRITICAL: Return ONLY valid JSON with no preamble, no explanation, no markdown.
Do NOT write "Here are the ideas:" or any introductory text.
Start your response with { and end with }

Format:
{
  "ideas": [
    {"name": "...", "description": "...", "target": "...", "differentiation": "..."}
  ]
}"""
    },
    "market_research": {
        "name": "Market Research Agent",
        "character": "market_research.png",
        "color": "#4A90E2",
        "description": "Analyzes market size and competition",
        "system_prompt": """You are a market research analyst. Use web search to find current, real data about the market for this startup idea.

Analyze:
1. Total Addressable Market (TAM)
2. Top 3-5 competitors
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
    },
    "validation": {
        "name": "Validation Agent",
        "character": "validation.png",
        "color": "#E74C3C",
        "description": "Identifies risks and validates feasibility",
        "system_prompt": """You are a startup validation expert. Critically analyze this idea against the market research.

Provide:
1. Feasibility score (0-100)
2. Top 3 risks
3. Key assumptions to test
4. Recommendation (proceed/pivot/stop)

CRITICAL: Return ONLY valid JSON with no preamble, no explanation, no markdown.
Start your response with { and end with }

Format:
{
  "feasibility_score": 75,
  "risks": ["...", "...", "..."],
  "assumptions": ["...", "..."],
  "recommendation": "proceed"
}"""
    },
    "refinement": {
        "name": "Refinement Agent",
        "character": "refinement.png",
        "color": "#9B59B6",
        "description": "Improves idea based on feedback",
        "system_prompt": """You are a startup strategy consultant. Refine the startup idea based on validation feedback.

Adjust:
1. Value proposition
2. Target market (if needed)
3. Go-to-market approach
4. Risk mitigation strategies

CRITICAL: Return ONLY valid JSON with no preamble, no explanation, no markdown.
Start your response with { and end with }

Format:
{
  "refined_idea": "...",
  "adjusted_target": "...",
  "gtm_strategy": "...",
  "risk_mitigation": "..."
}"""
    },
    "business_model": {
        "name": "Business Model Agent",
        "character": "business_model.png",
        "color": "#E67E22",
        "description": "Develops revenue and cost structure",
        "system_prompt": """You are a business model expert. Design a viable business model for this startup.

Define:
1. Revenue streams (how you make money)
2. Cost structure (main expenses)
3. Key partnerships needed
4. Unit economics estimate

CRITICAL: Return ONLY valid JSON with no preamble, no explanation, no markdown.
Start your response with { and end with }

Format:
{
  "revenue_streams": ["...", "..."],
  "cost_structure": ["...", "..."],
  "partnerships": ["...", "..."],
  "unit_economics": "..."
}"""
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

Write in professional, clear prose. Be specific and data-driven.
Return ONLY the markdown report text, no JSON, no preamble."""
    }
}


# =======================
# SHARED HELPERS
# =======================

def extract_json(text: str) -> Dict[str, Any]:
    """
    Robust JSON extraction from LLM responses.
    Strips markdown code fences and any preamble, then parses the first
    JSON object or array found in the text.
    """
    # Remove markdown code blocks
    cleaned = re.sub(r'```json\n?', '', text)
    cleaned = re.sub(r'```\n?', '', cleaned)
    cleaned = cleaned.strip()

    # Try to find a JSON object or array
    json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', cleaned)
    if json_match:
        cleaned = json_match.group(0)

    return json.loads(cleaned)


def format_sse(data: Dict[str, Any]) -> str:
    """Format a dictionary as a Server-Sent Event line."""
    return f"data: {json.dumps(data)}\n\n"
