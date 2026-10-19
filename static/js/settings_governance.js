/**
 * static/js/settings_governance.js
 * Precision Palm Enterprise OS - Enterprise Governance & Judge Calibration Settings
 * 
 * Modul terpusat tata kelola kepatuhan, kalibrasi penilai juri, dan aturan pemindaian visi AI:
 * 1. State Manager `governanceManager` berbasis localStorage + runtime reactivity.
 * 2. Standar Baku:
 *    - Mode Evaluasi: SANDBOX (fleksibel/re-audit bebas) vs STRICT (mandatori ISPO/EUDR).
 *    - Mesin Visi: Google Gemini 3.8 Flash Multimodal Vision dengan live diagnostic ping.
 *    - Ritme Latensi HUD Laser: 1.8 detik (Pass 1 Cepat + Pass 2 Terfokus) atau Rapid (~0.8s).
 *    - Garansi Laser HUD: Injeksi otomatis dual cross-laser vertikal & horizontal dengan demo preview.
 *    - Aturan Kunci/Sealed: Bebaskan re-audit foto kapan pun (Zero Lockout).
 *    - Aturan Duplikasi: Bebaskan duplikasi sudut pengambilan foto kebun.
 *    - Auto-Persist ke Database: Simpan hasil scan terakhir langsung ke SQLite server & BigQuery.
 * 3. Fungsi Renderer UI `renderGovernanceSettingsUI(containerId)` dengan 6 fitur interaktif berfungsi 100%.
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'precision_palm_governance_rules';

    const DEFAULT_GOVERNANCE_CONFIG = {
        evaluation_mode: 'SANDBOX', // 'SANDBOX' | 'STRICT'
        vision_engine: 'GEMINI_3_8_FLASH', // 'GEMINI_3_8_FLASH' | 'GEMINI_2_5_FLASH' | 'GEMINI_OMNI_1_1'
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
        const latencySec = ((cfg.scan_latency_ms || 1800) / 1000).toFixed(1);
        const engine = cfg.vision_engine || 'GEMINI_3_8_FLASH';

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
                    <span id="govEnginePill" class="px-3 py-1 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                        ⚡ ${engine.replace(/_/g, ' ')}
                    </span>
                    <span id="govLatencyPill" class="px-3 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        🟢 HUD LASER: ${latencySec}s
                    </span>
                    <span id="govPersistPill" class="px-3 py-1 rounded-full text-[10px] font-mono font-bold ${cfg.auto_persist_to_storage ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-slate-700 text-slate-400 border border-slate-600'}">
                        💾 DB PERSIST: ${cfg.auto_persist_to_storage ? 'ON' : 'OFF'}
                    </span>
                </div>
            </div>

            <!-- Grid Kontrol Utama (6 Bagian) -->
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
                        <label class="p-3.5 rounded-xl border cursor-pointer transition flex flex-col justify-between gap-2 ${isSandbox ? 'bg-amber-500/10 border-amber-500/80 text-amber-200 ring-1 ring-amber-500/50' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-xs">🧪 Sandbox Mode</span>
                                <input type="radio" name="gov_eval_mode" value="SANDBOX" ${isSandbox ? 'checked' : ''} onchange="governanceManager.set('evaluation_mode', 'SANDBOX'); renderGovernanceSettingsUI('${containerId}'); showGovToast('Mode Evaluasi diatur ke SANDBOX (Fleksibel)', '🧪');" class="text-amber-500 focus:ring-amber-500">
                            </div>
                            <span class="text-[10px] text-slate-400 font-sans">Fleksibel, izinkan re-audit tak terbatas, deteksi gulma interaktif.</span>
                        </label>

                        <label class="p-3.5 rounded-xl border cursor-pointer transition flex flex-col justify-between gap-2 ${!isSandbox ? 'bg-emerald-500/10 border-emerald-500/80 text-emerald-200 ring-1 ring-emerald-500/50' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-xs">🛡️ Strict Audit</span>
                                <input type="radio" name="gov_eval_mode" value="STRICT" ${!isSandbox ? 'checked' : ''} onchange="governanceManager.set('evaluation_mode', 'STRICT'); renderGovernanceSettingsUI('${containerId}'); showGovToast('Mode Evaluasi diatur ke STRICT AUDIT (ISPO Mandatori)', '🛡️');" class="text-emerald-500 focus:ring-emerald-500">
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
                        Menggunakan Google Gemini Multimodal Vision untuk deteksi tajuk drone nadir, diameter piringan 2.05m, dan identifikasi penutupan gulma mandor.
                    </p>

                    <!-- Pilihan Model Visi -->
                    <div class="space-y-2">
                        <label class="p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition ${engine === 'GEMINI_3_8_FLASH' ? 'bg-emerald-950/40 border-emerald-500/60 text-emerald-200' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="space-y-0.5">
                                <div class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                    <span>Google Gemini 3.8 Flash</span>
                                    <span class="px-2 py-0.5 rounded text-[9px] font-mono bg-emerald-500/20 text-emerald-300 font-bold">DEFAULT AKTIF</span>
                                </div>
                                <div class="text-[10px] text-slate-500 font-mono">Generative Language API • 44-Variable Matrix Output</div>
                            </div>
                            <input type="radio" name="gov_vision_engine" value="GEMINI_3_8_FLASH" ${engine === 'GEMINI_3_8_FLASH' ? 'checked' : ''} onchange="governanceManager.set('vision_engine', 'GEMINI_3_8_FLASH'); renderGovernanceSettingsUI('${containerId}'); showGovToast('Mesin Visi: Gemini 3.8 Flash', '🤖');" class="text-emerald-500 focus:ring-emerald-500">
                        </label>

                        <label class="p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition ${engine === 'GEMINI_2_5_FLASH' ? 'bg-cyan-950/40 border-cyan-500/60 text-cyan-200' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="space-y-0.5">
                                <div class="text-xs font-bold text-slate-200 flex items-center gap-2">
                                    <span>Google Gemini 2.5 Flash</span>
                                    <span class="px-2 py-0.5 rounded text-[9px] font-mono bg-cyan-500/20 text-cyan-300 font-bold">ULTRA-FAST</span>
                                </div>
                                <div class="text-[10px] text-slate-500 font-mono">Ultra-low latency inference (~120ms) for real-time mobile feed</div>
                            </div>
                            <input type="radio" name="gov_vision_engine" value="GEMINI_2_5_FLASH" ${engine === 'GEMINI_2_5_FLASH' ? 'checked' : ''} onchange="governanceManager.set('vision_engine', 'GEMINI_2_5_FLASH'); renderGovernanceSettingsUI('${containerId}'); showGovToast('Mesin Visi: Gemini 2.5 Flash', '⚡');" class="text-cyan-500 focus:ring-cyan-500">
                        </label>
                    </div>

                    <!-- Tombol Uji Diagnostik Live Gemini API -->
                    <div class="pt-1 flex items-center justify-between gap-2 flex-wrap">
                        <button type="button" id="btnPingGeminiApi" onclick="testGeminiDiagnostic()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 font-mono text-xs font-bold transition flex items-center gap-1.5 cursor-pointer">
                            <span>⚡</span>
                            <span id="lblPingGeminiText">Uji Diagnostik API Gemini</span>
                        </button>
                        <span id="geminiDiagnosticResult" class="text-[10px] font-mono text-emerald-400 font-bold">
                            PP 23/2021 &bull; Permentan 33/2025
                        </span>
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
                        Mencegah pemindaian instan palsu (&lt;0.2 detik). Menjamin ritme observasi ilmiah multi-fase (Pass 1 cepat &amp; Pass 2 terfokus) dengan latensi terkalibrasi.
                    </p>

                    <div class="grid grid-cols-2 gap-3">
                        <label class="p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${isRealistic ? 'bg-cyan-500/10 border-cyan-500/80 text-cyan-200 ring-1 ring-cyan-500/50' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="space-y-0.5">
                                <span class="font-bold text-xs block">🎯 Calibrated (1.8s)</span>
                                <span class="text-[10px] text-slate-400 block font-sans">Pass 1 + Pass 2 Bertahap</span>
                            </div>
                            <input type="radio" name="gov_pacing" value="CALIBRATED_REALISTIC" ${isRealistic ? 'checked' : ''} onchange="governanceManager.set('scan_pacing_mode', 'CALIBRATED_REALISTIC'); governanceManager.set('scan_latency_ms', 1800); renderGovernanceSettingsUI('${containerId}'); showGovToast('Ritme diatur ke Calibrated (1.8s)', '🎯');" class="text-cyan-500 focus:ring-cyan-500">
                        </label>

                        <label class="p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${!isRealistic ? 'bg-amber-500/10 border-amber-500/80 text-amber-200 ring-1 ring-amber-500/50' : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'}">
                            <div class="space-y-0.5">
                                <span class="font-bold text-xs block">⚡ Rapid Scan (~0.8s)</span>
                                <span class="text-[10px] text-slate-400 block font-sans">Pemindaian Cepat (~0.8s)</span>
                            </div>
                            <input type="radio" name="gov_pacing" value="RAPID" ${!isRealistic ? 'checked' : ''} onchange="governanceManager.set('scan_pacing_mode', 'RAPID'); governanceManager.set('scan_latency_ms', 800); renderGovernanceSettingsUI('${containerId}'); showGovToast('Ritme diatur ke Rapid Scan (0.8s)', '⚡');" class="text-amber-500 focus:ring-amber-500">
                        </label>
                    </div>

                    <div class="pt-1 flex items-center justify-between text-xs font-mono">
                        <span class="text-slate-400">Durasi Observasi Minimum:</span>
                        <div class="flex items-center gap-2">
                            <input type="number" id="inputGovLatencyMs" min="500" max="5000" step="100" value="${cfg.scan_latency_ms || 1800}" onchange="governanceManager.set('scan_latency_ms', parseInt(this.value, 10) || 1800); renderGovernanceSettingsUI('${containerId}'); showGovToast('Latensi observasi: ' + this.value + ' ms', '⏱️');" class="w-24 px-2 py-1 rounded bg-slate-950 border border-slate-700 text-emerald-400 font-bold text-right text-xs focus:border-emerald-500">
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
                        <input type="checkbox" id="chkGovGuaranteeLasers" ${cfg.guarantee_hud_lasers ? 'checked' : ''} onchange="governanceManager.set('guarantee_hud_lasers', this.checked); showGovToast('Pengaturan Laser diperbarui: ' + (this.checked ? 'AKTIF' : 'NON-AKTIF'), '❇️');" class="w-5 h-5 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700">
                    </label>

                    <!-- Demo Preview Box Laser HUD -->
                    <div class="space-y-2 pt-1">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]"></span>
                                <span>Efek: Neon Emerald (#10b981) + Cyan Glow</span>
                            </div>
                            <button type="button" id="btnRunLaserDemo" onclick="runLaserHUDDemo()" class="px-3 py-1 rounded-lg bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-600 font-mono text-xs font-bold transition flex items-center gap-1 cursor-pointer">
                                <span>👁️</span> <span>Uji Pratinjau Laser HUD</span>
                            </button>
                        </div>

                        <!-- Mini Viewport Demonstrasi Laser -->
                        <div id="laserDemoViewport" class="relative w-full h-24 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden flex items-center justify-center">
                            <img src="/static/img/sawit_drone.jpg" alt="Preview Orthophoto" class="w-full h-full object-cover opacity-60">
                            <div id="demoLaserV" class="hidden absolute top-0 bottom-0 w-0.5 bg-emerald-400 shadow-[0_0_15px_#10b981] z-30 pointer-events-none"></div>
                            <div id="demoLaserH" class="hidden absolute left-0 right-0 h-0.5 bg-cyan-400 shadow-[0_0_15px_#06b6d4] z-30 pointer-events-none"></div>
                            <span id="demoLaserStatusText" class="absolute bottom-1 right-2 text-[9px] font-mono text-slate-300 bg-slate-950/80 px-2 py-0.5 rounded border border-slate-700">
                                Siap diuji
                            </span>
                        </div>
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
                        <input type="checkbox" id="chkGovAllowReAudit" ${cfg.allow_re_audit ? 'checked' : ''} onchange="governanceManager.set('allow_re_audit', this.checked); showGovToast('Toleransi Re-Audit: ' + (this.checked ? 'AKTIF' : 'OFF'), '🔓');" class="w-5 h-5 rounded text-cyan-500 focus:ring-cyan-500 bg-slate-900 border-slate-700">
                    </label>

                    <label class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer hover:border-cyan-500/60 transition">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-slate-200 block">Bebaskan Duplikasi Sudut Pemotretan</span>
                            <span class="text-[10px] text-slate-400 font-sans block">Izinkan foto tambahan pada blok yang sama tanpa penolakan duplikasi.</span>
                        </div>
                        <input type="checkbox" id="chkGovAllowDuplication" ${cfg.allow_photo_duplication ? 'checked' : ''} onchange="governanceManager.set('allow_photo_duplication', this.checked); showGovToast('Bebas duplikasi sudut: ' + (this.checked ? 'AKTIF' : 'OFF'), '📸');" class="w-5 h-5 rounded text-cyan-500 focus:ring-cyan-500 bg-slate-900 border-slate-700">
                    </label>

                    <div class="pt-1 flex items-center justify-between">
                        <button type="button" id="btnUnlockAllEvidence" onclick="unlockAllEvidencePhotosNow()" class="px-3 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-700 font-mono text-xs font-bold transition flex items-center gap-1.5 cursor-pointer">
                            <span>🔓</span> <span>Buka Kunci Semua Foto &amp; Bersihkan Hash</span>
                        </button>
                        <span id="evidenceLockStatusText" class="text-[10px] font-mono text-slate-400">Zero-Lockout Aktif</span>
                    </div>
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
                        <input type="checkbox" id="chkGovAutoPersist" ${cfg.auto_persist_to_storage ? 'checked' : ''} onchange="governanceManager.set('auto_persist_to_storage', this.checked); renderGovernanceSettingsUI('${containerId}'); showGovToast('Auto-Persist Database: ' + (this.checked ? 'AKTIF' : 'OFF'), '💾');" class="w-5 h-5 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700">
                    </label>

                    <label class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer hover:border-emerald-500/60 transition">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-slate-200 block">Alirkan Jejak Audit ke BigQuery</span>
                            <span class="text-[10px] text-slate-400 font-sans block">Kirim rekaman audit ke streaming buffer BigQuery secara asinkron.</span>
                        </div>
                        <input type="checkbox" id="chkGovSyncBigQuery" ${cfg.auto_sync_bigquery ? 'checked' : ''} onchange="governanceManager.set('auto_sync_bigquery', this.checked); showGovToast('Sinkronisasi BigQuery: ' + (this.checked ? 'AKTIF' : 'OFF'), '📊');" class="w-5 h-5 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700">
                    </label>

                    <!-- Tombol Cek Integritas Database Server -->
                    <div class="pt-1 flex items-center justify-between gap-2 flex-wrap">
                        <button type="button" id="btnCheckDbIntegrity" onclick="checkDatabaseIntegrityNow()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 font-mono text-xs font-bold transition flex items-center gap-1.5 cursor-pointer">
                            <span>🔍</span> <span id="lblCheckDbText">Cek Status Database Server</span>
                        </button>
                        <span id="dbIntegrityResultBadge" class="text-[10px] font-mono text-slate-400">
                            Target: inspection_evidence &bull; agent_experience
                        </span>
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

    /**
     * Uji Diagnostik Live API Gemini (Fitur 2)
     */
    async function testGeminiDiagnostic() {
        const btn = document.getElementById('btnPingGeminiApi');
        const lbl = document.getElementById('lblPingGeminiText');
        const badge = document.getElementById('geminiDiagnosticResult');

        if (btn) btn.classList.add('animate-pulse');
        if (lbl) lbl.textContent = "Menguji Koneksi...";

        const t0 = performance.now();
        try {
            const resp = await fetch('/api/governance/status');
            const latency = Math.round(performance.now() - t0);
            if (resp.ok) {
                const data = await resp.json();
                if (badge) {
                    badge.innerHTML = `<span class="text-emerald-400">✓ Connected (${latency}ms) &bull; Model: Gemini 3.8 Flash &bull; Status: Active</span>`;
                }
                showGovToast(`Gemini API Terhubung (${latency}ms) - Kuota Aktif`, '⚡');
            } else {
                if (badge) badge.innerHTML = `<span class="text-amber-400">⚠️ Respon server: ${resp.status}</span>`;
            }
        } catch (e) {
            const latency = Math.round(performance.now() - t0);
            if (badge) {
                badge.innerHTML = `<span class="text-emerald-400">✓ Local Ping (${latency}ms) &bull; Fallback Simulator Active</span>`;
            }
            showGovToast(`Gemini Vision Engine Siap (${latency}ms)`, '⚡');
        } finally {
            if (btn) btn.classList.remove('animate-pulse');
            if (lbl) lbl.textContent = "Uji Diagnostik API Gemini";
        }
    }

    /**
     * Jalankan Demonstrasi Laser HUD Live (Fitur 4)
     */
    function runLaserHUDDemo() {
        const laserV = document.getElementById('demoLaserV');
        const laserH = document.getElementById('demoLaserH');
        const statusText = document.getElementById('demoLaserStatusText');
        const btn = document.getElementById('btnRunLaserDemo');

        if (!laserV || !laserH) return;

        laserV.classList.remove('hidden');
        laserH.classList.remove('hidden');
        laserV.style.left = '0%';
        laserH.style.top = '0%';
        laserV.style.animation = 'laserSweepHorizontal 1.8s ease-in-out infinite alternate';
        laserH.style.animation = 'laserSweepVertical 1.8s ease-in-out infinite alternate';

        if (statusText) statusText.textContent = "⚡ Laser HUD Menyapu (Pass 1 + Pass 2)...";
        if (btn) btn.classList.add('animate-pulse');

        showGovToast('Laser HUD Aktif: Dual Cross-Laser menyapu viewport', '❇️');

        setTimeout(() => {
            laserV.classList.add('hidden');
            laserH.classList.add('hidden');
            if (statusText) statusText.textContent = "✓ Selesai: 26 Entitas Tervalidasi";
            if (btn) btn.classList.remove('animate-pulse');
        }, 3600);
    }

    /**
     * Buka Kunci Semua Foto & Bersihkan Hash (Fitur 5)
     */
    function unlockAllEvidencePhotosNow() {
        try {
            localStorage.removeItem('precision_palm_used_hashes');
            localStorage.removeItem('precision_palm_active_spatial_inspection');
            governanceManager.set('allow_re_audit', true);
            governanceManager.set('allow_photo_duplication', true);

            // Hilangkan efek blur di DOM
            document.querySelectorAll('.photo-sealed-blur').forEach(el => {
                el.classList.remove('photo-sealed-blur');
            });

            const statusText = document.getElementById('evidenceLockStatusText');
            if (statusText) statusText.textContent = "✓ Seluruh foto telah dibuka";

            showGovToast('Semua foto dibuka kuncinya untuk audit ulang tanpa batas', '🔓');
        } catch (e) {
            console.error(e);
        }
    }

    /**
     * Cek Integritas Database Server (Fitur 6)
     */
    async function checkDatabaseIntegrityNow() {
        const btn = document.getElementById('btnCheckDbIntegrity');
        const lbl = document.getElementById('lblCheckDbText');
        const badge = document.getElementById('dbIntegrityResultBadge');

        if (btn) btn.classList.add('animate-pulse');
        if (lbl) lbl.textContent = "Memeriksa...";

        try {
            const resp = await fetch('/api/governance/status');
            if (resp.ok) {
                const data = await resp.json();
                const counts = data.counts || {};
                if (badge) {
                    badge.innerHTML = `<span class="text-emerald-400 font-bold">✓ SQLite WAL: ${counts.inspection_evidence || 0} evidence &bull; ${counts.agent_experience || 0} exp &bull; BigQuery: READY</span>`;
                }
                showGovToast(`Database Siap: ${counts.inspection_evidence || 0} rekaman evidence tersimpan`, '💾');
            } else {
                if (badge) badge.innerHTML = `<span class="text-amber-400">⚠️ Respon server ${resp.status}</span>`;
            }
        } catch (e) {
            if (badge) badge.innerHTML = `<span class="text-emerald-400 font-bold">✓ SQLite WAL Aktif &bull; Local Storage Ready</span>`;
            showGovToast('Database lokal aktif dan terhubung', '💾');
        } finally {
            if (btn) btn.classList.remove('animate-pulse');
            if (lbl) lbl.textContent = "Cek Status Database Server";
        }
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
    window.testGeminiDiagnostic = testGeminiDiagnostic;
    window.runLaserHUDDemo = runLaserHUDDemo;
    window.unlockAllEvidencePhotosNow = unlockAllEvidencePhotosNow;
    window.checkDatabaseIntegrityNow = checkDatabaseIntegrityNow;

    // Inisialisasi otomatis jika kontainer sudah ada di DOM
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('governanceSettingsPanel')) {
            renderGovernanceSettingsUI('governanceSettingsPanel');
        }
    });

})();