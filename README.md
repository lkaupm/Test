# ARAG Agentic Claimsflow — Proof of Concept

Een end-to-end multi-agent demonstratie van het claimsafhandelingsproces bij ARAG Rechtsbijstand.

## Wat is dit?

Deze PoC toont hoe AI-agents samenwerken om een juridische claim van intake tot afhandeling te verwerken, met een menselijke jurist als checkpoint.

## De 7-Agent Flow

```
📥 Claim Binnenkomst
    ↓
🤖 Intake Agent         — Analyseert claim, bepaalt rechtsgebied & urgentie
    ↓
🔍 Dekkingscheck Agent  — Controleert polisdekking en uitsluitingen
    ↓
⚖️ Juridisch Agent      — Beoordeelt juridische merites en slagingskans
    ↓
👤 JURIST CHECKPOINT    — Menselijke beslissing: goedkeuren / escaleren / weigeren
    ↓
📋 Strategie Agent      — Stelt behandelstrategie op
    ↓
✉️ Communicatie Agent   — Stelt brieven op aan klant en wederpartij
    ↓
📁 Afhandeling Agent    — Maakt dossiersamenvatting
    ↓
✅ Uitkomst
```

## Quick Start

### Installatie

```bash
cd /home/user/Test
pip install -r arag_poc/requirements.txt
```

### Demo Mode (geen API key vereist)

```bash
uvicorn arag_poc.app:app --reload
```

Open http://localhost:8000 in uw browser.

### Echte Claude API (optioneel)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn arag_poc.app:app --reload
```

## Mock Mode vs. Echte API

| | Mock Mode | Echte API |
|---|---|---|
| API key | Niet vereist | Vereist |
| Responses | Voorgedefinieerde voorbeeldteksten | Claude claude-sonnet-4-6 |
| Kosten | Gratis | Standaard API-tarieven |
| Demo | Ideaal voor presentaties | Ideaal voor productie-demo |

## Voorbeeldclaims

De UI bevat drie voorbeeldclaims:
1. **Arbeidsrecht** — Ontslag op staande voet zonder bewijs
2. **Huurrecht** — Defecte cv-ketel, verhuurder in gebreke
3. **Consumentenrecht** — Non-conforme auto, dealer aansprakelijk

## Technische Stack

- **Backend**: FastAPI + uvicorn
- **Streaming**: Server-Sent Events (SSE)
- **Frontend**: Vanilla JS + CSS Grid
- **AI**: Anthropic Claude claude-sonnet-4-6 (optioneel)
- **Templates**: Jinja2
