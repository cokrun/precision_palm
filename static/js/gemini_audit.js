// static/js/gemini_audit.js
window.runGeminiAudit = async function() {
    const btn = document.getElementById('btnRunAiAudit');
    const btnText = document.getElementById('btnAiText');
    const resultContainer = document.getElementById('aiAuditResult');

    if (btn) btn.disabled = true;
    if (btnText) btnText.textContent = "Auditing via Gemini 3.8 Flash...";
    if (resultContainer) {
        resultContainer.classList.remove('hidden');
        resultContainer.innerHTML = `
            <div class="flex items-center gap-2 text-emerald-400 p-2 font-mono text-xs">
                <span class="animate-spin text-base">⚙️</span>
                <span>Menghubungi Gemini 3.8 Flash untuk analisis spasial PIPPIB...</span>
            </div>
        `;
    }

    const concessionInput = document.getElementById('inp_nomor_hgu') 
        || document.getElementById('selectConcession')
        || document.getElementById('concessionSelect')
        || document.getElementById('dossierSelect')
        || document.querySelector('[name="concession_id"]');
    const urlParams = new URLSearchParams(window.location.search);
    const concessionId = (concessionInput?.value || urlParams.get('kode') || urlParams.get('dossier_id') || "").trim();

    if (!concessionId) {
        if (resultContainer) {
            resultContainer.classList.remove('hidden');
            resultContainer.innerHTML = `
                <div class="p-2 text-amber-400 font-mono text-xs">
                    ⚠️ Silakan pilih kebun / nomor HGU terlebih dahulu sebelum menjalankan audit AI.
                </div>
            `;
        }
        if (btn) btn.disabled = false;
        if (btnText) btnText.textContent = "Run Gemini Audit";
        return;
    }
    const overlapHa = 0.0;
    const zoneName = "PIPPIB 2024 & Sempadan Hutan Lindung (50m Buffer)";

    try {
        const resp = await fetch('/api/spatial/compliance-reasoning', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                concession_id: concessionId,
                overlap_ha: overlapHa,
                zone_name: zoneName
            })
        });

        const data = await resp.json();
        let auditData = (data && data.analysis !== undefined) ? data.analysis : data;

        if (typeof auditData === 'string') {
            try {
                auditData = JSON.parse(auditData);
            } catch (_) {}
        }

        const isId = (localStorage.getItem('precision_palm_lang') || 'en') === 'id';
        if (typeof auditData === 'object' && auditData !== null) {
            const statusBadge = (auditData.status === 'ERROR' || auditData.verdict === 'ERROR')
                ? '<span class="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-600 font-bold">REJECTED / MORATORIUM</span>'
                : '<span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-600 font-bold">COMPLIANT / SAFE APL</span>';

            const defaultSummary = isId ? 'Analisis kepatuhan tata ruang selesai diverifikasi.' : 'Spatial compliance analysis verified.';
            const mainText = auditData.analysis || auditData.summary || auditData.explanation || defaultSummary;
            const recoLabel = isId ? 'Rekomendasi:' : 'Recommendation:';
            const recoText = auditData.recommendation ? `<p class="text-amber-300 mt-1"><strong>${recoLabel}</strong> ${auditData.recommendation}</p>` : '';
            const reviewLabel = isId ? 'Ulasan Regulasi:' : 'Regulatory Review:';
            const openHistoryLabel = isId ? 'Buka Riwayat di AI Live Logs &rarr;' : 'Open History in AI Live Logs &rarr;';

            resultContainer.innerHTML = `
                <div class="space-y-2 p-1 font-sans text-xs">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-1.5 font-mono">
                        <span class="font-bold text-emerald-400 flex items-center gap-1.5">
                            <span>🤖</span> <span>Gemini 3.8 Flash Spatial Audit Verdict</span>
                        </span>
                        ${statusBadge}
                    </div>
                    <div class="text-slate-200 leading-relaxed space-y-1">
                        <p><strong>${reviewLabel}</strong> ${mainText}</p>
                        ${recoText}
                    </div>
                    <div class="text-[10px] font-mono text-slate-400 pt-1.5 border-t border-slate-800 flex flex-wrap items-center justify-between gap-1">
                        <span>Engine: Google Gemini 3.8 Flash (Non-Blocking)</span>
                        <a href="/ai-logs" target="_blank" class="text-emerald-400 hover:underline flex items-center gap-1">
                            <span>📜</span> <span>${openHistoryLabel}</span>
                        </a>
                    </div>
                </div>
            `;
        } else {
            const auditCompletedLabel = isId ? '✓ Hasil Audit Selesai' : '✓ Audit Completed';
            const viewLogsLabel = isId ? 'Lihat AI Logs &rarr;' : 'View AI Logs &rarr;';
            resultContainer.innerHTML = `
                <div class="space-y-1.5 p-1 font-mono text-xs">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-1">
                        <span class="text-emerald-400 font-bold">${auditCompletedLabel}</span>
                        <a href="/ai-logs" target="_blank" class="text-emerald-400 hover:underline text-[10px]">${viewLogsLabel}</a>
                    </div>
                    <div class="text-slate-200 whitespace-pre-wrap leading-relaxed">${auditData}</div>
                </div>
            `;
        }

    } catch (err) {
        console.error("[Gemini Spatial Audit Error]", err);
        const isId = (localStorage.getItem('precision_palm_lang') || 'en') === 'id';
        if (resultContainer) {
            const errMsg = isId ? 'Gagal menghubungkan ke layanan AI: ' : 'Failed to connect to AI service: ';
            const errConn = isId ? 'Koneksi terputus' : 'Connection lost';
            const checkErrLabel = isId ? 'Cek Error di AI Logs' : 'Check Error in AI Logs';
            resultContainer.innerHTML = `
                <div class="p-2 text-rose-300 font-mono text-xs flex items-center justify-between">
                    <span>❌ ${errMsg}${err.message || errConn}</span>
                    <a href="/ai-logs" target="_blank" class="text-amber-400 hover:underline text-[10px]">${checkErrLabel}</a>
                </div>
            `;
        }
    } finally {
        if (btn) btn.disabled = false;
        if (btnText) btnText.textContent = "Run Gemini Audit";
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('btnRunAiAudit');
    if (btn) {
        btn.onclick = window.runGeminiAudit;
    }
});
