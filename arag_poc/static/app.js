let claimId = null;
let eventSource = null;
let timerInterval = null;
let startTime = null;
let agentCount = 0;
const TOTAL_AGENTS = 11;

const SAMPLE_DATA = {
    arbeidsrecht: {
        type: "arbeidsrecht",
        desc: "Ik werk al 8 jaar bij Bouwbedrijf De Vries BV en ben afgelopen vrijdag op staande voet ontslagen. Mijn leidinggevende beschuldigde mij van het stelen van gereedschap ter waarde van €300. Ik heb dit niet gedaan en er is geen bewijs. Ik heb geen ontslagbrief ontvangen met onderbouwing."
    },
    huurrecht: {
        type: "huurrecht",
        desc: "Mijn verhuurder heeft mijn huur per 1 april verhoogd van €875 naar €1.050 per maand. Dat is een verhoging van €175, ruim 20%. Ik huur al 6 jaar dit appartement in Amsterdam. Mijn vrienden zeggen dat dit wettelijk niet mag. Ik heb een brief van de verhuurder ontvangen maar geen toelichting op de berekening."
    },
    consumentenrecht: {
        type: "consumentenrecht",
        desc: "Ik heb 4 maanden geleden een wasmachine gekocht bij MediaMarkt voor €649. Na 3 maanden stopte het apparaat met werken. De winkel weigert reparatie of vervanging en zegt dat ik zelf maar een reparateur moet bellen. De fabrikant (Bosch) zegt dat het buiten garantie is, maar dat kan toch niet na 3 maanden?"
    }
};

function loadSample(type) {
    const data = SAMPLE_DATA[type];
    if (!data) return;
    document.getElementById('claimType').value = data.type;
    document.getElementById('claimDesc').value = data.desc;
    setTimeout(() => submitClaim(), 100);
}

function submitClaim() {
    document.getElementById('claimForm').dispatchEvent(new Event('submit'));
}

document.getElementById('claimForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const claimType = document.getElementById('claimType').value;
    const description = document.getElementById('claimDesc').value;
    if (!claimType || !description) return;

    // Reset UI
    resetFlow();

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> Bezig...';

    try {
        const resp = await fetch('/claim', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ claim_type: claimType, description })
        });
        const data = await resp.json();
        claimId = data.claim_id;

        // Show stats
        document.getElementById('statsBar').style.display = 'flex';
        startTimer();

        // Start SSE
        startSSE();
    } catch (err) {
        addLog('Fout bij indienen claim: ' + err.message, 'system');
        btn.disabled = false;
        btn.innerHTML = '<span>🚀</span> Claim Indienen';
    }
});

function resetFlow() {
    // Stop existing SSE
    if (eventSource) { eventSource.close(); eventSource = null; }
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }

    agentCount = 0;
    document.getElementById('agentCounter').textContent = '0/11 agenten';
    document.getElementById('statsBar').style.display = 'none';

    // Reset phase tabs
    document.querySelectorAll('.phase-tab').forEach(t => t.classList.remove('active', 'done'));

    // Clear flow
    const fc = document.getElementById('flowContainer');
    fc.innerHTML = '';
    const empty = document.createElement('div');
    empty.className = 'flow-empty';
    empty.id = 'flowEmpty';
    empty.innerHTML = '<div class="flow-empty-icon">⚡</div><div>Dien een claim in om de agentic flow te starten</div>';
    fc.appendChild(empty);

    // Clear log
    const lp = document.getElementById('logPanel');
    lp.innerHTML = '<div class="log-entry system">Systeem gereed. Verwerking gestart...</div>';
}

function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById('timerDisplay').textContent = '⏱ ' + elapsed + 's';
    }, 1000);
}

function startSSE() {
    eventSource = new EventSource('/stream/' + claimId);

    eventSource.onmessage = (e) => {
        try {
            const msg = JSON.parse(e.data);
            handleMessage(msg);
        } catch (err) {
            console.error('Parse error:', err);
        }
    };

    eventSource.onerror = (e) => {
        addLog('Verbinding verbroken', 'system');
    };
}

// Track current text for each agent
const agentTexts = {};

function handleMessage(msg) {
    const { type } = msg;

    if (type === 'ping') return;

    if (type === 'phase_start') {
        handlePhaseStart(msg);
    } else if (type === 'agent_start') {
        handleAgentStart(msg);
    } else if (type === 'agent_chunk') {
        handleAgentChunk(msg);
    } else if (type === 'agent_complete') {
        handleAgentComplete(msg);
    } else if (type === 'sub_agent_start') {
        handleSubAgentStart(msg);
    } else if (type === 'sub_agent_chunk') {
        handleSubAgentChunk(msg);
    } else if (type === 'sub_agent_complete') {
        handleSubAgentComplete(msg);
    } else if (type === 'jurist_checkpoint') {
        handleJuristCheckpoint(msg);
    } else if (type === 'checkpoint_decided') {
        handleCheckpointDecided(msg);
    } else if (type === 'flow_complete') {
        handleFlowComplete(msg);
    } else if (type === 'end') {
        handleEnd();
    }
}

function handlePhaseStart(msg) {
    const { phase, label } = msg;

    // Remove empty state
    const empty = document.getElementById('flowEmpty');
    if (empty) empty.remove();

    // Update phase tab
    document.querySelectorAll('.phase-tab').forEach(t => {
        if (t.dataset.phase === phase) t.classList.add('active');
    });

    // Create phase section
    const section = document.createElement('div');
    section.className = `phase-section phase-${phase}`;
    section.id = `phase-${phase}`;

    const phaseLabels = { intake: '📥', assessment: '⚖️', handling: '📤' };
    section.innerHTML = `
        <div class="phase-section-header">
            <span>${phaseLabels[phase] || '📋'}</span>
            <span>${label}</span>
        </div>
        <div class="phase-section-body" id="phase-body-${phase}"></div>
    `;

    document.getElementById('flowContainer').appendChild(section);
    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    addLog(`=== ${label} ===`, 'phase');

    // Re-enable submit button
    const btn = document.getElementById('submitBtn');
    btn.disabled = false;
    btn.innerHTML = '<span>🚀</span> Claim Indienen';
}

function handleAgentStart(msg) {
    const { agent_id, label, icon, phase } = msg;

    // Check if node already exists (agent_start fires after sub_agents complete)
    let node = document.getElementById(`agent-${agent_id}`);
    if (!node) {
        node = document.createElement('div');
        node.className = 'agent-node';
        node.id = `agent-${agent_id}`;

        node.innerHTML = `
            <div class="agent-node-header">
                <span class="agent-icon">${icon}</span>
                <span class="agent-label">${label}</span>
                <span class="agent-status running" id="status-${agent_id}">Actief</span>
            </div>
            <div class="agent-preview" id="preview-${agent_id}"></div>
            <button class="agent-expand-btn" id="expand-${agent_id}" onclick="toggleExpand('${agent_id}')">Meer tonen ▼</button>
        `;

        const body = document.getElementById(`phase-body-${phase}`);
        if (body) body.appendChild(node);

        // Add sub-agents container placeholder after this node
        const subContainer = document.createElement('div');
        subContainer.className = 'sub-agents-container';
        subContainer.id = `sub-container-${agent_id}`;
        if (body) body.appendChild(subContainer);
    }

    node.classList.add('active');
    const statusEl = document.getElementById(`status-${agent_id}`);
    if (statusEl) { statusEl.className = 'agent-status running'; statusEl.textContent = 'Actief'; }

    agentTexts[agent_id] = '';
    addLog(`${icon} ${label} gestart`, phase);
    node.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleAgentChunk(msg) {
    const { agent_id, chunk } = msg;
    agentTexts[agent_id] = (agentTexts[agent_id] || '') + chunk;
    const preview = document.getElementById(`preview-${agent_id}`);
    if (preview) {
        preview.textContent = agentTexts[agent_id];
        const expandBtn = document.getElementById(`expand-${agent_id}`);
        if (expandBtn && agentTexts[agent_id].length > 150) expandBtn.style.display = 'block';
    }
}

function handleAgentComplete(msg) {
    const { agent_id, phase } = msg;
    agentCount++;
    document.getElementById('agentCounter').textContent = agentCount + '/' + TOTAL_AGENTS + ' agenten';

    const node = document.getElementById(`agent-${agent_id}`);
    if (node) { node.classList.remove('active'); node.classList.add('complete'); }

    const statusEl = document.getElementById(`status-${agent_id}`);
    if (statusEl) { statusEl.className = 'agent-status done'; statusEl.textContent = 'Klaar'; }

    addLog(`✓ Klaar`, phase);
}

function handleSubAgentStart(msg) {
    const { agent_id, parent_id, label, icon, phase } = msg;

    // Ensure parent agent node exists
    if (!document.getElementById(`agent-${parent_id}`)) {
        // Create placeholder
        const body = document.getElementById(`phase-body-${phase}`);
        if (body) {
            const node = document.createElement('div');
            node.className = 'agent-node';
            node.id = `agent-${parent_id}`;
            node.innerHTML = `
                <div class="agent-node-header">
                    <span class="agent-icon">🤖</span>
                    <span class="agent-label">${parent_id}</span>
                    <span class="agent-status running" id="status-${parent_id}">Actief</span>
                </div>
                <div class="agent-preview" id="preview-${parent_id}"></div>
                <button class="agent-expand-btn" id="expand-${parent_id}" onclick="toggleExpand('${parent_id}')">Meer tonen ▼</button>
            `;
            body.appendChild(node);

            const subContainer = document.createElement('div');
            subContainer.className = 'sub-agents-container';
            subContainer.id = `sub-container-${parent_id}`;
            body.appendChild(subContainer);
        }
    }

    // Create sub-agent node
    const subNode = document.createElement('div');
    subNode.className = 'sub-agent-node';
    subNode.id = `sub-agent-${agent_id}`;
    subNode.innerHTML = `
        <div class="sub-agent-header">
            <span class="sub-agent-icon">${icon}</span>
            <span class="sub-agent-label">${label}</span>
            <span class="sub-agent-status running" id="sub-status-${agent_id}">Actief</span>
        </div>
        <div class="sub-agent-preview" id="sub-preview-${agent_id}"></div>
    `;

    const container = document.getElementById(`sub-container-${parent_id}`);
    if (container) container.appendChild(subNode);

    agentTexts['sub_' + agent_id] = '';
    addLog(`${icon} ${label}`, 'sub-agent');
    subNode.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleSubAgentChunk(msg) {
    const { agent_id, chunk } = msg;
    const key = 'sub_' + agent_id;
    agentTexts[key] = (agentTexts[key] || '') + chunk;
    const preview = document.getElementById(`sub-preview-${agent_id}`);
    if (preview) preview.textContent = agentTexts[key];
}

function handleSubAgentComplete(msg) {
    const { agent_id } = msg;
    agentCount++;
    document.getElementById('agentCounter').textContent = agentCount + '/' + TOTAL_AGENTS + ' agenten';

    const node = document.getElementById(`sub-agent-${agent_id}`);
    if (node) { node.classList.remove('active'); node.classList.add('complete'); }

    const statusEl = document.getElementById(`sub-status-${agent_id}`);
    if (statusEl) { statusEl.className = 'sub-agent-status done'; statusEl.textContent = '✓'; }
}

function handleJuristCheckpoint(msg) {
    const { checkpoint, title, description, summary } = msg;

    const checkpointNode = document.createElement('div');
    checkpointNode.className = 'checkpoint-node';
    checkpointNode.id = `checkpoint-${checkpoint}`;

    // Build summary text
    let summaryText = '';
    if (summary.transcription_summary) summaryText += `📝 Transcriptie: ${summary.transcription_summary}\n\n`;
    if (summary.coverage_status) summaryText += `🔍 Coverage: ${summary.coverage_status}\n\n`;
    if (summary.key_facts) summaryText += `🔑 Feiten: ${summary.key_facts}\n\n`;
    if (summary.legal_analysis) summaryText += `⚖️ Juridisch: ${summary.legal_analysis}\n\n`;
    if (summary.letter_preview) summaryText += `✉️ Brief: ${summary.letter_preview}\n\n`;
    if (summary.legal_drafting_preview) summaryText += `📄 Processtuk: ${summary.legal_drafting_preview}`;

    checkpointNode.innerHTML = `
        <div class="checkpoint-title">🛑 ${title}</div>
        <div class="checkpoint-desc">${description}</div>
        <div class="checkpoint-summary">${summaryText.trim()}</div>
        <div class="checkpoint-actions" id="cp-actions-${checkpoint}">
            <button class="checkpoint-btn approve" onclick="approveCheckpoint(${checkpoint})">✅ Goedkeuren</button>
            <button class="checkpoint-btn adjust" onclick="showAdjustFeedback(${checkpoint})">✏️ Aanpassen</button>
            <button class="checkpoint-btn escalate" onclick="escalateCheckpoint(${checkpoint})">⬆️ Escaleren</button>
        </div>
        <div class="feedback-area" id="feedback-area-${checkpoint}">
            <textarea id="feedback-text-${checkpoint}" placeholder="Voer uw aanpassingsverzoek in..."></textarea>
            <button class="feedback-submit" onclick="submitAdjustFeedback(${checkpoint})">Verstuur aanpassing</button>
        </div>
    `;

    document.getElementById('flowContainer').appendChild(checkpointNode);
    checkpointNode.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    addLog(`🛑 Checkpoint ${checkpoint}: Wacht op juristbeslissing`, 'checkpoint');
}

function handleCheckpointDecided(msg) {
    const { checkpoint, decision } = msg;
    const node = document.getElementById(`checkpoint-${checkpoint}`);
    if (!node) return;

    node.classList.add('decided');

    const actions = document.getElementById(`cp-actions-${checkpoint}`);
    const decisionLabels = { goedgekeurd: '✅ Goedgekeurd', aanpassen: '✏️ Aangepast', escaleren: '⬆️ Geëscaleerd' };
    const decisionClasses = { goedgekeurd: 'approved', aanpassen: 'adjusted', escaleren: 'escalated' };

    if (actions) {
        actions.innerHTML = `<span class="checkpoint-decision-badge ${decisionClasses[decision] || 'approved'}">${decisionLabels[decision] || decision}</span>`;
    }

    const feedbackArea = document.getElementById(`feedback-area-${checkpoint}`);
    if (feedbackArea) feedbackArea.style.display = 'none';

    addLog(`✓ Checkpoint ${checkpoint} besloten: ${decision}`, 'checkpoint');
}

function handleFlowComplete(msg) {
    const outcomeCard = document.createElement('div');
    outcomeCard.className = 'outcome-card';
    outcomeCard.innerHTML = `
        <h3>🎉 Claimafhandeling Voltooid</h3>
        <p>Alle ${TOTAL_AGENTS} agenten hebben de claim succesvol verwerkt. Documenten zijn gereed voor verzending.</p>
    `;
    document.getElementById('flowContainer').appendChild(outcomeCard);
    outcomeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Mark all phases done
    document.querySelectorAll('.phase-tab').forEach(t => { t.classList.remove('active'); t.classList.add('done'); });

    addLog('🎉 Claimafhandeling volledig afgerond', 'success');
}

function handleEnd() {
    if (eventSource) { eventSource.close(); eventSource = null; }
    if (timerInterval) { clearInterval(timerInterval); }
}

function approveCheckpoint(checkpoint) {
    submitJuristDecision(checkpoint, 'goedgekeurd', '');
}

function showAdjustFeedback(checkpoint) {
    const area = document.getElementById(`feedback-area-${checkpoint}`);
    if (area) area.style.display = 'block';
}

function submitAdjustFeedback(checkpoint) {
    const text = document.getElementById(`feedback-text-${checkpoint}`)?.value || '';
    submitJuristDecision(checkpoint, 'aanpassen', text);
}

function escalateCheckpoint(checkpoint) {
    submitJuristDecision(checkpoint, 'escaleren', '');
}

async function submitJuristDecision(checkpoint, decision, note) {
    // Disable buttons
    const actions = document.getElementById(`cp-actions-${checkpoint}`);
    if (actions) actions.querySelectorAll('button').forEach(b => b.disabled = true);

    try {
        await fetch(`/jurist-decision/${claimId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ checkpoint, decision, note })
        });
    } catch (err) {
        addLog('Fout bij verzenden beslissing: ' + err.message, 'system');
    }
}

function toggleExpand(agentId) {
    const preview = document.getElementById(`preview-${agentId}`);
    const btn = document.getElementById(`expand-${agentId}`);
    if (!preview || !btn) return;
    if (preview.classList.contains('expanded')) {
        preview.classList.remove('expanded');
        btn.textContent = 'Meer tonen ▼';
    } else {
        preview.classList.add('expanded');
        btn.textContent = 'Minder tonen ▲';
    }
}

function addLog(message, type) {
    const lp = document.getElementById('logPanel');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type || ''}`;
    entry.textContent = message;
    lp.appendChild(entry);
    lp.scrollTop = lp.scrollHeight;
}

function clearLog() {
    document.getElementById('logPanel').innerHTML = '<div class="log-entry system">Log gewist.</div>';
}
