// static/js/fix_grounded_display.js
// Memastikan parser grounded audit aman dari nilai undefined

window.renderGroundedAuditResult = function(data, targetContainerId = 'aiAuditResultBox') {
    const container = document.getElementById(targetContainerId);
    if (!container) return;

    const isId = (localStorage.getItem('precision_palm_lang') || 'en') === 'id';
    // Normalisasi struktur data dari backend
    const answer = data.answer || data.verdict_answer || (isId ? "Tidak ada teks respon." : "No response text.");
    const citations = Array.isArray(data.citations) ? data.citations : [];
    const modelEngine = data.model || data.model_engine || "Google Gemini 3.8 Flash";
    const status = data.status || "ATTRIBUTED";

    // Format badge sitasi regulasi
    const citationsHtml = citations.length > 0 ? citations.map(c => `
        <div class="p-2 rounded-lg bg-slate-900 border border-slate-800 text-[11px] space-y-1">
            <div class="flex items-center gap-1.5 font-bold text-cyan-400">
                <span>${c.ref || '[•]'}</span>
                <span>${c.doc_title || c.title || (isId ? 'Regulasi Terkait' : 'Related Regulation')}</span>
            </div>
            <div class="text-slate-400 text-[10px]">${c.legal_basis || ''}</div>
            <p class="text-slate-300 italic text-[10px]">"${c.exact_quote || c.snippet || ''}"</p>
        </div>
    `).join('') : `<p class="text-slate-500 text-[10px]">${isId ? 'Tidak ada sitasi spesifik yang dilampirkan.' : 'No specific citations attached.'}</p>`;

    container.innerHTML = `
        <div class="space-y-3 font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2">
                <span class="text-emerald-400 font-bold flex items-center gap-1.5">
                    <span>⚡</span> <span>${modelEngine}</span>
                </span>
                <span class="px-2 py-0.5 rounded text-[9px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
                    ${status}
                </span>
            </div>
            <p class="text-slate-200 leading-relaxed font-sans text-xs">${answer}</p>
            <div class="space-y-1.5 pt-2">
                <span class="text-slate-400 font-bold text-[10px] uppercase block">${isId ? 'Daftar Regulasi Terverifikasi:' : 'Verified Regulation List:'}</span>
                ${citationsHtml}
            </div>
        </div>
    `;
};
