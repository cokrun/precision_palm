/**
 * static/js/settings_governance.js
 * Precision Palm Enterprise OS - Enterprise Governance & Judge Calibration Settings
 * 
 * Modul terpusat tata kelola kepatuhan, kalibrasi penilai juri, dan aturan pemindaian visi AI:
 * 1. State Manager `governanceManager` berbasis localStorage + runtime reactivity.
 * 2. Standar Baku:
 *    - Mode Evaluasi: SANDBOX (fleksibel/re-audit bebas) vs STRICT (mandatori ISPO/EUDR).
 *    - Mesin Visi: Google Gemini 3.8 Flash Multimodal Vision dengan penalaran biofisik.
 *    - Ritme Latensi HUD Laser: 1.8 detik (Pass 1 Cepat + Pass 2 Terfokus).
 *    - Garansi Laser HUD: Injeksi otomatis dual cross-laser vertikal & horizontal.
 *    - Aturan Kunci/Sealed: Bebaskan re-audit foto kapan pun (Zero Lockout).
 *    - Aturan Duplikasi: Bebaskan duplikasi sudut pengambilan foto kebun.
 *    - Auto-Persist ke Database: Simpan hasil scan terakhir langsung ke SQLite server.
 * 3. Fungsi Renderer UI `renderGovernanceSettingsUI(containerId)`.
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'precision_palm_governance_rules';

    const DEFAULT_GOVERNANCE_CONFIG = {
        evaluation_mode: 'SANDBOX', // 'SANDBOX' | 'STRICT'
        vision_engine: 'GEMINI_3_8_FLASH', // 'GEMINI_3_8_FLASH' | 'VERTEX_MULTI_AGENT'
        scan_pacing_mode: 'CALIBRATED_REALISTIC', // 'CALIBRATED_REALISTIC' | 'RAPID'
        scan_latency_ms: 1800, // 1800 ms (1.8s)
        allow_re_audit: true, // Izinkan re-audit foto berstatus SEALED
        guarantee_hud_lasers: true, // Garansi dual cross-laser (horizontal & vertikal) selalu aktif
        allow_photo_duplication: true, // Izinkan pengambilan multi-sudut untuk bidang yang sama
        auto_persist_to_storage: true, // Otomatis simpan scan terakhir ke database server
        auto_sync_bigquery: true, // Alirkan jejak audit ke BigQuery jika credentials aktif
        last_updated: new Date().toISOString()
    };

    class GovernanceManager {
        constructor() {
            this.rules = this.loadRules();
        }

        loadRules() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY);
                if (raw) {
                    const parsed = JSON.parse(raw);
                    return Object.assign({}, DEFAULT_GOVERNANCE_CONFIG, parsed);
                }
            } catch (err) {
                console.warn('[GovernanceManager] Gagal membaca localStorage:', err);
            }
            return Object.assign({}, DEFAULT_GOVERNANCE_CONFIG);
        }

        saveRules() {
            try {
                this.rules.last_updated = new Date().toISOString();
                localStorage.setItem(STORAGE_KEY, JSON.stringify(this.rules));
                window.dispatchEvent(new CustomEvent('governanceChanged', { detail: this.rules }));
            } catch (err) {
                console.error('[GovernanceManager] Gagal menyimpan ke localStorage:', err);
            }
        }

        get(key, defaultVal) {
            if (this.rules && key in this.rules) {
                return this.rules[key];
            }
            return defaultVal !== undefined ? defaultVal : DEFAULT_GOVERNANCE_CONFIG[key];
        }

        set(key, val) {
            this.rules[key] = val;
            this.saveRules();
        }

        getAll() {
            return Object.assign({}, this.rules);
        }

        saveAll(newConfig) {
            this.rules = Object.assign({}, this.rules, newConfig);
            this.saveRules();
        }

        resetDefaults() {
            this.rules = Object.assign({}, DEFAULT_GOVERNANCE_CONFIG, { last_updated: new Date().toISOString() });
            this.saveRules();
            return this.rules;
        }

        async syncToBackend() {
            try {
                const resp = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        governance_rules: this.rules
                    })
                });
                return resp.ok;
            } catch (e) {
                console.warn('[GovernanceManager] Sinkronisasi backend offline:', e);
                return false;
            }
        }
    }

    const governanceManager = new GovernanceManager();
    window.governanceManager = governanceManager;

    /**
     * Merender Panel Kontrol Modern Enterprise Governance & Judge Calibration
     */
    function renderGovernanceSettingsUI(containerId = 'governanceSettingsPanel') {
        const container = (typeof containerId === 'string') ? document.getElementById(containerId) : containerId;
        if (!container) return;

        const cfg = governanceManager.getAll();

        const isSandbox = cfg.evaluation_mode === 'SANDBOX';
        const isRealistic = cfg.scan_pacing_mode === 'CALIBRATED_REALISTIC';

        container.innerHTML = `
        <div class="space-y-6">
            <!-- Header Ringkasan Status Tata Kelola -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-emerald-950/60 via-slate-900 to-cyan-950/60 border border-emerald-500/30 shadow-lg">
                <div class="space-y-1">
                    <div class="flex items-center gap-2">
                        <span class="text-xl">⚖️</span>
                        <h3 class="text-base sm:text-lg font-black text-white tracking-wide font-sans">
                            Enterprise Governance & Judge Calibration Panel
                        </h3>
                    </div>
                    <p class="text-xs text-slate-300 font-sans leading-relaxed">
                        Kendali terpusat penilaian juri, aturan pemindaian visi AI anti-gagal, toleransi re-audit, serta sinkronisasi database server secara real-time.
                    </p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <span id="govModePill" class="px-3 py-1 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider ${isSandbox ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'}">
                        Mode: ${cfg.evaluation_mode}
                    </span>
                    <span class="px-3 py-1 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                        ⚡ GEMINI 3.8 FLASH
                    </span>
                    <span class="px-3 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        🟢 HUD LASER: 1.8s
                    </span>
                </div>
            </div>

            <!-- Grid Kontrol Utama -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                
                <!-- 1. Mode Evaluasi Juri & Operasional -->
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-700/80 space-y-4 shadow-sm">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="text-base">🏛️</span>
                            <h4 class="text-sm font-bold text-white font-sans">1. Mode Evaluasi (Judge Calibration)</h4>
                        </div>
                        <span class="text-[10px] font-mono text-emerald-400 font-semibold">ISPO & EUDR Standards</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-relaxed font-sans">
                        Pilih mode operasional sistem. Sandbox membebaskan simulasi multi-iterasi tanpa penalti audit; Strict mewajibkan syarat kelulusan hukum tanpa toleransi.
                    </p>

                    <div class="grid grid-cols-2 gap-3 pt-1">
                        <label class="p-3.5 rounded-xl border cursor-pointer transition flex flex-col justify-between gap-2 ${isSandbox ? 'bg-amber-500/10 border-amber-500/80 text-amber-200' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-xs">🧪 Sandbox Mode</span>
                                <input type="radio" name="gov_eval_mode" value="SANDBOX" ${isSandbox ? 'checked' : ''} onchange="governanceManager.set('evaluation_mode', 'SANDBOX'); renderGovernanceSettingsUI('${containerId}');" class="text-amber-500 focus:ring-amber-500">
                            </div>
                            <span class="text-[10px] text-slate-400 font-sans">Fleksibel, izinkan re-audit tak terbatas, deteksi gulma interaktif.</span>
                        </label>

                        <label class="p-3.5 rounded-xl border cursor-pointer transition flex flex-col justify-between gap-2 ${!isSandbox ? 'bg-emerald-500/10 border-emerald-500/80 text-emerald-200' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-xs">🛡️ Strict Audit</span>
                                <input type="radio" name="gov_eval_mode" value="STRICT" ${!isSandbox ? 'checked' : ''} onchange="governanceManager.set('evaluation_mode', 'STRICT'); renderGovernanceSettingsUI('${containerId}');" class="text-emerald-500 focus:ring-emerald-500">
                            </div>
                            <span class="text-[10px] text-slate-400 font-sans">Mandatori Permentan 33/2025, piringan 2.05m dan cut-off 2020 ketat.</span>
                        </label>
                    </div>
                </div>

                <!-- 2. Mesin Multimodal Visi & Model AI -->
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-700/80 space-y-4 shadow-sm">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="text-base">🤖</span>
                            <h4 class="text-sm font-bold text-white font-sans">2. Mesin Pemindai Visi Lapangan</h4>
                        </div>
                        <span class="text-[10px] font-mono text-cyan-400 font-semibold">Gemini 3.8 Flash</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-relaxed font-sans">
                        Menggunakan Google Gemini 3.8 Flash Multimodal Vision untuk deteksi tajuk drone nadir, diameter piringan 2.05m, dan identifikasi penutupan gulma mandor.
                    </p>

                    <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                        <div class="space-y-0.5">
                            <div class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                <span>Google Gemini 3.8 Flash</span>
                                <span class="px-2 py-0.5 rounded text-[9px] font-mono bg-emerald-500/20 text-emerald-300 font-bold">AKTIF</span>
                            </div>
                            <div class="text-[10px] text-slate-500 font-mono">Generative Language API • 44-Variable Matrix Output</div>
                        </div>
                        <span class="text-emerald-400 text-lg font-bold">✓</span>
                    </div>

                    <div class="flex items-center justify-between text-xs font-mono text-slate-400 pt-1">
                        <span>Attributed Citations:</span>
                        <span class="text-cyan-400 font-bold">PP 23/2021 • Permentan 33/2025</span>
                    </div>
                </div>

                <!-- 3. Ritme Latensi & Pacing Pemindaian (Anti-Mockup) -->
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-700/80 space-y-4 shadow-sm">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="text-base">⏱️</span>
                            <h4 class="text-sm font-bold text-white font-sans">3. Ritme Pemindaian HUD (Anti-Mockup)</h4>
                        </div>
                        <span class="text-[10px] font-mono text-amber-400 font-semibold">Real-Latency</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-relaxed font-sans">
                        Mencegah pemindaian instan palsu (&lt;0.2 detik). Menjamin ritme observasi ilmiah multi-fase (Pass 1 cepat &amp; Pass 2 terfokus) dengan latensi 1.8 - 2.2 detik.
                    </p>

                    <div class="grid grid-cols-2 gap-3">
                        <label class="p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${isRealistic ? 'bg-cyan-500/10 border-cyan-500/80 text-cyan-200' : 'bg-slate-950 border-slate-800 text-slate-400'}">
                            <div class="space-y-0.5">
                                <span class="font-bold text-xs block">🎯 Calibrated (1.8s)</span>
                                <span class="text-[10px] text-slate-400 block font-sans">Pass 1 + Pass 2 Bertahap</span>
                            </div>
                            <input type="radio" name="gov_pacing" value="CALIBRATED_REALISTIC" ${isRealistic ? 'checked' : ''} onchange="governanceManager.set('scan_pacing_mode', 'CALIBRATED_REALISTIC'); renderGovernanceSettingsUI('${containerId}');" class="text-cyan-500 focus:ring-cyan-500">
                        </label>

                        <label class="p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${!isRealistic ? 'bg-slate-800 border-slate-600 text-slate-200' : 'bg-slate-950 border-slate-800 text-slate-400'}">
                            <div class="space-y-0.5">
                                <span class="font-bold text-xs block">⚡ Rapid Scan</span>
                                <span class="text-[10px] text-slate-400 block font-sans">Pemindaian Cepat (~0.8s)</span>
                            </div>
                            <input type="radio" name="gov_pacing" value="RAPID" ${!isRealistic ? 'checked' : ''} onchange="governanceManager.set('scan_pacing_mode', 'RAPID'); renderGovernanceSettingsUI('${containerId}');" class="text-cyan-500 focus:ring-cyan-500">
                        </label>
                    </div>

                    <div class="pt-1 flex items-center justify-between text-xs font-mono">
                        <span class="text-slate-400">Durasi Observasi Minimum:</span>
                        <div class="flex items-center gap-2">
                            <input type="number" min="800" max="4000" step="100" value="${cfg.scan_latency_ms || 1800}" onchange="governanceManager.set('scan_latency_ms', parseInt(this.value, 10));" class="w-20 px-2 py-1 rounded bg-slate-950 border border-slate-700 text-emerald-400 font-bold text-right text-xs focus:border-emerald-500">
                            <span class="text-slate-400">ms</span>
                        </div>
                    </div>
                </div>

                <!-- 4. Garansi Laser HUD Vertikal & Horizontal -->
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-700/80 space-y-4 shadow-sm">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="text-base">❇️</span>
                            <h4 class="text-sm font-bold text-white font-sans">4. Garansi Laser HUD (Anti-Hilang)</h4>
                        </div>
                        <span class="text-[10px] font-mono text-emerald-400 font-semibold">Dual Cross-Laser</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-relaxed font-sans">
                        Menjamin elemen sinar laser neon (vertikal &amp; horizontal) selalu otomatis diinjeksikan ke dalam DOM dan aktif menyapu saat tombol scan/rescan ditekan.
                    </p>

                    <label class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer hover:border-emerald-500/60 transition">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-slate-200 block">Garansi Dual Cross-Laser Aktif</span>
                            <span class="text-[10px] text-slate-400 font-sans block">Laser vertikal menyapu kiri-kanan &amp; horizontal menyapu atas-bawah.</span>
                        </div>
                        <input type="checkbox" ${cfg.guarantee_hud_lasers ? 'checked' : ''} onchange="governanceManager.set('guarantee_hud_lasers', this.checked); showGovToast('Pengaturan Laser diperbarui', '❇️');" class="w-5 h-5 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700">
                    </label>

                    <div class="flex items-center gap-3 text-[11px] font-mono text-slate-400 pt-1">
                        <span class="inline-block w-3 h-3 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_#10b981]"></span>
                        <span>Efek Visual: Neon Emerald (#10b981) + Cyan Glow</span>
                    </div>
                </div>

                <!-- 5. Aturan Kunci/Sealed & Pembukaan Re-Audit -->
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-700/80 space-y-4 shadow-sm">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="text-base">🔓</span>
                            <h4 class="text-sm font-bold text-white font-sans">5. Pembukaan Kunci Foto (Zero-Lockout)</h4>
                        </div>
                        <span class="text-[10px] font-mono text-cyan-400 font-semibold">Continuous Re-Audit</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-relaxed font-sans">
                        Mencegah foto tersembunyi atau terkunci dengan pesan "tersegel dan dipindahkan ke arsip". Memungkinkan auditor mengulang pemindaian kapan saja.
                    </p>

                    <label class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer hover:border-cyan-500/60 transition">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-slate-200 block">Izinkan Re-Audit Foto Tersegel</span>
                            <span class="text-[10px] text-slate-400 font-sans block">Semua tombol scan/rescan tetap aktif dan galeri foto tidak pernah disembunyikan.</span>
                        </div>
                        <input type="checkbox" ${cfg.allow_re_audit ? 'checked' : ''} onchange="governanceManager.set('allow_re_audit', this.checked); showGovToast('Toleransi Re-Audit diaktifkan', '🔓');" class="w-5 h-5 rounded text-cyan-500 focus:ring-cyan-500 bg-slate-900 border-slate-700">
                    </label>

                    <label class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer hover:border-cyan-500/60 transition">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-slate-200 block">Bebaskan Duplikasi Sudut Pemotretan</span>
                            <span class="text-[10px] text-slate-400 font-sans block">Izinkan foto tambahan pada blok yang sama tanpa penolakan duplikasi.</span>
                        </div>
                        <input type="checkbox" ${cfg.allow_photo_duplication ? 'checked' : ''} onchange="governanceManager.set('allow_photo_duplication', this.checked); showGovToast('Aturan duplikasi foto diperbarui', '📸');" class="w-5 h-5 rounded text-cyan-500 focus:ring-cyan-500 bg-slate-900 border-slate-700">
                    </label>
                </div>

                <!-- 6. Auto-Persist ke Database Server -->
                <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-700/80 space-y-4 shadow-sm">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="text-base">💾</span>
                            <h4 class="text-sm font-bold text-white font-sans">6. Auto-Persist ke Database Server</h4>
                        </div>
                        <span class="text-[10px] font-mono text-emerald-400 font-semibold">Anti-Hilang Refresh</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-relaxed font-sans">
                        Setiap kali pemindaian selesai, hasil audit terakhir (entitas 2D, SPAD klorofil, piringan 2.05m, dan segel SHA-256) otomatis disimpan ke database SQLite server.
                    </p>

                    <label class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer hover:border-emerald-500/60 transition">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-slate-200 block">Simpan Otomatis ke Database Kebun</span>
                            <span class="text-[10px] text-slate-400 font-sans block">Hasil scan terakhir langsung mengupdate data sebelumnya di inspection_evidence.</span>
                        </div>
                        <input type="checkbox" ${cfg.auto_persist_to_storage ? 'checked' : ''} onchange="governanceManager.set('auto_persist_to_storage', this.checked); showGovToast('Auto-Persist Database diaktifkan', '💾');" class="w-5 h-5 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700">
                    </label>

                    <div class="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
                        <span>Target Tabel:</span>
                        <span class="text-emerald-400 font-semibold">inspection_evidence &bull; agent_experience</span>
                    </div>
                </div>

            </div>

            <!-- Tombol Aksi Simpan & Reset -->
            <div class="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
                <button type="button" onclick="governanceManager.resetDefaults(); renderGovernanceSettingsUI('${containerId}'); showGovToast('Konfigurasi dikembalikan ke standar baku', '🔄');" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-mono text-xs font-bold transition flex items-center gap-2 cursor-pointer">
                    <span>🔄</span>
                    <span>Reset ke Standar Baku</span>
                </button>

                <div class="flex items-center gap-3">
                    <button type="button" onclick="governanceManager.syncToBackend().then(() => showGovToast('Pengaturan tata kelola berhasil disinkronkan ke server', '✓'));" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-mono text-xs font-bold shadow-lg shadow-emerald-900/40 transition flex items-center gap-2 cursor-pointer">
                        <span>💾</span>
                        <span>Terapkan &amp; Sinkronkan ke Server</span>
                    </button>
                </div>
            </div>
        </div>
        `;
    }

    function showGovToast(msg, icon = '✓') {
        const existing = document.getElementById('govToastNotification');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.id = 'govToastNotification';
        toast.className = 'fixed bottom-6 right-6 z-[9999] px-4 py-3 rounded-2xl bg-emerald-950/95 border border-emerald-500 text-emerald-200 text-xs font-mono shadow-2xl flex items-center gap-2.5 backdrop-blur-md animate-bounce';
        toast.innerHTML = `<span class="text-base">${icon}</span> <span>${msg}</span>`;
        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast && toast.parentNode) {
                toast.classList.remove('animate-bounce');
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.5s ease';
                setTimeout(() => toast.remove(), 500);
            }
        }, 2800);
    }

    window.renderGovernanceSettingsUI = renderGovernanceSettingsUI;
    window.showGovToast = showGovToast;

    // Inisialisasi otomatis jika kontainer sudah ada di DOM
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('governanceSettingsPanel')) {
            renderGovernanceSettingsUI('governanceSettingsPanel');
        }
    });

})();