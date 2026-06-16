# ARAG Agentic Claimsflow — Proof of Concept

Een visuele showcase simulatie van de toekomstige agent-gedreven claimsbehandeling bij ARAG Rechtsbijstand.

## Overzicht

Deze PoC demonstreert een end-to-end claimsflow met 7 gespecialiseerde AI agents:

| Agent | Rol |
|-------|-----|
| 🤖 Intake Agent | Categorisering, rechtsgebied, urgentie |
| 🔍 Dekkingscheck Agent | Polis/dekking verificatie |
| ⚖️ Juridisch Beoordelaar | Juridische merites, slagingskans |
| 👤 **Jurist Review** | **Menselijk checkpoint — go/no-go** |
| 📋 Strategie Agent | Behandelstrategie en tijdlijn |
| ✉️ Communicatie Agent | Klant- en wederpartijbrieven |
| 📁 Afhandeling Agent | Dossierafronding, volgende stappen |

## Installatie

```bash
cd arag_poc
pip install -r requirements.txt
```

## Starten

**Demo modus** (geen API key nodig, realistische mock-antwoorden):
```bash
cd /pad/naar/project
uvicorn arag_poc.app:app --reload
```

**Live AI modus** (echte Claude API):
```bash
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn arag_poc.app:app --reload
```

Open: http://localhost:8000

## Gebruik

1. Vul een claim in of gebruik een voorbeeldclaim (arbeidsrecht, huurrecht, consumentenrecht)
2. Klik **Claim Indienen** — agents starten real-time
3. Volg de voortgang in de flow-diagram en agent log
4. Bij de **Jurist Review** stap: kies Goedkeuren / Escaleren / Weigeren
5. De resterende agents verwerken de claim op basis van de beslissing
6. Eindresultaat verschijnt onderaan de flow

## Technische opzet

- **Backend**: FastAPI + asyncio + Server-Sent Events (SSE)
- **Frontend**: Vanilla JS + CSS animations
- **AI**: Anthropic Claude claude-sonnet-4-6 (of mock in demo modus)
- **State**: In-memory (PoC scope)
