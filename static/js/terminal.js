/**
 * static/js/terminal.js
 * Precision Palm - Floating AI Execution Terminal Controller
 * Manages 3-phase transparent telemetry logging ([REQUEST] -> [PROCESS] -> [RESULT]),
 * log stream filters, auto-scroll, window minimize/maximize, and clipboard export.
 * Adheres to zero-alert UI guidelines and English system standard.
 */

let isTerminalOpen = false;
let isTerminalMinimized = false;
let currentTerminalFilter = 'ALL';
let terminalLogCounter = 0;

const TERMINAL_LOG_STORAGE_KEY = 'precision_palm_terminal_logs_cache';

document.addEventListener('DOMContentLoaded', function () {
    initTerminalUI();
    loadCachedTerminalLogs();
});

/**
 * Initializes terminal UI bindings and keyboard shortcuts
 */
function initTerminalUI() {
    const termContainer = document.getElementById('floatingAiTerminalContainer');
    if (!termContainer) return;

    // Keyboard Shortcut: Ctrl + ` or Alt + T to toggle terminal
    window.addEventListener('keydown', function (e) {
        if ((e.ctrlKey && e.key === '`') || (e.altKey && (e.key === 't' || e.key === 'T'))) {
            e.preventDefault();
            toggleTerminalWindow();
        }
    });

    updateTerminalFilterUI('ALL');
}
async function executeTerminalCommand(cmdText) {
    appendTerminalLine(`root@precision-palm:~# ${cmdText}`);
    appendTerminalLine("Processing kernel instruction via Google Gemini 3.8 Flash...");

    try {
        const res = await fetch('/api/ai/terminal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmdText })
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            appendTerminalLine(data.output);
        } else {
            appendTerminalLine(`[ERROR] ${data.output}`);
        }
    } catch (err) {
        const isId = (localStorage.getItem('precision_palm_lang') || 'en') === 'id';
        appendTerminalLine(`[NET_ERR] ${isId ? 'Gagal menghubungi Google Cloud Run' : 'Failed to connect to Google Cloud Run'}: ${err.message}`);
    }
}
/**
 * Opens the floating terminal window
 */
function openTerminalWindow() {
    const term = document.getElementById('floatingAiTerminalContainer');
    if (!term) return;
    term.classList.remove('hidden');
    isTerminalOpen = true;

    if (isTerminalMinimized) {
        maximizeTerminalWindow();
    }
    scrollTerminalToBottom();
}

/**
 * Closes the floating terminal window
 */
function closeTerminalWindow() {
    const term = document.getElementById('floatingAiTerminalContainer');
    if (!term) return;
    term.classList.add('hidden');
    isTerminalOpen = false;
}

/**
 * Toggles the open/close state of the terminal window
 */
function toggleTerminalWindow() {
    if (isTerminalOpen) {
        closeTerminalWindow();
    } else {
        openTerminalWindow();
    }
}

/**
 * Minimizes the terminal window to a compact header
 */
function minimizeTerminalWindow() {
    const body = document.getElementById('floatingAiTerminalBody');
    const toolbar = document.getElementById('floatingAiTerminalToolbar');
    const footer = document.getElementById('floatingAiTerminalFooter');
    const btnMin = document.getElementById('btnTerminalMinimize');

    if (body) body.classList.add('hidden');
    if (toolbar) toolbar.classList.add('hidden');
    if (footer) footer.classList.add('hidden');
    if (btnMin) btnMin.textContent = '🗖';
    isTerminalMinimized = true;
}

/**
 * Maximizes the terminal window back to full expanded view
 */
function maximizeTerminalWindow() {
    const body = document.getElementById('floatingAiTerminalBody');
    const toolbar = document.getElementById('floatingAiTerminalToolbar');
    const footer = document.getElementById('floatingAiTerminalFooter');
    const btnMin = document.getElementById('btnTerminalMinimize');

    if (body) body.classList.remove('hidden');
    if (toolbar) toolbar.classList.remove('hidden');
    if (footer) footer.classList.remove('hidden');
    if (btnMin) btnMin.textContent = '🗕';
    isTerminalMinimized = false;
    scrollTerminalToBottom();
}

/**
 * Toggles minimize and maximize states
 */
function toggleMinimizeTerminal() {
    if (isTerminalMinimized) {
        maximizeTerminalWindow();
    } else {
        minimizeTerminalWindow();
    }
}

/**
 * Primary Logging Dispatcher: Records AI transactions across 3 standardized phases
 * @param {'REQUEST'|'PROCESS'|'RESULT'|'ERROR'} phase - Inference pipeline phase
 * @param {string} title - Action description or event title
 * @param {string|object} detail - Structured JSON payload or narrative log
 */
function logAiInteraction(phase, title, detail) {
    terminalLogCounter++;
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    const formattedDetail = (typeof detail === 'object') ? JSON.stringify(detail, null, 2) : String(detail || '');

    const logItem = {
        id: terminalLogCounter,
        phase: (phase || 'INFO').toUpperCase(),
        title: title || 'System Telemetry Event',
        detail: formattedDetail,
        timestamp: timestamp
    };

    appendLogToTerminalDOM(logItem);
    cacheTerminalLog(logItem);
    updateTerminalStatusBadge(logItem.phase);
}

/**
 * Legacy compatibility alias
 */
function logAiTerminal(message, type = 'sys') {
    let phase = 'PROCESS';
    if (type === 'req' || String(message).includes('[REQUEST]')) phase = 'REQUEST';
    else if (type === 'fb' || String(message).includes('[FALLBACK]')) phase = 'FALLBACK';
    else if (type === 'res' || String(message).includes('[RESULT]')) phase = 'RESULT';
    else if (type === 'err' || String(message).includes('[ERROR]')) phase = 'ERROR';

    logAiInteraction(phase, 'Terminal Event', message);
}

/**
 * Appends a formatted log card into the terminal DOM stream
 */
function appendLogToTerminalDOM(logItem) {
    const container = document.getElementById('floatingTerminalLogStream');
    if (!container) return;

    const emptyState = document.getElementById('terminalEmptyPlaceholder');
    if (emptyState) emptyState.remove();

    let borderCls = 'border-slate-800';
    let badgeCls = 'bg-slate-800 text-slate-300 border-slate-700';
    let icon = '⚡';
    let titleCls = 'text-slate-200';

    if (logItem.phase === 'REQUEST') {
        borderCls = 'border-sky-800/80 bg-sky-950/20';
        badgeCls = 'bg-sky-950 text-sky-400 border-sky-800';
        icon = '📤';
        titleCls = 'text-sky-300 font-bold';
    } else if (logItem.phase === 'PROCESS') {
        borderCls = 'border-blue-800/80 bg-blue-950/20';
        badgeCls = 'bg-blue-950 text-blue-400 border-blue-800';
        icon = '⚙️';
        titleCls = 'text-blue-300 font-bold';
    } else if (logItem.phase === 'FALLBACK') {
        borderCls = 'border-amber-600/80 bg-amber-950/30';
        badgeCls = 'bg-amber-950 text-amber-400 border border-amber-500/60 font-bold';
        icon = '⚡';
        titleCls = 'text-amber-300 font-bold';
    } else if (logItem.phase === 'RESULT') {
        borderCls = 'border-emerald-800/80 bg-emerald-950/20';
        badgeCls = 'bg-emerald-950 text-emerald-400 border-emerald-800';
        icon = '✅';
        titleCls = 'text-emerald-300 font-bold';
    } else if (logItem.phase === 'ERROR') {
        borderCls = 'border-rose-800/80 bg-rose-950/20';
        badgeCls = 'bg-rose-950 text-rose-400 border-rose-800';
        icon = '❌';
        titleCls = 'text-rose-300 font-bold';
    }

    const logEl = document.createElement('div');
    logEl.className = `p-2.5 rounded-xl border ${borderCls} font-mono text-[11px] space-y-1.5 transition-all terminal-log-item`;
    logEl.dataset.phase = logItem.phase;

    logEl.innerHTML = `
        <div class="flex items-center justify-between text-[10px]">
            <div class="flex items-center gap-1.5">
                <span class="px-1.5 py-0.2 rounded border font-bold ${badgeCls}">
                    ${icon} [${logItem.phase}]
                </span>
                <span class="${titleCls}">${escapeHtml(logItem.title)}</span>
            </div>
            <span class="text-slate-500 font-mono text-[9px]">${logItem.timestamp}</span>
        </div>
        <pre class="text-[10px] text-slate-300 whitespace-pre-wrap leading-relaxed overflow-x-auto bg-slate-950/80 p-2 rounded-lg border border-slate-900 select-text font-mono">${escapeHtml(logItem.detail)}</pre>
    `;

    if (currentTerminalFilter !== 'ALL' && logItem.phase !== currentTerminalFilter) {
        logEl.style.display = 'none';
    }

    container.appendChild(logEl);
    scrollTerminalToBottom();
}

/**
 * Filters the active terminal log cards
 */
function setTerminalFilter(phaseFilter) {
    currentTerminalFilter = (phaseFilter || 'ALL').toUpperCase();
    updateTerminalFilterUI(currentTerminalFilter);

    const logElements = document.querySelectorAll('.terminal-log-item');
    logElements.forEach(el => {
        if (currentTerminalFilter === 'ALL' || el.dataset.phase === currentTerminalFilter) {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });

    scrollTerminalToBottom();
}

/**
 * Updates filter button styling
 */
function updateTerminalFilterUI(activeFilter) {
    const filters = ['ALL', 'REQUEST', 'PROCESS', 'FALLBACK', 'RESULT'];
    filters.forEach(f => {
        const btn = document.getElementById(`btnTermFilter_${f}`);
        if (!btn) return;
        if (f === activeFilter) {
            btn.className = "px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-600 text-white cursor-pointer shadow-xs";
        } else {
            btn.className = "px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 hover:text-white cursor-pointer transition";
        }
    });
}

/**
 * Scrolls terminal stream container to bottom
 */
function scrollTerminalToBottom() {
    const body = document.getElementById('floatingAiTerminalBody');
    if (body) {
        body.scrollTop = body.scrollHeight;
    }
}

/**
 * Clears terminal log stream and local storage cache
 */
function clearTerminalLogs() {
    const container = document.getElementById('floatingTerminalLogStream');
    if (container) {
        container.innerHTML = `
            <div id="terminalEmptyPlaceholder" class="p-6 text-center text-slate-500 font-mono text-xs">
                <span>⚡ AI Terminal stream cleared. Standing by for telemetry dispatch...</span>
            </div>
        `;
    }
    terminalLogCounter = 0;
    try {
        localStorage.removeItem(TERMINAL_LOG_STORAGE_KEY);
    } catch (e) {
        console.warn("[Terminal] Storage clear notice:", e);
    }
}

/**
 * Copies the terminal log content to the system clipboard without using alert()
 */
function copyTerminalLogsToClipboard() {
    const logs = document.querySelectorAll('.terminal-log-item');
    const copyBtn = document.getElementById('btnTerminalCopy');

    if (!logs || logs.length === 0) {
        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<span class="text-amber-400">Empty</span>';
            setTimeout(() => { copyBtn.innerHTML = originalText; }, 1200);
        }
        return;
    }

    let textToCopy = "=== PRECISION PALM • AI STATUTORY EXECUTION LOGS ===\n\n";
    logs.forEach(el => {
        textToCopy += `${el.innerText}\n----------------------------------------\n`;
    });

    try {
        const dummyArea = document.createElement("textarea");
        dummyArea.value = textToCopy;
        dummyArea.style.position = "fixed";
        dummyArea.style.left = "-9999px";
        document.body.appendChild(dummyArea);
        dummyArea.select();
        document.execCommand("copy");
        document.body.removeChild(dummyArea);

        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<span class="text-emerald-400 font-bold">Copied!</span>';
            setTimeout(() => { copyBtn.innerHTML = originalText; }, 1500);
        }
    } catch (err) {
        console.error("[Terminal] Clipboard write notice:", err);
    }
}

function cacheTerminalLog(logItem) {
    try {
        const raw = localStorage.getItem(TERMINAL_LOG_STORAGE_KEY);
        let logs = raw ? JSON.parse(raw) : [];
        if (!Array.isArray(logs)) logs = [];
        logs.push(logItem);
        if (logs.length > 30) logs = logs.slice(-30);
        localStorage.setItem(TERMINAL_LOG_STORAGE_KEY, JSON.stringify(logs));
    } catch (e) {
        console.warn("[Terminal] Cache write notice:", e);
    }
}

function loadCachedTerminalLogs() {
    try {
        const raw = localStorage.getItem(TERMINAL_LOG_STORAGE_KEY);
        if (!raw) return;
        const logs = JSON.parse(raw);
        if (Array.isArray(logs) && logs.length > 0) {
            logs.forEach(item => appendLogToTerminalDOM(item));
        }
    } catch (e) {
        console.warn("[Terminal] Cache load notice:", e);
    }
}

function updateTerminalStatusBadge(phase) {
    const badge = document.getElementById('terminalStatusIndicator');
    if (!badge) return;

    if (phase === 'PROCESS') {
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span> Reasoning';
        badge.className = "text-[9px] font-mono px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-700 flex items-center gap-1 font-bold";
    } else if (phase === 'FALLBACK') {
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span> Fallback';
        badge.className = "text-[9px] font-mono px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-600 flex items-center gap-1 font-bold";
    } else if (phase === 'RESULT') {
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Sealed';
        badge.className = "text-[9px] font-mono px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-700 flex items-center gap-1 font-bold";
    } else {
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span> Dispatched';
        badge.className = "text-[9px] font-mono px-2 py-0.5 rounded-full bg-sky-950 text-sky-300 border border-sky-700 flex items-center gap-1 font-bold";
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

window.openTerminalWindow = openTerminalWindow;
window.closeTerminalWindow = closeTerminalWindow;
window.toggleTerminalWindow = toggleTerminalWindow;
window.minimizeTerminalWindow = minimizeTerminalWindow;
window.maximizeTerminalWindow = maximizeTerminalWindow;
window.toggleMinimizeTerminal = toggleMinimizeTerminal;
window.logAiInteraction = logAiInteraction;
window.logAiTerminal = logAiTerminal;
window.setTerminalFilter = setTerminalFilter;
window.clearTerminalLogs = clearTerminalLogs;
window.copyTerminalLogsToClipboard = copyTerminalLogsToClipboard;