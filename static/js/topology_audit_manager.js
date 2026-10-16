// static/js/topology_audit_manager.js
// Mengelola state pemeriksaan berulang & integrasi BigQuery pada modal topologi

let currentAuditedNode = {
    id: '',
    title: '',
    estate_code: 'EST-MDN-001',
    verdict_answer: '',
    citations: []
};

// Fungsi cek status review saat modal simpul terbuka
async function checkNodeAuditState(nodeId, nodeTitle, estateCode = 'EST-MDN-001') {
    currentAuditedNode.id = nodeId;
    currentAuditedNode.title = nodeTitle;
    currentAuditedNode.estate_code = estateCode;

    const actionContainer = document.querySelector('.modal-action-bar') || document.querySelector('#modalActions') || document.querySelector('.modal-footer');
    const consultBtn = document.querySelector('button[onclick*="Consult"], button:has-text("Consult AI Auditor")') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Consult AI Auditor'));

    try {
        const resp = await fetch(`/api/ai/get-node-review?node_id=${encodeURIComponent(nodeId)}&estate_code=${encodeURIComponent(estateCode)}`);
        const json = await resp.json();

        if (json.has_record) {
            // Data sudah ada di BigQuery: Ganti tombol menjadi "Review Previous Audit"
            if (consultBtn) {
                consultBtn.className = "px-4 py-2 rounded-xl bg-purple-900/90 hover:bg-purple-800 text-purple-200 border border-purple-500 font-bold text-xs shadow-lg transition flex items-center gap-1.5 cursor-pointer";
                consultBtn.innerHTML = `<span>📑</span> <span>Review Previous Audit (${json.storage})</span>`;
                consultBtn.onclick = () => renderAuditReviewUI(json);
            }
        } else {
            // Belum ada data: Biarkan sebagai "Consult AI Auditor"
            if (consultBtn) {
                consultBtn.className = "px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-lg transition flex items-center gap-1.5 cursor-pointer";
                consultBtn.innerHTML = `<span>💬</span> <span>Consult AI Auditor</span>`;
            }
        }
    } catch (err) {
        console.warn("[Node State Check Warning]:", err);
    }
}

// Menampilkan hasil review yang sudah tersimpan tanpa panggil API Gemini
function renderAuditReviewUI(record) {
    let resultBox = document.getElementById('aiAuditResultBox');
    if (!resultBox) {
        resultBox = document.createElement('div');
        resultBox.id = 'aiAuditResultBox';
        resultBox.className = 'mt-4 p-4 rounded-2xl bg-slate-950/90 border border-purple-500/60 font-mono text-xs space-y-3';
        const targetParent = document.querySelector('.modal-body') || document.querySelector('#modalContent') || document.querySelector('.space-y-4');
        if (targetParent) targetParent.appendChild(resultBox);
    }

    resultBox.innerHTML = `
        <div class="flex items-center justify-between border-b border-purple-800/40 pb-2">
            <span class="text-purple-300 font-bold flex items-center gap-1.5">
                <span>📑</span> <span>ARCHIVED BIGQUERY AUDIT RECORD</span>
            </span>
            <span class="text-[10px] text-slate-400 font-sans">${record.timestamp}</span>
        </div>
        <p class="text-slate-200 leading-relaxed font-sans text-xs">${record.verdict_answer}</p>
        <div class="text-[10px] text-emerald-400 select-all break-all">
            <strong>SHA-256 SEAL:</strong> ${record.sha256_hash}
        </div>
        <div class="pt-2 flex justify-end">
            <button type="button" onclick="triggerFreshAuditConsultation()" class="text-[10px] text-cyan-400 hover:underline cursor-pointer">
                ↻ Re-run Fresh Audit Inspection
            </button>
        </div>
    `;
    resultBox.scrollIntoView({ behavior: 'smooth' });
}

// Fungsi Simpan hasil ke BigQuery setelah AI selesai menjawab
async function saveAuditVerdictToBigQuery(nodeId, nodeTitle, answerText, citationsList, estateCode = 'EST-MDN-001') {
    const saveBtn = document.getElementById('btnSaveToBigQuery');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = `<span>🌀</span> <span>Saving to BigQuery...</span>`;
    }

    try {
        const resp = await fetch('/api/ai/save-node-review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                node_id: nodeId,
                node_title: nodeTitle,
                estate_code: estateCode,
                verdict_answer: answerText,
                citations: citationsList
            })
        });
        const json = await resp.json();
        if (json.success) {
            alert(`✓ Audit Verdict Successfully Sealed to ${json.storage} Ledger!\nSHA-256: ${json.sha256_hash}`);
            await checkNodeAuditState(nodeId, nodeTitle, estateCode);
        }
    } catch (err) {
        alert("Failed to save to BigQuery: " + err.message);
    }
}
