import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from arag_poc.agents import AGENT_SEQUENCE, run_agent

app = FastAPI(title="ARAG Agentic Claimsflow PoC")

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

claims: dict = {}
USE_MOCK = not bool(os.getenv("ANTHROPIC_API_KEY"))


class ClaimSubmission(BaseModel):
    naam: str
    polisnummer: str
    type_claim: str
    omschrijving: str
    belang: str
    wederpartij: str


class JuristDecision(BaseModel):
    decision: str  # goedkeuren | escaleren | weigeren
    note: str = ""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "date": datetime.now().strftime("%d %B %Y")})


@app.post("/submit-claim")
async def submit_claim(claim: ClaimSubmission, background_tasks: BackgroundTasks):
    claim_id = str(uuid.uuid4())[:8]
    claims[claim_id] = {
        "id": claim_id,
        "status": "processing",
        "current_agent": None,
        "outputs": {},
        "jurist_event": asyncio.Event(),
        "jurist_decision": None,
        "queue": asyncio.Queue(),
        "data": claim.dict(),
        "created_at": datetime.now().isoformat(),
    }
    background_tasks.add_task(process_claim, claim_id)
    return {"claim_id": claim_id, "status": "started"}


async def process_claim(claim_id: str):
    claim = claims[claim_id]
    queue = claim["queue"]
    claim_data = claim["data"]
    context = {}

    try:
        # Run pre-jurist agents
        pre_jurist = ["intake", "dekkingscheck", "juridisch"]
        for agent_name in pre_jurist:
            claim["current_agent"] = agent_name
            await queue.put({"type": "agent_start", "agent": agent_name, "label": AGENT_SEQUENCE[agent_name]["label"]})
            result = await run_agent(agent_name, claim_data, context, queue, use_mock=USE_MOCK)
            claim["outputs"][agent_name] = result
            context[agent_name] = result
            await queue.put({"type": "agent_complete", "agent": agent_name, "result": result})

        # Jurist checkpoint
        claim["current_agent"] = "jurist"
        summary = {k: claim["outputs"][k][:300] + "..." if len(claim["outputs"].get(k, "")) > 300 else claim["outputs"].get(k, "") for k in pre_jurist}
        await queue.put({"type": "jurist_checkpoint", "summary": summary})

        # Wait for jurist decision
        await claim["jurist_event"].wait()
        decision = claim["jurist_decision"]

        if decision["decision"] == "weigeren":
            await queue.put({"type": "flow_complete", "outcome": {
                "status": "Geweigerd",
                "decision": "weigeren",
                "note": decision.get("note", ""),
                "timeline": "N.v.t.",
                "next_steps": ["Claim afgewezen door jurist", "Klant wordt geïnformeerd"]
            }})
            claim["status"] = "weigered"
            await queue.put({"type": "end"})
            return

        context["jurist_decision"] = decision["decision"]
        context["jurist_note"] = decision.get("note", "")

        # Run post-jurist agents
        post_jurist = ["strategie", "communicatie", "afhandeling"]
        for agent_name in post_jurist:
            claim["current_agent"] = agent_name
            await queue.put({"type": "agent_start", "agent": agent_name, "label": AGENT_SEQUENCE[agent_name]["label"]})
            result = await run_agent(agent_name, claim_data, context, queue, use_mock=USE_MOCK)
            claim["outputs"][agent_name] = result
            context[agent_name] = result
            await queue.put({"type": "agent_complete", "agent": agent_name, "result": result})

        claim["status"] = "complete"
        outcome_status = "Goedgekeurd" if decision["decision"] == "goedkeuren" else "Geëscaleerd"
        await queue.put({"type": "flow_complete", "outcome": {
            "status": outcome_status,
            "decision": decision["decision"],
            "note": decision.get("note", ""),
            "timeline": "6-8 weken",
            "next_steps": [
                "Bezwaarbrief opstellen",
                "Contact opnemen met wederpartij",
                "Dossier toewijzen aan behandelaar"
            ]
        }})
        await queue.put({"type": "end"})

    except Exception as e:
        await queue.put({"type": "error", "message": str(e)})
        await queue.put({"type": "end"})
        claim["status"] = "error"


@app.get("/stream/{claim_id}")
async def stream_claim(claim_id: str):
    if claim_id not in claims:
        return HTMLResponse("Claim niet gevonden", status_code=404)

    async def event_generator():
        queue = claims[claim_id]["queue"]
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=60.0)
                data = json.dumps(msg)
                yield f"data: {data}\n\n"
                if msg.get("type") == "end":
                    break
            except asyncio.TimeoutError:
                yield "data: {\"type\": \"ping\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.post("/jurist-decision/{claim_id}")
async def jurist_decision(claim_id: str, decision: JuristDecision):
    if claim_id not in claims:
        return {"error": "Claim niet gevonden"}
    claim = claims[claim_id]
    claim["jurist_decision"] = decision.dict()
    claim["jurist_event"].set()
    return {"status": "ok", "decision": decision.decision}
