import asyncio
import json
import os
import uuid
from typing import Dict, Any

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agents import run_agent

app = FastAPI(title="ARAG Agentic Claimsflow PoC")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# In-memory claim state
claims: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    api_mode = "live" if os.environ.get("ANTHROPIC_API_KEY") else "mock"
    return templates.TemplateResponse("index.html", {"request": request, "api_mode": api_mode})


@app.post("/submit-claim")
async def submit_claim(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    claim_id = str(uuid.uuid4())[:8]

    claims[claim_id] = {
        "data": data,
        "status": "running",
        "queue": asyncio.Queue(),
        "jurist_event": asyncio.Event(),
        "jurist_decision": None,
        "context": {},
    }

    background_tasks.add_task(run_flow, claim_id)
    return {"claim_id": claim_id}


@app.post("/jurist-decision/{claim_id}")
async def jurist_decision(claim_id: str, request: Request):
    if claim_id not in claims:
        return {"error": "Claim niet gevonden"}
    body = await request.json()
    claims[claim_id]["jurist_decision"] = body
    claims[claim_id]["jurist_event"].set()
    return {"ok": True}


@app.get("/stream/{claim_id}")
async def stream(claim_id: str):
    async def event_generator():
        if claim_id not in claims:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Claim niet gevonden'})}\n\n"
            return

        queue = claims[claim_id]["queue"]
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") in ("flow_complete", "flow_error"):
                    break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def run_flow(claim_id: str):
    claim = claims[claim_id]
    queue = claim["queue"]
    data = claim["data"]
    context = claim["context"]

    agents_sequence = ["intake", "dekkingscheck", "juridisch"]
    post_jurist_agents = ["strategie", "communicatie", "afhandeling"]

    try:
        # Phase 1: pre-jurist agents
        for agent_name in agents_sequence:
            result = await run_agent(agent_name, data, context, queue)
            context[agent_name] = result
            await asyncio.sleep(0.3)

        # Jurist checkpoint
        summary = {
            "intake": context.get("intake", ""),
            "dekkingscheck": context.get("dekkingscheck", ""),
            "juridisch": context.get("juridisch", ""),
        }
        await queue.put({"type": "jurist_checkpoint", "summary": summary})

        # Wait for jurist decision
        await claim["jurist_event"].wait()
        decision = claim["jurist_decision"]

        await queue.put({"type": "jurist_decided", "decision": decision})

        if decision and decision.get("decision") == "weigeren":
            await queue.put({
                "type": "flow_complete",
                "outcome": {
                    "status": "Geweigerd",
                    "status_class": "danger",
                    "beslissing": "Claim geweigerd door jurist",
                    "reden": decision.get("note", "Geen nadere toelichting"),
                    "timeline": "N.v.t.",
                    "next_steps": ["Klant informeren over weigering", "Bezwaarmogelijkheid communiceren"],
                }
            })
            return

        if decision and decision.get("decision") == "escaleren":
            await queue.put({
                "type": "flow_escalated",
                "note": decision.get("note", ""),
            })

        # Phase 2: post-jurist agents
        for agent_name in post_jurist_agents:
            result = await run_agent(agent_name, data, context, queue)
            context[agent_name] = result
            await asyncio.sleep(0.3)

        # Final outcome
        status = "Geëscaleerd" if (decision and decision.get("decision") == "escaleren") else "Goedgekeurd"
        status_class = "warning" if status == "Geëscaleerd" else "success"

        await queue.put({
            "type": "flow_complete",
            "outcome": {
                "status": status,
                "status_class": status_class,
                "beslissing": f"Claim {status.lower()} — behandeling gestart",
                "reden": decision.get("note", "") if decision else "",
                "timeline": _extract_timeline(context),
                "next_steps": [
                    "Bezwaarbrief / sommatie versturen",
                    "Klant bevestigingsbrief sturen",
                    "Dossier aanmaken in systeem",
                    "Behandelend jurist toewijzen",
                ],
            }
        })

    except Exception as e:
        await queue.put({"type": "flow_error", "message": str(e)})


def _extract_timeline(context: dict) -> str:
    strategie = context.get("strategie", "")
    for line in strategie.split("\n"):
        if "week" in line.lower() and ("maand" in line.lower() or "weken" in line.lower()):
            return line.strip().lstrip("- *")
    return "6–8 weken (buitengerechtelijk)"
