/**
 * AGT Network Dashboard — Frontend Logic
 *
 * Connects to the AGT API Server via REST + WebSocket.
 * Displays real-time node, agent, task, contribution, ledger, and reputation data.
 */

const API_BASE = window.location.origin;

// ============================================================
// State
// ============================================================

let nodeId = "connecting...";
let ws = null;
let autoRefreshInterval = null;

// ============================================================
// Initialization
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    connectWebSocket();
    refreshAll();
    autoRefreshInterval = setInterval(refreshAll, 5000);
});

// ============================================================
// WebSocket — Real-time events
// ============================================================

function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);
    ws.onopen = () => {
        document.getElementById("conn-status").innerHTML = "● Connected";
        document.getElementById("conn-status").style.color = "var(--green)";
        logEvent("connected", "Dashboard connected to AGT Node");
    };
    ws.onclose = () => {
        document.getElementById("conn-status").innerHTML = "● Disconnected";
        document.getElementById("conn-status").style.color = "var(--red)";
        setTimeout(connectWebSocket, 3000);
    };
    ws.onmessage = (e) => {
        try {
            const msg = JSON.parse(e.data);
            handleEvent(msg.type, msg.data);
        } catch (err) {
            // Ignore parse errors
        }
    };
    ws.onerror = () => {};
}

function handleEvent(type, data) {
    switch (type) {
        case "task_completed":
            logEvent("contribution", `Task completed: ${data.task_name || data.task_id}`);
            refreshContributions();
            refreshLedger();
            break;
        case "reward_issued":
            logEvent("reward", `AGT Credit issued: +${data.amount || data.reward_credit} → ${data.agent_id}`);
            refreshAll();
            break;
        case "proof_generated":
            logEvent("contribution", `PoI generated: ${data.proof_id} (score: ${data.contribution_score})`);
            refreshContributions();
            break;
        default:
            break;
    }
}

// ============================================================
// Data Fetching
// ============================================================

async function refreshAll() {
    await Promise.all([
        refreshNode(),
        refreshAgents(),
        refreshTasks(),
        refreshContributions(),
        refreshLedger(),
        refreshReputation(),
    ]);
}

async function refreshNode() {
    try {
        const r = await fetch(`${API_BASE}/api/node/status`);
        const data = await r.json();
        nodeId = data.node_id;
        document.getElementById("node-id-display").textContent = `Node: ${nodeId}`;
        document.getElementById("stat-peers").textContent = data.peers_count || 0;
    } catch (e) {
        // Node not ready
    }
}

async function refreshAgents() {
    try {
        const r = await fetch(`${API_BASE}/api/agents`);
        const agents = await r.json();
        document.getElementById("stat-agents").textContent = agents.length;
        document.getElementById("agent-count").textContent = agents.length;

        const panel = document.getElementById("agents-panel");
        if (!agents.length) {
            panel.innerHTML = '<div style="color:var(--dim);text-align:center;padding:20px;">No agents registered</div>';
            return;
        }

        panel.innerHTML = agents.map(a => {
            const repClass = getRepClass(a.reputation_level);
            const repPct = Math.min(100, (a.reputation / 1000) * 100);
            return `
            <div class="list-item">
                <div style="flex:1;">
                    <div style="font-weight:600;">${a.name}</div>
                    <div style="font-size:10px;color:var(--dim);">${a.agent_id}</div>
                    <div class="rep-bar"><div class="rep-bar-fill ${repClass}" style="width:${repPct}%;"></div></div>
                </div>
                <div style="text-align:right;font-size:11px;">
                    <div>${a.reputation.toFixed(0)} rep</div>
                    <div style="color:var(--dim);">${a.reputation_level}</div>
                    <div style="font-size:10px;">${a.tasks_completed} tasks | ${a.total_reward.toFixed(1)} AGT</div>
                </div>
            </div>`;
        }).join("");
    } catch (e) {
        // Agents not ready
    }
}

async function refreshTasks() {
    try {
        const r = await fetch(`${API_BASE}/api/tasks`);
        const tasks = await r.json();
        document.getElementById("stat-tasks").textContent = tasks.length;

        const panel = document.getElementById("tasks-panel");
        if (!tasks.length) {
            panel.innerHTML = '<div style="color:var(--dim);text-align:center;padding:20px;">No open tasks</div>';
            return;
        }

        panel.innerHTML = tasks.map(t => `
        <div class="list-item">
            <div style="flex:1;">
                <div style="font-weight:600;">${t.name}</div>
                <div style="font-size:10px;color:var(--dim);">${t.description.slice(0, 80)}...</div>
                <div style="margin-top:4px;">
                    <span class="tag tag-gen">${t.source}</span>
                    <span class="tag tag-open">${t.status}</span>
                    <span style="font-size:10px;color:var(--dim);margin-left:8px;">Diff: ${t.difficulty}/10</span>
                </div>
            </div>
            <div style="text-align:right;font-size:12px;font-weight:600;color:var(--accent);">${t.value} AGT</div>
        </div>`).join("");
    } catch (e) {
        // Tasks not ready
    }
}

async function refreshContributions() {
    try {
        const r = await fetch(`${API_BASE}/api/contributions?limit=10`);
        const contribs = await r.json();
        document.getElementById("contrib-count").textContent = contribs.length;

        const panel = document.getElementById("contributions-panel");
        if (!contribs.length) {
            panel.innerHTML = '<div style="color:var(--dim);text-align:center;padding:20px;">No contributions yet</div>';
            return;
        }

        panel.innerHTML = contribs.map(c => `
        <div class="list-item">
            <div style="flex:1;">
                <div style="font-weight:600;font-size:12px;">${c.task_name}</div>
                <div style="font-size:10px;color:var(--dim);">By: ${c.agent_id} | Score: ${c.contribution_score.toFixed(1)}</div>
                <div style="font-size:10px;color:var(--dim);">Evidence: ${c.evidence_count} items | Validator: ${c.validator_node_id}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-weight:600;color:var(--yellow);">+${c.agt_credit.toFixed(1)}</div>
                <div style="font-size:10px;color:var(--dim);">AGT Credit</div>
            </div>
        </div>`).join("");
    } catch (e) {
        // Contributions not ready
    }
}

async function refreshLedger() {
    try {
        const r = await fetch(`${API_BASE}/api/ledger/blocks?limit=8`);
        const blocks = await r.json();
        document.getElementById("stat-credit").textContent = blocks.reduce((s, b) => s + b.reward_credit, 0).toFixed(0);

        const panel = document.getElementById("ledger-panel");
        if (!blocks.length) {
            panel.innerHTML = '<div style="color:var(--dim);text-align:center;padding:20px;">Ledger empty</div>';
            return;
        }

        panel.innerHTML = blocks.map(b => `
        <div class="list-item">
            <div style="flex:1;">
                <div style="font-size:11px;font-weight:600;font-family:monospace;">Block #${b.index} — ${b.block_id}</div>
                <div style="font-size:10px;color:var(--dim);">Agent: ${b.agent_id} | Task: ${b.task_id}</div>
                <div style="font-size:9px;color:var(--dim);font-family:monospace;">Hash: ${b.block_hash.slice(0, 16)}...</div>
            </div>
            <div style="text-align:right;font-size:11px;">
                <div style="color:var(--yellow);">+${b.reward_credit.toFixed(1)} AGT</div>
                <div style="color:${b.reputation_change >= 0 ? 'var(--green)' : 'var(--red)'};">Rep ${b.reputation_change >= 0 ? '+' : ''}${b.reputation_change}</div>
            </div>
        </div>`).join("");
    } catch (e) {
        // Ledger not ready
    }
}

async function refreshReputation() {
    try {
        const r = await fetch(`${API_BASE}/api/reputation`);
        const reps = await r.json();

        const panel = document.getElementById("reputation-panel");
        if (!reps.length) {
            panel.innerHTML = '<div style="color:var(--dim);text-align:center;padding:20px;">No reputations tracked</div>';
            return;
        }

        panel.innerHTML = reps.map((r, i) => {
            const repClass = getRepClass(r.level);
            const repPct = Math.min(100, (r.score / 1000) * 100);
            return `
            <div class="list-item">
                <div style="font-size:14px;font-weight:700;color:var(--dim);width:24px;">#${i + 1}</div>
                <div style="flex:1;">
                    <div style="font-weight:600;font-size:12px;">${r.agent_id}</div>
                    <div class="rep-bar"><div class="rep-bar-fill ${repClass}" style="width:${repPct}%;"></div></div>
                </div>
                <div style="text-align:right;font-size:12px;">
                    <div style="font-weight:600;">${r.score.toFixed(0)}</div>
                    <div style="font-size:10px;color:var(--dim);">${r.level} (${r.reward_multiplier}x)</div>
                </div>
            </div>`;
        }).join("");
    } catch (e) {
        // Reputation not ready
    }
}

async function verifyChain() {
    try {
        const r = await fetch(`${API_BASE}/api/ledger/verify`);
        const data = await r.json();
        if (data.valid) {
            logEvent("contribution", `Chain integrity VERIFIED — ${data.blocks} blocks`);
        } else {
            logEvent("error", `Chain BROKEN! ${data.message}`);
        }
    } catch (e) {
        logEvent("error", `Verify failed: ${e.message}`);
    }
}

// ============================================================
// Event Log
// ============================================================

function logEvent(type, message) {
    const log = document.getElementById("event-log");
    const now = new Date();
    const time = now.toTimeString().slice(0, 8);

    const div = document.createElement("div");
    div.className = `event ${type}`;
    div.innerHTML = `<span class="time">${time}</span> ${message}`;

    log.prepend(div);

    // Keep max 50 events
    while (log.children.length > 50) {
        log.removeChild(log.lastChild);
    }
}

// ============================================================
// Helpers
// ============================================================

function getRepClass(level) {
    const map = {
        "Sage": "rep-sage",
        "Expert": "rep-expert",
        "Trusted": "rep-trusted",
        "Active": "rep-active",
        "Newcomer": "rep-new",
        "Unreliable": "rep-low",
    };
    return map[level] || "rep-active";
}
