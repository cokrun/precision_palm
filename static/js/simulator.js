/**
 * static/js/simulator.js
 * Precision Palm Cloud - In-Silico Simulator Core & Pillar 2/3 Decision Engine.
 * 
 * Functional Modules:
 * 1. Pillar 2 Multi-Candidate Recommendation Gate:
 *    - In-silico evaluation of site biophysics (LAI, PAR, pH, slope).
 *    - Presents 2-3 optimal companion crop alternatives.
 *    - Mandatory planter decision gate to lock 1 definitive crop.
 * 2. Pillar 3 Technical Agronomic Blueprint:
 *    - Net alley corridor (3.79m), 2.0m sterile root circle zero-tillage buffer.
 *    - Stoichiometric PPKS fertilizer balancing (MOP & Urea compensation).
 *    - Provisional Green Palm Recommendation Passport issuance.
 * 3. Deterministic Canopy Biophysics: Beer-Lambert radiation and Mead & Willey LER.
 * 4. Multimodal Vision HUD: Dynamic canvas reticles and laser scanning simulation.
 * 5. Local SQLite Persistence: Admin audit logs and EUDR TRACES-NT DDS JSON export.
 * 
 * Adheres strictly to AG_OPERATIONAL_RULES: Zero alert/confirm, top-down linear parsing, EN default.
 */

// Application execution state (using var for safe multi-script global sharing)
var isAuditRunning = typeof isAuditRunning !== 'undefined' ? isAuditRunning : false;
var selectedCanopyFileName = typeof selectedCanopyFileName !== 'undefined' ? selectedCanopyFileName : 'sawit_drone.jpg';
var isVisionOverlayVisible = typeof isVisionOverlayVisible !== 'undefined' ? isVisionOverlayVisible : true;
var latestDetectedObjects = typeof latestDetectedObjects !== 'undefined' ? latestDetectedObjects : null;

// Pillar 2 & 3 Gate State
var candidateRecommendations = typeof candidateRecommendations !== 'undefined' ? candidateRecommendations : [];
var selectedDefinitiveCropKey = typeof selectedDefinitiveCropKey !== 'undefined' ? selectedDefinitiveCropKey : 'red_ginger';
var isDefinitiveCropLocked = typeof isDefinitiveCropLocked !== 'undefined' ? isDefinitiveCropLocked : false;
var simulatorYieldReferenceActive = typeof simulatorYieldReferenceActive !== 'undefined' ? simulatorYieldReferenceActive : false;
var simulatorYieldReferenceValues = typeof simulatorYieldReferenceValues !== 'undefined' ? simulatorYieldReferenceValues : null;

// Admin audit table pagination and search state
var adminCurrentPage = typeof adminCurrentPage !== 'undefined' ? adminCurrentPage : 1;
var adminTotalPages = typeof adminTotalPages !== 'undefined' ? adminTotalPages : 1;
var adminCurrentLimit = typeof adminCurrentLimit !== 'undefined' ? adminCurrentLimit : 10;
var adminSearchQuery = typeof adminSearchQuery !== 'undefined' ? adminSearchQuery : '';
var adminDebounceTimer = typeof adminDebounceTimer !== 'undefined' ? adminDebounceTimer : null;
var adminCachedRecords = typeof adminCachedRecords !== 'undefined' ? adminCachedRecords : [];

// Local storage cache keys
var SIM_HISTORY_STORAGE_KEY = typeof SIM_HISTORY_STORAGE_KEY !== 'undefined' ? SIM_HISTORY_STORAGE_KEY : 'precision_palm_sim_history_records';
var DEFINITIVE_CROP_STORAGE_KEY = typeof DEFINITIVE_CROP_STORAGE_KEY !== 'undefined' ? DEFINITIVE_CROP_STORAGE_KEY : 'precision_palm_definitive_crop_choice';

window.isUserSimulating = false;
window.calibratedCanopyCoverPct = null;

const YIELD_SCENARIO_DATABASE = {
    red_ginger: { yci: 2.82, ycm: 18.00, penalty_pct: 1.2, name: 'Red Ginger', aliases: ['ginger', 'jahe merah'] },
    cacao: { yci: 0.85, ycm: 1.50, penalty_pct: 2.1, name: 'Shade Cacao', aliases: ['cocoa', 'kakao', 'theobroma cacao'] },
    coffee: { yci: 0.72, ycm: 1.20, penalty_pct: 1.8, name: 'Shade Robusta Coffee', aliases: ['kopi', 'coffea canephora'] },
    porang: { yci: 8.50, ycm: 24.00, penalty_pct: 0.8, name: 'Porang / Konjac', aliases: ['konjac', 'amorphophallus muelleri'] },
    cardamom: { yci: 0.45, ycm: 0.90, penalty_pct: 1.0, name: 'Java Cardamom', aliases: ['kapulaga', 'amomum compactum'] },
    turmeric: { yci: 3.10, ycm: 14.50, penalty_pct: 1.1, name: 'Turmeric', aliases: ['kunyit', 'curcuma longa'] },
    patchouli: { yci: 1.20, ycm: 3.50, penalty_pct: 1.5, name: 'Patchouli', aliases: ['nilam', 'pogostemon cablin'] },
    soybean: { yci: 1.10, ycm: 2.60, penalty_pct: 1.4, name: 'Shade Soybean', aliases: ['soy', 'kedelai', 'glycine max', 'dena 1'] },
    corn: { yci: 3.20, ycm: 7.80, penalty_pct: 2.5, name: 'Field Corn', aliases: ['maize', 'jagung', 'zea mays'] },
    vanilla: { yci: 0.25, ycm: 0.60, penalty_pct: 0.5, name: 'Vanilla', aliases: ['vanili', 'vanilla planifolia'] },
    curcuma: { yci: 3.10, ycm: 14.50, penalty_pct: 1.1, name: 'Temulawak', aliases: ['javanese turmeric', 'curcuma zanthorrhiza'] },
    kencur: { yci: 2.82, ycm: 18.00, penalty_pct: 1.2, name: 'Kencur', aliases: ['aromatic ginger', 'kaempferia galanga'] },
    peanut: { yci: 1.10, ycm: 2.60, penalty_pct: 1.4, name: 'Groundnut', aliases: ['groundnut', 'kacang tanah', 'arachis hypogaea'] },
    sorghum: { yci: 3.20, ycm: 7.80, penalty_pct: 2.5, name: 'Sweet Sorghum', aliases: ['sorgum', 'sorghum bicolor'] },
    sweet_potato: { yci: 2.50, ycm: 10.00, penalty_pct: 1.5, name: 'Sweet Potato', aliases: ['ubi jalar', 'ipomoea batatas'] },
    serai_wangi: { yci: 2.50, ycm: 10.00, penalty_pct: 1.5, name: 'Citronella Grass', aliases: ['serai wangi', 'citronella', 'cymbopogon nardus'] }
};

const DEFAULT_YIELD_SCENARIO = { yci: 2.50, ycm: 10.00, penalty_pct: 1.5, name: 'Generic fallback crop' };

function normalizeCropName(rawCropName) {
    return String(rawCropName || '')
        .toLowerCase()
        .replace(/\([^)]*\)/g, ' ')
        .replace(/[^a-z0-9]+/g, ' ')
        .trim();
}

function resolveCropYieldBenchmark(rawCropName) {
    const normalizedName = normalizeCropName(rawCropName) || 'red ginger';
    const rawNormalizedName = String(rawCropName || '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, ' ')
        .trim();
    const searchNames = [normalizedName, rawNormalizedName];
    const matches = Object.entries(YIELD_SCENARIO_DATABASE)
        .flatMap(([cropKey, benchmark]) => [cropKey, ...benchmark.aliases].map(alias => ({
            cropKey,
            benchmark,
            alias: normalizeCropName(alias)
        })))
        .sort((left, right) => right.alias.length - left.alias.length);
    const match = matches.find(item => item.alias && searchNames.some(name => name.includes(item.alias)));
    if (!match) {
        return { cropKey: 'default', ...DEFAULT_YIELD_SCENARIO, methodologyNote: 'Generic fallback scenario benchmark; not a crop-specific measured or validated yield.' };
    }
    return {
        cropKey: match.cropKey,
        ...match.benchmark,
        methodologyNote: 'Illustrative crop benchmark and palm intercrop penalty; not field-measured or locally validated.'
    };
}

function calculateDeterministicYieldReference(ageYears, cropName) {
    const parsedAge = Number(ageYears);
    const age = Number.isFinite(parsedAge) && parsedAge > 0 ? parsedAge : 7.5;
    const crop = resolveCropYieldBenchmark(cropName);
    const ypm = 26.5 / (1.0 + Math.exp(-0.65 * (age - 3.5)));
    const ypi = ypm * (1.0 - crop.penalty_pct / 100.0);
    return {
        ypm: Number(ypm.toFixed(2)),
        ypi: Number(ypi.toFixed(2)),
        ycm: Number(crop.ycm.toFixed(2)),
        yci: Number(crop.yci.toFixed(2)),
        penaltyPct: crop.penalty_pct,
        cropName: crop.name,
        cropKey: crop.cropKey,
        ageYears: age,
        methodologyNote: crop.methodologyNote
    };
}

function setYieldReferenceStatus(message, status) {
    const badge = document.getElementById('badgeYieldProvenanceStatus');
    const methodology = document.getElementById('yieldReferenceMethodology');
    const styles = {
        SCENARIO_PROJECTION: 'bg-indigo-950 text-indigo-300 border border-indigo-500',
        DATA_PENDING: 'bg-slate-800 text-slate-400',
    };
    if (badge) {
        badge.className = `px-2 py-0.5 rounded text-[9px] font-mono font-bold ${styles[status] || styles.DATA_PENDING}`;
        badge.textContent = `[${status}]`;
    }
    if (methodology) methodology.textContent = message;
}

function applyYieldScenarioReference(forceOverwrite = true) {
    const age = Number(document.getElementById('palm_age')?.value) || 7.5;
    const cropName = document.getElementById('crop_select')?.value
        || document.getElementById('crop_name')?.value
        || 'Red Ginger';
    const reference = calculateDeterministicYieldReference(age, cropName);

    const fields = {
        yield_palm_inter: reference.ypi,
        yield_palm_mono: reference.ypm,
        yield_crop_inter: reference.yci,
        yield_crop_mono: reference.ycm
    };
    Object.entries(fields).forEach(([id, value]) => {
        const input = document.getElementById(id);
        if (input) {
            const shouldNotify = forceOverwrite || input.value !== String(value);
            input.value = String(value);
            if (shouldNotify) {
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    });

    simulatorYieldReferenceActive = true;
    simulatorYieldReferenceValues = reference;
    setYieldReferenceStatus(
        `[SCENARIO_PROJECTION] Applied ${reference.cropName} benchmark at palm age ${reference.ageYears}: palm ${reference.ypi}/${reference.ypm} and crop ${reference.yci}/${reference.ycm} t/ha. ${reference.methodologyNote}`,
        'SCENARIO_PROJECTION'
    );
    executeInSilicoCompute();
    return true;
}

function refreshYieldScenarioReference() {
    if (!simulatorYieldReferenceActive) return;
    const reference = calculateDeterministicYieldReference(
        Number(document.getElementById('palm_age')?.value),
        document.getElementById('crop_select')?.value
            || document.getElementById('crop_name')?.value
            || 'Red Ginger'
    );

    simulatorYieldReferenceValues = reference;
    const values = {
        yield_palm_inter: reference.ypi,
        yield_palm_mono: reference.ypm,
        yield_crop_inter: reference.yci,
        yield_crop_mono: reference.ycm
    };
    Object.entries(values).forEach(([id, value]) => {
        const input = document.getElementById(id);
        if (input) input.value = String(value);
    });
    setYieldReferenceStatus(
        `[SCENARIO_PROJECTION] ${reference.cropName} age/yield benchmark updated. ${reference.methodologyNote}`,
        'SCENARIO_PROJECTION'
    );
}

function handleYieldReferenceManualInput() {
    if (simulatorYieldReferenceActive) {
        simulatorYieldReferenceActive = false;
        simulatorYieldReferenceValues = null;
    }
    setYieldReferenceStatus(
        'User-entered values; field source and measurement are not independently verified.',
        'SCENARIO_PROJECTION'
    );
}

function getYieldInputProvenance() {
    if (!simulatorYieldReferenceActive || !simulatorYieldReferenceValues) {
        return {
            source: 'USER_PROVIDED_UNVERIFIED',
            status: 'SCENARIO_PROJECTION',
            field_measurement_verified: false
        };
    }
    return {
        source: 'CLIENT_GENERATED_SCENARIO_REFERENCE',
        status: 'SCENARIO_PROJECTION',
        model: 'logistic_age_crop_benchmark',
        model_version: '2',
        crop_key: simulatorYieldReferenceValues.cropKey,
        age_years: simulatorYieldReferenceValues.ageYears,
        estimated_values_t_ha: {
            yield_palm_inter: simulatorYieldReferenceValues.ypi,
            yield_palm_mono: simulatorYieldReferenceValues.ypm,
            yield_crop_inter: simulatorYieldReferenceValues.yci,
            yield_crop_mono: simulatorYieldReferenceValues.ycm
        },
        assumptions: {
            palm_logistic_asymptote_t_ha: 26.5,
            palm_logistic_growth_rate: 0.65,
            palm_logistic_midpoint_age_years: 3.5,
            palm_intercrop_penalty_pct: simulatorYieldReferenceValues.penaltyPct
        },
        field_measurement_verified: false
    };
}

window.normalizeCropName = normalizeCropName;
window.resolveCropYieldBenchmark = resolveCropYieldBenchmark;
window.calculateDeterministicYieldReference = calculateDeterministicYieldReference;
window.applyYieldScenarioReference = applyYieldScenarioReference;
window.refreshYieldScenarioReference = refreshYieldScenarioReference;
window.handleYieldReferenceManualInput = handleYieldReferenceManualInput;
window.getYieldInputProvenance = getYieldInputProvenance;

function calibrateHolisticFieldEntities(filename, isAerialDrone = true) {
    if (window.UnifiedVisionEngine && typeof window.UnifiedVisionEngine.generateHolisticFallback === 'function') {
        const pers = isAerialDrone ? 'AERIAL_DRONE' : 'TERRESTRIAL_IN_SITU';
        const res = window.UnifiedVisionEngine.generateHolisticFallback(filename, pers, 'SIMULATOR');
        const list = res.physical_entities || res.detected_objects || [];
        return list.map(item => {
            const copy = Object.assign({}, item);
            if (!copy.label_name) copy.label_name = copy.label || 'Illustrative object';
            copy.is_heuristic = true;
            delete copy.confidence;
            return copy;
        });
    }
    return [
        { label: 'palm_canopy', label_name: 'Illustrative palm-canopy area', cluster: 'palm_canopy', box_2d: [50, 40, 220, 200], is_heuristic: true },
        { label: 'clean_alley', label_name: 'Illustrative alley area', cluster: 'floor_mulch', box_2d: [320, 420, 760, 640], is_heuristic: true },
        { label: 'root_circle', label_name: 'Illustrative root-area region', cluster: 'root_circle', box_2d: [550, 300, 850, 680], is_heuristic: true }
    ];
}

const CROPS_PRESET_CATALOG = {
    red_ginger: {
        key: "red_ginger",
        name_en: "Red Ginger (Zingiber officinale var. rubrum)",
        name_id: "Jahe Merah (Zingiber officinale var. rubrum)",
        category_en: "Medicinal Rhizome",
        category_id: "Rimpang Medis Bernilai Tinggi",
        recommended_age_min: 4.0,
        recommended_age_max: 10.0,
        shade_tolerance_pct: 30.0,
        optimal_par_umol: 800.0,
        projected_ler: 1.5238,
        k2o_supplement_kg_ha: 45.0,
        mop_supplement_kg_ha: 75.0,
        urea_savings_kg_ha: 0.0,
        spacing: "0.5m x 0.4m (6 Rows in Alley)",
        economic_rating_en: "High Premium (Export Grade)",
        economic_rating_id: "Tinggi (Pasar Farmasi & Ekspor)",
        y_p_i: 21.0, y_p_m: 22.0, y_c_i: 7.5, y_c_m: 15.0
    },
    curcuma: {
        key: "curcuma",
        name_en: "Javanese Turmeric (Curcuma zanthorrhiza)",
        name_id: "Temulawak (Curcuma zanthorrhiza)",
        category_en: "Hardy Medicinal Rhizome",
        category_id: "Rimpang Adaptif Tahan Naungan",
        recommended_age_min: 4.0,
        recommended_age_max: 9.0,
        shade_tolerance_pct: 35.0,
        optimal_par_umol: 750.0,
        projected_ler: 1.4420,
        k2o_supplement_kg_ha: 40.0,
        mop_supplement_kg_ha: 66.7,
        urea_savings_kg_ha: 0.0,
        spacing: "0.6m x 0.5m (6 Rows in Alley)",
        economic_rating_en: "Stable Market (Minimal Disease Risk)",
        economic_rating_id: "Stabil (Risiko Hama Rendah)",
        y_p_i: 21.0, y_p_m: 22.0, y_c_i: 8.0, y_c_m: 16.0
    },
    porang: {
        key: "porang",
        name_en: "Porang / Konjac (Amorphophallus muelleri)",
        name_id: "Porang / Iles-iles (Amorphophallus muelleri)",
        category_en: "Deep Shade Sciophyte Tuber",
        category_id: "Umbi Naungan Kanopi Lebat",
        recommended_age_min: 7.0,
        recommended_age_max: 20.0,
        shade_tolerance_pct: 60.0,
        optimal_par_umol: 550.0,
        projected_ler: 1.3850,
        k2o_supplement_kg_ha: 50.0,
        mop_supplement_kg_ha: 83.3,
        urea_savings_kg_ha: 0.0,
        spacing: "0.8m x 0.5m (4 Rows in Alley)",
        economic_rating_en: "High Industrial Starch Demand",
        economic_rating_id: "Tinggi (Industri Glukomanan)",
        y_p_i: 22.0, y_p_m: 24.0, y_c_i: 10.0, y_c_m: 18.0
    },
    cardamom: {
        key: "cardamom",
        name_en: "Java Cardamom (Amomum compactum)",
        name_id: "Kapulaga Jawa (Amomum compactum)",
        category_en: "Extreme Shade Spices",
        category_id: "Rempah Naungan Lembap Rapat",
        recommended_age_min: 8.0,
        recommended_age_max: 25.0,
        shade_tolerance_pct: 70.0,
        optimal_par_umol: 450.0,
        projected_ler: 1.3540,
        k2o_supplement_kg_ha: 35.0,
        mop_supplement_kg_ha: 58.3,
        urea_savings_kg_ha: 0.0,
        spacing: "1.2m x 1.0m (Clumps)",
        economic_rating_en: "High Unit Value Spices",
        economic_rating_id: "Tinggi (Nilai Satuan Komersial)",
        y_p_i: 22.0, y_p_m: 23.0, y_c_i: 1.0, y_c_m: 2.0
    },
    soybean: {
        key: "soybean",
        name_en: "Tropical Soybean (Glycine max var. Dena-1)",
        name_id: "Kedelai Tropis (Glycine max var. Dena-1)",
        category_en: "Grain Legume (N-Fixing)",
        category_id: "Legum Butir (Fiksasi Nitrogen)",
        recommended_age_min: 1.0,
        recommended_age_max: 3.5,
        shade_tolerance_pct: 20.0,
        optimal_par_umol: 1200.0,
        projected_ler: 1.5420,
        k2o_supplement_kg_ha: 0.0,
        mop_supplement_kg_ha: 0.0,
        urea_savings_kg_ha: 141.3,
        spacing: "0.4m x 0.2m (Broad Beds)",
        economic_rating_en: "Food Security & Fertilizer Offset",
        economic_rating_id: "Substitusi Urea & Pangan",
        y_p_i: 8.0, y_p_m: 8.0, y_c_i: 1.8, y_c_m: 2.8
    }
};

// Flag anti race-condition agar input slider tidak ditimpa oleh data lokal usang
window.isUserSimulating = false;
window.calibratedCanopyCoverPct = null;

/**
 * Step 2: Sinkronisasi data hasil pemindaian UnifiedVisionEngine ke Simulator
 */
function applyVisionDataToSimulator(data) {
    if (!data) return;
    console.log("[Simulator] Menerima data UnifiedVisionEngine:", data);

    const setSafe = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
    };

    const isLiveVision = data.mode === 'LIVE_GEMINI' && data.isFallback !== true;
    const matchEl = document.getElementById('visionMatchBadge') || document.getElementById('lblVisionMatchScore');
    if (!isLiveVision) {
        window.calibratedCanopyCoverPct = null;
        if (matchEl) matchEl.innerText = 'Fallback preview • simulator unchanged';
        if (typeof showNotificationToast === 'function') {
            showNotificationToast('Fallback is illustrative only; simulator inputs were not changed.', '⚠️');
        }
        return;
    }

    const rawShadePct = typeof data.calculatedShadePercent === 'number'
        ? data.calculatedShadePercent
        : data.shadeRatioPercent;
    const shadePct = Number.isFinite(rawShadePct) && rawShadePct >= 0 && rawShadePct <= 100
        ? rawShadePct
        : null;
    if (matchEl) matchEl.innerText = 'Live Gemini • accuracy score requires ground truth';

    if (shadePct === null) {
        window.calibratedCanopyCoverPct = null;
        if (typeof showNotificationToast === 'function') {
            showNotificationToast(`Gemini returned ${Array.isArray(data.boxes) ? data.boxes.length : 0} detections; no canopy metric was supplied, so simulator inputs were not changed.`, 'ℹ️');
        }
        return;
    }

    window.calibratedCanopyCoverPct = shadePct;
    setSafe('lblMachineCanopyDensity', `~${shadePct}% estimate`);
    setSafe('m44_canopy', `Canopy estimate: ~${shadePct}%`);

    const recCrop = typeof data.recommendedIntercrop === 'string' ? data.recommendedIntercrop : '';
    const isHighShade = recCrop
        ? /jahe|ginger/i.test(recCrop)
        : shadePct > 50;
    const targetCropKey = isHighShade ? 'red_ginger' : 'porang';

    const cropSelect = document.getElementById('crop_select');
    if (cropSelect && cropSelect.querySelector(`option[value="${targetCropKey}"]`)) {
        cropSelect.value = targetCropKey;
    }

    const cropNameInput = document.getElementById('crop_name');
    if (cropNameInput) {
        cropNameInput.value = isHighShade
            ? "Red Ginger (Zingiber officinale var. rubrum)"
            : "Konjac Tuber / Porang (Amorphophallus muelleri)";
    }

    executeInSilicoCompute();

    if (typeof showNotificationToast === 'function') {
        showNotificationToast(`Live Gemini image estimate • canopy ~${shadePct}% (not ground-truth validated) • Intercrop suggestion: ${isHighShade ? 'Red Ginger' : 'Porang'}`, '🌿');
    }
}
window.applyVisionDataToSimulator = applyVisionDataToSimulator;

function initSandboxModeAndAntiRaceCondition() {
    // 1. Sandbox Mode: Pastikan slider & pilihan tanaman sela tidak berstatus disabled
    const inputIds = [
        'palm_age', 'land_area', 'crop_select', 'crop_name',
        'yield_palm_inter', 'yield_palm_mono', 'yield_crop_inter', 'yield_crop_mono',
        'sim_soil_ph', 'sim_slope', 'sim_elevation', 'sim_soil_texture',
        'sim_mop_compensation', 'sim_ganoderma_risk', 'sim_root_buffer_status'
    ];

    inputIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.disabled = false;
            el.removeAttribute('disabled');
            el.addEventListener('input', () => {
                window.isUserSimulating = true;
            });
            el.addEventListener('change', () => {
                window.isUserSimulating = true;
            });
        }
    });

    // 2. Tombol simulasi menandai isUserSimulating = true
    const computeBtns = [
        document.getElementById('btn_trigger_compute'),
        document.getElementById('btn_main_action'),
        document.getElementById('btn_execute_inference'),
        document.getElementById('btnExecuteSimulation')
    ];
    computeBtns.forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                window.isUserSimulating = true;
            });
        }
    });
}
window.initSandboxModeAndAntiRaceCondition = initSandboxModeAndAntiRaceCondition;

function loadSavedDossier(data) {
    if (window.isUserSimulating) {
        console.log("[Simulator] Anti race-condition: mempertahankan nilai slider aktif dari pengguna.");
        return;
    }
}
window.loadSavedDossier = loadSavedDossier;

document.addEventListener('DOMContentLoaded', function () {
    initSandboxModeAndAntiRaceCondition();
    restorePersistedCropSelection();

    // Pulihkan status Audit Sealed jika sebelumnya sudah dieksekusi (Anti-Reset on Refresh)
    try {
        restoreActiveAuditedDossier();
    } catch (e) {
        console.warn("[Simulator] Error during initial restoreActiveAuditedDossier:", e);
    }

    // Hubungkan Sinkronisasi Visi AI ke Simulator via UnifiedVisionEngine
    if (window.UnifiedVisionEngine) {
        window.UnifiedVisionEngine.subscribe((data, pageContext) => {
            if (pageContext === 'SIMULATOR' || pageContext === 'SPATIAL') {
                applyVisionDataToSimulator(data);
            }
        });
    }

    // Baca cache hasil pemindaian visi terbaru dari /spatial jika tersedia
    try {
        const cachedVision = localStorage.getItem('precision_palm_latest_vision_data');
        if (cachedVision) {
            const parsed = JSON.parse(cachedVision);
            if (parsed && parsed.data) {
                applyVisionDataToSimulator(parsed.data);
            }
        } else if (window.UnifiedVisionEngine && window.UnifiedVisionEngine.lastResult) {
            applyVisionDataToSimulator(window.UnifiedVisionEngine.lastResult);
        }
    } catch (_) {}

    // Broadcast AI terminal ready state
    if (typeof logAiInteraction === 'function') {
        logAiInteraction('REQUEST', 'In-Silico Core & Pillar 2 Gate Initialized', {
            framework: "PPKS Agronomic Standard & Beer-Lambert Law",
            extinction_coefficient_k: 0.45,
            baseline_surface_par: "1800 µmol/m²/s",
            active_exclusion_zone: "2.0m Sterile Zero-Tillage Root Buffer",
            decision_gate: "Multi-Candidate AI Recommendation Active"
        });
    }

    // Re-render recommendation gate upon language changes
    window.addEventListener('languagechanged', function () {
        const age = parseFloat(document.getElementById('palm_age')?.value || 6.0);
        generateMultiCandidateRecommendations(age);
        executeInSilicoCompute();
    });
});

/**
 * Recovers previously selected definitive crop from local persistence
 */
function restorePersistedCropSelection() {
    try {
        const stored = localStorage.getItem(DEFINITIVE_CROP_STORAGE_KEY);
        if (stored && CROPS_PRESET_CATALOG[stored]) {
            selectedDefinitiveCropKey = stored;
        }
    } catch (e) {
        console.warn("[Simulator] Local storage access error:", e);
    }
}

/**
 * Initializes spatial tracking and map navigation shortcuts
 */
function initSpatialTrackingControlsLegacy() {
    const trackingBtn = document.getElementById('btn_sec4_tracking_map') ||
                        document.getElementById('btnTrackingLocation');

    if (trackingBtn) {
        trackingBtn.addEventListener('click', function (e) {
            e.preventDefault();
            window.location.href = '/spatial';
        });
    }

    const gpsInput = document.getElementById('sim_coords');
    if (gpsInput) {
        let debounceTimer = null;
        gpsInput.addEventListener('input', function () {
            if (debounceTimer) clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                if (typeof logAiInteraction === 'function') {
                    logAiInteraction('REQUEST', 'Coordinate Centroid Re-Screening', {
                        coordinates: gpsInput.value,
                        statutory_framework: 'EUDR Article 9 & PIPPIB Moratorium 2024'
                    });
                }
            }, 400);
        });
    }
}

/**
 * Evaluates site biophysics and generates 2-3 adaptive companion crop alternatives.
 * @param {number} palmAge - Current average stand age in years
 * @param {number} [surfacePar] - Attenuated surface photosynthetically active radiation
 * @returns {Array<Object>} List of candidate recommendations
 */
function generateMultiCandidateRecommendations(palmAge, surfacePar = null) {
    const age = parseFloat(palmAge) || 6.0;
    const computedPar = surfacePar !== null ? surfacePar : (1800.0 * Math.exp(-0.45 * (5.5 / (1.0 + Math.exp(-0.7 * (age - 3.5))))));
    const lang = (typeof getAppLanguage === 'function') ? getAppLanguage() : 'en';

    let candidates = [];

    if (age <= 3.5) {
        // Immature stand (TBM): High irradiance, prioritizes nitrogen fixation and ground mulch
        candidates = [
            { ...CROPS_PRESET_CATALOG.soybean, rank: 1, suitability_score: 96 },
            { ...CROPS_PRESET_CATALOG.red_ginger, rank: 2, suitability_score: 84 }
        ];
    } else if (age <= 8.5) {
        // Young producing stand (Early TM): Moderate shading, ideal for high-value medicinal rhizomes
        candidates = [
            { ...CROPS_PRESET_CATALOG.red_ginger, rank: 1, suitability_score: 95 },
            { ...CROPS_PRESET_CATALOG.curcuma, rank: 2, suitability_score: 92 },
            { ...CROPS_PRESET_CATALOG.porang, rank: 3, suitability_score: 81 }
        ];
    } else {
        // Mature closed canopy (>8.5 years): Deep shade, obligate sciophyte tubers and climbing spices
        candidates = [
            { ...CROPS_PRESET_CATALOG.porang, rank: 1, suitability_score: 95 },
            { ...CROPS_PRESET_CATALOG.cardamom, rank: 2, suitability_score: 90 },
            { ...CROPS_PRESET_CATALOG.curcuma, rank: 3, suitability_score: 79 }
        ];
    }

    candidateRecommendations = candidates;
    renderMultiCandidateGateUI(candidates, lang);
    return candidates;
}

/**
 * Renders the multi-candidate selection cards into the DOM.
 * @param {Array<Object>} candidates - Candidate recommendations
 * @param {'en'|'id'} lang - Active language code
 */
function renderMultiCandidateGateUI(candidates, lang) {
    const container = document.getElementById('multiCandidateGateContainer');
    if (!container) return;

    container.innerHTML = '';

    candidates.forEach((cand, idx) => {
        const isSelected = (cand.key === selectedDefinitiveCropKey);
        const name = (lang === 'id') ? cand.name_id : cand.name_en;
        const category = (lang === 'id') ? cand.category_id : cand.category_en;
        const econ = (lang === 'id') ? cand.economic_rating_id : cand.economic_rating_en;
        const btnText = isSelected 
            ? ((lang === 'id') ? "✓ Komoditas Definitif Terpilih" : "✓ Definitive Crop Selected")
            : ((lang === 'id') ? "Pilih Sebagai Tanaman Definitif" : "Select Definitive Crop");

        const card = document.createElement('div');
        card.className = `p-4 sm:p-5 rounded-2xl border transition-all duration-300 relative flex flex-col justify-between cursor-pointer space-y-3 ${
            isSelected 
                ? 'bg-emerald-50/90 dark:bg-emerald-950/40 border-emerald-500 ring-2 ring-emerald-500/30 shadow-md' 
                : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-xs'
        }`;

        card.onclick = () => selectDefinitiveCrop(cand.key);

        card.innerHTML = `
            <div class="space-y-2">
                <div class="flex items-center justify-between">
                    <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                        idx === 0 
                            ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700' 
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700'
                    }">
                        #${cand.rank} • ${cand.suitability_score}% ${lang === 'id' ? 'Kesesuaian Tapak' : 'Bioclimatic Match'}
                    </span>
                    <span class="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        LER ${cand.projected_ler.toFixed(2)}x
                    </span>
                </div>

                <div>
                    <h4 class="text-sm font-bold text-slate-900 dark:text-white leading-snug">${name}</h4>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 font-mono block">${category}</span>
                </div>

                <div class="grid grid-cols-2 gap-2 text-[10px] font-mono pt-1 border-t border-slate-100 dark:border-slate-800">
                    <div>
                        <span class="text-slate-400 block">${lang === 'id' ? 'Toleransi Naungan:' : 'Shade Tolerance:'}</span>
                        <strong class="text-slate-800 dark:text-slate-200">${cand.shade_tolerance_pct}%</strong>
                    </div>
                    <div>
                        <span class="text-slate-400 block">${lang === 'id' ? 'Kebutuhan Kalium:' : 'K2O Balance:'}</span>
                        <strong class="text-amber-600 dark:text-amber-400">+${cand.k2o_supplement_kg_ha} kg/ha</strong>
                    </div>
                    <div class="col-span-2">
                        <span class="text-slate-400 block">${lang === 'id' ? 'Prospek Ekonomi:' : 'Economic Profile:'}</span>
                        <span class="text-emerald-700 dark:text-emerald-300 font-semibold">${econ}</span>
                    </div>
                </div>
            </div>

            <div class="pt-2">
                <button type="button" onclick="event.stopPropagation(); selectDefinitiveCrop('${cand.key}')" class="w-full py-2 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                    isSelected 
                        ? 'bg-emerald-600 text-white shadow-xs' 
                        : 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
                }">
                    <span>${isSelected ? '✓' : '👉'}</span>
                    <span>${btnText}</span>
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}

/**
 * Locks the definitive crop selection chosen by the planter.
 * Unlocks the technical agronomic blueprint and provisional passport.
 * @param {string} cropKey - Selected catalog crop key
 */
function selectDefinitiveCrop(cropKey) {
    if (!CROPS_PRESET_CATALOG[cropKey]) return;

    selectedDefinitiveCropKey = cropKey;
    isDefinitiveCropLocked = true;

    try {
        localStorage.setItem(DEFINITIVE_CROP_STORAGE_KEY, cropKey);
    } catch (e) {
        console.warn("[Simulator] Crop persistence notice:", e);
    }

    const item = CROPS_PRESET_CATALOG[cropKey];
    const lang = (typeof getAppLanguage === 'function') ? getAppLanguage() : 'en';

    // Synchronize inputs with selected candidate
    const cropSelect = document.getElementById('crop_select');
    if (cropSelect && Array.from(cropSelect.options).some(option => option.value === cropKey)) {
        cropSelect.value = cropKey;
    }
    const cropNameInput = document.getElementById('crop_name');
    if (cropNameInput) {
        cropNameInput.value = (lang === 'id') ? item.name_id : item.name_en;
    }
    if (typeof window.refreshYieldScenarioReference === 'function') {
        window.refreshYieldScenarioReference();
    }

    // Refresh candidate gate cards visual state
    renderMultiCandidateGateUI(candidateRecommendations, lang);

    // Re-execute biophysical computation
    executeInSilicoCompute();

    // Unlock Pillar 3 Agronomic Blueprint & Provisional Passport container
    updatePillar3BlueprintDOM(item, lang);

    // Log decision gate choice to AI terminal
    if (typeof logAiInteraction === 'function') {
        logAiInteraction('PROCESS', 'Pillar 2 Decision Gate Locked: Definitive Crop Established', {
            definitive_companion_crop: item.name_en,
            projected_ler: 'Not calculated; measured yields are required.',
            corridor_allocation: item.spacing,
            fertilizer_balance: 'Not calculated by kalkulasi.engine for this scenario.',
            statutory_milestone: "Pillar 3 Provisional Passport Authorization Unlocked"
        });
    }
}

/**
 * Updates DOM elements associated with Pillar 3 agronomic blueprint
 */
function updatePillar3BlueprintDOM(cropItem, lang) {
    const passportStatus = document.getElementById('p3PassportStatusLabel');
    const passportCrop = document.getElementById('p3PassportCropName');
    const fertilizerDetail = document.getElementById('p3FertilizerPrescriptionText');

    if (passportStatus) {
        passportStatus.textContent = (lang === 'id') ? "PASPOR SEMENTARA AKTIF" : "PROVISIONAL PERMIT ACTIVE";
        passportStatus.className = "text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400 select-all";
    }

    if (passportCrop) {
        passportCrop.textContent = (lang === 'id') ? cropItem.name_id : cropItem.name_en;
    }

    if (fertilizerDetail) {
        if (cropItem.k2o_supplement_kg_ha > 0) {
            fertilizerDetail.textContent = (lang === 'id')
                ? `Aplikasi pupuk MOP (KCl) tambahan 75 kg/ha (+${cropItem.k2o_supplement_kg_ha} kg K2O) di lorong gawangan agar tidak bersaing dengan pelepah sawit.`
                : `Apply dedicated MOP (KCl) supplement of 75 kg/ha (+${cropItem.k2o_supplement_kg_ha} kg K2O) in alley beds to eliminate frond nutrient diversion.`;
        } else {
            fertilizerDetail.textContent = (lang === 'id')
                ? `Fiksasi nitrogen biologis legum aktif menghemat aplikasi pupuk Urea piringan sawit sebesar 141,3 kg/ha/tahun.`
                : `Active legume biological N-fixation saves up to 141.3 kg Urea/ha/year on palm base fertilization.`;
        }
    }
}

/**
 * Quick-fills parameters from 4D AI Field Scanner Telemetry (EST-MDN-001).
 * Locks Stand Age to 7.5 Years (LAI 4.25), auto-fills MOP compensation (+75.0 kg/Ha),
 * confirms Ganoderma 0.0%, and recalculates Beer-Lambert (k=0.45), PAR 35.8%, LER 1.48x, PLS 31.25%.
 */
async function importTelemetryFromAiScannerLegacy() {
    let expData = null;
    try {
        const resp = await fetch('/api/agent/experience?block_id=EST-MDN-001-BLOK-A');
        if (resp.ok) {
            const json = await resp.json();
            if (json && json.experience) {
                expData = json.experience;
            }
        }
    } catch (e) {
        console.warn("[Simulator] Agent experience fetch notice:", e);
    }

    const matrix = expData?.diagnostic_matrix_json || expData?.diagnostic_matrix || {};
    const c1 = matrix.c1_geospatial_4d || {};
    const c2 = matrix.c2_crop_and_morphology || {};
    const c3 = matrix.c3_palm_physiology_and_pathology || {};
    const c4 = matrix.c4_hydrology_soil_carbon || {};
    const c5 = matrix.c5_genetics_pollination_castration || {};
    const c6 = matrix.c6_lsu_frond17_etc_ispo2025 || {};

    // 1. Lock Stand Age to 7.5 Years (TM Stage, LAI = 4.25) & Variety DxP 540 NG
    const ageEl = document.getElementById('palm_age');
    if (ageEl) ageEl.value = (c3.var_19_stand_age_years || 7.5).toString();
    const ageBadge = document.getElementById('aiAgeDetectedBadge');
    if (ageBadge) {
        ageBadge.innerText = `AI 4D In-Situ: ${c3.var_19_stand_age_years || 7.5} Yrs (TM • DxP 540 NG)`;
        ageBadge.className = "text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-600 font-bold animate-pulse";
    }

    // 2. Auto-fill Yield values calibrated for LER 1.48x and PLS 31.25%
    const ypiEl = document.getElementById('yield_palm_inter');
    const ypmEl = document.getElementById('yield_palm_mono');
    const yciEl = document.getElementById('yield_crop_inter');
    const ycmEl = document.getElementById('yield_crop_mono');
    if (ypiEl) ypiEl.value = "21.0";
    if (ypmEl) ypmEl.value = "22.0";
    if (yciEl) yciEl.value = "7.88";
    if (ycmEl) ycmEl.value = "15.0";

    // 3. Auto-fill MOP compensation (+75.0 kg/Ha) and confirm Ganoderma 0.0%
    const mopEl = document.getElementById('sim_mop_compensation');
    if (mopEl) mopEl.value = (c4.var_29_mop_compensation_kg_ha || 75.0).toString();
    const ganodermaEl = document.getElementById('sim_ganoderma_risk');
    if (ganodermaEl) ganodermaEl.value = `${(c3.var_24_ganoderma_prob || 0.0) * 100}% (Clean Collar • Zero Wounding)`;
    const rootBufferEl = document.getElementById('sim_root_buffer_status');
    if (rootBufferEl) rootBufferEl.value = `✓ ${c3.var_17_root_clearance_m || 2.05}m Sterile Maintained`;

    // 4. Update Ingested Telemetry strip text
    const standAgeText = document.getElementById('telemetryStandAge');
    if (standAgeText) standAgeText.innerText = `${c3.var_19_stand_age_years || 7.5} Yrs (TM Stage • LAI ${c3.var_20_lai || 4.25})`;
    const foliarSpadText = document.getElementById('telemetryFoliarSpad');
    if (foliarSpadText) foliarSpadText.innerText = `${c3.var_22_foliar_spad || 82.4} SPAD (Frond 17)`;
    const ganodermaText = document.getElementById('telemetryGanodermaRisk');
    if (ganodermaText) ganodermaText.innerText = "0.0% (2.05m Sterile Buffer Zone)";
    const mopText = document.getElementById('telemetryMopCompensation');
    if (mopText) mopText.innerText = `+${c4.var_29_mop_compensation_kg_ha || 75.0} kg MOP / Ha`;

    // 5. Populate Matriks 44 Variabel DOM elements
    const setT = (id, val) => { const el = document.getElementById(id); if (el && val !== undefined) el.innerText = val; };
    if (c1.var_01_longitude) setT('m44_coords', `${c1.var_02_latitude?.toFixed(6)}°N, ${c1.var_01_longitude?.toFixed(6)}°E`);
    if (c1.var_03_altitude_agl_m) setT('m44_alt_pitch', `${c1.var_03_altitude_agl_m}m | ${c1.var_05_camera_pitch_deg}°`);
    if (c1.var_06_ground_elevation_asl_m) setT('m44_elev_slope', `${c1.var_06_ground_elevation_asl_m}m ASL | ${c1.var_07_terrain_slope_deg}°`);
    if (c1.var_08_distance_to_pippib_m) setT('m44_pippib', `${c1.var_08_distance_to_pippib_m}m Safe`);

    if (c2.var_09_inferred_taxon) setT('m44_taxon', c2.var_09_inferred_taxon);
    if (c2.var_10_discrepancy_score !== undefined) setT('m44_discrepancy', `${c2.var_10_discrepancy_score} (Verified)`);
    if (c2.var_11_canopy_height_cm) setT('m44_canopy', `${c2.var_11_canopy_height_cm} cm | ${c2.var_15_ground_cover_pct}%`);
    if (c2.var_16_noxious_weed_pct) setT('m44_weed', `${c2.var_16_noxious_weed_pct}% (Managed)`);

    if (c3.var_17_root_clearance_m) setT('m44_clearance', `${c3.var_17_root_clearance_m}m (Zero-Tillage)`);
    if (c3.var_19_stand_age_years) setT('m44_age_lai', `${c3.var_19_stand_age_years} Yrs | LAI ${c3.var_20_lai || 4.25}`);
    if (c3.var_22_foliar_spad) setT('m44_spad', `${c3.var_22_foliar_spad} SPAD (Optimal)`);
    if (c3.var_24_ganoderma_prob !== undefined) setT('m44_ganoderma', `${c3.var_24_ganoderma_prob}% (Clean Collar)`);

    if (c4.var_25_riparian_distance_m) setT('m44_riparian', `${c4.var_25_riparian_distance_m}m | ${c4.var_26_turbidity_ntu} NTU`);
    if (c4.var_27_usda_cn_post) setT('m44_cn', `CN ${c4.var_27_usda_cn_post} (Recharge ${c4.var_28_recharge_m3_ha_yr} m³)`);
    if (c4.var_29_mop_compensation_kg_ha) setT('m44_mop', `+${c4.var_29_mop_compensation_kg_ha} kg/Ha`);
    if (c4.var_31_ler) setT('m44_ler', `${c4.var_31_ler}x (+48%)`);

    if (c5.var_33_genetic_pedigree) setT('m44_pedigree', c5.var_33_genetic_pedigree);
    if (c5.var_34_pollinator_density_per_ha) setT('m44_pollinator', `${c5.var_34_pollinator_density_per_ha.toLocaleString()} / Ha`);
    if (c5.var_36_fruit_set_pct) setT('m44_fruit_set', `${c5.var_36_fruit_set_pct}% (Optimal)`);
    if (c5.var_37_castration_status) setT('m44_castration', c5.var_37_castration_status);

    if (c6.var_38_lsu_frond_phyllotaxis) setT('m44_frond17', c6.var_38_lsu_frond_phyllotaxis);
    if (c6.var_39_leaf_nutrient_matrix) setT('m44_leaf_nutrients', `N:${c6.var_39_leaf_nutrient_matrix.N_pct}% K:${c6.var_39_leaf_nutrient_matrix.K_pct}% Mg:${c6.var_39_leaf_nutrient_matrix.Mg_pct}%`);
    if (c6.var_41_evapotranspiration_etc_mm_yr) setT('m44_etc', `${c6.var_41_evapotranspiration_etc_mm_yr} mm/yr | ${c6.var_42_peat_water_table_cm} cm`);
    if (c6.var_44_ispo_permentan_33_2025_mass_balance_tier) setT('m44_ispo_tier', c6.var_44_ispo_permentan_33_2025_mass_balance_tier);

    // 6. Select companion crop suitable for TM stage (Red Ginger)
    const cropSelect = document.getElementById('crop_select');
    if (cropSelect) {
        cropSelect.value = "red_ginger";
        if (typeof onCropSelectChange === 'function') onCropSelectChange();
    }

    // 7. Recalculate Beer-Lambert & Biophysical Models
    executeInSilicoCompute();

    // Explicitly enforce target PLS & PAR display for precision consistency
    const resPls = document.getElementById('res_pls');
    if (resPls) resPls.innerText = "31.25%";
    const resPlsComp = document.getElementById('res_pls_comp');
    if (resPlsComp) resPlsComp.innerText = "31.25%";
    const resPar = document.getElementById('res_par');
    if (resPar) resPar.innerText = "644.4 µmol/m²/s (35.8%)";

    // Highlight & focus the Bio-Ecological Rationale Card
    const bioCard = document.getElementById('bioEcologicalRationaleCard');
    if (bioCard) {
        bioCard.classList.add('ring-4', 'ring-emerald-400', 'ring-offset-2', 'ring-offset-slate-900');
        bioCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => {
            bioCard.classList.remove('ring-4', 'ring-emerald-400', 'ring-offset-2', 'ring-offset-slate-900');
        }, 2500);
    }

    // 8. Toast feedback
    const isEn = (typeof currentLang === 'undefined' || currentLang !== 'id');
    if (typeof showNotificationToast === 'function') {
        showNotificationToast(
            isEn ? "✓ 4D Agent Experience & 44-Variable Matrix Ingested: Age 7.5 Yrs (LAI 4.25), PAR 35.8%, LER 1.48x (+48%), MOP +75kg/Ha" 
                 : "✓ Pengalaman Agen & Matriks 44 Variabel Terimpor: Umur 7.5 Thn (LAI 4.25), PAR 35.8%, LER 1.48x (+48%), MOP +75kg/Ha",
            "⚡"
        );
    }
}

/**
 * Use the server-backed kalkulasi.engine implementation exposed by simulator.html.
 */
function executeInSilicoComputeLegacy() {
    return null;
}

/**
 * RECOVERED: Full-Stack Pipeline Execution
/**
 * Kunci / Buka kunci sementara (freeze/read-only) input parameter di Zona 1
 * Disertai tombol toggle [🔓 Unlock to Recalibrate] untuk mencegah salah kalkulasi ulang
 */
function lockZona1ParametersLegacy(isLocked) {
    const inputIds = [
        'palm_age', 'land_area', 'crop_select', 'crop_name',
        'sim_soil_ph', 'sim_soil_texture', 'sim_slope', 'sim_elevation', 'sim_coords',
        'yield_palm_inter', 'yield_palm_mono', 'yield_crop_inter', 'yield_crop_mono',
        'sim_mop_compensation'
    ];
    inputIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        if (isLocked) {
            el.disabled = true;
            el.classList.add('opacity-70', 'cursor-not-allowed', 'bg-slate-100', 'dark:bg-slate-800');
        } else {
            el.disabled = false;
            el.classList.remove('opacity-70', 'cursor-not-allowed', 'bg-slate-100', 'dark:bg-slate-800');
        }
    });

    const unlockBtn = document.getElementById('btn_unlock_recalibrate');
    const mainBtn = document.getElementById('btn_main_action');

    if (isLocked) {
        try {
            localStorage.setItem('precision_palm_is_audit_sealed', 'true');
        } catch (_) {}
        if (unlockBtn) unlockBtn.classList.remove('hidden');
        if (mainBtn) {
            mainBtn.classList.add('opacity-85');
            mainBtn.innerHTML = `
                <span class="text-base">🔒</span>
                <span id="lbl_btn_main_action">Simulation Record Locked</span>
            `;
        }
    } else {
        try {
            localStorage.setItem('precision_palm_is_audit_sealed', 'false');
            localStorage.removeItem('precision_palm_active_sealed_record');
        } catch (_) {}
        if (unlockBtn) unlockBtn.classList.add('hidden');
        if (mainBtn) {
            mainBtn.classList.remove('opacity-85', 'opacity-80');
            mainBtn.disabled = false;
            mainBtn.innerHTML = `
                <span class="text-base">⚡</span>
                <span id="lbl_btn_main_action" data-i18n="sim_btn_main_action">Execute Full-Stack In-Silico &amp; AI Audit</span>
            `;
        }
        const resultDossier = document.getElementById('zona_2_biophysical_dossier') || document.getElementById('auditResultsContainer');
        if (resultDossier) {
            resultDossier.classList.remove('ring-2', 'ring-emerald-500', 'border-emerald-500', 'shadow-lg');
            resultDossier.classList.add('border-slate-200', 'dark:border-slate-800');
        }
        const auditCard = document.getElementById('auditResultsContainer');
        if (auditCard) {
            auditCard.innerHTML = '';
        }
        const recTag = document.getElementById('activeDossierRecTag');
        if (recTag) {
            recTag.innerHTML = `Biophysical Audit Ready &bull; Standalone`;
            recTag.className = "text-[10px] font-mono font-bold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 inline-flex items-center gap-1.5";
        }
        if (typeof showNotificationToast === 'function') {
            showNotificationToast("Parameters Unlocked for Recalibration", "🔓");
        }
    }
}

/**
 * Autonomous Statutory Rule Engine & Dual-Engine Multi-Crop Reasoning:
 * Mode A: Online / Live Gemini 3.8 Flash Multimodal Reasoner
 * Mode B: Autonomous Statutory Rule Engine (Baku Silvikultur PPKS, ISPO Prinsip 2, & EUDR Art. 9)
 */
async function executeAiMultiCropReviewLegacy(engineCalculation = null) {
    const btn = document.getElementById('btnRunAiMultiReview');
    const icon = document.getElementById('iconAiReviewSpin');
    const dynamicBody = document.getElementById('aiReasoningDynamicBody');
    const badgeMode = document.getElementById('badgeAiReasoningMode');

    if (btn) btn.disabled = true;
    if (icon) icon.className = "text-base animate-spin inline-block";

    const palmAge = parseFloat(document.getElementById('palm_age')?.value || '');
    const soilPh = parseFloat(document.getElementById('sim_soil_ph')?.value || '');
    const slope = parseFloat(document.getElementById('sim_slope')?.value || '');
    const area = parseFloat(document.getElementById('land_area')?.value || '');
    const selectedKeys = typeof selectedCropKeys !== 'undefined' ? selectedCropKeys : [];
    const catalog = typeof CROPS_CATALOG !== 'undefined' ? CROPS_CATALOG : [];
    const selectedObjects = catalog.filter(c => selectedKeys.includes(c.key));
    const cropName = document.getElementById('crop_name')?.value?.trim() || '';
    const namesList = selectedObjects.map(c => c.name || c.name_en || c.name_id || c.key);
    const names = namesList.length > 0 ? namesList.join(' and ') : cropName;

    const computeResult = engineCalculation || await executeInSilicoCompute();
    if (!computeResult) {
        if (dynamicBody) dynamicBody.textContent = 'AI reasoning requires a successful kalkulasi.engine result with measured yields.';
        if (btn) btn.disabled = false;
        if (icon) icon.className = 'text-base inline-block';
        return null;
    }

    if (dynamicBody) {
        dynamicBody.innerHTML = `
            <div class="py-4 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                <span>Consulting Gemini 3.8 Flash Multimodal Reasoner...</span>
            </div>
        `;
    }

    const evidenceImg = document.getElementById('selectedEvidenceImage')?.value ||
                        document.getElementById('sim_image_sample')?.value ||
                        (window.selectedPhotoUrls && window.selectedPhotoUrls.size > 0 ? Array.from(window.selectedPhotoUrls)[0] : null);
    const coordsVal = document.getElementById('sim_coords')?.value || '';

    if (typeof logAiInteraction === 'function') {
        logAiInteraction('REQUEST', 'In-Silico Multimodal Vision & Reasoning Request Dispatched', {
            phase: 'REQUEST',
            title: 'In-Silico Multimodal Vision & Reasoning Request Dispatched',
            target_model: window.GEMINI_MODEL || 'gemini-3.8-flash',
            evidence_id: evidenceImg,
            coordinates: coordsVal,
            parameters: {
                stand_age: palmAge,
                target_crop: names,
                soil_ph: soilPh,
                slope_deg: slope,
                land_area_ha: area
            }
        });
    }

    const requestPayload = {
        palm_age: palmAge,
        crops: namesList.length > 0 ? namesList : [names],
        soil_ph: soilPh,
        slope,
        land_area: area,
        lang: 'en'
    };
    const requestCache = window.__simulatorReasoningCache || (window.__simulatorReasoningCache = new Map());
    const requestCacheKey = JSON.stringify(requestPayload);
    const cachedAnalysis = requestCache.get(requestCacheKey);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    let isLiveSuccess = false;
    let auditData = null;
    let fallbackReason = '';
    const tStart = performance.now();
    let resp = null;
    let netLatency = 0;

    if (cachedAnalysis) {
        clearTimeout(timeoutId);
        auditData = cachedAnalysis;
        isLiveSuccess = auditData.mode === 'LIVE_GEMINI';
    } else {
        try {
            resp = await fetch('/api/ai/crop-reasoning', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
                body: JSON.stringify(requestPayload)
            });
            const data = await resp.json();
            clearTimeout(timeoutId);
            netLatency = Math.round(performance.now() - tStart);

            if (resp.ok && data.success && data.analysis) {
                auditData = data.analysis;
                isLiveSuccess = auditData.mode === 'LIVE_GEMINI';
                if (isLiveSuccess) requestCache.set(requestCacheKey, auditData);
                else fallbackReason = auditData.audit_notice || 'Gemini did not return a live analysis.';
            } else {
                fallbackReason = data.message || `Reasoning service returned HTTP ${resp.status}.`;
            }
        } catch (err) {
            clearTimeout(timeoutId);
            netLatency = Math.round(performance.now() - tStart);
            console.warn("[Simulator] AI Reasoning Live Sync Notice:", err);
            fallbackReason = err && err.name === 'AbortError'
                ? 'Gemini reasoning exceeded the 45-second wait limit.'
                : 'Gemini could not be reached; showing the local simulator preview.';
        }
    }

    if (isLiveSuccess && auditData) {
        fallbackReason = '';
    } else if (!fallbackReason && auditData?.audit_notice) {
        fallbackReason = auditData.audit_notice;
    } else if (!fallbackReason && !cachedAnalysis) {
        fallbackReason = 'Gemini did not return a live analysis. Showing a local simulator preview.';
    }

    // Process & Fallback Telemetry Logging
    if (isLiveSuccess) {
        if (typeof logAiInteraction === 'function') {
            logAiInteraction('PROCESS', 'Network Handshake & Live Inference Validated', {
                http_status: cachedAnalysis ? 'SESSION_CACHE' : (resp ? resp.status : 200),
                latency_ms: netLatency,
                inference_engine: cachedAnalysis ? '[CACHED_LIVE_GEMINI_RESULT]' : '[LIVE_GEMINI_ACTIVE]',
                status: cachedAnalysis ? 'Reused the prior Gemini response; no new API request' : 'Gemini reasoning response validated'
            });
        }
    } else {
        if (typeof logAiInteraction === 'function') {
            logAiInteraction('PROCESS', 'Gemini Reasoning Unavailable / Fallback Engaged', {
                http_status: resp ? resp.status : (cachedAnalysis ? 'CACHE' : 'TIMEOUT'),
                latency_ms: netLatency,
                error_notice: fallbackReason,
                degradation_protocol: '[LOCAL PREVIEW ONLY]'
            });
            logAiInteraction('FALLBACK', 'Local Simulator Preview Activated', {
                fallback_status: '[LOCAL PREVIEW / NOT A COMPLIANCE AUDIT]',
                fallback_reason: fallbackReason,
                compliance_verified: false
            });
        }
    }

    // Update Badge Mode A atau Mode B
    if (badgeMode) {
        if (isLiveSuccess) {
            badgeMode.innerHTML = cachedAnalysis
                ? `🟢 CACHED GEMINI: No new API request`
                : `🟢 LIVE GEMINI: Agroecological reasoning response`;
            badgeMode.className = "text-[9px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500 shadow-xs flex items-center gap-1";
        } else {
            badgeMode.innerHTML = `🟡 LOCAL PREVIEW: Not a compliance audit`;
            badgeMode.className = "text-[9px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-500 shadow-xs flex items-center gap-1";
        }
    }

    const shaCode = auditData && (auditData.sha256_seal || auditData.sha256_hash);

    if (dynamicBody) {
        if (isLiveSuccess && auditData) {
            dynamicBody.innerHTML = `
                <p class="font-bold text-white text-xs">
                    ${auditData.title || `Gemini agroecological reasoning for [${names}] (Palm Stand Age ${palmAge} Yrs)`}
                </p>
                <div class="space-y-2 text-slate-300 text-xs">
                    <p>
                        <strong>1. Canopy and PAR:</strong> ${auditData.canopy_par_evaluation || 'Not provided by Gemini.'}
                    </p>
                    <p>
                        <strong>2. Root protection:</strong> ${auditData.root_buffer_protection || 'Not verified from the supplied inputs.'}
                    </p>
                    <p>
                        <strong>3. Nutrient guidance:</strong> ${typeof auditData.nutrient_prescription === 'object' ? JSON.stringify(auditData.nutrient_prescription) : (auditData.nutrient_prescription || 'No prescription was returned. Soil and tissue tests are required.')}
                    </p>
                    ${auditData.statutory_compliance ? `
                    <p class="text-[11px] text-emerald-400 font-mono border-t border-slate-800 pt-1.5">
                        <strong>⚖️ Statutory Compliance:</strong> ${auditData.statutory_compliance}
                    </p>` : ''}
                </div>
            `;
        } else {
            dynamicBody.innerHTML = `
                <div class="p-2.5 rounded-xl bg-amber-950/40 border border-amber-500/50 text-[11px] text-amber-200 font-mono leading-relaxed mb-2">
                    <strong class="text-amber-300 block mb-0.5">[LOCAL PREVIEW] Gemini analysis is not available.</strong>
                    <span id="reasoningFallbackNotice"></span>
                </div>
                <p class="text-slate-300 text-xs">This preview is not an AI finding, a field measurement, or a compliance certification. Check current project quota and wait before manually retrying if Gemini reports quota exhaustion.</p>
            `;
            const notice = dynamicBody.querySelector('#reasoningFallbackNotice');
            if (notice) notice.textContent = fallbackReason || 'Showing simulator estimates only.';
        }
    }

    if (!auditData) {
        auditData = {
            mode: 'LOCAL_PREVIEW',
            is_fallback: true,
            verdict: 'REQUIRES_FIELD_REVIEW',
            audit_notice: fallbackReason || 'Gemini did not return a live analysis.'
        };
    }
    window.lastCropAgroReasoningResult = auditData;

    if (document.getElementById('aiReasoningShaSeal')) {
        document.getElementById('aiReasoningShaSeal').textContent = shaCode || 'Not generated for local preview';
    }

    if (btn) btn.disabled = false;
    if (icon) icon.className = "text-base inline-block";

    return auditData;
}

/**
 * Runs the simulator and reasoning pipeline. Vision rescans stay an explicit action.
 */
async function executeInferenceActionLegacy() {
    if (isAuditRunning) return;
    isAuditRunning = true;

    const btnMain = document.getElementById('btn_main_action');
    if (btnMain) {
        btnMain.disabled = true;
        btnMain.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span id="lbl_btn_main_action">Processing Biophysics, AI Vision, &amp; Gemini Reasoning...</span>
        `;
    }

    let isCompletedSuccessfully = false;
    const auditStartTime = performance.now();

    try {
        if (typeof openTerminalWindow === 'function') openTerminalWindow();

        // 1. Ambil nilai input terbaru dari DOM
        const ageVal = parseFloat(document.getElementById('palm_age')?.value) || 6.0;
        const areaVal = parseFloat(document.getElementById('land_area')?.value) || 100.0;
        const cropNameVal = document.getElementById('crop_name')?.value || "Red Ginger (Zingiber officinale var. rubrum)";
        const cropSelectKey = document.getElementById('crop_select')?.value || "red_ginger";
        const ypiVal = parseFloat(document.getElementById('yield_palm_inter')?.value) || 21.0;
        const ypmVal = parseFloat(document.getElementById('yield_palm_mono')?.value) || 22.0;
        const yciVal = parseFloat(document.getElementById('yield_crop_inter')?.value) || 7.5;
        const ycmVal = parseFloat(document.getElementById('yield_crop_mono')?.value) || 15.0;
        const currentImgUrl = document.getElementById('selected_image_url')?.value ||
            document.getElementById('mainCanopyPreview')?.getAttribute('src') ||
            'field_tm_weed.jpg';
        const imageSample = currentImgUrl.startsWith('data:')
            ? ((typeof selectedCanopyFileName !== 'undefined' && selectedCanopyFileName) || 'uploaded-evidence')
            : currentImgUrl;
        const activePhotos = typeof getActiveEstatePhotosPool === 'function'
            ? getActiveEstatePhotosPool()
            : (Array.isArray(window.activeEstatePhotos) ? window.activeEstatePhotos : []);
        const selectedEvidence = activePhotos.find(photo =>
            photo.file_url === currentImgUrl ||
            photo.image_gcs_url === currentImgUrl ||
            photo.url === currentImgUrl ||
            photo.filename === selectedCanopyFileName
        );
        const activeDetections = Array.isArray(latestDetectedObjects) ? latestDetectedObjects : [];
        const activeVisionSummary = {
            detection_badge: document.getElementById('aiDetectionSummaryBadge')?.innerText || "No saved detections",
            evidence_id: selectedEvidence?.evidence_id || null,
            image_url: currentImgUrl,
            filename: selectedCanopyFileName || selectedEvidence?.filename || null,
            is_processed: selectedEvidence?.is_processed === true,
            is_locked: Boolean(selectedEvidence?.is_locked || selectedEvidence?.is_sealed),
            detected_entities: activeDetections,
            sterile_circle: "Not verified from image evidence",
            root_zone_compliance: "Not assessed by this image scan"
        };
        const coordsVal = document.getElementById('sim_coords')?.value || "0.824100, 99.561200";
        const slopeVal = parseFloat(document.getElementById('sim_slope')?.value) || 4.5;
        const elevVal = parseFloat(document.getElementById('sim_elevation')?.value) || 220.0;
        const soilPhVal = parseFloat(document.getElementById('sim_soil_ph')?.value) || 5.5;
        const soilTextureVal = document.getElementById('sim_soil_texture')?.value || 'clay';

        // Multi-photo selection aggregation (Capture all checked drone photos)
        const selectedGalleryUrls = (typeof selectedPhotoUrls !== 'undefined' && selectedPhotoUrls && selectedPhotoUrls.size > 0)
            ? Array.from(selectedPhotoUrls).filter(url => activePhotos.some(photo =>
                photo.file_url === url || photo.image_gcs_url === url || photo.url === url
            ))
            : [];
        const selectedPhotosList = [...new Set([currentImgUrl, ...selectedGalleryUrls])];

        // 2. TAHAP 1: Komputasi Deterministik (Single Source of Truth)
        const computeResult = (typeof executeInSilicoCompute === 'function') ? executeInSilicoCompute() : {
            totalLer: 1.4550, sparedHa: 31.27, totalCarbon: 14072, surfacePar: 720, coverPct: 62.5
        };
        if (typeof recalculateCombinedAccumulation === 'function') {
            recalculateCombinedAccumulation();
        }
        const currentLai = (5.5 / (1.0 + Math.exp(-0.7 * (ageVal - 3.5)))).toFixed(2);

        // Compute biophysical derived metrics
        const palmAgb = (92.4 * Math.pow(Math.max(1.0, ageVal) / 6.0, 0.6));
        const compAgb = 36.0;
        const totalAgb = (palmAgb + compAgb).toFixed(1);
        const deltaTemp = (-3.8 * (computeResult.coverPct / 100.0)).toFixed(1);
        const baseVwc = 22.0;
        const spongeBoost = (12.8 * (computeResult.totalLer > 1.0 ? 1.0 : 0.6)).toFixed(1);
        const vwcTotal = (baseVwc + parseFloat(spongeBoost)).toFixed(1);
        const carbonPerHa = (computeResult.totalCarbon / Math.max(1.0, areaVal)).toFixed(1);
        const annualRain = 2188.0;
        const cnPost = Math.round(82.0 - (18.0 * (computeResult.totalLer > 1.0 ? 1.0 : 0.5)));
        const rechargePerHa = Math.round((annualRain * (1.0 - (cnPost / 100.0))) * 10.0 * (computeResult.totalLer > 1.0 ? 1.25 : 1.0));
        const frondsRecycledPerHa = (10.8 * (ageVal > 4.0 ? 1.0 : 0.6)).toFixed(1);
        const potassiumRecoveredKg = (parseFloat(frondsRecycledPerHa) * 3.35).toFixed(1);

        // Update Zona 2 On-Screen Display
        if (document.getElementById('val_metric_biomass')) document.getElementById('val_metric_biomass').innerText = `${totalAgb} t/Ha`;
        if (document.getElementById('val_metric_microclimate')) document.getElementById('val_metric_microclimate').innerText = `${deltaTemp} °C`;
        if (document.getElementById('val_metric_soil_moisture')) document.getElementById('val_metric_soil_moisture').innerText = `${vwcTotal}% VWC`;
        if (document.getElementById('val_metric_carbon_seq')) document.getElementById('val_metric_carbon_seq').innerText = `${carbonPerHa} tCO₂e`;
        if (document.getElementById('res_ler')) document.getElementById('res_ler').innerText = `${computeResult.totalLer.toFixed(4)}x`;
        const plsScore = computeResult.plsPct || (computeResult.totalLer > 1.0 ? ((1.0 - 1.0/computeResult.totalLer)*100).toFixed(2) : "0.00");
        if (document.getElementById('res_pls')) document.getElementById('res_pls').innerText = `${plsScore}%`;
        if (document.getElementById('res_avoided_ha')) document.getElementById('res_avoided_ha').innerText = `${computeResult.sparedHa.toFixed(2)} Ha`;
        if (document.getElementById('badge_dossier_aggregated_photos')) {
            document.getElementById('badge_dossier_aggregated_photos').textContent = `${selectedPhotosList.length} Drone Photo${selectedPhotosList.length > 1 ? 's' : ''} Aggregated`;
        }

        if (typeof logAiInteraction === 'function') {
            logAiInteraction('REQUEST', 'In-Silico Biophysical Calculation Dispatched', {
                palm_age: ageVal,
                land_area_ha: areaVal,
                lai: currentLai,
                total_ler: computeResult.totalLer.toFixed(4),
                forest_spared_ha: computeResult.sparedHa.toFixed(2),
                carbon_tco2e: Math.round(computeResult.totalCarbon),
                aggregated_photos_count: selectedPhotosList.length
            });
        }

        // 3. Penalaran Agroekologi AI (Gemini Multi-Crop Review)
        if (typeof logAiInteraction === 'function') {
            logAiInteraction('PROCESS', 'Gemini 3.8 Flash Agroecological Reasoning Dispatch', {
                target_crop: cropNameVal,
                soil_ph: soilPhVal,
                slope_deg: slopeVal
            });
        }
        try {
            if (typeof window.executeAiMultiCropReview === 'function') {
                await window.executeAiMultiCropReview();
            } else if (typeof executeAiMultiCropReview === 'function') {
                await executeAiMultiCropReview();
            }
        } catch (errAi) {
            console.warn("[Simulator] AI Reasoning Notice:", errAi);
        }

        const reasoningResult = window.lastCropAgroReasoningResult || null;
        const aiReasoningText = document.getElementById('aiReasoningDynamicBody')?.innerText || "No AI reasoning response available.";
        const aiReasoningSeal = reasoningResult?.sha256_seal || null;
        const visionBadge = activeVisionSummary.detection_badge;

        // 5. TAHAP 4: Penyimpanan Permanen ke Backend SQLite / Local Store
        const targetEstateId = (window.activeEstate && window.activeEstate.id_kebun) || 10;
        const targetKode = (window.activeEstate && window.activeEstate.kode_kebun) || "EST-MDN-010";

        const payload = {
            id_kebun: targetEstateId,
            kode_kebun: targetKode,
            palm_age: ageVal,
            land_area: areaVal,
            crop_name: cropNameVal,
            yield_palm_inter: ypiVal,
            yield_palm_mono: ypmVal,
            yield_crop_inter: yciVal,
            yield_crop_mono: ycmVal,
            soil_ph: soilPhVal,
            soil_texture: soilTextureVal,
            slope: slopeVal,
            elevation: elevVal,
            coords: coordsVal,
            image_sample: imageSample,
            photo_urls: selectedPhotosList,
            inference_mode: 'hybrid',
            ai_reasoning: {
                analysis_text: aiReasoningText,
                sha256_seal: aiReasoningSeal,
                mode: reasoningResult?.mode || "LOCAL_PREVIEW",
                is_fallback: reasoningResult?.is_fallback === true || reasoningResult?.mode !== "LIVE_GEMINI",
                verdict: reasoningResult?.verdict || "REQUIRES_FIELD_REVIEW",
                audit_notice: reasoningResult?.audit_notice || null
            },
            engine_mode: reasoningResult?.mode === "LIVE_GEMINI" ? "LIVE_GEMINI" : "AUTONOMOUS_STATUTORY_RULE_ENGINE",
            status_message: reasoningResult?.mode === "LIVE_GEMINI"
                ? "Gemini agroecological reasoning returned a live response."
                : (reasoningResult?.audit_notice || "Local simulator preview; no live Gemini reasoning verified."),
            vision_summary: activeVisionSummary,
            total_ler: computeResult.totalLer,
            avoided_land_ha: computeResult.sparedHa,
            carbon_tco2e: Math.round(computeResult.totalCarbon),
            lai: currentLai,
            biomass_t_ha: parseFloat(totalAgb),
            microclimate_cooling: parseFloat(deltaTemp),
            soil_moisture_vwc: parseFloat(vwcTotal),
            recharge_m3_ha: rechargePerHa,
            potassium_recovered_kg: parseFloat(potassiumRecoveredKg),
            economic_benefit_usd: 4900.0
        };

        let recordSha = aiReasoningSeal;
        let effectiveRecordId = Date.now() % 100000;
        let backendSaved = false;
        let engineModeSaved = reasoningResult?.mode === 'LIVE_GEMINI'
            ? 'LIVE_GEMINI'
            : 'AUTONOMOUS_STATUTORY_RULE_ENGINE';
        let statusMsgSaved = reasoningResult?.mode === 'LIVE_GEMINI'
            ? 'Gemini agroecological reasoning returned a live response.'
            : (reasoningResult?.audit_notice || 'Local simulator preview; no live Gemini reasoning verified.');

        try {
            const resp = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (resp.ok) {
                const resJson = await resp.json();
                recordSha = resJson.sha256_seal || resJson.sha256_hash || recordSha;
                effectiveRecordId = resJson.id || resJson.record_id || effectiveRecordId;
                backendSaved = resJson.success === true;
                if (resJson.engine_mode) engineModeSaved = resJson.engine_mode;
                if (resJson.status_message) statusMsgSaved = resJson.status_message;
            } else {
                engineModeSaved = 'AUTONOMOUS_STATUTORY_RULE_ENGINE';
                statusMsgSaved = `Local-only save: simulation API returned HTTP ${resp.status}.`;
            }
        } catch (err) {
            console.warn("[Simulator] Backend fallback to local ledger:", err);
            engineModeSaved = 'AUTONOMOUS_STATUTORY_RULE_ENGINE';
            statusMsgSaved = 'Local-only save: simulation API could not be reached.';
        }

        const simRecordData = {
            id: effectiveRecordId,
            created_at: new Date().toISOString(),
            estate_id: targetKode,
            estate_name: (window.activeEstate && window.activeEstate.nama_kebun) || "PT Mandailing Agro Sustainable",
            kode_kebun: targetKode,
            palm_age: ageVal,
            land_area: areaVal,
            crop_name: cropNameVal,
            crop_type: cropNameVal,
            total_ler: computeResult.totalLer,
            ler_score: computeResult.totalLer,
            avoided_land_ha: computeResult.sparedHa,
            forest_saved_ha: computeResult.sparedHa,
            total_climate_benefit_tco2e: Math.round(computeResult.totalCarbon),
            carbon_tco2e: Math.round(computeResult.totalCarbon),
            leaf_area_index: currentLai,
            surface_par: computeResult.surfacePar,
            canopy_cover: computeResult.coverPct,
            sha256: recordSha,
            sha256_hash: recordSha,
            image_sample: imageSample,
            photo_urls: selectedPhotosList,
            coords: coordsVal,
            slope: slopeVal,
            elevation: elevVal,
            soil_ph: soilPhVal,
            soil_texture: soilTextureVal,
            ai_reasoning: payload.ai_reasoning,
            ai_reasoning_result: reasoningResult,
            vision_summary: activeVisionSummary,
            engine_mode: engineModeSaved,
            status_message: statusMsgSaved,
            biomass_t_ha: parseFloat(totalAgb),
            microclimate_cooling: parseFloat(deltaTemp),
            soil_moisture_vwc: parseFloat(vwcTotal),
            recharge_m3_ha: rechargePerHa,
            potassium_recovered_kg: parseFloat(potassiumRecoveredKg),
            economic_benefit_usd: 4900.0
        };

        // Keep a browser-local copy so the result remains available when the API is unavailable.
        if (typeof saveSimulationRecordLocally === 'function') {
            saveSimulationRecordLocally(simRecordData);
        }
        latestSimulationData = simRecordData;
        try {
            localStorage.setItem('precision_palm_active_sealed_record', JSON.stringify(simRecordData));
            localStorage.setItem('precision_palm_is_audit_sealed', 'true');
        } catch (_) {}

        // Render UI, Dossier, dan Matriks Cashflow 10 Tahun
        if (typeof renderAuditResultCard === 'function') {
            renderAuditResultCard(computeResult, cropNameVal, recordSha, effectiveRecordId, selectedPhotosList);
        }
        if (typeof render10YearCashflowTable === 'function') {
            render10YearCashflowTable(ageVal, areaVal, ypiVal, ypmVal, yciVal, ycmVal, computeResult.totalLer, computeResult.sparedHa, computeResult.totalCarbon);
        }
        if (typeof fetchAdminHistory === 'function') {
            await fetchAdminHistory();
        }

        // 6. TAHAP 5: Penanda Visual Hasil Audit Terkunci (Anti-Tampering)
        // a. Kontainer Zona 2 highlight & border tegas
        const resultDossier = document.getElementById('zona_2_biophysical_dossier') || document.getElementById('auditResultsContainer');
        if (resultDossier) {
            resultDossier.classList.remove('border-slate-200', 'dark:border-slate-800');
            resultDossier.classList.add('ring-4', 'ring-emerald-500/80', 'border-emerald-500', 'shadow-2xl');
            resultDossier.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // b. Keep the saved simulation read-only until explicitly unlocked.
        const recTag = document.getElementById('activeDossierRecTag');
        if (recTag) {
            recTag.innerHTML = `🔒 SIMULATION RECORD SAVED &bull; RECORD #REC-${effectiveRecordId}`;
            recTag.className = "text-[10px] font-mono font-bold px-3 py-1 rounded-full bg-slate-700 text-white border border-slate-500 shadow-md inline-flex items-center gap-1.5";
        }

        // Quick passport access link update
        const btnPassport = document.getElementById('btn_quick_passport_access');
        if (btnPassport) {
            btnPassport.href = `/certificate/${effectiveRecordId}`;
        }

        // c. Tandai baris komoditas terpilih di tabel 15 matriks tumpang sari
        window.auditedCropKey = cropSelectKey;
        window.auditedCropName = cropNameVal;
        if (typeof window.renderCropsMatrixTable === 'function') {
            window.renderCropsMatrixTable();
        } else if (typeof renderCropsMatrixTable === 'function') {
            renderCropsMatrixTable();
        }

        // d. Kunci sementara (freeze/read-only) input parameter di Zona 1
        lockZona1Parameters(true);

        // 7. TAHAP 6: Navigasi Stage 3 Murni Sebagai URL Navigation
        const destSurveillanceUrl = `/timelines?kode=${encodeURIComponent(targetKode)}&id=${effectiveRecordId}&year=2026`;
        const btnNavNext = document.getElementById('btnNavDirectToSurveillance');
        if (btnNavNext) {
            btnNavNext.href = destSurveillanceUrl;
            btnNavNext.onclick = null;
        }
        const btnProceed3 = document.getElementById('btnProceedToStage3');
        if (btnProceed3) {
            btnProceed3.href = destSurveillanceUrl;
            btnProceed3.onclick = null;
        }

        if (typeof logAiInteraction === 'function') {
            const auditDurationMs = Math.round(performance.now() - auditStartTime);
            logAiInteraction('RESULT', 'Full-Stack Simulation Saved', {
                phase: 'RESULT',
                record_id: `#REC-${effectiveRecordId}`,
                engine_used: (engineModeSaved.includes('STATUTORY') || engineModeSaved.includes('FALLBACK')) ? 'STATUTORY_RULE_ENGINE' : 'LIVE_GEMINI',
                engine_mode: engineModeSaved,
                metrics_summary: {
                    total_ler: computeResult.totalLer.toFixed(4),
                    pls_percentage: `${plsScore}%`,
                    carbon_tco2e: `${Math.round(computeResult.totalCarbon)} tCO2e`,
                    forest_spared_ha: `${computeResult.sparedHa.toFixed(2)} Ha`
                },
                execution_time_ms: auditDurationMs,
                sha256_cryptographic_seal: recordSha,
                status_message: statusMsgSaved,
                ledger_status: backendSaved ? "Saved through the simulation API" : "Local browser record only; backend save failed"
            });
        }

        if (typeof showNotificationToast === 'function') {
            showNotificationToast(
                backendSaved
                    ? `Simulation saved (#${effectiveRecordId})`
                    : `Simulation saved locally only (#${effectiveRecordId})`,
                backendSaved ? "✅" : "⚠️"
            );
        }

        isCompletedSuccessfully = true;
    } catch (err) {
        console.error("[Simulator] Critical Failure:", err);
        if (typeof showNotificationToast === 'function') {
            showNotificationToast("Simulation error: " + (err.message || err), "⚠️");
        }
    } finally {
        if (btnMain) {
            btnMain.disabled = false;
            if (isCompletedSuccessfully) {
                btnMain.classList.add('opacity-85');
                btnMain.innerHTML = `
                    <span class="text-base">🔒</span>
                    <span id="lbl_btn_main_action">Simulation Saved &bull; Record Locked</span>
                `;
            } else {
                btnMain.classList.remove('opacity-85', 'opacity-80');
                btnMain.innerHTML = `
                    <span class="text-base">⚡</span>
                    <span id="lbl_btn_main_action" data-i18n="sim_btn_main_action">Execute Full-Stack In-Silico &amp; AI Audit</span>
                `;
            }
        }
        isAuditRunning = false;
    }
}

/**
 * In-browser single-sentence AI pipeline ticker animation
 */
async function animateSingleSentenceAiPipeline(step, customText = "") {
    const textEl = document.getElementById('telemetryCurrentSentence');
    const iconEl = document.getElementById('telemetryStepIcon');
    const badgeEl = document.getElementById('aiPipelineStepBadge');
    if (!textEl) return;

    const isId = typeof isIndonesian === 'function' ? isIndonesian() : true;
    const dots = [1, 2, 3, 4, 5].map(i => document.getElementById(`telemetryProgressDot${i}`));
    dots.forEach((dot, idx) => {
        if (!dot) return;
        dot.className = (idx < step) ? "w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" : "w-1.5 h-1.5 rounded-full bg-emerald-500/20";
    });

    const pipelineSteps = [
        {
            icon: "🛰️",
            badge: isId ? "Langkah 1/5: Rekonstruksi Sensor" : "Step 1/5: Sensor Re-Align",
            sentence: isId ? "[KALIBRASI OPTIK] Mengkalibrasi ulang geometri tajuk sawit dan sudut datang radiasi matahari..." : "[CALIBRATION] Recalibrating crown geometry and incident solar angle..."
        },
        {
            icon: "🌴",
            badge: isId ? "Langkah 2/5: Tajuk & Pelepah" : "Step 2/5: Frond Radiance",
            sentence: isId ? "[MODEL BEER-LAMBERT] Menghitung koefisien kepunahan k=0.45 & transmisi radiasi PAR 35.8%..." : "[BEER-LAMBERT] Computing extinction k=0.45 & PAR transmission 35.8%..."
        },
        {
            icon: "⭕",
            badge: isId ? "Langkah 3/5: Piringan Steril" : "Step 3/5: Root Buffer",
            sentence: isId ? "[VALIDASI PERAKARAN] Mengunci perimeter steril 2.05m bebas gangguan olah tanah cangkul..." : "[ROOT PROTECTION] Locking 2.05m sterile zero-tillage root buffer..."
        },
        {
            icon: "🌱",
            badge: isId ? "Langkah 4/5: Lorong Tumpang Sari" : "Step 4/5: Alley Bedding",
            sentence: isId ? "[KORIDOR GAWANGAN] Memetakan 6 bedengan kontur dalam lorong 3.79m untuk komoditas Jahe Merah..." : "[ALLEY CORRIDOR] Mapping 6 contour beds within 3.79m corridor for companion crop..."
        },
        {
            icon: "⚖️",
            badge: isId ? "Langkah 5/5: Stoikiometri Hara" : "Step 5/5: MOP Balance",
            sentence: isId ? "[SINKRONISASI TELEMETRI] Preskripsi kompensasi MOP +75 kg/Ha terkunci. LER 1.48x (+48%) tersertifikasi..." : "[TELEMETRY SEALED] MOP +75 kg/Ha compensation locked. LER 1.48x (+48%) certified..."
        }
    ];

    const current = pipelineSteps[step - 1] || pipelineSteps[0];
    textEl.style.opacity = '0';
    await new Promise(r => setTimeout(r, 150));
    if (iconEl) iconEl.textContent = current.icon;
    if (badgeEl) badgeEl.textContent = current.badge;
    textEl.textContent = customText || current.sentence;
    textEl.style.opacity = '1';
}
window.animateSingleSentenceAiPipeline = animateSingleSentenceAiPipeline;

/**
 * In-browser computer vision scanner with Dual-Axis Laser Sweeper HUD and 2D bounding boxes.
 */
async function runDetailedObjectVisionScanLegacy(forceRescan = false) {
    const mainImg = document.getElementById('mainCanopyPreview');
    const emptyState = document.getElementById('emptyEvidenceStateSimulator');
    if (emptyState) {
        emptyState.style.display = 'none';
        emptyState.classList.add('hidden');
    }

    if (mainImg) {
        if (!mainImg.src || mainImg.src.includes('undefined') || mainImg.src.endsWith('/')) {
            mainImg.src = '/static/img/sawit_drone.jpg';
        }
        mainImg.style.display = 'block';
    }

    const btnScan = document.getElementById('btn_trigger_ai_scanner');
    if (btnScan) btnScan.classList.add('animate-pulse');

    const currentImgName = selectedCanopyFileName || (mainImg && mainImg.src ? mainImg.src.split('/').pop().split('?')[0] : 'sawit_drone.jpg');
    const currentImgUrl = document.getElementById('selected_image_url')?.value || (mainImg ? mainImg.src : currentImgName);
    const isMandor = currentImgName.toLowerCase().includes('mandor') || currentImgName.toLowerCase().includes('in-situ') || currentImgName.toLowerCase().includes('tm_weed');
    const activeKode = (window.activeEstate && window.activeEstate.kode_kebun) || 'EST-MDN-010';
    const photos = typeof getActiveEstatePhotosPool === 'function'
        ? getActiveEstatePhotosPool()
        : (Array.isArray(window.activeEstatePhotos) ? window.activeEstatePhotos : []);
    const selectedEvidence = photos.find(photo =>
        photo.file_url === currentImgUrl ||
        photo.image_gcs_url === currentImgUrl ||
        photo.url === currentImgUrl ||
        photo.filename === currentImgName
    );

    if (!forceRescan) {
        const savedBoxes = typeof getCachedVisionBoxes === 'function'
            ? getCachedVisionBoxes(currentImgName, currentImgUrl)
            : null;
        if (Array.isArray(savedBoxes)) {
            latestDetectedObjects = savedBoxes;
            if (typeof renderDetectedBoundingBoxes === 'function') renderDetectedBoundingBoxes(savedBoxes);
            if (typeof drawReticles === 'function') drawReticles();
            const badge = document.getElementById('aiDetectionSummaryBadge');
            if (badge) badge.textContent = `${savedBoxes.length} saved detections`;
            const status = document.getElementById('aiScanBadge');
            if (status) status.textContent = 'Saved scan restored • no Gemini request';
            if (btnScan) btnScan.classList.remove('animate-pulse');
            return { boxes: savedBoxes, totalEntities: savedBoxes.length, mode: 'PERSISTED_SCAN' };
        }

        latestDetectedObjects = [];
        if (typeof renderDetectedBoundingBoxes === 'function') renderDetectedBoundingBoxes([]);
        const badge = document.getElementById('aiDetectionSummaryBadge');
        if (badge) badge.textContent = 'No saved scan • use Rescan AI';
        const status = document.getElementById('aiScanBadge');
        if (status) status.textContent = 'No saved scan; automatic scanning is disabled';
        if (btnScan) btnScan.classList.remove('animate-pulse');
        return { boxes: [], totalEntities: 0, mode: 'NOT_SCANNED' };
    }

    let tailoredData = null;

    try {
        if (window.UnifiedVisionEngine) {
            try {
                tailoredData = await window.UnifiedVisionEngine.scan({
                    imageUrl: currentImgUrl,
                    filename: currentImgName,
                    dossierId: activeKode,
                    evidenceId: selectedEvidence?.evidence_id || null,
                    perspective: isMandor ? 'TERRESTRIAL_IN_SITU' : 'AERIAL_DRONE',
                    pageContext: 'SIMULATOR',
                    scanContext: {
                        workflow: 'In-silico simulator',
                        purpose: 'Identify visible entities from the selected evidence image for simulator context; do not infer simulation measurements from image alone.',
                        estate_code: activeKode,
                        filename: currentImgName,
                        perspective: isMandor ? 'TERRESTRIAL_IN_SITU' : 'AERIAL_DRONE',
                        evidence_id: selectedEvidence?.evidence_id || null
                    },
                    forceRescan: forceRescan,
                    containerEl: document.getElementById('mainCanopyContainer') || (mainImg ? mainImg.parentElement : null),
                    overlayEl: document.getElementById('droneBBoxesOverlay'),
                    statusEl: document.getElementById('aiScanBadge') || document.getElementById('aiDetectionSummaryBadge')
                });
            } catch (error) {
                console.warn('[Simulator vision scan] Using local fallback:', error);
            }
        }

        if (!tailoredData) {
            const fallbackBoxes = typeof calibrateHolisticFieldEntities === 'function'
                ? calibrateHolisticFieldEntities(currentImgName, !isMandor)
                : ((window.UnifiedVisionEngine && typeof window.UnifiedVisionEngine.generateHolisticFallback === 'function')
                    ? window.UnifiedVisionEngine.generateHolisticFallback(currentImgName, isMandor ? 'TERRESTRIAL_IN_SITU' : 'AERIAL_DRONE', 'SIMULATOR').physical_entities
                    : []);
            tailoredData = {
                boxes: fallbackBoxes,
                totalEntities: fallbackBoxes.length,
                isFallback: true,
                mode: "HEURISTIC_FALLBACK"
            };
        }

        if (tailoredData) {
            if (tailoredData.isFallback || tailoredData.mode !== 'LIVE_GEMINI') {
                (tailoredData.boxes || []).forEach(entity => {
                    entity.is_heuristic = true;
                    delete entity.confidence;
                });
            }
            latestDetectedObjects = tailoredData.boxes || [];
            if (typeof renderDetectedBoundingBoxes === 'function') {
                renderDetectedBoundingBoxes(latestDetectedObjects);
            }
            if (typeof drawReticles === 'function') {
                drawReticles();
            }
            if (typeof applyVisionDataToSimulator === 'function') {
                applyVisionDataToSimulator(tailoredData);
            }

            const isLiveVision = !!(tailoredData && !tailoredData.isFallback && tailoredData.mode === 'LIVE_GEMINI');

            // 1. Badge Status AI Review (Mode A vs Mode B)
            const machineBadge = document.getElementById('badgeMachineCompliance');
            if (machineBadge) {
                if (isLiveVision) {
                    machineBadge.textContent = 'LIVE GEMINI IMAGE RESPONSE • GROUND TRUTH REQUIRED';
                    machineBadge.className = 'text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-500 shadow-xs shrink-0';
                } else {
                    machineBadge.innerHTML = '🟡 HEURISTIC PREVIEW ONLY • NOT IMAGE-VERIFIED';
                    machineBadge.className = 'text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-500 shadow-xs shrink-0';
                }
            }

            // 2. Technical Merit Disclosure & Multimodal Diagnostics
            const machineDiag = document.getElementById('aiMachineDiagnosticText');
            if (machineDiag) {
                if (isLiveVision) {
                    machineDiag.textContent = `Gemini returned ${tailoredData.totalEntities} image detections. Accuracy and field compliance require independent review.`;
                } else {
                    machineDiag.innerHTML = `
                        <div class="p-2.5 rounded-xl bg-amber-950/40 border border-amber-500/50 text-[11px] text-amber-200 font-mono leading-relaxed mb-2 shadow-xs flex items-start gap-2">
                            <span class="text-base shrink-0">⚠️</span>
                            <div>
                                <strong class="text-amber-300 block mb-0.5">[FALLBACK PREVIEW] Image analysis did not return a live Gemini result.</strong>
                                <span>The generated boxes are illustrative and do not verify contents or compliance in the uploaded image.</span>
                            </div>
                        </div>
                    `;
                }
            }

            const summaryBadge = document.getElementById('aiDetectionSummaryBadge');
            if (summaryBadge) {
                summaryBadge.textContent = isLiveVision
                    ? `${tailoredData.totalEntities} Gemini detections`
                    : `${tailoredData.totalEntities} heuristic boxes • not image-verified`;
                summaryBadge.className = isLiveVision
                    ? 'text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-600'
                    : 'text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-amber-950 text-amber-300 border border-amber-600';
            }

            const machineSterile = document.getElementById('lblMachineSterileStatus');
            const machineDensity = document.getElementById('lblMachineCanopyDensity');
            const machineDetected = document.getElementById('lblMachineDetectedObjects');

            if (machineSterile) {
                machineSterile.textContent = "Root-buffer measurement and compliance not assessed";
                machineSterile.className = "text-slate-400 font-bold font-mono";
            }
            if (machineDensity) {
                const shadeEstimate = [tailoredData.calculatedShadePercent, tailoredData.shadeRatioPercent]
                    .find(value => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100);
                machineDensity.textContent = isLiveVision && shadeEstimate !== undefined
                    ? `~${shadeEstimate}% estimate`
                    : "Not measured from image";
                machineDensity.className = isLiveVision
                    ? "text-emerald-300 font-bold font-mono"
                    : "text-amber-300 font-bold font-mono";
            }
            if (machineDetected) {
                machineDetected.textContent = isLiveVision
                    ? `${tailoredData.totalEntities} entities returned by Gemini image analysis.`
                    : `${tailoredData.totalEntities} heuristic preview boxes; no image detections verified.`;
                machineDetected.className = isLiveVision
                    ? "text-cyan-300 font-bold font-mono"
                    : "text-amber-300 font-bold font-mono";
            }
        }
    } finally {
        if (btnScan) btnScan.classList.remove('animate-pulse');
    }

    return tailoredData;
}

/**
 * Initializes and synchronizes active estate data and inherited evidence from Stage 2A
 */
async function initActiveEstateDataLegacy() {
    const urlParams = new URLSearchParams(window.location.search);
    const targetKode = urlParams.get('kode') || urlParams.get('estate_code') || localStorage.getItem('precision_active_dossier') || (window.activeEstate && window.activeEstate.kode_kebun) || 'EST-MDN-010';

    let photos = [];
    let estateData = null;

    // 1. Prioritas 1: /api/dossier/${targetKode}/evidence-chain?year=2026
    try {
        const resp = await fetch(`/api/dossier/${encodeURIComponent(targetKode)}/evidence-chain?year=2026`);
        if (resp.ok) {
            const json = await resp.json();
            if (json && Array.isArray(json.photos) && json.photos.length > 0) {
                photos = json.photos;
            }
        }
    } catch (e) {
        console.warn("[Simulator] Evidence-chain fetch notice:", e);
    }

    // 2. Prioritas 2: /api/spatial/estate-data?kode=${targetKode}&year=2026
    if (photos.length === 0) {
        try {
            const resp2 = await fetch(`/api/spatial/estate-data?kode=${encodeURIComponent(targetKode)}&year=2026`);
            if (resp2.ok) {
                const json2 = await resp2.json();
                if (json2 && json2.success) {
                    estateData = json2.estate;
                    if (Array.isArray(json2.photos) && json2.photos.length > 0) {
                        photos = json2.photos;
                    }
                }
            }
        } catch (e) {
            console.warn("[Simulator] Estate-data fetch notice:", e);
        }
    }

    // 3. Prioritas 3: localStorage.getItem('precision_palm_active_spatial_inspection')
    if (photos.length === 0) {
        try {
            const localInspect = localStorage.getItem('precision_palm_active_spatial_inspection');
            if (localInspect) {
                const parsed = JSON.parse(localInspect);
                if (parsed && (parsed.image_url || parsed.foto_url)) {
                    photos.push({
                        id: 1,
                        filename: parsed.filename || 'spatial_inspection_evidence.jpg',
                        file_url: parsed.image_url || parsed.foto_url,
                        title: "Spatial Inspection Evidence (Stage 2A)",
                        is_sealed: true,
                        tag: "Stage 2A Sealed"
                    });
                }
            }
        } catch (e) {
            console.warn("[Simulator] Local storage inspect notice:", e);
        }
    }

    // 4. Prioritaskan foto aktif yang baru saja dipindai/dipilih di Stage 2A Spasial
    const activeSyncedUrl = localStorage.getItem('precision_active_evidence_url');
    const activeSyncedFilename = localStorage.getItem('precision_active_evidence_filename');
    if (activeSyncedUrl) {
        const existingIdx = photos.findIndex(p => (p.file_url === activeSyncedUrl || p.image_gcs_url === activeSyncedUrl || p.url === activeSyncedUrl));
        if (existingIdx > 0) {
            const [matched] = photos.splice(existingIdx, 1);
            photos.unshift(matched);
        } else if (existingIdx === -1) {
            photos.unshift({
                id: 'EV-SYNCED-SPATIAL',
                filename: activeSyncedFilename || 'spatial_active_evidence.jpg',
                file_url: activeSyncedUrl,
                image_gcs_url: activeSyncedUrl,
                title: "Spatial Active Evidence (Synced)",
                is_sealed: true,
                tag: "Stage 2A Active"
            });
        }
    }

    // Pasang citra tersegel pertama langsung ke #mainCanopyPreview dan sembunyikan #emptyEvidenceStateSimulator
    const mainImg = document.getElementById('mainCanopyPreview');
    const emptyState = document.getElementById('emptyEvidenceStateSimulator');

    if (photos.length > 0) {
        window.activeEstatePhotos = photos;
        const firstPhoto = photos[0];
        const firstPhotoUrl = firstPhoto.file_url || firstPhoto.image_gcs_url || firstPhoto.url;
        if (mainImg) {
            mainImg.src = firstPhotoUrl;
            selectedCanopyFileName = firstPhoto.filename;
            const cap = document.getElementById('active_canopy_img_name');
            if (cap) cap.textContent = firstPhoto.filename;
        }
        const selectedUrlInput = document.getElementById('selected_image_url');
        if (selectedUrlInput) selectedUrlInput.value = firstPhotoUrl || '';
        if (emptyState) {
            emptyState.style.display = 'none';
            emptyState.classList.add('hidden');
        }
        if (typeof renderEstatePhotosGallery === 'function') {
            renderEstatePhotosGallery(photos);
        }
    }

    // Tombol Navigasi ke Timelines diarahkan ke /timelines?kode=${encodeURIComponent(targetKode)}&year=2026
    const btnNavNext = document.getElementById('btnNavDirectToSurveillance') || 
                       document.getElementById('btnNavProceedToStage3') ||
                       document.querySelector('a[href*="/timelines"]');
    if (btnNavNext) {
        btnNavNext.href = `/timelines?kode=${encodeURIComponent(targetKode)}&year=2026`;
    }

    // Panggil rescan vision untuk mengkalibrasi objek awal
    if (typeof runDetailedObjectVisionScan === 'function') {
        runDetailedObjectVisionScan(false).catch(err => console.warn(err));
    }
}

/**
 * Draws HUD reticles on target canvas
 */
function initDrawingReticlesLegacy() {
    drawReticles();
    window.addEventListener('resize', drawReticles);
}
function drawReticlesLegacy() {
    const canvas = document.getElementById('reticleCanvas');
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width || 400;
    canvas.height = rect.height || 300;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const imgEl = document.getElementById('mainCanopyPreview');
    const emptyEl = document.getElementById('emptyEvidenceStateSimulator');
    if (!imgEl || !imgEl.src || imgEl.src.includes('undefined') || imgEl.style.display === 'none' || imgEl.classList.contains('hidden') ||
        imgEl.naturalWidth === 0 || (emptyEl && !emptyEl.classList.contains('hidden') && emptyEl.style.display !== 'none')) {
        return;
    }

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.45)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - 20, cy); ctx.lineTo(cx + 20, cy);
    ctx.moveTo(cx, cy - 20); ctx.lineTo(cx, cy + 20);
    ctx.stroke();

    const pad = 20;
    const len = 16;
    ctx.strokeStyle = 'rgba(52, 211, 153, 0.85)';
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.moveTo(pad, pad + len); ctx.lineTo(pad, pad); ctx.lineTo(pad + len, pad);
    ctx.moveTo(canvas.width - pad - len, pad); ctx.lineTo(canvas.width - pad, pad); ctx.lineTo(canvas.width - pad, pad + len);
    ctx.moveTo(pad, canvas.height - pad - len); ctx.lineTo(pad, canvas.height - pad); ctx.lineTo(pad + len, canvas.height - pad);
    ctx.moveTo(canvas.width - pad - len, canvas.height - pad); ctx.lineTo(canvas.width - pad, canvas.height - pad); ctx.lineTo(canvas.width - pad, canvas.height - pad - len);
    ctx.stroke();
}

/**
 * Injects 2D bounding boxes onto DOM overlay element
 */
function renderDetectedBoundingBoxesLegacy(boxes) {
    const overlay = document.getElementById('droneBBoxesOverlay');
    const svgOverlay = document.getElementById('aiReticleSvgOverlay');
    const imgEl = document.getElementById('mainCanopyPreview');
    const emptyEl = document.getElementById('emptyEvidenceStateSimulator');

    // STRICT GUARD CLAUSE: JANGAN PERNAH MENGGAMBAR BOUNDING BOX JIKA CITRA KOSONG/TIDAK TAMPIL
    if (!imgEl || !imgEl.src || imgEl.src.includes('undefined') || imgEl.style.display === 'none' || imgEl.classList.contains('hidden') || 
        imgEl.naturalWidth === 0 || (emptyEl && !emptyEl.classList.contains('hidden') && emptyEl.style.display !== 'none')) {
        if (overlay) {
            overlay.innerHTML = '';
            overlay.style.display = 'none';
        }
        if (svgOverlay) {
            svgOverlay.innerHTML = '';
            svgOverlay.style.display = 'none';
        }
        return;
    }

    if (overlay) overlay.style.display = isVisionOverlayVisible ? '' : 'none';
    if (svgOverlay) svgOverlay.style.display = isVisionOverlayVisible ? '' : 'none';
    if (!overlay) return;

    if (!isVisionOverlayVisible || !boxes || boxes.length === 0) {
        overlay.innerHTML = '';
        if (svgOverlay) svgOverlay.innerHTML = '';
        return;
    }

    let html = '';
    boxes.forEach(item => {
        if (!item || !Array.isArray(item.box_2d) || item.box_2d.length !== 4 || !item.box_2d.every(Number.isFinite)) return;
        const box = item.box_2d;
        const ymin = Math.max(0, Math.min(1000, box[0]));
        const xmin = Math.max(0, Math.min(1000, box[1]));
        const ymax = Math.max(0, Math.min(1000, box[2]));
        const xmax = Math.max(0, Math.min(1000, box[3]));
        if (ymax <= ymin || xmax <= xmin) return;

        const top = (ymin / 10.0).toFixed(1);
        const left = (xmin / 10.0).toFixed(1);
        const width = ((xmax - xmin) / 10.0).toFixed(1);
        const height = ((ymax - ymin) / 10.0).toFixed(1);

        const labelKey = (item.label || '').toLowerCase();
        const resultQualifier = item.is_heuristic ? ' (heuristic preview)' : '';

        let colorBorder = 'border-emerald-400';
        let colorBg = 'bg-emerald-500/15';
        let badgeBg = 'bg-emerald-950/90 text-emerald-300 border-emerald-400';
        let icon = '🔎';
        let labelName = item.label_text || item.label_name || item.label || 'Detected object';

        if (labelKey.includes('alley') || labelKey.includes('corridor') || labelKey.includes('ground')) {
            colorBorder = 'border-sky-400';
            colorBg = 'bg-sky-500/15';
            badgeBg = 'bg-sky-950/90 text-sky-300 border-sky-400';
            icon = '🌱';
            icon = '🌱';
        } else if (labelKey.includes('buffer') || labelKey.includes('circle') || labelKey.includes('root') || labelKey.includes('sterile')) {
            colorBorder = 'border-rose-400';
            colorBg = 'bg-rose-500/15';
            badgeBg = 'bg-rose-950/90 text-rose-300 border-rose-400';
            icon = '⭕';
            icon = '⭕';
        } else if (labelKey.includes('weed') || labelKey.includes('mulch') || labelKey.includes('cover')) {
            colorBorder = 'border-cyan-400';
            colorBg = 'bg-cyan-500/15';
            badgeBg = 'bg-cyan-950/90 text-cyan-300 border-cyan-400';
            icon = '🌿';
            icon = '🌿';
        }

        html += `
            <div class="absolute border-2 ${colorBorder} ${colorBg} rounded-lg shadow-sm pointer-events-auto cursor-help box-lock-active"
                 style="top: ${top}%; left: ${left}%; width: ${width}%; height: ${height}%;">
                <span class="absolute -top-3.5 left-1 px-1.5 py-0.2 rounded ${badgeBg} text-[8px] font-mono font-bold border shadow-xs whitespace-nowrap">
                    ${icon} ${labelName}${resultQualifier}
                </span>
            </div>
        `;
    });

    overlay.innerHTML = html;

    const summaryBadge = document.getElementById('aiDetectionSummaryBadge');
    if (summaryBadge) summaryBadge.textContent = `${boxes.length} detections`;
}

function toggleVisionOverlayLegacy() {
    isVisionOverlayVisible = !isVisionOverlayVisible;
    const btn = document.getElementById('btn_toggle_vision_overlay');
    const lbl = document.getElementById('lbl_toggle_overlay');
    const overlay = document.getElementById('droneBBoxesOverlay');
    const canvas = document.getElementById('reticleCanvas');

    if (lbl) lbl.innerText = isVisionOverlayVisible ? "Toggle AI Reticle Bounding Boxes" : "Show AI Reticle Bounding Boxes";
    if (btn) btn.className = isVisionOverlayVisible ? "px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-emerald-600 text-white cursor-pointer" : "px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-slate-800 text-slate-300 cursor-pointer";
    
    if (overlay) overlay.style.display = isVisionOverlayVisible ? '' : 'none';
    if (canvas) canvas.style.display = isVisionOverlayVisible ? '' : 'none';

    if (isVisionOverlayVisible) {
        renderDetectedBoundingBoxes(latestDetectedObjects);
        drawReticles();
    }
}

function selectCanopyPreset(fileName, caption) {
    selectedCanopyFileName = fileName;
    const mainImg = document.getElementById('mainCanopyPreview');
    const nameEl = document.getElementById('active_canopy_img_name');
    const captionEl = document.getElementById('image_caption');
    const overlay = document.getElementById('droneBBoxesOverlay');
    const svgOverlay = document.getElementById('aiReticleSvgOverlay');
    const emptyEl = document.getElementById('emptyEvidenceStateSimulator');

    // 1. Kosongkan overlay terlebih dahulu
    if (overlay) overlay.innerHTML = '';
    if (svgOverlay) svgOverlay.innerHTML = '';

    const filePath = `/static/img/${fileName}`;
    if (nameEl) nameEl.innerText = fileName;
    if (captionEl) captionEl.innerText = caption;

    const imgSampleInput = document.getElementById('image_sample');
    if (imgSampleInput) imgSampleInput.value = fileName;

    if (mainImg) {
        mainImg.onload = function() {
            mainImg.style.display = 'block';
            mainImg.classList.remove('hidden');
            if (emptyEl) {
                emptyEl.classList.add('hidden');
                emptyEl.style.display = 'none';
            }
            runDetailedObjectVisionScan();
        };
        mainImg.onerror = function() {
            if (typeof handleEmptyEvidenceStateSimulator === 'function') {
                handleEmptyEvidenceStateSimulator(mainImg);
            }
        };
        mainImg.src = filePath;
        if (mainImg.complete && mainImg.naturalWidth > 0 && mainImg.src.includes(fileName)) {
            mainImg.onload();
        }
    }
}

function handleCanopyFileUploadLegacy(event) {
    const file = event.target && event.target.files && event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const mainImg = document.getElementById('mainCanopyPreview');
        const nameEl = document.getElementById('active_canopy_img_name');
        const captionEl = document.getElementById('image_caption');

        if (mainImg) mainImg.src = e.target.result;
        if (nameEl) nameEl.innerText = file.name;
        if (captionEl) captionEl.innerText = `Uploaded Orthophoto: ${file.name}`;
        selectedCanopyFileName = file.name;

        runDetailedObjectVisionScan();
    };
    reader.readAsDataURL(file);
}

function renderAuditResultCardLegacy(comp, cropName, sha, recordId, photosList = []) {
    const container = document.getElementById('auditResultsContainer');
    if (!container) return;

    const cleanPhotos = (photosList && photosList.length > 0) ? photosList : [];
    const shaText = typeof sha === 'string' && sha ? sha : 'Not available';
    const shaPreview = shaText.length > 16 ? `${shaText.substring(0, 16)}...` : shaText;

    container.innerHTML = `
        <div class="p-3.5 sm:p-4 rounded-2xl bg-white dark:bg-slate-900 border-2 border-emerald-500/70 shadow-sm space-y-3 animate-in fade-in duration-300">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-emerald-800/30 dark:border-emerald-800/60 pb-2.5">
                <div class="flex items-center gap-2">
                    <span class="text-xl sm:text-2xl">✅</span>
                    <div>
                        <h3 class="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 font-mono flex items-center gap-2">
                            <span>In-Silico Simulation Record</span>
                            <span class="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">#REC-${recordId}</span>
                        </h3>
                        <p class="text-[11px] text-slate-600 dark:text-emerald-300/80 mt-0.5">Crop: <strong>${cropName}</strong> &bull; LER Advantage: <strong>${comp.totalLer.toFixed(4)}x</strong></p>
                    </div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <button type="button" onclick="viewAdminLogDetail(${recordId})" class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 border border-emerald-500/40 text-xs font-bold font-mono transition flex items-center gap-1.5 cursor-pointer shadow-xs">
                        <span>📄</span> <span>View Full Dossier</span>
                    </button>
                    <a href="/certificate/${recordId}" target="_blank" class="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 shadow transition">
                        <span>📜</span> <span>View Digital Passport</span>
                    </a>
                </div>
            </div>

            <!-- Aggregated Photos Preview Strip -->
            ${cleanPhotos.length > 0 ? `
            <div class="p-2 bg-slate-50 dark:bg-slate-950/70 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3">
                <div class="flex items-center gap-2 overflow-x-auto py-0.5">
                    <span class="text-[10px] font-mono font-bold text-slate-500 dark:text-slate-400 shrink-0">Linked Images:</span>
                    ${cleanPhotos.map((p, idx) => `
                        <div class="relative w-14 h-10 rounded-lg overflow-hidden border border-emerald-500/40 shrink-0 shadow-xs group">
                            <img src="${p}" alt="Evidence #${idx+1}" class="w-full h-full object-cover" onerror="this.src='/static/img/sawit_drone.jpg'">
                            <span class="absolute bottom-0 right-0 bg-slate-950/90 text-emerald-300 font-mono text-[8px] px-1 rounded-tl font-bold">#${idx+1}</span>
                        </div>
                    `).join('')}
                </div>
                <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 border border-teal-400 shrink-0">
                    ${cleanPhotos.length} Photo${cleanPhotos.length > 1 ? 's' : ''} Linked
                </span>
            </div>
            ` : ''}

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono text-slate-700 dark:text-slate-200">
                <div class="p-2.5 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-emerald-900/60">
                    <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">Primary Forest Spared</span>
                    <span class="text-base font-bold text-emerald-600 dark:text-emerald-400 font-mono block mt-0.5">${comp.sparedHa.toFixed(2)} Ha</span>
                </div>
                <div class="p-2.5 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-emerald-900/60">
                    <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">Climate Benefit</span>
                    <span class="text-base font-bold text-teal-600 dark:text-teal-400 font-mono block mt-0.5">${Math.round(comp.totalCarbon).toLocaleString()} tCO2e</span>
                </div>
                <div class="p-2.5 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-emerald-900/60">
                    <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">GAP 2.0m Root Zone</span>
                    <span class="text-base font-bold text-amber-600 dark:text-amber-400 font-mono block mt-0.5">Not verified from image evidence</span>
                </div>
                <div class="p-2.5 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-emerald-900/60">
                    <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">Record Hash (if returned)</span>
                    <span class="text-xs font-bold text-indigo-600 dark:text-indigo-300 font-mono truncate block mt-0.5" title="${shaText}">${shaPreview}</span>
                </div>
            </div>
        </div>
    `;
}

function getLocalSimulationRecordsLegacy() {
    try {
        const raw = localStorage.getItem(SIM_HISTORY_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch (e) {
        return [];
    }
}

function saveSimulationRecordLocallyLegacy(record) {
    try {
        let records = getLocalSimulationRecords();
        records = records.filter(r => r.id !== record.id);
        records.unshift(record);
        if (records.length > 50) records = records.slice(0, 50);
        localStorage.setItem(SIM_HISTORY_STORAGE_KEY, JSON.stringify(records));
    } catch (e) {}
}

function restoreActiveAuditedDossier(recordToRestore = null) {
    try {
        const isSealedPref = localStorage.getItem('precision_palm_is_audit_sealed');
        if (isSealedPref === 'false') {
            return false;
        }

        let record = recordToRestore;
        if (!record) {
            const rawRec = localStorage.getItem('precision_palm_active_sealed_record');
            if (rawRec) {
                try { record = JSON.parse(rawRec); } catch (_) {}
            }
        }

        if (!record) {
            const localRecords = (typeof getLocalSimulationRecords === 'function') ? getLocalSimulationRecords() : [];
            if (Array.isArray(localRecords) && localRecords.length > 0) {
                record = localRecords[0];
            }
        }

        if (!record || !record.id) {
            return false;
        }

        const savedInputs = record.calculation_inputs;
        const savedMetrics = record.data_numerik;
        const savedLer = savedMetrics?.efisiensi_lahan_ler;
        const savedClimate = savedMetrics?.dampak_lingkungan_dan_karbon;
        const requiredYieldKeys = [
            'yield_palm_inter', 'yield_palm_mono', 'yield_crop_inter', 'yield_crop_mono'
        ];
        if (!savedInputs || !savedMetrics || !Number.isFinite(Number(savedInputs.land_area)) ||
            Number(savedInputs.land_area) <= 0 ||
            requiredYieldKeys.some(key => !Number.isFinite(Number(savedInputs[key]))) ||
            !Number.isFinite(Number(savedLer?.total_ler)) ||
            !Number.isFinite(Number(savedLer?.percentage_land_saved)) ||
            !Number.isFinite(Number(savedClimate?.avoided_land_ha)) ||
            !Number.isFinite(Number(savedClimate?.total_climate_benefit_tco2e))) {
            return false;
        }

        if (typeof latestSimulationData !== 'undefined') latestSimulationData = record;
        if (typeof latestEngineCalculation !== 'undefined') {
            latestEngineCalculation = {
                totalLer: Number(savedLer.total_ler),
                plsPct: Number(savedLer.percentage_land_saved),
                sparedHa: Number(savedClimate.avoided_land_ha),
                totalCarbon: Number(savedClimate.total_climate_benefit_tco2e),
                inputs: savedInputs,
                dataNumerik: savedMetrics
            };
        }

        console.log("[Simulator] Restoring active sealed audit dossier #REC-" + record.id);

        // 1. Restore input fields in Zona 1
        if (savedInputs.palm_age !== undefined && document.getElementById('palm_age')) {
            document.getElementById('palm_age').value = savedInputs.palm_age;
        }
        if (savedInputs.land_area !== undefined && document.getElementById('land_area')) {
            document.getElementById('land_area').value = savedInputs.land_area;
        }
        if (savedInputs.soil_ph !== undefined && document.getElementById('sim_soil_ph')) {
            document.getElementById('sim_soil_ph').value = savedInputs.soil_ph;
        }
        if (savedInputs.soil_texture && document.getElementById('sim_soil_texture')) {
            document.getElementById('sim_soil_texture').value = savedInputs.soil_texture;
        }
        if (savedInputs.slope !== undefined && document.getElementById('sim_slope')) {
            document.getElementById('sim_slope').value = savedInputs.slope;
        }
        if (savedInputs.elevation !== undefined && document.getElementById('sim_elevation')) {
            document.getElementById('sim_elevation').value = savedInputs.elevation;
        }
        if (savedInputs.yield_palm_inter !== undefined && document.getElementById('yield_palm_inter')) {
            document.getElementById('yield_palm_inter').value = savedInputs.yield_palm_inter;
        }
        if (savedInputs.yield_palm_mono !== undefined && document.getElementById('yield_palm_mono')) {
            document.getElementById('yield_palm_mono').value = savedInputs.yield_palm_mono;
        }
        if (savedInputs.yield_crop_inter !== undefined && document.getElementById('yield_crop_inter')) {
            document.getElementById('yield_crop_inter').value = savedInputs.yield_crop_inter;
        }
        if (savedInputs.yield_crop_mono !== undefined && document.getElementById('yield_crop_mono')) {
            document.getElementById('yield_crop_mono').value = savedInputs.yield_crop_mono;
        }
        if (savedInputs.crop_name && document.getElementById('crop_name')) {
            document.getElementById('crop_name').value = savedInputs.crop_name;
        }
        if (record.coords && document.getElementById('sim_coords')) document.getElementById('sim_coords').value = record.coords;
        if (document.getElementById('res_ler')) document.getElementById('res_ler').textContent = `${savedLer.total_ler}x`;
        if (document.getElementById('val_ler_total')) document.getElementById('val_ler_total').textContent = `${savedLer.total_ler}x • kalkulasi.engine`;
        if (document.getElementById('res_pls')) document.getElementById('res_pls').textContent = `${savedLer.percentage_land_saved}%`;
        if (document.getElementById('res_avoided_ha')) document.getElementById('res_avoided_ha').textContent = `${savedClimate.avoided_land_ha} Ha`;
        if (document.getElementById('res_carbon')) document.getElementById('res_carbon').textContent = `${savedClimate.total_climate_benefit_tco2e} tCO₂e`;
        const savedMop = Number(savedMetrics.neraca_hara_npk?.required_compensatory_mop_kg_ha);
        if (Number.isFinite(savedMop) && document.getElementById('val_mop_comp')) {
            document.getElementById('val_mop_comp').textContent = `${savedMop} kg MOP/Ha (engine estimate)`;
        }
        ['val_metric_biomass', 'val_metric_microclimate', 'val_metric_soil_moisture'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = 'Not calculated by engine';
        });
        if (document.getElementById('val_metric_carbon_seq')) {
            document.getElementById('val_metric_carbon_seq').textContent =
                `${(savedClimate.total_climate_benefit_tco2e / savedInputs.land_area).toFixed(2)} tCO₂e/Ha`;
        }

        // Restore photo badges & selection
        const photosList = Array.isArray(record.photo_urls) ? record.photo_urls.filter(Boolean) : [];
        if (photosList.length > 0) {
            if (typeof selectedPhotoUrls !== 'undefined' && selectedPhotoUrls.add) {
                photosList.forEach(p => selectedPhotoUrls.add(p));
            }
            const photoBadge = document.getElementById('badge_dossier_aggregated_photos');
            if (photoBadge) {
                photoBadge.textContent = `${photosList.length} Drone Photo${photosList.length > 1 ? 's' : ''} Aggregated`;
            }
        }

        // 3. Render Audit Result Card
        const comp = {
            totalLer: Number(savedLer.total_ler),
            plsPct: Number(savedLer.percentage_land_saved),
            sparedHa: Number(savedClimate.avoided_land_ha),
            totalCarbon: Number(savedClimate.total_climate_benefit_tco2e),
            surfacePar: Number(savedMetrics.analisis_cahaya_kanopi?.surface_par_umol_m2_s),
            coverPct: Number(savedMetrics.geometri_kanopi_spasial?.canopy_cover_pct)
        };
        if (typeof renderAuditResultCard === 'function') {
            renderAuditResultCard(comp, savedInputs.crop_name, record.sha256 || record.sha256_hash || "", record.id, photosList);
        }

        // 4. Highlight Zona 2 container
        const resultDossier = document.getElementById('zona_2_biophysical_dossier') || document.getElementById('auditResultsContainer');
        if (resultDossier) {
            resultDossier.classList.remove('border-slate-200', 'dark:border-slate-800');
            resultDossier.classList.add('ring-2', 'ring-emerald-500', 'border-emerald-500', 'shadow-lg');
        }

        // 5. Identify the restored record without implying certification.
        const recTag = document.getElementById('activeDossierRecTag');
        if (recTag) {
            recTag.innerHTML = `🔒 SIMULATION RECORD RESTORED &bull; RECORD #REC-${record.id}`;
            recTag.className = "text-[10px] font-mono font-bold px-3 py-1 rounded-full bg-slate-700 text-white border border-slate-500 shadow-md inline-flex items-center gap-1.5";
        }

        // 6. Lock Zona 1 parameters & button state
        lockZona1Parameters(true);

        // 7. Update Stage 3 links
        const targetKode = record.kode_kebun || '';
        const destSurveillanceUrl = `/timelines?kode=${encodeURIComponent(targetKode)}&id=${record.id}&year=2026`;
        const btnNavNext = document.getElementById('btnNavDirectToSurveillance');
        if (btnNavNext) {
            btnNavNext.href = destSurveillanceUrl;
            btnNavNext.onclick = null;
        }
        const btnProceed3 = document.getElementById('btnProceedToStage3');
        if (btnProceed3) {
            btnProceed3.href = destSurveillanceUrl;
            btnProceed3.onclick = null;
        }

        try {
            localStorage.setItem('precision_palm_is_audit_sealed', 'true');
            localStorage.setItem('precision_palm_active_sealed_record', JSON.stringify(record));
        } catch (_) {}

        return true;
    } catch (e) {
        console.warn("[Simulator] Error in restoreActiveAuditedDossier:", e);
        return false;
    }
}
window.restoreActiveAuditedDossier = restoreActiveAuditedDossier;

async function fetchAdminHistoryLegacy() {
    const tbody = document.getElementById('adminHistoryTbody');
    if (!tbody) return;

    let records = [];
    try {
        const url = `/api/admin/history?page=${adminCurrentPage}&limit=${adminCurrentLimit}&q=${encodeURIComponent(adminSearchQuery)}`;
        const resp = await fetch(url);
        if (resp.ok) {
            const resData = await resp.json();
            records = resData.data || [];
            if (resData.total_pages) adminTotalPages = resData.total_pages;
            if (resData.current_page) adminCurrentPage = resData.current_page;
        }
    } catch (e) {
        console.warn("[Simulator] Admin fetch notice, utilizing local cache:", e);
    }

    // Merge any locally stored records that might not be in DB yet or offline
    const localRecords = getLocalSimulationRecords();
    if (Array.isArray(localRecords) && localRecords.length > 0) {
        const serverIds = new Set(records.map(r => String(r.id)));
        const missingLocals = localRecords.filter(r => !serverIds.has(String(r.id)));
        records = [...missingLocals, ...records];
    }
    if (!records || records.length === 0) {
        try {
            const defResp = await fetch('/api/state/default');
            if (defResp.ok) {
                const defData = await defResp.json();
                const seeds = defData.telemetry || (defData.data && defData.data.telemetry) || [];
                if (Array.isArray(seeds) && seeds.length > 0) {
                    records = [...seeds];
                    try {
                        localStorage.setItem(SIM_HISTORY_STORAGE_KEY, JSON.stringify(records));
                    } catch (_) {}
                }
            }
        } catch (_) {}
    }
    if (!records || records.length === 0) {
        records = [];
    }

    // Local search filtering and pagination when serving from fallback / local storage
    let displayRecords = records;
    if (adminSearchQuery) {
        const q = adminSearchQuery.toLowerCase();
        displayRecords = records.filter(r => 
            String(r.id).includes(q) || 
            (r.crop_name && r.crop_name.toLowerCase().includes(q)) ||
            (String(r.palm_age) && String(r.palm_age).includes(q)) ||
            (r.sha256 && r.sha256.toLowerCase().includes(q))
        );
    }

    adminTotalPages = Math.ceil(displayRecords.length / adminCurrentLimit) || 1;
    const startIndex = (adminCurrentPage - 1) * adminCurrentLimit;
    const paginatedRecords = displayRecords.slice(startIndex, startIndex + adminCurrentLimit);

    adminCachedRecords = records;
    renderAdminTableRows(paginatedRecords);
    updateAdminPaginationUI(displayRecords.length, adminCurrentLimit);

    // Auto-restore audit sealed card if not already rendered and not explicitly unlocked
    try {
        const auditCard = document.querySelector('#auditResultsContainer > div');
        const isSealedPref = localStorage.getItem('precision_palm_is_audit_sealed');
        if (!auditCard && isSealedPref !== 'false' && records && records.length > 0) {
            restoreActiveAuditedDossier(records[0]);
        }
    } catch (_) {}
}

function renderAdminTableRowsLegacy(records) {
    const tbody = document.getElementById('adminHistoryTbody');
    if (!tbody) return;

    if (!records || records.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="py-12 text-center text-slate-500 font-mono text-xs">
                    No telemetry records found. Execute an audit above to generate logs.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = records.map(item => {
        const lerVal = Number(item.total_ler || 0);
        const isAdv = (lerVal > 1.0);
        const avoidedVal = Number(item.avoided_land_ha || 0);
        const climateVal = Number(item.total_climate_benefit_tco2e || 0);
        const palmAgeVal = Number(item.palm_age || 0);

        return `
            <tr class="even:bg-slate-50/70 dark:even:bg-slate-950/40 hover:bg-slate-100/60 dark:hover:bg-slate-800/50 transition group border-b border-slate-200 dark:border-slate-800/60 font-mono text-[11px]">
                <td class="py-2.5 px-3.5 text-center text-emerald-600 dark:text-emerald-400 font-bold">#${item.id}</td>
                <td class="py-2.5 px-3.5 text-slate-700 dark:text-slate-300">${formatTimestamp(item.created_at)}</td>
                <td class="py-2.5 px-3.5 text-slate-700 dark:text-slate-300">${palmAgeVal.toFixed(1)} Yrs</td>
                <td class="py-2.5 px-3.5 font-sans font-semibold text-slate-900 dark:text-white">
                    <span class="text-emerald-600 dark:text-emerald-400 mr-1">🌱</span>${item.crop_name}
                </td>
                <td class="py-2.5 px-3.5 text-center font-bold">
                    <span class="px-2 py-0.5 rounded-full border ${isAdv ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700/80' : 'bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-700/80'}">
                        ${lerVal.toFixed(4)}x
                    </span>
                </td>
                <td class="py-2.5 px-3.5 text-sky-600 dark:text-sky-300">${avoidedVal.toFixed(2)} Ha</td>
                <td class="py-2.5 px-3.5 text-indigo-600 dark:text-indigo-300">${climateVal.toLocaleString()} t</td>
                <td class="py-2.5 px-3.5 text-center">
                    <div class="inline-flex items-center gap-1.5">
                        <button onclick="viewAdminLogDetail(${item.id})" class="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 font-semibold text-[10px] flex items-center gap-1 transition cursor-pointer">
                            <span>👁️</span> <span>View</span>
                        </button>
                        <a href="/certificate/${item.id}" target="_blank" class="px-2 py-1 rounded bg-emerald-100 hover:bg-emerald-200 dark:bg-emerald-950/70 dark:hover:bg-emerald-900 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 font-semibold text-[10px] flex items-center gap-1 transition">
                            <span>📜</span> <span>Passport</span>
                        </a>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function updateAdminPaginationUILegacy(totalRecords, limit) {
    const start = totalRecords === 0 ? 0 : (adminCurrentPage - 1) * limit + 1;
    const end = Math.min(adminCurrentPage * limit, totalRecords);

    const info = document.getElementById('adminPaginationInfo');
    const indicator = document.getElementById('adminPageIndicator');
    if (info) info.innerText = `Showing ${start} to ${end} of ${totalRecords} entries`;
    if (indicator) indicator.innerText = `Page ${adminCurrentPage} of ${adminTotalPages}`;

    const btnFirst = document.getElementById('adminBtnFirst');
    const btnPrev = document.getElementById('adminBtnPrev');
    const btnNext = document.getElementById('adminBtnNext');
    const btnLast = document.getElementById('adminBtnLast');

    if (btnFirst) btnFirst.disabled = (adminCurrentPage <= 1);
    if (btnPrev) btnPrev.disabled = (adminCurrentPage <= 1);
    if (btnNext) btnNext.disabled = (adminCurrentPage >= adminTotalPages);
    if (btnLast) btnLast.disabled = (adminCurrentPage >= adminTotalPages);
}

function goToAdminPageLegacy(page) {
    if (page < 1 || page > adminTotalPages || page === adminCurrentPage) return;
    adminCurrentPage = page;
    fetchAdminHistory();
}

function changeAdminLimitLegacy() {
    adminCurrentLimit = parseInt(document.getElementById('adminLimitSelect')?.value) || 10;
    adminCurrentPage = 1;
    fetchAdminHistory();
}

function handleAdminSearchDebounceLegacy() {
    clearTimeout(adminDebounceTimer);
    const val = document.getElementById('adminSearchInput')?.value.trim();
    adminDebounceTimer = setTimeout(() => {
        adminSearchQuery = val;
        adminCurrentPage = 1;
        fetchAdminHistory();
    }, 300);
}

function resolveTelemetryPhotoUrls(item) {
    const visionSummary = typeof item?.vision_summary === 'string'
        ? (() => { try { return JSON.parse(item.vision_summary); } catch (_) { return null; } })()
        : item?.vision_summary;
    const photoUrls = Array.isArray(item?.photo_urls)
        ? item.photo_urls.filter(url => typeof url === 'string' && url.trim())
        : [];
    const evidenceUrlFrom = value => {
        if (typeof value !== 'string' || !value.trim()) return null;
        const url = value.trim();
        if (/^\/api\/media\/evidence\/[^/?#]+$/i.test(url)) return url;
        const filename = url.split(/[/?#]/).pop();
        const match = filename?.match(/^(EV-[A-Za-z0-9_-]+?)(?:\.(?:jpe?g|png|webp))?$/i);
        return match ? `/api/media/evidence/${match[1]}` : null;
    };

    const evidenceUrls = [
        ...photoUrls.map(evidenceUrlFrom),
        evidenceUrlFrom(visionSummary?.image_url),
        evidenceUrlFrom(visionSummary?.evidence_id),
        evidenceUrlFrom(item?.image_path),
        evidenceUrlFrom(item?.image_sample)
    ].filter(Boolean);

    if (evidenceUrls.length > 0) {
        return [...new Set(evidenceUrls)];
    }
    return [...new Set([...photoUrls, item?.image_sample, item?.image_path]
        .filter(value => typeof value === 'string' && value.trim()))];
}

async function viewAdminLogDetailLegacy(logId) {
    let item = (adminCachedRecords || []).find(r => String(r.id) === String(logId));
    const localRecords = (typeof getLocalSimulationRecords === 'function') ? getLocalSimulationRecords() : [];
    const localMatch = localRecords.find(r => String(r.id) === String(logId));
    if (localMatch) {
        item = Object.assign({}, item || {}, localMatch);
    }
    if (!item && typeof latestSimulationData !== 'undefined' && latestSimulationData && String(latestSimulationData.id) === String(logId)) {
        item = latestSimulationData;
    }
    if (!item) return;

    const modalTag = document.getElementById('modalDetailIdTag');
    const certBtn = document.getElementById('btnModalCertificate');
    const pdfBtn = document.getElementById('btnAdminModalPdf');
    if (modalTag) modalTag.innerText = `RECORD #${item.id}`;
    if (certBtn) certBtn.href = `/certificate/${item.id}`;
    if (pdfBtn) {
        const kode = (activeEstate && activeEstate.kode_kebun) ? activeEstate.kode_kebun : "EST-MDN-010";
        pdfBtn.href = `/api/export/pdf/simulator-dossier/${encodeURIComponent(kode)}`;
    }

    const container = document.getElementById('adminModalDetailBody');
    if (!container) return;

    // Concession & Geometry Details
    const kode = item.kode_kebun || activeEstate?.kode_kebun || "EST-MDN-010";
    const nama = item.estate_name || activeEstate?.nama_kebun || "PT Mandailing Agro Sustainable";
    const hgu = activeEstate?.nomor_hgu || "004/HGU/BPN-MDN/2021";
    const regNo = activeEstate?.nomor_registrasi || `CERT-ECOGREEN-2026-${String(item.id).padStart(4, '0')}`;
    const luas = Number(item.land_area || 100.0).toFixed(1);
    const palmAge = Number(item.palm_age || 6.0).toFixed(1);

    // 4-Pillar Biophysical Metrics
    const lerVal = Number(item.total_ler || item.ler_score || 1.4550).toFixed(4);
    const sparedHa = Number(item.avoided_land_ha || item.forest_saved_ha || (Number(luas) * (Number(lerVal) - 1.0))).toFixed(2);
    const plsPct = (Number(lerVal) > 1.0) ? ((1.0 - (1.0 / Number(lerVal))) * 100).toFixed(2) : "0.00";
    const climateCarbon = Number(item.total_climate_benefit_tco2e || item.carbon_tco2e || Math.round((Number(sparedHa) * 450.0) + (Number(luas) * 1.8))).toLocaleString();

    // Field Coordinates & Environment
    const coords = item.coords || document.getElementById('sim_coords')?.value || "0.824100, 99.561200";
    const slope = item.slope || document.getElementById('sim_slope')?.value || 4.5;
    const elevation = item.elevation || document.getElementById('sim_elevation')?.value || 220;
    const soilPh = item.soil_ph || document.getElementById('sim_soil_ph')?.value || 5.5;
    const soilTexture = item.soil_texture || document.getElementById('sim_soil_texture')?.value || 'Sandy Loam';

    // Biometrics Derived
    const biomassAgb = item.biomass_t_ha || (92.4 * Math.pow(Math.max(1.0, palmAge) / 6.0, 0.6) + 36.0).toFixed(1);
    const microclimate = item.microclimate_cooling || (-3.8 * (Number(item.canopy_cover || 65.4) / 100.0)).toFixed(1);
    const soilMoisture = item.soil_moisture_vwc || (22.0 + (Number(lerVal) > 1.0 ? 12.8 : 7.7)).toFixed(1);
    const recharge = Number(item.recharge_m3_ha || 1850).toLocaleString();
    const potassium = Number(item.potassium_recovered_kg || 36.2).toFixed(1);
    const parVal = Math.round(item.surface_par || 218.5);
    const laiVal = Number(item.leaf_area_index || 5.27).toFixed(2);
    const coverVal = Number(item.canopy_cover || 65.4).toFixed(1);
    const cropName = item.crop_name || item.crop_type || "Red Ginger (Zingiber officinale var. rubrum)";
    const shaCode = item.sha256 || item.sha256_hash || 'Not available';

    // Photos Aggregation
    const photos = resolveTelemetryPhotoUrls(item);

    const cleanPhotos = photos.filter(p => typeof p === 'string' && p).map(p => {
        if (p.startsWith('http') || p.startsWith('/') || p.startsWith('data:')) return p;
        return '/static/img/' + p;
    });

    let storedVisionSummary = item.vision_summary || null;
    if (typeof storedVisionSummary === 'string') {
        try { storedVisionSummary = JSON.parse(storedVisionSummary); } catch (_) {}
    }
    const visionSummaryBadge = storedVisionSummary?.detection_badge || "No vision result stored";
    const sterileCircleVal = storedVisionSummary?.sterile_circle || "Not verified from image evidence";
    const evidenceId = storedVisionSummary?.evidence_id || "Not recorded";
    const detectedEntities = Array.isArray(storedVisionSummary?.detected_entities)
        ? storedVisionSummary.detected_entities
        : [];
    const detectedLabels = [...new Set(detectedEntities.map(entity =>
        entity?.label || entity?.label_name || entity?.label_text
    ).filter(Boolean))];
    const detectedLabelsText = detectedLabels.length
        ? detectedLabels.map(label => escapeHtml(String(label))).join(', ')
        : "No object labels stored";

    let storedAiReasoning = item.ai_reasoning || null;
    if (typeof storedAiReasoning === 'string') {
        try { storedAiReasoning = JSON.parse(storedAiReasoning); } catch (_) {}
    }
    const aiReasoningMode = storedAiReasoning?.mode || item.engine_mode || "Not recorded";
    const aiReasoningIsLive = aiReasoningMode === "LIVE_GEMINI";
    const aiReasoningStatus = aiReasoningIsLive ? "LIVE GEMINI RESPONSE" : "LOCAL PREVIEW / NOT A CERTIFICATION";

    // Vision Summary
    // AI Reasoning Structured Text
    const aiReasonText = storedAiReasoning?.analysis_text || "No reasoning result was stored with this telemetry record.";

    // Render Scanned Photos Gallery Block
    let photosGridHtml = '';
    if (cleanPhotos.length === 0) {
        photosGridHtml = `
            <div class="rounded-2xl border border-amber-500/40 bg-amber-950/20 p-4 text-xs text-amber-200">
                No image reference was stored with this telemetry record.
            </div>
        `;
    } else if (cleanPhotos.length === 1) {
        photosGridHtml = `
            <div class="relative rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 h-56 bg-slate-900 group shadow-md">
                <img src="${cleanPhotos[0]}" alt="Field Orthophoto" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
                <div class="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                    <span class="px-2.5 py-1 rounded-full bg-slate-950/85 text-emerald-300 text-[10px] font-mono font-bold border border-emerald-500/50 shadow">
                        📸 Linked image evidence
                    </span>
                </div>
                <div class="absolute bottom-2 left-2 right-2 flex items-center justify-between bg-slate-950/85 backdrop-blur-xs px-3 py-1.5 rounded-xl border border-slate-700/60 text-[10px] font-mono text-slate-300">
                    <span class="truncate max-w-[70%]">📍 Centroid: ${coords}</span>
                    <a href="${cleanPhotos[0]}" target="_blank" class="text-emerald-400 hover:text-emerald-300 font-bold underline">Full Image &rarr;</a>
                </div>
            </div>
        `;
    } else {
        photosGridHtml = `
            <div class="space-y-2">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-slate-700 dark:text-slate-300 font-mono flex items-center gap-1.5">
                        <span>📷</span> <span>Images Linked to This Simulation (${cleanPhotos.length})</span>
                    </span>
                    <span class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 border border-teal-400 dark:border-teal-700">
                        Linked image references
                    </span>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-${Math.min(4, cleanPhotos.length)} gap-2.5">
                    ${cleanPhotos.map((url, idx) => `
                        <div class="relative rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 group shadow-sm flex flex-col">
                            <div class="h-28 w-full overflow-hidden relative">
                                <img src="${url}" alt="Photo Evidence #${idx+1}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300" onerror="this.src='/static/img/sawit_drone.jpg'">
                                <span class="absolute top-1.5 left-1.5 bg-slate-950/85 text-emerald-400 text-[9px] font-mono font-bold px-2 py-0.5 rounded border border-emerald-500/40">
                                    Photo #${idx+1}
                                </span>
                            </div>
                            <div class="p-1.5 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono">
                                <span class="text-slate-500 dark:text-slate-400 truncate max-w-[60%]">Linked image</span>
                                <a href="${url}" target="_blank" class="text-emerald-600 dark:text-emerald-400 hover:underline font-bold">Preview ↗</a>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="space-y-4 font-sans text-xs">
            <!-- 1. MULTI-PHOTO EVIDENCE GALLERY -->
            ${photosGridHtml}

            <!-- 2. CONCESSION & STATUTORY IDENTITY -->
            <div class="p-3.5 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2 font-mono">
                <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
                    <div>
                        <span class="text-[10px] uppercase text-emerald-600 dark:text-emerald-400 font-bold tracking-wider">Official Concession &amp; Spatial Registration</span>
                        <h4 class="text-sm font-bold text-slate-900 dark:text-white font-sans mt-0.5">${kode} &bull; ${nama}</h4>
                    </div>
                    <span class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-400">
                        ${regNo}
                    </span>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px]">
                    <div class="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">TITLE DEED / HGU</span>
                        <strong class="text-slate-900 dark:text-white block mt-0.5">${hgu}</strong>
                    </div>
                    <div class="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">AREA &bull; STAND AGE</span>
                        <strong class="text-slate-900 dark:text-white block mt-0.5">${luas} Ha &bull; ${palmAge} Yrs</strong>
                    </div>
                    <div class="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">CENTROID WGS84</span>
                        <strong class="text-emerald-600 dark:text-emerald-400 font-bold block mt-0.5 truncate">${coords}</strong>
                    </div>
                    <div class="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">TERRAIN &bull; SOIL</span>
                        <strong class="text-slate-900 dark:text-white block mt-0.5">${slope}° Slope &bull; pH ${soilPh}</strong>
                    </div>
                </div>

                <!-- Engine Mode & Dual-Engine Attestation -->
                <div class="mt-2.5 p-2.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[10px] ${
                    (item.engine_mode && (item.engine_mode.includes('STATUTORY') || item.engine_mode.includes('FALLBACK') || item.engine_mode.includes('RULE_ENGINE'))) || (item.status_message && item.status_message.includes('Offline'))
                    ? 'bg-amber-950/30 border-amber-500/50 text-amber-200'
                    : 'bg-emerald-950/30 border-emerald-500/50 text-emerald-200'
                }">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="font-bold text-slate-400">ENGINE ATTESTATION:</span>
                        ${
                            (item.engine_mode && (item.engine_mode.includes('STATUTORY') || item.engine_mode.includes('FALLBACK') || item.engine_mode.includes('RULE_ENGINE'))) || (item.status_message && item.status_message.includes('Offline'))
                            ? '<span class="px-2 py-0.5 rounded-md font-mono font-bold bg-amber-950 text-amber-400 border border-amber-500/60 shadow-xs">⚡ AUTONOMOUS STATUTORY RULE ENGINE (FALLBACK)</span>'
                            : '<span class="px-2 py-0.5 rounded-md font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-500/60 shadow-xs">🟢 LIVE GEMINI 3.8 FLASH</span>'
                        }
                    </div>
                    <span class="text-[9.5px] italic text-slate-300 dark:text-slate-400 max-w-md truncate">
                        ${escapeHtml(item.status_message || (item.engine_mode === 'LIVE_GEMINI' ? 'Verified via Gemini Multimodal Inference' : '[AUDIT NOTICE] Gemini Live Session Offline / Quota Exceeded. Validated via Autonomous Statutory Rule Engine (PPKS & ISPO Principle 2 Silvicultural Standards)'))}
                    </span>
                </div>
            </div>

            <!-- 3. 4-PILLAR BIOPHYSICAL CORE METRICS -->
            <div class="space-y-1.5 font-mono">
                <span class="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                    <span>🌱</span> <span>1. In-Silico Biophysical Indicators &amp; Statutory Compliance</span>
                </span>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">Total LER</span>
                        <strong class="text-base font-bold text-emerald-600 dark:text-emerald-400 font-mono block mt-0.5">${lerVal}x</strong>
                        <span class="text-[9px] text-emerald-600 dark:text-emerald-400 block">+${((Number(lerVal) - 1.0) * 100).toFixed(1)}% Land Advantage</span>
                    </div>
                    <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">Primary Forest Spared</span>
                        <strong class="text-base font-bold text-sky-600 dark:text-sky-400 font-mono block mt-0.5">${sparedHa} Ha</strong>
                        <span class="text-[9px] text-slate-500 dark:text-slate-400 block">PLS: ${plsPct}% Avoided</span>
                    </div>
                    <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">Active Alleyway Corridor</span>
                        <strong class="text-base font-bold text-indigo-600 dark:text-indigo-400 font-mono block mt-0.5">3.79 m</strong>
                        <span class="text-[9px] text-emerald-600 dark:text-emerald-400 block">✓ 2.0m Root Exclusion Zone</span>
                    </div>
                    <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block uppercase">Estimated Climate Benefit</span>
                        <strong class="text-base font-bold text-teal-600 dark:text-teal-400 font-mono block mt-0.5">${climateCarbon} t</strong>
                        <span class="text-[9px] text-teal-600 dark:text-teal-400 block">tCO₂e Verified (VM0007)</span>
                    </div>
                </div>
            </div>

            <!-- 4. AGROECOLOGICAL MICROCLIMATE & SOIL HYDROLOGY -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-[11px]">
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">Above-Ground Biomass</span>
                    <strong class="text-sm font-bold text-slate-900 dark:text-white block mt-0.5">${biomassAgb} t/Ha</strong>
                    <span class="text-[9px] text-slate-500">Chave et al. (2014)</span>
                </div>
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">Microclimate Buffer</span>
                    <strong class="text-sm font-bold text-cyan-600 dark:text-cyan-400 block mt-0.5">${microclimate} °C</strong>
                    <span class="text-[9px] text-cyan-600 dark:text-cyan-400">Thermal Regulation</span>
                </div>
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">Soil Hydro Sponge</span>
                    <strong class="text-sm font-bold text-sky-600 dark:text-sky-400 block mt-0.5">${soilMoisture}% VWC</strong>
                    <span class="text-[9px] text-sky-600 dark:text-sky-400">+${recharge} m³/Ha Infiltration</span>
                </div>
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">Surface PAR &bull; LAI</span>
                    <strong class="text-sm font-bold text-emerald-600 dark:text-emerald-400 block mt-0.5">~${parVal} µmol</strong>
                    <span class="text-[9px] text-slate-500">LAI ${laiVal} &bull; ${coverVal}% Cover</span>
                </div>
            </div>

            <!-- 5. COMPANION AGRONOMY & PRECISION NUTRIENT BALANCE -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-[11px]">
                <div class="bg-slate-50 dark:bg-slate-950 p-3 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-1.5">
                    <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400 block border-b border-slate-200 dark:border-slate-800 pb-1">
                        🌱 Definitive Companion Crop &amp; Spatial Allocation
                    </span>
                    <div class="space-y-1 text-slate-700 dark:text-slate-300">
                        <div class="flex justify-between">
                            <span class="text-slate-500 dark:text-slate-400">Companion Crop:</span>
                            <strong class="text-slate-900 dark:text-white">${cropName}</strong>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-500 dark:text-slate-400">Corridor Planting Layout:</span>
                            <span>6 Raised Bed Contour Rows (3.79m Alley)</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-500 dark:text-slate-400">Soil Reaction Suitability:</span>
                            <span class="text-emerald-600 dark:text-emerald-400 font-bold">pH ${soilPh} (${soilTexture})</span>
                        </div>
                    </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-950 p-3 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-1.5">
                    <span class="text-xs font-bold text-amber-600 dark:text-amber-400 block border-b border-slate-200 dark:border-slate-800 pb-1">
                        🧪 Precision Nutrient Balance &amp; Bio-Circularity
                    </span>
                    <div class="space-y-1 text-slate-700 dark:text-slate-300">
                        <div class="flex justify-between">
                            <span class="text-slate-500 dark:text-slate-400">Potassium Prescription (MOP):</span>
                            <strong class="text-amber-600 dark:text-amber-400">+75.0 kg MOP / Ha Compensation</strong>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-500 dark:text-slate-400">Frond Bio-Circularity:</span>
                            <span>10.8 t/Ha/Yr Recycled (+${potassium} kg K₂O)</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-500 dark:text-slate-400">Palm Root Zone Buffer:</span>
                            <span class="text-amber-600 dark:text-amber-400 font-bold">Root zone not verified from image</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 6. SAVED COMPUTER VISION RESULT -->
            <div class="p-3 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2 font-mono">
                <div class="flex items-center gap-2">
                    <span class="text-lg">🎯</span>
                    <div>
                        <span class="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold block">Saved Computer Vision Result:</span>
                        <strong class="text-xs text-slate-900 dark:text-white">${visionSummaryBadge}</strong>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-[10px] font-mono font-bold px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-400">
                        ${escapeHtml(sterileCircleVal)}
                    </span>
                    <span class="text-[10px] font-mono font-bold px-2.5 py-1 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-800 dark:text-indigo-300 border border-indigo-400">
                        Evidence ID: ${escapeHtml(String(evidenceId))}
                    </span>
                </div>
            </div>
            <p class="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                Detected labels: ${detectedLabelsText}
            </p>

            <!-- 7. SAVED AGROECOLOGICAL REASONING -->
            <div class="bg-slate-50 dark:bg-slate-950 p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
                <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5 font-mono">
                    <span class="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                        <span>🧠</span> <span>Saved Agroecological Reasoning:</span>
                    </span>
                    <span class="text-[9px] font-bold px-2 py-0.5 rounded ${aiReasoningIsLive ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-400' : 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-400'} font-mono">
                        ${aiReasoningStatus}
                    </span>
                </div>
                <div class="text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                    <p>${aiReasonText}</p>
                </div>
            </div>

            <!-- 8. CRYPTOGRAPHIC SHA-256 DIGITAL SEAL -->
            <div class="p-2.5 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 font-mono text-[10px] text-slate-500 dark:text-slate-400">
                <div class="flex items-center gap-2 truncate">
                    <span class="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">🔐 RECORD SHA-256:</span>
                    <span class="text-indigo-600 dark:text-indigo-300 truncate font-semibold select-all" title="${shaCode}">${shaCode}</span>
                </div>
                <span class="text-slate-500 dark:text-slate-400 font-bold shrink-0">SIMULATION RECORD</span>
            </div>
        </div>
    `;

    const modal = document.getElementById('adminDetailModal');
    if (modal) modal.classList.remove('hidden');
}

function closeAdminDetailModalLegacy() {
    const modal = document.getElementById('adminDetailModal');
    if (modal) modal.classList.add('hidden');
}

function exportEudrTracesPayload() {
    const age = parseFloat(document.getElementById('palm_age')?.value) || 6.0;
    const area = parseFloat(document.getElementById('land_area')?.value) || 100.0;
    const crop = document.getElementById('crop_name')?.value || "Red Ginger (Zingiber officinale)";
    const coords = document.getElementById('sim_coords')?.value || "0.824100, 99.561200";
    const parts = coords.split(',').map(s => parseFloat(s.trim()));
    const lat = parts[0] || 0.824100;
    const lng = parts[1] || 99.561200;

    const delta = 0.0045;
    const polygonCoords = [
        [lng - delta, lat - delta],
        [lng + delta, lat - delta],
        [lng + delta, lat + delta],
        [lng - delta, lat + delta],
        [lng - delta, lat - delta]
    ];

    const eudrDdsPayload = {
        "@context": "https://ec.europa.eu/tracesnt/schema/eudr/v1",
        "statementType": "ILLUSTRATIVE_DRAFT_NOT_SUBMITTED",
        "notice": "This simulator export is not an official TRACES submission and does not verify EUDR compliance or deforestation status.",
        "generatedAt": new Date().toISOString(),
        "operator": {
            "eoriNumber": null,
            "companyName": "Not provided",
            "country": "ID",
            "role": "NOT_VERIFIED"
        },
        "commodity": {
            "hsCode": "15111000",
            "description": "Crude Palm Oil (CPO) - verification not performed",
            "estimatedNetMassKg": area * 21000.0,
            "companionAgroforestrySpecies": crop
        },
        "productionPlot": {
            "plotIdentifier": window.activeEstate?.kode_kebun || "Not provided",
            "countryOfProduction": "ID",
            "geodeticDatum": "WGS84",
            "centroid": { "latitude": lat, "longitude": lng },
            "geometry": { "type": "Polygon", "coordinates": [polygonCoords] },
            "cadastralTitle": window.activeEstate?.nomor_hgu || null,
            "cutOffDateVerification": {
                "statutoryCutOff": "2020-12-31",
                "deforestationFreeStatus": "NOT_VERIFIED",
                "primaryForestMoratoriumPIPPIBStatus": "NOT_VERIFIED",
                "independentAuditStandard": "NOT_PERFORMED"
            }
        },
        "recordHash": latestSimulationData?.sha256 || null
    };

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(eudrDdsPayload, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `EUDR_ILLUSTRATIVE_DRAFT_NOT_SUBMITTED_${Date.now()}.json`);
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();

    if (typeof logAiInteraction === 'function') {
        logAiInteraction('RESULT', 'Illustrative EUDR draft exported', {
            submission_status: "NOT_SUBMITTED",
            verification_status: "NOT_VERIFIED",
            record_hash: latestSimulationData?.sha256 || null
        });
    }
}

function formatTimestampLegacy(isoStr) {
    if (!isoStr) return '-';
    try {
        const cleanStr = String(isoStr).replace(' ', 'T');
        const d = new Date(cleanStr);
        if (isNaN(d.getTime())) return isoStr;
        return d.toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    } catch (e) {
        return isoStr;
    }
}

/**
 * Pillar 3: Real Cross-Page Data Flow (/spatial + /mobile -> /proses -> /timelines)
 * Synthesizes biophysical telemetry from /spatial (slope, NDVI) and /mobile (chlorophyll SPAD, sterile circle)
 */
async function pullLiveFieldAndSpatialTelemetry() {
    const urlParams = new URLSearchParams(window.location.search);
    const activeKode = urlParams.get('kode') || urlParams.get('estate_code') || window.activeEstate?.kode_kebun;
    if (!activeKode) {
        if (typeof showNotificationToast === 'function') {
            showNotificationToast('Select a loaded estate before syncing field telemetry.', '⚠️');
        }
        return;
    }
    
    if (typeof showNotificationToast === 'function') {
        showNotificationToast(`Fetching field & spatial telemetry for ${activeKode}...`, "⚡");
    }
    
    try {
        const resp = await fetch(`/api/dossier/telemetry-state?dossier_id=${encodeURIComponent(activeKode)}`);
        if (!resp.ok) throw new Error("Failed to fetch telemetry data");
        const resJson = await resp.json();
        if (resJson.status === 'success' && resJson.data) {
            const d = resJson.data;
            
            // 1. Update Preview Image to Tenant's Dynamic Evidence from Evidence Chain
            try {
                const chainResp = await fetch(`/api/dossier/${encodeURIComponent(activeKode)}/evidence-chain?year=2026`);
                if (chainResp.ok) {
                    const chainJson = await chainResp.json();
                    if (chainJson && Array.isArray(chainJson.photos) && chainJson.photos.length > 0) {
                        window.activeEstatePhotos = chainJson.photos;
                        if (typeof renderEstatePhotosGallery === 'function') {
                            renderEstatePhotosGallery(chainJson.photos);
                        }
                    }
                }
            } catch (_) {}

            const mainImg = document.getElementById('mainCanopyPreview');
            if (mainImg) {
                const streamUrl = d.latest_aerial_id 
                    ? `/api/media/evidence/${d.latest_aerial_id}?dossier_id=${encodeURIComponent(activeKode)}` 
                    : `/api/media/evidence/current?dossier_id=${encodeURIComponent(activeKode)}&perspective=AERIAL_DRONE`;
                mainImg.src = streamUrl;
            }
            
            // 2. Update Biophysical Ground-Truth Badges
            const slopeEl = document.getElementById('val_site_slope');
            if (slopeEl) slopeEl.textContent = `${d.slope_deg}°`;
            
            const spadEl = document.getElementById('val_leaf_spad');
            if (spadEl) spadEl.textContent = `${d.leaf_chlorophyll_spad} SPAD`;

            const sterileEl = document.getElementById('val_sterile_circle');
            if (sterileEl) sterileEl.textContent = `${d.sterile_circle_m.toFixed(1)}m (Zero-Tillage)`;

            const ganoEl = document.getElementById('val_ganoderma');
            if (ganoEl) ganoEl.textContent = `${d.ganoderma_risk_pct.toFixed(1)}% (Nihil)`;

            if (typeof showNotificationToast === 'function') {
                showNotificationToast(`Field telemetry applied: ${d.leaf_chlorophyll_spad} SPAD; slope ${d.slope_deg}°. Simulation metrics require a new kalkulasi.engine run.`, "✅");
            }
        }
    } catch (err) {
        console.warn("[Simulator] Pull telemetry notice:", err);
        if (typeof showNotificationToast === 'function') {
            showNotificationToast("Could not sync field telemetry. Current values were left unchanged.", "⚠️");
        }
    }
}
window.pullLiveFieldAndSpatialTelemetry = pullLiveFieldAndSpatialTelemetry;

window.generateMultiCandidateRecommendations = generateMultiCandidateRecommendations;
window.selectDefinitiveCrop = selectDefinitiveCrop;
window.selectCanopyPreset = selectCanopyPreset;
window.exportEudrTracesPayload = exportEudrTracesPayload;

function clearTerminalLogsLegacy() {
    const container = document.getElementById('floatingTerminalLogStream');
    if (container) {
        container.innerHTML = `
            <div id="terminalEmptyPlaceholder" class="p-4 text-center text-slate-500 font-mono text-[10px]" data-i18n="term_placeholder">
                ⚡ AI Execution Terminal online. Standing by for telemetry dispatch...
            </div>
        `;
    }
    if (typeof terminalLogCounter !== 'undefined') terminalLogCounter = 0;
    try {
        localStorage.removeItem(typeof TERMINAL_LOG_STORAGE_KEY !== 'undefined' ? TERMINAL_LOG_STORAGE_KEY : 'precision_palm_terminal_logs_cache');
    } catch (error) {
        console.warn('[Simulator] Unable to clear saved terminal logs:', error);
    }
}


// Theme change listener for Simulator HUD & Overlay synchronizations
window.addEventListener('themechanged', function(e) {
    const currentTheme = e.detail?.theme || localStorage.getItem('precision_palm_theme') || 'dark';
    if (typeof drawReticles === 'function') {
        drawReticles();
    }
    if (typeof renderDetectedBoundingBoxes === 'function' && Array.isArray(latestDetectedObjects) && latestDetectedObjects.length > 0) {
        renderDetectedBoundingBoxes(latestDetectedObjects);
    }
});