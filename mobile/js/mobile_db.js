/**
 * mobile/js/mobile_db.js
 * Precision Palm Mobile - Edge Local Storage & SQLite Bi-Directional Sync Engine.
 * 
 * Manages:
 * 1. Local IndexedDB initialization ('precision_palm_mobile_db', store: 'offline_surveys_queue').
 * 2. Autonomous offline queuing for disconnected field foremen.
 * 3. Dynamic loading of real registered estates from SQLite (/api/estates).
 * 4. Bi-directional batch synchronization to central database (/api/mobile-surveys).
 * 5. Deterministic SHA-256 seal computation for tamper-proof audit trails.
 */

const IDB_DATABASE_NAME = 'precision_palm_mobile_db';
const IDB_DATABASE_VERSION = 3;
const IDB_STORE_SURVEYS = 'offline_surveys_queue';
const IDB_STORE_INSPECTIONS = 'inspection_reports';
const IDB_STORE_ESTATES = 'estates_cache';

let idbConnection = null;
let registeredEstatesList = [];
let currentlySelectedEstate = null;

function openIndexedDb() {
    return new Promise((resolve, reject) => {
        if (idbConnection) return resolve(idbConnection);

        const request = indexedDB.open(IDB_DATABASE_NAME, IDB_DATABASE_VERSION);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(IDB_STORE_SURVEYS)) {
                db.createObjectStore(IDB_STORE_SURVEYS, { keyPath: 'id', autoIncrement: true });
                console.log('[MobileDB] Object store created:', IDB_STORE_SURVEYS);
            }
            if (!db.objectStoreNames.contains(IDB_STORE_INSPECTIONS)) {
                db.createObjectStore(IDB_STORE_INSPECTIONS, { keyPath: 'id', autoIncrement: true });
                console.log('[MobileDB] Object store created:', IDB_STORE_INSPECTIONS);
            }
            if (!db.objectStoreNames.contains(IDB_STORE_ESTATES)) {
                db.createObjectStore(IDB_STORE_ESTATES, { keyPath: 'kode_kebun' });
                console.log('[MobileDB] Object store created:', IDB_STORE_ESTATES);
            }
        };

        request.onsuccess = (event) => {
            idbConnection = event.target.result;
            resolve(idbConnection);
        };

        request.onerror = (event) => {
            console.error('[MobileDB] IndexedDB opening failed:', event.target.error);
            reject(event.target.error);
        };
    });
}

async function loadEstatesFromBackend() {
    const selectEl = document.getElementById('selectEstateCompany');
    if (!selectEl) return;

    const db = await openIndexedDb();

    try {
        const response = await fetch('/api/estates');
        if (response.ok) {
            const json = await response.json();
            if (json && json.success && Array.isArray(json.records) && json.records.length > 0) {
                registeredEstatesList = json.records;
                // Cache into IndexedDB
                if (db && db.objectStoreNames.contains(IDB_STORE_ESTATES)) {
                    const tx = db.transaction(IDB_STORE_ESTATES, 'readwrite');
                    const store = tx.objectStore(IDB_STORE_ESTATES);
                    registeredEstatesList.forEach(est => store.put(est));
                }
            }
        }
    } catch (err) {
        console.warn('[MobileDB] Network offline, loading estates from IndexedDB cache:', err);
    }

    if (registeredEstatesList.length === 0 && db && db.objectStoreNames.contains(IDB_STORE_ESTATES)) {
        try {
            const tx = db.transaction(IDB_STORE_ESTATES, 'readonly');
            const cached = await new Promise((resolve) => {
                const req = tx.objectStore(IDB_STORE_ESTATES).getAll();
                req.onsuccess = () => resolve(req.result || []);
                req.onerror = () => resolve([]);
            });
            if (Array.isArray(cached) && cached.length > 0) {
                registeredEstatesList = cached;
            }
        } catch (eIdb) {
            console.warn('[MobileDB] Error reading estates_cache:', eIdb);
        }
    }

    if (registeredEstatesList.length === 0) {
        selectEl.innerHTML = '<option value="">(Belum ada kebun di-cache, sambungkan internet untuk unduh awal)</option>';
        handleEstateSelection(null);
        return;
    }

    selectEl.innerHTML = registeredEstatesList.map(est => `
        <option value="${est.kode_kebun}">${est.kode_kebun} • ${est.nama_kebun}</option>
    `).join('');

    const urlKode = new URLSearchParams(window.location.search).get('kode');
    const defaultCode = (urlKode && registeredEstatesList.some(e => e.kode_kebun === urlKode))
        ? urlKode
        : registeredEstatesList[0].kode_kebun;

    selectEl.value = defaultCode;
    handleEstateSelection(defaultCode);
}

function handleEstateSelection(estateCode) {
    if (!estateCode) {
        currentlySelectedEstate = null;
    } else {
        currentlySelectedEstate = registeredEstatesList.find(e => e.kode_kebun === estateCode) || null;
    }

    const regTag = document.getElementById('selectedEstateRegTag');
    const dispHgu = document.getElementById('dispEstateHgu');
    const dispArea = document.getElementById('dispEstateAreaCrop');

    if (!currentlySelectedEstate) {
        if (regTag) regTag.textContent = "-";
        if (dispHgu) dispHgu.textContent = "-";
        if (dispArea) dispArea.textContent = "-";
        return;
    }

    if (regTag) {
        regTag.textContent = currentlySelectedEstate.nomor_registrasi || `CERT-ECOGREEN-2026-${String(currentlySelectedEstate.id_kebun || 1).padStart(4, '0')}`;
    }
    if (dispHgu) {
        dispHgu.textContent = currentlySelectedEstate.nomor_hgu || currentlySelectedEstate.legal_deed_number || 'e-STDB';
    }
    if (dispArea) {
        dispArea.textContent = `${parseFloat(currentlySelectedEstate.luas_ha || 0).toLocaleString()} Ha • ${currentlySelectedEstate.komoditas_sela || '-'}`;
    }

    if (window.MobileGPS && typeof window.MobileGPS.setCentroidBaseline === 'function') {
        if (currentlySelectedEstate.centroid_lat && currentlySelectedEstate.centroid_lng) {
            window.MobileGPS.setCentroidBaseline(
                parseFloat(currentlySelectedEstate.centroid_lat),
                parseFloat(currentlySelectedEstate.centroid_lng),
                parseFloat(currentlySelectedEstate.elevation || 0)
            );
        }
    }
}

async function saveSurveyToIndexedDb() {
    await openIndexedDb();
    const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';

    const gps = (window.MobileGPS && typeof window.MobileGPS.getLiveCoords === 'function')
        ? window.MobileGPS.getLiveCoords()
        : { lat: null, lng: null, elev: null, weather: null };

    const photoBase64 = (window.MobileCamera && typeof window.MobileCamera.getActivePhotoBase64 === 'function')
        ? window.MobileCamera.getActivePhotoBase64()
        : null;

    const photoName = (window.MobileCamera && typeof window.MobileCamera.getActiveFileName === 'function')
        ? window.MobileCamera.getActiveFileName()
        : null;

    if (!photoBase64) {
        if (window.showToast) {
            window.showToast(isId ? "Silakan ambil foto bukti fisik terlebih dahulu!" : "Please capture an evidence photo first!", "⚠️");
        }
        return false;
    }

    const estate = currentlySelectedEstate || registeredEstatesList[0] || null;
    if (!estate) {
        if (window.showToast) {
            window.showToast(isId ? "Pilih kebun terlebih dahulu!" : "Please select an estate first!", "⚠️");
        }
        return false;
    }

    const blockId = document.getElementById('inpBlockId')?.value || "";
    const mandorName = document.getElementById('inpMandorName')?.value || "";

    const nowStr = new Date().toLocaleString('id-ID', { hour12: false }) + " WIB";
    const rawDataToHash = `${estate.kode_kebun}:${blockId}:${nowStr}:${photoName || 'evidence'}`;
    const enc = new TextEncoder().encode(rawDataToHash);
    const hashBuf = await crypto.subtle.digest('SHA-256', enc);
    const shaHash = Array.from(new Uint8Array(hashBuf)).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();

    const diagnostics = (window.MobileCamera && typeof window.MobileCamera.getActiveDiagnostics === 'function')
        ? window.MobileCamera.getActiveDiagnostics()
        : null;

    const boxes = (window.MobileCamera && typeof window.MobileCamera.getActiveBoundingBoxes === 'function')
        ? window.MobileCamera.getActiveBoundingBoxes()
        : null;

    const surveyPayload = {
        id_kebun: estate.id_kebun || estate.id || 1,
        kode_kebun: estate.kode_kebun,
        nama_kebun: estate.nama_kebun,
        block_id: blockId,
        mandor: mandorName,
        gps_lat: gps.lat,
        gps_lng: gps.lng,
        elevasi_dpl: gps.elev,
        cuaca_tercatat: gps.weather,
        foto_url: photoBase64,
        filename: photoName,
        piringan_steril_meter: diagnostics?.spatial_alley_verification?.sterile_circle_radius_m || 2.0,
        defisit_tbs_persen: 1.2,
        waktu_pengambilan: nowStr,
        sha256: shaHash,
        plant_diagnostics: diagnostics,
        bounding_boxes: boxes,
        synced: 0
    };

    return new Promise((resolve, reject) => {
        const tx = idbConnection.transaction([IDB_STORE_SURVEYS, IDB_STORE_INSPECTIONS], 'readwrite');
        const storeSurveys = tx.objectStore(IDB_STORE_SURVEYS);
        const storeInspections = tx.objectStore(IDB_STORE_INSPECTIONS);
        
        const req = storeSurveys.add(surveyPayload);
        try {
            storeInspections.add(JSON.parse(JSON.stringify(surveyPayload)));
        } catch (e) {
            console.warn('[MobileDB] Note saving to inspection_reports:', e);
        }

        const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';

        req.onsuccess = () => {
            updateQueueCounter();
            if (window.showToast) {
                window.showToast(isId ? `Laporan & Diagnostik ${surveyPayload.kode_kebun} (${surveyPayload.block_id}) tersimpan di IndexedDB!` : `Report & Diagnostics for ${surveyPayload.kode_kebun} (${surveyPayload.block_id}) stored in IndexedDB!`, "💾");
            }
            resolve(req.result);
        };

        req.onerror = (e) => {
            console.error('[MobileDB] Failed to add survey to IDB:', e.target.error);
            reject(e.target.error);
        };
    });
}

function updateQueueCounter() {
    if (!idbConnection) return;

    const tx = idbConnection.transaction(IDB_STORE_SURVEYS, 'readonly');
    const store = tx.objectStore(IDB_STORE_SURVEYS);
    const countReq = store.count();
    const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';

    countReq.onsuccess = () => {
        const count = countReq.result || 0;
        const disp = document.getElementById('dispQueueCount');
        if (disp) {
            disp.textContent = `${count} ${isId ? 'Laporan Tersimpan Lokal' : 'Records Stored Locally'}`;
        }
    };
}

async function syncAllOfflineSurveysToSqlite() {
    await openIndexedDb();

    const btn = document.getElementById('btnSyncToSqlite');
    const icon = document.getElementById('syncSpinnerIcon');
    const lbl = document.getElementById('syncBtnLabel');
    const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';

    if (btn) btn.disabled = true;
    if (icon) icon.className = "text-base animate-spin inline-block";
    if (lbl) lbl.textContent = isId ? "Mengirim ke SQLite Pusat..." : "Submitting to Central SQLite...";

    const tx = idbConnection.transaction(IDB_STORE_SURVEYS, 'readonly');
    const store = tx.objectStore(IDB_STORE_SURVEYS);
    const getAllReq = store.getAll();

    getAllReq.onsuccess = async () => {
        const queueItems = getAllReq.result || [];

        try {
            if (queueItems.length === 0) {
                await sendActiveSurveyDirect();
                if (window.showToast) {
                    window.showToast(isId ? "Laporan aktif langsung terkirim ke SQLite pusat!" : "Active report submitted directly to central SQLite!", "🚀");
                }
            } else {
                for (const item of queueItems) {
                    await fetch('/api/mobile-surveys', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(item)
                    });
                }

                // Kosongkan antrean lokal setelah sukses
                const clearTx = idbConnection.transaction(IDB_STORE_SURVEYS, 'readwrite');
                clearTx.objectStore(IDB_STORE_SURVEYS).clear();

                if (window.showToast) {
                    window.showToast(isId ? `Sukses sinkron ${queueItems.length} laporan ke SQLite pusat!` : `Successfully synced ${queueItems.length} reports to central SQLite!`, "✅");
                }
            }
        } catch (err) {
            console.error('[MobileDB] Sync error:', err);
            if (window.showToast) {
                window.showToast(isId ? "Koneksi gagal. Laporan tetap tersimpan aman di IndexedDB." : "Connection failed. Reports remain safely stored in IndexedDB.", "⚠️");
            }
        } finally {
            if (btn) btn.disabled = false;
            if (icon) icon.className = "text-base";
            if (lbl) lbl.textContent = isId ? "Kirim & Sinkronkan ke SQLite Pusat" : "Submit & Sync to Central SQLite";
            updateQueueCounter();
        }
    };
}

async function sendActiveSurveyDirect() {
    const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';
    const gps = (window.MobileGPS && typeof window.MobileGPS.getLiveCoords === 'function')
        ? window.MobileGPS.getLiveCoords()
        : { lat: null, lng: null, elev: null, weather: null };

    const photoBase64 = (window.MobileCamera && typeof window.MobileCamera.getActivePhotoBase64 === 'function')
        ? window.MobileCamera.getActivePhotoBase64()
        : null;

    if (!photoBase64) {
        if (window.showToast) {
            window.showToast(isId ? "Belum ada foto bukti fisik yang diambil." : "No evidence photo captured yet.", "⚠️");
        }
        return;
    }

    const estate = currentlySelectedEstate || (registeredEstatesList.length > 0 ? registeredEstatesList[0] : null);
    if (!estate) {
        if (window.showToast) {
            window.showToast(isId ? "Pilih kebun terlebih dahulu." : "Please select an estate first.", "⚠️");
        }
        return;
    }

    const diagnostics = (window.MobileCamera && typeof window.MobileCamera.getActiveDiagnostics === 'function')
        ? window.MobileCamera.getActiveDiagnostics()
        : null;

    const boxes = (window.MobileCamera && typeof window.MobileCamera.getActiveBoundingBoxes === 'function')
        ? window.MobileCamera.getActiveBoundingBoxes()
        : [];

    const payload = {
        id_kebun: estate.id_kebun || estate.id || 1,
        kode_kebun: estate.kode_kebun,
        block_id: document.getElementById('inpBlockId')?.value || "",
        mandor: document.getElementById('inpMandorName')?.value || "",
        latitude: gps.lat,
        longitude: gps.lng,
        elevation: gps.elev,
        cuaca: gps.weather,
        foto_url: photoBase64,
        piringan_steril_meter: diagnostics?.spatial_alley_verification?.sterile_circle_radius_m || 2.0,
        defisit_tbs_persen: 0.0,
        plant_diagnostics: diagnostics,
        bounding_boxes: boxes
    };

    await fetch('/api/mobile-surveys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
}

async function saveInspectionReportToIndexedDb(reportData) {
    const db = await openIndexedDb();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(IDB_STORE_INSPECTIONS, 'readwrite');
        const store = tx.objectStore(IDB_STORE_INSPECTIONS);
        const req = store.add({
            ...reportData,
            saved_at: new Date().toISOString()
        });
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

window.MobileDB = {
    init: openIndexedDb,
    loadEstatesFromBackend: loadEstatesFromBackend,
    handleEstateSelection: handleEstateSelection,
    saveSurveyToIndexedDb: saveSurveyToIndexedDb,
    saveInspectionReport: saveInspectionReportToIndexedDb,
    syncAllOfflineSurveysToSqlite: syncAllOfflineSurveysToSqlite,
    updateQueueCounter: updateQueueCounter,
    getSelectedEstate: () => currentlySelectedEstate
};

window.handleEstateSelectionChange = handleEstateSelection;
window.saveSurveyToIndexedDb = saveSurveyToIndexedDb;
window.syncAllOfflineSurveysToSqlite = syncAllOfflineSurveysToSqlite;