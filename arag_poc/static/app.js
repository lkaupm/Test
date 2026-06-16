const AGENT_ICONS = {
    intake: '🤖',
    dekkingscheck: '🔍',
    juridisch: '⚖️',
    strategie: '📋',
    communicatie: '✉️',
    afhandeling: '📁',
};

const AGENT_LABELS = {
    intake: 'Intake Agent',
    dekkingscheck: 'Dekkingscheck Agent',
    juridisch: 'Juridisch Beoordelingsagent',
    strategie: 'Strategie Agent',
    communicatie: 'Communicatie Agent',
    afhandeling: 'Afhandeling Agent',
};

let currentClaimId = null;
let isRunning = false;
let currentLogEntry = null;

const SAMPLES = {
    arbeidsrecht: {
        naam: 'Piet Janssen',
        polisnummer: 'ARAG-2024-88123',
        type_claim: 'arbeidsrecht',
        omschrijving: 'Ik ben op staande voet ontslagen wegens diefstal, maar ik heb niets gestolen. Mijn werkgever weigert enig bewijs te tonen.',
        belang: '45000',
        wederpartij: 'Bouwbedrijf De Vries BV',
    },
    huurrecht: {
        naam: 'Maria Garcia',
        polisnummer: 'ARAG-2024-55234',
        type_claim: 'huurrecht',
        omschrijving: 'Mijn verhuurder weigert de cv-ketel te repareren al 3 maanden. Inmiddels is het winter en is de woning onbewoonbaar.',
        belang: '8000',
        wederpartij: 'Vastgoed Beheer Utrecht',
    },
    consumentenrecht: {
        naam: 'Tom Bakker',
        polisnummer: 'ARAG-2024-71892',
        type_claim: 'consumentenrecht',
        omschrijving: 'Ik heb een auto gekocht voor €18.500 maar na 2 weken staat hij vast wegens motorschade. Dealer weigert elke aansprakelijkheid.',
        belang: '18500',
        wederpartij: 'AutoDeal Rotterdam',
    },
};

function loadSample(type) {
    const s = SAMPLES[type];
    if (!s) return;
    document.getElementById('naam').value = s.naam;
    document.getElementById('polisnummer').value = s.polisnummer;
    document.getElementById('type_claim').value = s.type_claim;
    document.getElementById('omschrijving').value = s.omschrijving;
    document.getElementById('belang').value = s.belang;
    document.getElementById('wederpartij').value = s.wederpartij;
}

function setNodeState(agent, state) {
    const node = document.querySelector(`[data-agent="${agent}"]`);
    if (!node) return;
    node.className = 'flow-node';
    if (node.dataset.agent === 'jurist') node.classList.add('node-human');
    node.classList.add(`node-${state}`);
    const statusIcon = node.querySelector('.node-status-icon');
    if (statusIcon) statusIcon.textContent = '';
}

function addLogEntry(agent, label, icon) {
    const container = document.getElementById('logContainer');
    const placeholder = container.querySelector('.log-placeholder');
    if (placeholder) placeholder.remove();

    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.dataset.agent = agent;

    const now = new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    entry.innerHTML = `
        <div class="log-entry-header">
            <span>${icon || AGENT_ICONS[agent] || '🔄'}</span>
            <span>${label || AGENT_LABELS[agent] || agent}</span>
            <span class="ts">${now}</span>
        </div>
        <div class="log-entry-body"></div>
    `;
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
    currentLogEntry = entry.querySelector('.log-entry-body');
    return currentLogEntry;
}

function appendToLog(text) {
    if (!currentLogEntry) return;
    currentLogEntry.textContent += text;
    const container = document.getElementById('logContainer');
    container.scrollTop = container.scrollHeight;
}

function showJuristPanel(summary) {
    setNodeState('jurist', 'active');
    const panel = document.getElementById('juristPanel');
    const summaryDiv = document.getElementById('juristSummary');

    let html = '';
    for (const [key, val] of Object.entries(summary)) {
        const labels = { intake: '🤖 Intake', dekkingscheck: '🔍 Dekking', juridisch: '⚖️ Juridisch' };
        html += `<div class="summary-agent">${labels[key] || key}</div><div>${escapeHtml(val)}</div>`;
    }
    summaryDiv.innerHTML = html;
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    addLogEntry('system', 'Jurist Checkpoint', '👤');
    appendToLog('Wachten op jurist beslissing...');
}

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function submitJuristDecision(decision) {
    if (!currentClaimId) return;
    const note = document.getElementById('juristNote').value;

    const btns = document.querySelectorAll('.jurist-buttons .btn');
    btns.forEach(b => b.disabled = true);

    try {
        const res = await fetch(`/jurist-decision/${currentClaimId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision, note }),
        });

        document.getElementById('juristPanel').style.display = 'none';
        setNodeState('jurist', 'complete');

        addLogEntry('system', 'Jurist Beslissing', '👤');
        const decisionLabels = { goedkeuren: '✅ Goedgekeurd', escaleren: '⚠️ Geëscaleerd', weigeren: '❌ Geweigerd' };
        appendToLog(`Beslissing: ${decisionLabels[decision] || decision}${note ? '\nNotitie: ' + note : ''}`);
    } catch (e) {
        console.error(e);
        btns.forEach(b => b.disabled = false);
    }
}

function showOutcomeCard(outcome) {
    setNodeState('uitkomst', 'complete');
    const card = document.getElementById('outcomeCard');
    const header = document.getElementById('outcomeHeader');
    const body = document.getElementById('outcomeBody');

    const classMap = { goedkeuren: 'approved', escaleren: 'escalated', weigeren: 'rejected' };
    const emojiMap = { goedkeuren: '✅', escaleren: '⚠️', weigeren: '❌' };

    header.className = `outcome-header ${classMap[outcome.decision] || 'approved'}`;
    header.textContent = `${emojiMap[outcome.decision] || '✅'} ${outcome.status}`;

    let html = '';
    if (outcome.note) html += `<p><strong>Notitie:</strong> ${escapeHtml(outcome.note)}</p>`;
    if (outcome.timeline) html += `<p><strong>Tijdlijn:</strong> ${escapeHtml(outcome.timeline)}</p>`;
    if (outcome.next_steps && outcome.next_steps.length) {
        html += `<p><strong>Volgende stappen:</strong></p><ul>`;
        outcome.next_steps.forEach(s => { html += `<li>${escapeHtml(s)}</li>`; });
        html += '</ul>';
    }
    body.innerHTML = html;
    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function resetUI() {
    // Reset all nodes
    ['binnenkomst', 'intake', 'dekkingscheck', 'juridisch', 'jurist', 'strategie', 'communicatie', 'afhandeling', 'uitkomst'].forEach(a => setNodeState(a, 'waiting'));
    document.getElementById('juristPanel').style.display = 'none';
    document.getElementById('outcomeCard').style.display = 'none';
    document.getElementById('logContainer').innerHTML = '';
    document.getElementById('claimIdBadge').textContent = '';
    currentLogEntry = null;
}

document.getElementById('claimForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isRunning) return;

    resetUI();
    isRunning = true;

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Verwerken...';

    const formData = {
        naam: document.getElementById('naam').value,
        polisnummer: document.getElementById('polisnummer').value,
        type_claim: document.getElementById('type_claim').value,
        omschrijving: document.getElementById('omschrijving').value,
        belang: document.getElementById('belang').value,
        wederpartij: document.getElementById('wederpartij').value,
    };

    try {
        const res = await fetch('/submit-claim', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });
        const data = await res.json();
        currentClaimId = data.claim_id;

        document.getElementById('claimIdBadge').textContent = `#${currentClaimId}`;
        setNodeState('binnenkomst', 'complete');

        // Start SSE
        const evtSource = new EventSource(`/stream/${currentClaimId}`);

        evtSource.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            if (msg.type === 'ping') return;

            if (msg.type === 'agent_start') {
                setNodeState(msg.agent, 'active');
                addLogEntry(msg.agent, msg.label, AGENT_ICONS[msg.agent]);
            } else if (msg.type === 'agent_chunk') {
                appendToLog(msg.text);
            } else if (msg.type === 'agent_complete') {
                setNodeState(msg.agent, 'complete');
            } else if (msg.type === 'jurist_checkpoint') {
                showJuristPanel(msg.summary);
            } else if (msg.type === 'flow_complete') {
                showOutcomeCard(msg.outcome);
            } else if (msg.type === 'error') {
                addLogEntry('error', 'Fout', '❌');
                appendToLog(msg.message);
                isRunning = false;
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Claim Indienen';
            } else if (msg.type === 'end') {
                evtSource.close();
                isRunning = false;
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Nieuwe Claim';
            }
        };

        evtSource.onerror = () => {
            evtSource.close();
            isRunning = false;
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Claim Indienen';
        };

    } catch (err) {
        console.error(err);
        isRunning = false;
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Claim Indienen';
    }
});
