import asyncio
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from arag_poc.agents import AGENTS, PHASES, run_agent

BASE_DIR = Path(__file__).parent
app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# In-memory claim store
claims = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "phases": PHASES,
        "agents": AGENTS
    })


@app.post("/claim")
async def create_claim(request: Request):
    body = await request.json()
    claim_id = str(uuid.uuid4())[:8]

    claim_state = {
        "id": claim_id,
        "data": body,
        "results": {},
        "queue": asyncio.Queue(),
        "checkpoint_1_event": asyncio.Event(),
        "checkpoint_1_decision": None,
        "checkpoint_2_event": asyncio.Event(),
        "checkpoint_2_decision": None,
    }
    claims[claim_id] = claim_state

    # Start processing in background
    asyncio.create_task(process_claim(claim_id))

    return {"claim_id": claim_id}


@app.post("/jurist-decision/{claim_id}")
async def jurist_decision(claim_id: str, request: Request):
    body = await request.json()
    claim = claims.get(claim_id)
    if not claim:
        return {"error": "Claim niet gevonden"}

    checkpoint = body.get("checkpoint")
    decision = body.get("decision")
    note = body.get("note", "")

    if checkpoint == 1:
        claim["checkpoint_1_decision"] = {"decision": decision, "note": note}
        claim["checkpoint_1_event"].set()
    elif checkpoint == 2:
        claim["checkpoint_2_decision"] = {"decision": decision, "note": note}
        claim["checkpoint_2_event"].set()

    return {"status": "ok"}


@app.get("/stream/{claim_id}")
async def stream(claim_id: str, request: Request):
    claim = claims.get(claim_id)
    if not claim:
        return {"error": "Claim niet gevonden"}

    queue = claim["queue"]

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield {"data": json.dumps(msg, ensure_ascii=False)}
                if msg.get("type") == "end":
                    break
            except asyncio.TimeoutError:
                yield {"data": json.dumps({"type": "ping"})}

    return EventSourceResponse(event_generator())


async def process_claim(claim_id: str):
    claim = claims[claim_id]
    queue = claim["queue"]
    results = claim["results"]
    claim_data = claim["data"]

    # Phase 1: Intake
    await queue.put({"type": "phase_start", "phase": "intake", "label": PHASES["intake"]["label"]})

    intake_agents = ["transcription", "summary", "key_facts", "completeness", "coverage"]
    for agent_id in intake_agents:
        result = await run_agent(agent_id, claim_data, results, queue)
        results[agent_id] = result

    # Phase 2: Assessment
    await queue.put({"type": "phase_start", "phase": "assessment", "label": PHASES["assessment"]["label"]})

    result = await run_agent("legal_analysis", claim_data, results, queue)
    results["legal_analysis"] = result

    # Checkpoint 1 summary
    checkpoint_1_summary = {
        "transcription_summary": results.get("transcription", "")[:200],
        "coverage_status": results.get("coverage", "")[:100],
        "key_facts": results.get("key_facts", "")[:200],
        "legal_analysis": results.get("legal_analysis", "")[:300],
        "completeness": results.get("completeness", "")[:150],
    }

    await queue.put({
        "type": "jurist_checkpoint",
        "checkpoint": 1,
        "title": "Checkpoint 1: Juridische Analyse Gereed",
        "description": "De intake en juridische analyse zijn voltooid. Beoordeel de bevindingen voordat brieven en processtukken worden opgesteld.",
        "summary": checkpoint_1_summary
    })

    # Wait for checkpoint 1 decision
    await claim["checkpoint_1_event"].wait()
    decision_1 = claim["checkpoint_1_decision"]

    await queue.put({
        "type": "checkpoint_decided",
        "checkpoint": 1,
        "decision": decision_1["decision"],
        "note": decision_1["note"]
    })

    # Phase 3: Handling
    await queue.put({"type": "phase_start", "phase": "handling", "label": PHASES["handling"]["label"]})

    # Run letter agent
    result = await run_agent("letter", claim_data, results, queue)
    results["letter"] = result

    # Run legal drafting agent
    result = await run_agent("legal_drafting", claim_data, results, queue)
    results["legal_drafting"] = result

    # Checkpoint 2 summary
    checkpoint_2_summary = {
        "letter_preview": results.get("letter", "")[:300],
        "legal_drafting_preview": results.get("legal_drafting", "")[:300],
        "legal_analysis": results.get("legal_analysis", "")[:200],
    }

    await queue.put({
        "type": "jurist_checkpoint",
        "checkpoint": 2,
        "title": "Checkpoint 2: Documenten Gereed voor Verzending",
        "description": "Brieven en processtukken zijn opgesteld. Beoordeel en keur goed voor verzending.",
        "summary": checkpoint_2_summary
    })

    # Wait for checkpoint 2 decision
    await claim["checkpoint_2_event"].wait()
    decision_2 = claim["checkpoint_2_decision"]

    await queue.put({
        "type": "checkpoint_decided",
        "checkpoint": 2,
        "decision": decision_2["decision"],
        "note": decision_2["note"]
    })

    # Flow complete
    await queue.put({
        "type": "flow_complete",
        "message": "Claimafhandeling voltooid",
        "total_agents": 11
    })

    await queue.put({"type": "end"})
