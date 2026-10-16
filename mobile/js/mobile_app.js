/**
 * mobile/js/mobile_app.js
 * Precision Palm Mobile - Standalone Edge Node PWA Application Controller.
 * 
 * Manages:
 * 1. PWA Service Worker bootstrap & network connectivity monitoring (Online/Offline).
 * 2. Active estate dossier state binding from SQLite backend.
 * 3. 3-tier workflow switcher: Fast Mode (Sensor), Photo AI, and Full Audit.
 * 4. GAP In-situ checklist counter & statutory compliance validation (ISPO P2 & P3).
 * 5. Reactive bilingual dictionary (EN / ID) & dark/light theme persistence.
 * 6. Non-blocking UI notification system (zero alert() compliance).
 */

let currentActiveEstateCode = "EST-MDN-001";
let activeWorkflowMode = "full"; // 'fast', 'photo', 'full'
let activeLanguage = localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en';

var MOBILE_I18N_DICT = window.MOBILE_I18N_DICT || {
    en: {
        app_title: "PRECISION PALM",
        app_subtitle: "EDGE NODE PWA",
        conn_online: "Online",
        conn_offline: "Offline (Buffer)",
        hero_tag: "SELECT REGISTERED ESTATE",
        lbl_select_estate: "Registered Estate Dossiers (Stage 1 Application):",
        lbl_hgu: "Land Title (HGU/e-STDB):",
        lbl_area_crop: "Area • Intercrop:",
        wf_all: "All Sections",
        wf_camera: "AI Camera",
        wf_sensor: "Sensors & GPS",
        cam_section_title: "IN-SITU CAMERA & AI RETICLE",
        cam_section_sub: "Canopy, 3.79m alley & 2.0m root circle detection",
        badge_verified: "4 Objects Verified",
        badge_scanning: "AI Scanning...",
        btn_open_camera: "Open Phone Camera",
        btn_open_gallery: "Choose from Gallery",
        btn_scan_ai: "Scan AI",
        hud_palm: "[Palm Stand]",
        hud_alley: "[3.79m Alley]",
        hud_buffer: "[2.0m Circle]",
        telemetry_title: "WGS84 GPS TELEMETRY & SATELLITE WEATHER",
        btn_refresh_gps: "Refresh GPS",
        lbl_lat: "LATITUDE (N)",
        lbl_lng: "LONGITUDE (E)",
        lbl_elev: "ELEVATION (MSL)",
        lbl_weather: "WEATHER CONDITION",
        lbl_block: "Alley Block ID:",
        lbl_mandor: "Foreman Name:",
        gap_title: "FOREMAN GAP CHECKLIST (ISPO P2 & P3)",
        gap_verified_suffix: "Verified",
        gap_item_1_title: "2.0m Sterile Feeder Root Buffer (Zero-Tillage)",
        gap_item_1_desc: "Strict zero-tillage within 2.0m radius from palm base to safeguard superficial roots.",
        gap_item_2_title: "3.79m Clean Alley Corridor",
        gap_item_2_desc: "Intercrop beds aligned strictly in active alley without encroaching palm root circles.",
        gap_item_3_title: "Chopped Frond Mulch & Silt Pits",
        gap_item_3_desc: "Pruned fronds stacked in dead alleys to suppress erosion runoff and cycle potassium.",
        gap_item_4_title: "Riparian Stream Buffer Protected (>50m)",
        gap_item_4_desc: "Natural waterways strictly free from chemical runoff and mechanical tillage.",
        btn_save_idb: "Save to Local Buffer (IndexedDB)",
        btn_sync_sqlite: "Submit & Sync to Central SQLite",
        lbl_queue: "Offline Queue Status:",
        queue_count_tpl: "Records Stored Locally",
        footer_title: "Precision Palm Mobile • Standalone Edge Node PWA",
        footer_sub: "IndexedDB Local Engine • Bi-Directional SQLite Synchronization",
        toast_photo_loaded: "Photo loaded from camera successfully!",
        toast_scan_ai: "Laser AI Vision analyzing field evidence...",
        toast_gps_locked: "GPS Locked: ",
        toast_saved_idb: "Survey saved to phone's IndexedDB buffer!",
        sync_in_progress: "Submitting to Central SQLite...",
        toast_sync_success: "Synchronization complete! Committed to SQLite.",
        toast_sync_direct: "Active survey dispatched directly to central SQLite!",
        toast_offline_notice: "Offline. Data safely queued in phone's IndexedDB.",
        box_palm: "Productive Palm Stand",
        box_alley: "3.79m Alley Corridor",
        box_buffer: "2.0m Zero-Tillage Circle",
        box_mulch: "Chopped Frond Mulch"
    },
    id: {
        app_title: "PRECISION PALM",
        app_subtitle: "NODE MANDOR PWA",
        conn_online: "Online",
        conn_offline: "Offline (Buffer)",
        hero_tag: "PILIH PERUSAHAAN / BERKAS KEBUN",
        lbl_select_estate: "Daftar Kebun Terdaftar (Tahap 1 Permohonan):",
        lbl_hgu: "Nomor HGU / e-STDB:",
        lbl_area_crop: "Luas • Komoditas Sela:",
        wf_all: "Semua Fitur",
        wf_camera: "Kamera AI",
        wf_sensor: "Sensor & GPS",
        cam_section_title: "KAMERA IN-SITU & RETIKEL AI",
        cam_section_sub: "Deteksi tajuk, lorong 3.79m & piringan 2.0m",
        badge_verified: "4 Objek Terverifikasi",
        badge_scanning: "AI Memindai...",
        btn_open_camera: "Buka Kamera HP",
        btn_open_gallery: "Pilih dari Galeri",
        btn_scan_ai: "Scan AI",
        hud_palm: "[Pokok Sawit]",
        hud_alley: "[Lorong 3.79m]",
        hud_buffer: "[Piringan 2.0m]",
        telemetry_title: "TELEMETRI GPS WGS84 & CUACA SATELIT",
        btn_refresh_gps: "Perbarui GPS",
        lbl_lat: "LATITUDE (N)",
        lbl_lng: "LONGITUDE (E)",
        lbl_elev: "ELEVASI (DPL)",
        lbl_weather: "KONDISI CUACA",
        lbl_block: "Blok Gawangan:",
        lbl_mandor: "Nama Mandor:",
        gap_title: "CHECKLIST GAP MANDOR (ISPO P2 & P3)",
        gap_verified_suffix: "Terverifikasi",
        gap_item_1_title: "Piringan 2.0m Steril (Zero-Tillage)",
        gap_item_1_desc: "Radius 2.0m bebas mutlak dari olah tanah cangkul dan tanaman sela.",
        gap_item_2_title: "Koridor Lorong Bersih 3.79m",
        gap_item_2_desc: "Bedengan sela tertata rapi di tengah gawangan aktif tanpa mengokupasi piringan.",
        gap_item_3_title: "Mulsa Pelepah Cincang & Rorak Sedimen",
        gap_item_3_desc: "Pelepah pangkasan disusun di gawangan mati menahan limpasan erosi.",
        gap_item_4_title: "Sempadan Air Alami Terjaga (>50m)",
        gap_item_4_desc: "Bebas dari limbah kimia dan pengolahan tanah di sempadan air HCV.",
        btn_save_idb: "Simpan ke Buffer Offline (IndexedDB)",
        btn_sync_sqlite: "Kirim & Sinkronkan ke SQLite Pusat",
        lbl_queue: "Status Antrean Offline:",
        queue_count_tpl: "Laporan Tersimpan Lokal",
        footer_title: "Precision Palm Mobile • Node Lapangan Mandor Mandiri PWA",
        footer_sub: "IndexedDB Local Engine • Bi-Directional SQLite Synchronization",
        toast_photo_loaded: "Foto berhasil dimuat dari kamera HP!",
        toast_scan_ai: "Laser AI Vision memindai foto lapangan...",
        toast_gps_locked: "GPS Terkunci: ",
        toast_saved_idb: "Laporan tersimpan di IndexedDB HP!",
        sync_in_progress: "Mengirim ke SQLite Pusat...",
        toast_sync_success: "Sukses sinkron laporan ke SQLite pusat!",
        toast_sync_direct: "Laporan aktif langsung terkirim ke SQLite pusat!",
        toast_offline_notice: "Offline. Data aman di IndexedDB ponsel mandor.",
        box_palm: "Pokok Sawit Produktif",
        box_alley: "Lorong Sela 3.79m",
        box_buffer: "Piringan 2.0m Zero-Tillage",
        box_mulch: "Mulsa Pelepah Cincang"
    }
};

document.addEventListener('DOMContentLoaded', async function () {
    initServiceWorker();
    initNetworkMonitor();
    initThemePreference();
    setAppLanguage(activeLanguage);

    if (window.MobileDB && typeof window.MobileDB.init === 'function') {
        await window.MobileDB.init();
        await window.MobileDB.loadEstatesFromBackend();
        window.MobileDB.updateQueueCounter();
    }

    if (window.MobileGPS && typeof window.MobileGPS.acquireLocation === 'function') {
        window.MobileGPS.acquireLocation();
        window.MobileGPS.initOrientationSensor();
    }

    if (window.MobileCamera && typeof window.MobileCamera.init === 'function') {
        window.MobileCamera.init();
    }

    updateGapChecklistCounter();
});

function initServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/mobile/sw.js', { scope: '/mobile/' })
            .then(reg => console.log('[PWA] Service Worker active with scope:', reg.scope))
            .catch(err => console.warn('[PWA] Service Worker registration note:', err));
    }
}

function initNetworkMonitor() {
    window.addEventListener('online', updateConnectionUI);
    window.addEventListener('offline', updateConnectionUI);
    updateConnectionUI();
}

function updateConnectionUI() {
    const isOnline = navigator.onLine;
    const badge = document.getElementById('connStatusBadge');
    const dot = document.getElementById('connDot');
    const text = document.getElementById('connText');
    const dict = MOBILE_I18N_DICT[activeLanguage] || MOBILE_I18N_DICT.en;

    if (!badge || !dot || !text) return;

    if (isOnline) {
        badge.className = "flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-400";
        dot.className = "w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse";
        text.textContent = dict.conn_online;
    } else {
        badge.className = "flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border border-rose-400";
        dot.className = "w-1.5 h-1.5 rounded-full bg-rose-500";
        text.textContent = dict.conn_offline;
    }
}

function initThemePreference() {
    const savedTheme = localStorage.getItem('precision_palm_theme') || 'dark';
    applyThemeMode(savedTheme);
}

function applyThemeMode(theme) {
    const icon = document.getElementById('themeIcon');
    if (theme === 'light') {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('precision_palm_theme', 'light');
        if (icon) icon.textContent = '☀️';
    } else {
        document.documentElement.classList.add('dark');
        localStorage.setItem('precision_palm_theme', 'dark');
        if (icon) icon.textContent = '🌙';
    }
}

function toggleTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    applyThemeMode(isDark ? 'light' : 'dark');
}

function setAppLanguage(lang) {
    activeLanguage = (lang === 'en' || lang === 'id') ? lang : 'en';
    localStorage.setItem('precision_palm_mobile_lang', activeLanguage);
    localStorage.setItem('precision_palm_lang', activeLanguage);

    const btnEN = document.getElementById('btnLangEN');
    const btnID = document.getElementById('btnLangID');
    const activeCls = "px-2 py-1 rounded-lg transition-all bg-emerald-600 text-white font-bold text-[10px] shadow-xs cursor-pointer";
    const inactiveCls = "px-2 py-1 rounded-lg transition-all text-slate-500 hover:text-white font-bold text-[10px] cursor-pointer";

    if (btnEN && btnID) {
        btnEN.className = (activeLanguage === 'en') ? activeCls : inactiveCls;
        btnID.className = (activeLanguage === 'id') ? activeCls : inactiveCls;
    }

    const dict = MOBILE_I18N_DICT[activeLanguage] || MOBILE_I18N_DICT.en;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict && dict[key]) {
            el.innerHTML = dict[key];
        }
    });

    updateConnectionUI();
    updateGapChecklistCounter();
}

function setWorkflowMode(mode) {
    activeWorkflowMode = mode;
    const secCam = document.getElementById('secMobileCamera');
    const secTel = document.getElementById('secMobileTelemetry');
    const secGap = document.getElementById('secMobileGapChecklist');

    if (mode === 'fast') {
        if (secCam) secCam.classList.add('hidden');
        if (secTel) secTel.classList.remove('hidden');
        if (secGap) secGap.classList.remove('hidden');
    } else if (mode === 'photo') {
        if (secCam) secCam.classList.remove('hidden');
        if (secTel) secTel.classList.add('hidden');
        if (secGap) secGap.classList.add('hidden');
    } else {
        if (secCam) secCam.classList.remove('hidden');
        if (secTel) secTel.classList.remove('hidden');
        if (secGap) secGap.classList.remove('hidden');
    }
}

function updateGapChecklistCounter() {
    let checkedCount = 0;
    const items = ['chkGapBuffer2m', 'chkGapAlley379', 'chkGapMulch', 'chkGapRiparian'];

    items.forEach(id => {
        const el = document.getElementById(id);
        if (el && el.checked) checkedCount++;
    });

    const badge = document.getElementById('gapCounterLabel');
    if (!badge) return;

    badge.textContent = `${checkedCount}/${items.length} ${activeLanguage === 'en' ? 'Verified' : 'Terverifikasi'}`;
    if (checkedCount === items.length) {
        badge.className = "text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-400";
    } else {
        badge.className = "text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-400";
    }
}

function showToast(message, icon = "ℹ️") {
    let toast = document.getElementById('mobileToastAlert');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'mobileToastAlert';
        toast.className = 'fixed bottom-14 left-1/2 -translate-x-1/2 z-50 max-w-xs w-full px-4 py-2.5 bg-slate-950/95 border border-slate-700 text-white rounded-2xl shadow-2xl flex items-center gap-2 text-xs font-mono transition-all duration-300 opacity-0 translate-y-4 pointer-events-none';
        document.body.appendChild(toast);
    }

    toast.innerHTML = `<span class="text-base">${icon}</span> <span class="leading-tight">${message}</span>`;
    toast.classList.remove('opacity-0', 'translate-y-4');
    toast.classList.add('opacity-100', 'translate-y-0');

    setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', 'translate-y-4');
    }, 3200);
}

window.toggleTheme = toggleTheme;
window.setAppLanguage = setAppLanguage;
window.setWorkflowMode = setWorkflowMode;
window.updateGapChecklistCounter = updateGapChecklistCounter;
window.showToast = showToast;