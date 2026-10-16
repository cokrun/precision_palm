// static/js/global_ai_triggers.js
// Menghubungkan tombol Photo Scan (Spatial) dan Simpan Laporan (Timelines) ke Google Gemini Vision

document.addEventListener('DOMContentLoaded', () => {
    // 1. TOMBOL "PHOTO SCAN" DI HALAMAN SPATIAL
    document.querySelectorAll('button, a').forEach(el => {
        const text = (el.textContent || '').trim().toLowerCase();
        
        if (text.includes('photo scan') || text.includes('scan photo') || text.includes('foto scan')) {
            el.addEventListener('click', async (e) => {
                console.log("[Precision Palm] Memicu Gemini Vision: Spatial Photo Scan");
                
                const originalText = el.innerHTML;
                const isId = (localStorage.getItem('precision_palm_lang') || 'en') === 'id';
                el.innerHTML = `<span class="animate-spin">🌀</span> ${isId ? 'Memindai Gemini Vision...' : 'Scanning Gemini Vision...'}`;
                el.disabled = true;

                try {
                    const fd = new FormData();
                    fd.append('feature_name', 'Spatial: Canopy Photo Scanner (Gemini Vision)');
                    
                    const lat = document.getElementById('inpLat')?.value || "0.824100";
                    const lng = document.getElementById('inpLng')?.value || "99.561200";
                    fd.append('meta_info', `Titik Pantau Koordinat: ${lat}, ${lng} - Verifikasi Moratorium`);

                    const fileInp = document.querySelector('input[type="file"][name*="foto"], input[type="file"][id*="photo"], input[type="file"][id*="foto"]');
                    if (fileInp && fileInp.files && fileInp.files[0]) {
                        fd.append('image', fileInp.files[0]);
                    }

                    const res = await fetch('/api/ai/scan-image', { method: 'POST', body: fd });
                    const json = await res.json();
                    
                    if (json.status === 'success') {
                        const ai = json.analysis;
                        const badge = document.getElementById('badgeAiScanResult') || document.getElementById('scanResultBadge');
                        if (badge) {
                            badge.className = "px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-600";
                            badge.textContent = `✓ GEMINI SCAN: ${ai.canopy_density_pct}% DENSITY`;
                        }
                    }
                } catch (err) {
                    console.error("[Spatial Photo Scan Error]:", err);
                } finally {
                    el.innerHTML = originalText;
                    el.disabled = false;
                }
            });
        }
    });

    // 2. TOMBOL / FORM "SIMPAN LAPORAN & PINDAI DENGAN AI VISION" DI TIMELINES
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            const submitBtn = form.querySelector('button[type="submit"]');
            const btnText = (submitBtn ? submitBtn.textContent : '').toLowerCase();

            if (btnText.includes('pindai dengan ai vision') || btnText.includes('simpan laporan') || btnText.includes('scan with ai vision') || btnText.includes('save report')) {
                console.log("[Precision Palm] Memicu Gemini Vision: Timelines Mandor Field Report");
                
                try {
                    const fd = new FormData(form);
                    fd.append('feature_name', 'Timelines: Mandor Field Vision & 2.0m Circle');
                    fd.append('meta_info', 'Survei Mandor Lapangan Triwulanan');
                    
                    await fetch('/api/ai/scan-image', { method: 'POST', body: fd });
                } catch (err) {
                    console.error("[Timelines AI Submit Error]:", err);
                }
            }
        });
    });
});
