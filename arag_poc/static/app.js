const SAMPLE_CLAIMS = [
  {
    naam: "Piet Janssen",
    polisnummer: "ARAG-2024-88123",
    claim_type: "Arbeidsrecht",
    omschrijving: "Ik ben op staande voet ontslagen wegens diefstal, maar ik heb niets gestolen. Mijn werkgever bij Bouwbedrijf De Vries BV geeft geen enkel bewijs en weigert te reageren op mijn verzoek om toelichting. Ik werk al 8 jaar bij dit bedrijf en heb altijd goed gefunctioneerd.",
    belang: "45000",
    wederpartij: "Bouwbedrijf De Vries BV",
  },
  {
    naam: "Maria Garcia",
    polisnummer: "ARAG-2024-55234",
    claim_type: "Huurrecht",
    omschrijving: "Mijn verhuurder weigert de cv-ketel te repareren al 3 maanden. Inmiddels is het winter en is de woning onbewoonbaar. Ik heb hem meerdere keren schriftelijk en mondeling verzocht om actie te ondernemen maar hij reageert niet.",
    belang: "8000",
    wederpartij: "Vastgoed Beheer Utrecht",
  },
  {
    naam: "Tom Bakker",
    polisnummer: "ARAG-2024-71892",
    claim_type: "Consumentenrecht",
    omschrijving: "Ik heb een auto gekocht voor €18.500 bij AutoDeal Rotterdam. Na slechts 2 weken rijden staat de auto vast wegens ernstige motorschade. De dealer weigert elke aansprakelijkheid en beweert dat ik het zelf veroorzaakt heb, wat aantoonbaar onjuist is.",
    belang: "18500",
    wederpartij: "AutoDeal Rotterdam",
  },
];

const AGENT_ORDER = ["intake", "dekkingscheck", "juridisch", "jurist", "strategie", "communicatie", "afhandeling"];
const TOTAL_STEPS = 7;

let currentClaimId = null;
let eventSource = null;
let logEntries = {};
let currentAgent = null;
let stepsCompleted = 0;

function updateProgress(steps) {
  const pct = Math.round((steps / TOTAL_STEPS) * 100);
  document.getElementById("progress-fill").style.width = pct + "%";
  document.getElementById("progress-pct").textContent = pct + "%";
}

function setNodeState(nodeId, state) {
  const node = document.getElementById("node-" + nodeId);
  if (!node) return;
  node.className = "flow-node " + state;
  const statusEl = node.querySelector(".node-status");
  const states = {
    waiting: "Wachtend",
    active: "⏳ Bezig...",
    done: "✓ Voltooid",
    error: "✗ Fout",
  };
  if (statusEl) statusEl.textContent = states[state] || "";

  const connector = document.getElementById("conn-" + nodeId);
  if (connector) {
    connector.className = "flow-connector " + (state === "done" ? "done" : state === "active" ? "active" : "");
  }
}

function addLogEntry(agentKey, agentLabel) {
  const container = document.getElementById("log-container");
  const emptyState = container.querySelector(".empty-state");
  if (emptyState) emptyState.remove();

  const ts = new Date().toLocaleTimeString("nl-NL");
  const entry = document.createElement("div");
  entry.className = `log-entry agent-${agentKey}`;
  entry.id = `log-${agentKey}`;
  entry.innerHTML = `
    <div class="log-entry-header">
      <span class="log-agent-name">${agentLabel}</span>
      <span class="log-timestamp">${ts}</span>
    </div>
    <div class="log-text" id="log-text-${agentKey}"><span class="cursor"></span></div>
  `;
  container.appendChild(entry);
  container.scrollTop = container.scrollHeight;
  logEntries[agentKey] = "";
}

function appendLogText(agentKey, text) {
  const el = document.getElementById("log-text-" + agentKey);
  if (!el) return;
  logEntries[agentKey] = (logEntries[agentKey] || "") + text;
  // Remove cursor, update text, re-add cursor
  el.innerHTML = escapeHtml(logEntries[agentKey]) + '<span class="cursor"></span>';
  const container = document.getElementById("log-container");
  container.scrollTop = container.scrollHeight;
}

function finalizeLogText(agentKey) {
  const el = document.getElementById("log-text-" + agentKey);
  if (!el) return;
  el.innerHTML = formatMarkdown(logEntries[agentKey] || "");
}

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatMarkdown(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function showJuristPanel(summary) {
  setNodeState("jurist", "active");
  stepsCompleted = 3;
  updateProgress(stepsCompleted);

  addLogEntry("jurist", "👤 Jurist Review");
  appendLogText("jurist", "⚠️ Wachten op beoordeling door jurist...\n\nSamenvatting vorige agents:\n");

  const summaryText = Object.entries(summary)
    .map(([k, v]) => `[${k.toUpperCase()}]\n${v.substring(0, 200)}...`)
    .join("\n\n");
  appendLogText("jurist", summaryText);

  const panel = document.getElementById("jurist-panel");
  panel.classList.add("visible");

  const summaryEl = document.getElementById("jurist-summary");
  summaryEl.textContent = Object.entries(summary)
    .map(([k, v]) => `▶ ${k.toUpperCase()}\n${v.substring(0, 300)}`)
    .join("\n\n---\n\n");
}

function hideJuristPanel() {
  document.getElementById("jurist-panel").classList.remove("visible");
}

async function sendJuristDecision(decision) {
  const note = document.getElementById("jurist-note").value;

  finalizeLogText("jurist");
  const el = document.getElementById("log-text-jurist");
  if (el) {
    el.innerHTML += `<br><br><strong>Beslissing: ${decision.toUpperCase()}</strong>${note ? `<br>Toelichting: ${escapeHtml(note)}` : ""}`;
  }

  await fetch(`/jurist-decision/${currentClaimId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, note }),
  });

  hideJuristPanel();

  if (decision === "weigeren") {
    setNodeState("jurist", "error");
  } else {
    setNodeState("jurist", "done");
    stepsCompleted = 4;
    updateProgress(stepsCompleted);
  }
}

function showOutcomeCard(outcome) {
  const card = document.getElementById("outcome-card");
  const cls = outcome.status_class || "success";
  card.querySelector(".outcome-header").className = `outcome-header ${cls}`;
  card.querySelector(".outcome-status").textContent =
    cls === "success" ? "✅ " + outcome.status :
    cls === "warning" ? "⚠️ " + outcome.status : "❌ " + outcome.status;
  card.querySelector(".outcome-subtitle").textContent = outcome.beslissing;

  const body = card.querySelector(".outcome-body");
  body.innerHTML = `
    ${outcome.reden ? `<div class="outcome-row"><span class="outcome-label">Toelichting:</span><span>${escapeHtml(outcome.reden)}</span></div>` : ""}
    <div class="outcome-row"><span class="outcome-label">Tijdlijn:</span><span>${escapeHtml(outcome.timeline)}</span></div>
    <div class="outcome-steps">
      <strong style="font-size:12px;color:var(--gray-600);">VOLGENDE STAPPEN:</strong>
      <ul>${(outcome.next_steps || []).map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
    </div>
  `;

  card.classList.add("visible");
  card.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function submitClaim(e) {
  e.preventDefault();

  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Verwerken...';

  // Reset UI
  AGENT_ORDER.forEach(a => setNodeState(a, "waiting"));
  document.getElementById("log-container").innerHTML = '<div class="empty-state"><div class="icon">📋</div><span>Verbinding maken met agents...</span></div>';
  document.getElementById("outcome-card").classList.remove("visible");
  document.getElementById("jurist-panel").classList.remove("visible");
  document.getElementById("jurist-note").value = "";
  logEntries = {};
  stepsCompleted = 0;
  updateProgress(0);

  const formData = {
    naam: document.getElementById("naam").value,
    polisnummer: document.getElementById("polisnummer").value,
    claim_type: document.getElementById("claim_type").value,
    omschrijving: document.getElementById("omschrijving").value,
    belang: document.getElementById("belang").value,
    wederpartij: document.getElementById("wederpartij").value,
  };

  const res = await fetch("/submit-claim", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });
  const { claim_id } = await res.json();
  currentClaimId = claim_id;

  if (eventSource) eventSource.close();
  eventSource = new EventSource(`/stream/${claim_id}`);

  const AGENT_LABELS = {
    intake: "🤖 Intake Agent",
    dekkingscheck: "🔍 Dekkingscheck Agent",
    juridisch: "⚖️ Juridisch Beoordelaar",
    strategie: "📋 Strategie Agent",
    communicatie: "✉️ Communicatie Agent",
    afhandeling: "📁 Afhandeling Agent",
  };

  eventSource.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === "keepalive") return;

    if (msg.type === "agent_start") {
      currentAgent = msg.agent;
      setNodeState(msg.agent, "active");
      addLogEntry(msg.agent, AGENT_LABELS[msg.agent] || msg.label);
    }

    if (msg.type === "agent_chunk") {
      appendLogText(msg.agent, msg.text);
    }

    if (msg.type === "agent_complete") {
      finalizeLogText(msg.agent);
      setNodeState(msg.agent, "done");
      stepsCompleted = Math.min(stepsCompleted + 1, 3);
      if (!["strategie", "communicatie", "afhandeling"].includes(msg.agent)) {
        updateProgress(stepsCompleted);
      } else {
        stepsCompleted = Math.min(stepsCompleted + 1, TOTAL_STEPS);
        updateProgress(stepsCompleted);
      }
    }

    if (msg.type === "jurist_checkpoint") {
      showJuristPanel(msg.summary);
    }

    if (msg.type === "jurist_decided") {
      // handled in sendJuristDecision
    }

    if (msg.type === "flow_escalated") {
      addLogEntry("system", "🔀 Systeemmelding");
      appendLogText("system", `⚠️ Zaak geëscaleerd door jurist.\nToelichting: ${msg.note || "Geen"}\n\nFlow gaat door met hogere prioriteit.`);
      finalizeLogText("system");
    }

    if (msg.type === "flow_complete") {
      updateProgress(TOTAL_STEPS);
      showOutcomeCard(msg.outcome);
      btn.disabled = false;
      btn.innerHTML = "🚀 Nieuwe Claim Indienen";
      eventSource.close();
    }

    if (msg.type === "flow_error") {
      addLogEntry("system", "❌ Systeemfout");
      appendLogText("system", msg.message);
      finalizeLogText("system");
      btn.disabled = false;
      btn.innerHTML = "🚀 Claim Indienen";
      eventSource.close();
    }
  };

  eventSource.onerror = () => {
    btn.disabled = false;
    btn.innerHTML = "🚀 Claim Indienen";
  };
}

function loadSample(idx) {
  const s = SAMPLE_CLAIMS[idx];
  document.getElementById("naam").value = s.naam;
  document.getElementById("polisnummer").value = s.polisnummer;
  document.getElementById("claim_type").value = s.claim_type;
  document.getElementById("omschrijving").value = s.omschrijving;
  document.getElementById("belang").value = s.belang;
  document.getElementById("wederpartij").value = s.wederpartij;
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("claim-form").addEventListener("submit", submitClaim);

  document.querySelectorAll(".sample-btn").forEach((btn, i) => {
    btn.addEventListener("click", () => loadSample(i));
  });

  document.getElementById("btn-goedkeuren").addEventListener("click", () => sendJuristDecision("goedkeuren"));
  document.getElementById("btn-escaleren").addEventListener("click", () => sendJuristDecision("escaleren"));
  document.getElementById("btn-weigeren").addEventListener("click", () => sendJuristDecision("weigeren"));
});
