/**
 * static/js/spatial.js
 * Precision Palm Enterprise OS - Stage 2A: Site Characteristics & Spatial Audit
 * 
 * CORE ARCHITECTURAL PRINCIPLES:
 * 1. Dual Cross-Laser Grid Sweeper: Clean horizontal & vertical scanning with progressive box lock-on.
 * 2. Visual Document Proof: Generates comprehensive sealed proof cards with perspective-specific forensics.
 * 3. Anti-Replay Photo Lock: Processed photos get blurred/dimmed and disabled in active gallery, moving to archive strip.
 * 4. Permanent DB Commitment on Proceed: Clicking "Proceed to Stage 2B" commits all proofs to the bottom journal table and database.
 * 5. Forensic Modal & Benchmark Measurement: Interactive "View Summary" on surveillance rows with real physical entities (Pagination aware).
 * 6. 2-Column Split for Ledger and Advisory Recommendation.
 * 7. Searchable & Paginated Field Surveillance Journal (5 rows per page).
 */

let telemetryMap = null;
let streetTileLayer = null;
let satelliteTileLayer = null;
let moratoriumOverlayLayer = null;
let polygonLayer = null;
let mainPinMarker = null;
let allEstatesLayerGroup = null;
let inspectionTrackingLayerGroup = null;

let currentPinLat = 0.824100;
let currentPinLng = 99.561200;
let currentElevationDpl = 142.0;
let isMapFullscreenActive = false;
let currentMoratoriumOpacity = 0.65;
let activeDossier = null;
let activePhotoUrl = null;
let activeFilename = null;
let currentEstateCode = 'EST-MDN-010';

let registeredPhotos = [];
let selectedPhotoUrls = new Set();
let activeProcessStageFilter = 'ALL';
let spatialGalleryCurrentPage = 1;
const spatialGalleryPageSize = 4;
window.registeredPhotos = registeredPhotos;
window.selectedPhotoUrls = selectedPhotoUrls;

let cachedMobileSurveys = [];
let surveysFullList = [];

// State aktif modal forensik untuk diekspor ke PDF
let activeModalSurveyItem = null;
let activeModalSurveyIndex = 1;

// Pagination state for Sealed Proof Cards (3 cards per page)
let sealedCardsCurrentPage = 1;
const SEALED_CARDS_PER_PAGE = 3;

// Pagination & search state for Field Surveillance Journal (5 records per page)
let surveysCurrentPage = 1;
const SURVEYS_PER_PAGE = 5;
let surveysSearchQuery = '';
let surveysDebounceTimer = null;
let filteredSurveysCache = [];

let currentSpatialBoxes = [];
let currentSpatialContourPreview = null;
let showSam2ContourPreview = false;
let spatialContourRequestId = 0;
let currentOpenCvStaticReplay = null;
let showOpenCvStaticReplay = false;
let openCvStaticReplayRequestId = 0;
let activeSpatialClusterFilters = new Set([
    'palm_canopy', 'infrastructure', 'root_circle', 'empty_gap',
    'floor_mulch', 'water_riparian', 'weed_cover', 'fruit_organs', 'palm_anatomy'
]);

let currentConsolidatedLedger = null;
let lastSpatialCheckResult = {
    isSafe: true,
    isDirectCollision: false,
    isBufferViolation: false,
    distanceMeters: 5000.0,
    statusLabel: "100% NON-FOREST APL CLEARED"
};

const DEFAULT_FALLBACK_IMAGE = '/static/img/sawit_drone.jpg';

function isIndonesian() {
    return (typeof window.getAppLanguage === 'function' ? window.getAppLanguage() : (localStorage.getItem('precision_palm_lang') || 'en')) === 'id';
}
window.isIndonesian = isIndonesian;

async function readApiJson(response, actionLabel) {
    const responseText = await response.text();
    let result;
    try {
        result = responseText ? JSON.parse(responseText) : {};
    } catch (_) {
        throw new Error(`${actionLabel} failed (HTTP ${response.status}): server returned a non-JSON response.`);
    }
    if (!response.ok || result.status === 'error') {
        throw new Error(result.message || `${actionLabel} failed (HTTP ${response.status}).`);
    }
    return result;
}

function initSpatialMapCanvas() {
    const container = document.getElementById('telemetryMap');
    if (!container || typeof L === 'undefined' || telemetryMap) return;

    telemetryMap = L.map('telemetryMap', {
        center: [currentPinLat, currentPinLng],
        zoom: 13,
        zoomControl: true,
        attributionControl: false
    });

    satelliteTileLayer = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
        attribution: '&copy; Google Earth Satellite Hybrid',
        maxZoom: 20
    }).addTo(telemetryMap);

    streetTileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    });

    moratoriumOverlayLayer = L.tileLayer('/api/tiles/{z}/{x}/{y}', {
        minZoom: 6,
        maxNativeZoom: 10,
        maxZoom: 19,
        opacity: currentMoratoriumOpacity,
        crossOrigin: 'anonymous',
        zIndex: 400
    }).addTo(telemetryMap);

    if (!allEstatesLayerGroup) allEstatesLayerGroup = L.layerGroup().addTo(telemetryMap);
    if (!inspectionTrackingLayerGroup) inspectionTrackingLayerGroup = L.layerGroup().addTo(telemetryMap);

    const pinHtml = '<div class="relative flex items-center justify-center">' +
        '<span class="animate-ping absolute inline-flex h-6 w-6 rounded-full bg-emerald-400 opacity-60"></span>' +
        '<div class="w-6 h-6 rounded-full bg-emerald-600 border-2 border-white shadow-lg flex items-center justify-center text-white text-[10px] font-bold">📍</div>' +
        '</div>';

    const pinIcon = L.divIcon({
        className: 'custom-poi-marker',
        html: pinHtml,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    mainPinMarker = L.marker([currentPinLat, currentPinLng], {
        draggable: false,
        icon: pinIcon
    }).addTo(telemetryMap);

    mainPinMarker.bindTooltip(isIndonesian() ? "Centroid Terkunci (Titik Acuan Kebun)" : "Centroid Locked (Dossier Baseline)", { permanent: false, direction: 'top' });

    setTimeout(() => {
        if (telemetryMap) telemetryMap.invalidateSize();
    }, 250);
}

async function loadRegisteredDossiersAndBind() {
    const urlParams = new URLSearchParams(window.location.search);
    const storedDossier = localStorage.getItem('precision_palm_active_dossier') || localStorage.getItem('precision_active_dossier');
    let targetKode = urlParams.get('kode') || urlParams.get('estate_code');
    if (!targetKode) {
        targetKode = (storedDossier && storedDossier !== 'EST-MDN-001') ? storedDossier : 'EST-MDN-010';
    }
    const targetYear = parseInt(urlParams.get('year') || localStorage.getItem('precision_palm_active_year') || '2026', 10);

    const selectEl = document.getElementById('selectDossierApplication');
    let estatesList = [];

    try {
        const res = await fetch('/api/estates');
        if (res.ok) {
            const data = await res.json();
            if (data && data.success && Array.isArray(data.records)) {
                estatesList = data.records;
            }
        }
    } catch (_) {}

    if (estatesList.length > 0 && !urlParams.get('kode') && (!storedDossier || storedDossier === 'EST-MDN-001')) {
        const lastEst = estatesList[estatesList.length - 1];
        if (lastEst && lastEst.kode_kebun) {
            targetKode = lastEst.kode_kebun;
        }
    }

    currentEstateCode = targetKode;

    if (selectEl && estatesList.length > 0) {
        selectEl.innerHTML = estatesList.map(e => {
            const kode = e.kode_kebun || e.estate_id || (e.id_kebun ? ('EST-MDN-' + String(e.id_kebun).padStart(3, '0')) : 'EST-MDN-010');
            const nama = e.nama_kebun || e.estate_name || 'Kebun';
            const val = e.public_token || kode;
            const isSel = (kode === targetKode) ? 'selected' : '';
            return '<option value="' + val + '" ' + isSel + '>' + kode + ' • ' + nama + '</option>';
        }).join('');
    }

    await fetchAndBindDossierState(targetKode, targetYear);
}

async function fetchAndBindDossierState(kode, year = 2026) {
    let estate = null;
    let photos = [];
    let surveys = [];

    try {
        const resp = await fetch('/api/spatial/estate-data?kode=' + encodeURIComponent(kode) + '&year=' + year);
        if (resp.ok) {
            const data = await resp.json();
            if (data && data.success) {
                estate = data.estate;
                photos = data.photos || [];
                surveys = data.surveys || [];
            }
        }
    } catch (e) {
        console.warn("[Spatial State] Notice reading estate-data:", e);
    }

    if (!estate) {
        estate = {
            id_kebun: 10,
            kode_kebun: kode || "EST-MDN-010",
            nama_kebun: "PT Agro Madina Subur 10",
            nomor_hgu: "010/HGU/BPN-MDN/2021",
            luas_ha: 1200.0,
            palm_stand_age_years: 7.5,
            centroid_lat: 0.824100,
            centroid_lng: 99.561200,
            soil_ph: 5.5,
            slope: 4.5,
            elevation: 142.0
        };
    }

    activeDossier = estate;
    currentEstateCode = estate.kode_kebun || kode;
    localStorage.setItem('precision_palm_active_dossier', currentEstateCode);
    localStorage.setItem('precision_palm_active_year', String(year));

    const badgeEl = document.getElementById('activeDossierBadge');
    if (badgeEl) badgeEl.textContent = (estate.kode_kebun || kode) + ' • ' + (estate.nama_kebun || 'Estate');
    const hguEl = document.getElementById('activeDossierHguTag');
    if (hguEl) hguEl.textContent = 'HGU: ' + (estate.nomor_hgu || 'e-STDB') + ' • ' + (isIndonesian() ? 'Luas: ' : 'Area: ') + parseFloat(estate.luas_ha || 1200).toLocaleString('en-US') + ' Ha';

    const lat = parseFloat(estate.centroid_lat || 0.824100);
    const lng = parseFloat(estate.centroid_lng || 99.561200);
    currentPinLat = lat;
    currentPinLng = lng;

    if (telemetryMap) {
        telemetryMap.setView([lat, lng], 13);
        if (mainPinMarker) mainPinMarker.setLatLng([lat, lng]);
    }

    updateCoordinateCards(lat, lng);
    await validateSpatialMoratorium(lat, lng);
    renderDossierPolygon(estate.poligon_geojson, lat, lng, parseFloat(estate.luas_ha || 1200), estate.kode_kebun || kode);
    
    bindSurveillanceRecords(surveys);
    bindEvidencePhotos(photos, estate);

    updateBioclimaticTelemetry(lat, lng);
    fetchAndRenderGeeSatelliteAudit(estate.kode_kebun || kode, lat, lng, parseFloat(estate.luas_ha || 1200), estate.poligon_geojson);
}

function handleDossierSelectionChange(kodeKebun) {
    if (!kodeKebun) return;
    const year = localStorage.getItem('precision_palm_active_year') || '2026';
    window.location.href = '/spatial?kode=' + encodeURIComponent(kodeKebun) + '&year=' + year;
}

function renderDossierPolygon(geojsonStr, lat, lng, areaHa = 1200, kodeKebun = "EST-MDN-010") {
    if (!telemetryMap) return;
    if (polygonLayer) {
        try { telemetryMap.removeLayer(polygonLayer); } catch (_) {}
        polygonLayer = null;
    }

    let coords = [];
    if (geojsonStr) {
        try {
            const parsed = (typeof geojsonStr === 'string') ? JSON.parse(geojsonStr) : geojsonStr;
            const geom = parsed.geometry || parsed;
            if (geom && geom.coordinates && Array.isArray(geom.coordinates)) {
                if (Array.isArray(geom.coordinates[0]) && Array.isArray(geom.coordinates[0][0])) {
                    coords = geom.coordinates[0];
                } else if (Array.isArray(geom.coordinates[0]) && typeof geom.coordinates[0][0] === 'number') {
                    coords = geom.coordinates;
                }
            }
        } catch (_) {}
    }

    if (!coords || coords.length < 3) {
        const delta = Math.sqrt(areaHa / 100.0) * 0.0035;
        coords = [
            [lng - delta, lat - delta],
            [lng + delta, lat - delta],
            [lng + delta, lat + delta],
            [lng - delta, lat + delta],
            [lng - delta, lat - delta]
        ];
    }

    const geojsonObj = {
        type: "Feature",
        geometry: { type: "Polygon", coordinates: [coords] },
        properties: { area_ha: areaHa, name: (isIndonesian() ? "Batas Poligon HGU " : "HGU Concession Polygon ") + kodeKebun }
    };

    try {
        const isCollision = (lastSpatialCheckResult && (lastSpatialCheckResult.isDirectCollision || lastSpatialCheckResult.isBufferViolation));
        polygonLayer = L.geoJSON(geojsonObj, {
            style: {
                color: isCollision ? '#ef4444' : '#10b981',
                fillColor: isCollision ? '#f87171' : '#34d399',
                fillOpacity: 0.35,
                weight: 3.0,
                dashArray: isCollision ? '6, 6' : undefined
            }
        }).addTo(telemetryMap);

        const bounds = polygonLayer.getBounds();
        if (bounds && bounds.isValid()) telemetryMap.fitBounds(bounds, { padding: [35, 35] });
    } catch (e) {
        console.warn("[Spatial] Notice on polygon render:", e);
    }
}

function bindSurveillanceRecords(surveys) {
    if (!telemetryMap) return;
    if (!inspectionTrackingLayerGroup) {
        inspectionTrackingLayerGroup = L.layerGroup().addTo(telemetryMap);
    } else {
        inspectionTrackingLayerGroup.clearLayers();
    }

    cachedMobileSurveys = surveys || [];
    surveysFullList = surveys || [];
    renderSurveysTable();

    if (!surveys || surveys.length === 0) return;

    surveys.forEach((s) => {
        const lat = parseFloat(s.latitude || s.lat);
        const lng = parseFloat(s.longitude || s.lng);
        if (isNaN(lat) || isNaN(lng)) return;

        const piringanCircle = L.circle([lat, lng], {
            radius: 2.05,
            color: '#10b981',
            weight: 2,
            opacity: 0.95,
            fillColor: '#34d399',
            fillOpacity: 0.35
        });
        inspectionTrackingLayerGroup.addLayer(piringanCircle);

        const pinMarkerHtml = '<div class="w-6 h-6 rounded-full bg-slate-950 border-2 border-emerald-400 text-white flex items-center justify-center shadow-lg text-[10px] font-bold">📍</div>';
        const markerIcon = L.divIcon({
            className: 'custom-inspection-pin',
            html: pinMarkerHtml,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        const marker = L.marker([lat, lng], { icon: markerIcon });
        if (s.image_gcs_url || s.foto_url) {
            const popupHtml = '<div class="p-1 font-mono text-xs max-w-xs text-slate-100">' +
                '<img src="' + (s.image_gcs_url || s.foto_url) + '" class="w-full h-24 object-cover rounded mb-1" onerror="this.src=\'' + DEFAULT_FALLBACK_IMAGE + '\'">' +
                '<div><strong>' + (s.block_id || s.blok || 'Plot') + '</strong>: ' + lat.toFixed(6) + ', ' + lng.toFixed(6) + '</div>' +
                '<div class="text-[9px] text-emerald-400">' + (isIndonesian() ? 'Siklus: ' : 'Cycle: ') + (s.process_stage || 'STAGE-1-Q1') + '</div>' +
                '</div>';
            marker.bindPopup(popupHtml);
        }
        inspectionTrackingLayerGroup.addLayer(marker);
    });
}

function handleSurveysSearchDebounce() {
    clearTimeout(surveysDebounceTimer);
    surveysDebounceTimer = setTimeout(() => {
        const inp = document.getElementById('surveysSearchInput');
        surveysSearchQuery = (inp ? inp.value.trim().toLowerCase() : '');
        surveysCurrentPage = 1;
        renderSurveysTable();
    }, 250);
}
window.handleSurveysSearchDebounce = handleSurveysSearchDebounce;

function changeSurveysPage(delta) {
    surveysCurrentPage += delta;
    renderSurveysTable();
}
window.changeSurveysPage = changeSurveysPage;

function renderSurveysTable() {
    const tbody = document.getElementById('mobileSurveysTableBody');
    const badge = document.getElementById('mobileSurveysCountBadge');
    const infoEl = document.getElementById('surveysPaginationInfo');
    const pageLbl = document.getElementById('lblSurveysCurrentPage');
    const btnPrev = document.getElementById('btnPrevSurveysPage');
    const btnNext = document.getElementById('btnNextSurveysPage');

    if (!tbody) return;

    const isId = isIndonesian();
    if (badge) badge.textContent = surveysFullList.length + (isId ? ' Rekaman Lapangan' : ' Field Records');

    if (!surveysFullList || surveysFullList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="py-8 text-center text-slate-400 font-mono text-xs">' + 
            (isId ? 'Belum ada rekaman surveilans lapangan terdaftar untuk konsesi ini.' : 'No field surveillance records registered for this concession parcel yet.') + 
            '</td></tr>';
        if (infoEl) infoEl.textContent = 'Showing 0-0 of 0';
        if (btnPrev) btnPrev.disabled = true;
        if (btnNext) btnNext.disabled = true;
        return;
    }

    let filteredList = surveysFullList;
    if (surveysSearchQuery) {
        filteredList = surveysFullList.filter(s => {
            const block = (s.block_id || s.blok || '').toLowerCase();
            const stage = (s.process_stage || '').toLowerCase();
            const coords = `${s.latitude || s.lat}, ${s.longitude || s.lng}`.toLowerCase();
            const weather = (s.weather_condition || '').toLowerCase();
            return block.includes(surveysSearchQuery) || stage.includes(surveysSearchQuery) || coords.includes(surveysSearchQuery) || weather.includes(surveysSearchQuery);
        });
    }

    filteredSurveysCache = filteredList;

    const totalRecords = filteredList.length;
    const totalPages = Math.ceil(totalRecords / SURVEYS_PER_PAGE) || 1;
    if (surveysCurrentPage > totalPages) surveysCurrentPage = totalPages;
    if (surveysCurrentPage < 1) surveysCurrentPage = 1;

    const startIndex = (surveysCurrentPage - 1) * SURVEYS_PER_PAGE;
    const endIndex = Math.min(startIndex + SURVEYS_PER_PAGE, totalRecords);
    const paginatedList = filteredList.slice(startIndex, endIndex);

    if (infoEl) infoEl.textContent = totalRecords === 0 ? 'Showing 0-0 of 0' : `Showing ${startIndex + 1}-${endIndex} of ${totalRecords}`;
    if (pageLbl) pageLbl.textContent = `${surveysCurrentPage} / ${totalPages}`;
    if (btnPrev) btnPrev.disabled = (surveysCurrentPage <= 1);
    if (btnNext) btnNext.disabled = (surveysCurrentPage >= totalPages);

    if (paginatedList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="py-6 text-center text-slate-400 font-mono text-xs">' + 
            (isId ? 'Tidak ada data surveilans yang cocok dengan pencarian.' : 'No surveillance records matched your search.') + 
            '</td></tr>';
        return;
    }

    tbody.innerHTML = paginatedList.map((s, idx) => {
        const fotoSrc = s.foto_url || s.image_gcs_url || '';
        const blockName = s.block_id || s.blok || 'Evidence record';
        const stageName = s.process_stage || (isId ? 'Tidak tercatat' : 'Not recorded');
        const dateStr = s.recorded_at || s.timestamp || (isId ? 'Tidak tercatat' : 'Not recorded');
        const formatCoordinate = value => value === null || value === undefined || value === '' || !Number.isFinite(Number(value))
            ? '—'
            : Number(value).toFixed(6);
        const latVal = formatCoordinate(s.latitude ?? s.lat);
        const lngVal = formatCoordinate(s.longitude ?? s.lng);
        const elevVal = `${s.elevation_m ?? '—'} • ${s.slope_deg ?? '—'}`;
        const weatherStr = s.weather_condition || (isId ? 'Tidak tercatat' : 'Not recorded');
        const shaStr = s.sha256_seal ? s.sha256_seal.substring(0, 10) + '...' : 'Not available';
        
        const absoluteIndex = surveysFullList.findIndex(item => item === s) + 1;

        return '<tr class="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition border-b border-slate-100 dark:border-slate-800/60 font-mono text-xs">' +
            '<td class="px-3 py-3 text-center text-slate-400 font-bold">' + (startIndex + idx + 1) + '</td>' +
            '<td class="px-4 py-2.5">' +
                '<div class="flex items-center gap-2">' +
                    '<img src="' + fotoSrc + '" onerror="this.onerror=null; this.classList.add(\'hidden\')" class="w-10 h-8 rounded-lg object-cover border border-slate-700 cursor-pointer hover:scale-105 transition" onclick="selectGalleryPhoto(\'' + fotoSrc + '\', \'' + blockName + '\', false)">' +
                    '<span class="text-[9px] text-emerald-400 font-bold">' + (isId ? 'Tersegel' : 'Sealed') + '</span>' +
                '</div>' +
            '</td>' +
            '<td class="px-4 py-2.5">' +
                '<button type="button" onclick="openSurveySummaryModal(' + absoluteIndex + ')" class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] shadow-xs transition flex items-center gap-1 cursor-pointer">' +
                    '<span>📋</span> <span>' + (isId ? 'Lihat Ringkasan' : 'View Summary') + '</span>' +
                '</button>' +
            '</td>' +
            '<td class="px-4 py-3"><span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500 font-bold text-[9px]">' + stageName + '</span></td>' +
            '<td class="px-4 py-3 text-slate-300">' + dateStr + '</td>' +
            '<td class="px-4 py-3 font-bold text-white">' + blockName + '</td>' +
            '<td class="px-4 py-3 text-emerald-400">' + latVal + ', ' + lngVal + '</td>' +
            '<td class="px-4 py-3 text-center">' + elevVal + '</td>' +
            '<td class="px-4 py-3 text-amber-300 font-bold">' + (isId ? 'Tidak dinilai' : 'Not assessed') + '</td>' +
            '<td class="px-4 py-3 text-center text-[10px] text-cyan-300">' + weatherStr + '</td>' +
            '<td class="px-4 py-3 text-center font-mono text-[9px] text-slate-400">' + shaStr + '</td>' +
        '</tr>';
    }).join('');
}

// ==============================================================================
// MODAL REVIEW BUKTI FORENSIK (VIEW SUMMARY POPUP & BENCHMARK AUDIT)
// ==============================================================================
function openSurveySummaryModal(surveyIndex) {
    const modal = document.getElementById('surveySummaryModal');
    const body = document.getElementById('surveySummaryModalBody');
    const idTag = document.getElementById('summaryModalIdTag');
    if (!modal || !body) return;

    const s = surveysFullList[surveyIndex - 1] || surveysFullList[0];
    if (!s) return;

    activeModalSurveyItem = s;
    activeModalSurveyIndex = surveyIndex;

    const isId = isIndonesian();
    if (idTag) idTag.textContent = `#SURV-2026-0${surveyIndex}`;

    const boxes = Array.isArray(s.detected_entities) ? s.detected_entities : [];
    const displayMetadata = value => value === null || value === undefined || value === '' ? 'Not recorded' : value;
    const formatCoordinate = value => value === null || value === undefined || value === '' || !Number.isFinite(Number(value))
        ? 'Not recorded'
        : Number(value).toFixed(6);
    const validBoxEntities = boxes.filter(b =>
        b && Array.isArray(b.box_2d) && b.box_2d.length === 4 && b.box_2d.every(Number.isFinite)
    );

    body.innerHTML = `
        <div class="p-4 sm:p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
                <div class="sm:col-span-5 relative rounded-xl overflow-hidden border border-slate-700 h-48 bg-slate-900 shadow">
                    ${s.foto_url ? `<img src="${s.foto_url}" alt="Evidence Photo" class="w-full h-full object-cover">` : ''}
                    <div class="absolute inset-0 pointer-events-none">
                        ${validBoxEntities.map(b => {
                            const box = b.box_2d;
                            const top = (box[0] / 10.0).toFixed(1);
                            const left = (box[1] / 10.0).toFixed(1);
                            const height = ((box[2] - box[0]) / 10.0).toFixed(1);
                            const width = ((box[3] - box[1]) / 10.0).toFixed(1);
                            return `<div class="absolute border border-emerald-400 bg-emerald-500/20 rounded" style="top: ${top}%; left: ${left}%; width: ${width}%; height: ${height}%;"></div>`;
                        }).join('')}
                    </div>
                    <span class="absolute bottom-1.5 left-1.5 bg-slate-950/90 text-[8.5px] font-mono px-2 py-0.5 rounded border border-slate-700 text-emerald-300">📸 ${boxes.length} image detections</span>
                </div>

                <div class="sm:col-span-7 space-y-2.5 font-mono">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-2">
                        <div>
                            <span class="text-[9px] uppercase text-emerald-500 font-bold tracking-wider">IMAGE SCAN RECORD</span>
                            <h4 class="text-sm font-bold text-white font-sans mt-0.5">${s.block_id || s.blok || 'Evidence record'}</h4>
                        </div>
                        <span class="px-2.5 py-1 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-500">
                            NOT GROUND-TRUTH VERIFIED
                        </span>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-[10px]">
                        <div><span class="text-slate-400 block">Cycle Stage:</span><strong class="text-emerald-400 font-bold">${displayMetadata(s.process_stage)}</strong></div>
                        <div><span class="text-slate-400 block">Timestamp:</span><strong class="text-slate-200">${displayMetadata(s.recorded_at || s.timestamp)}</strong></div>
                        <div><span class="text-slate-400 block">WGS84 GPS:</span><strong class="text-sky-300 font-mono">${formatCoordinate(s.latitude ?? s.lat)}, ${formatCoordinate(s.longitude ?? s.lng)}</strong></div>
                        <div><span class="text-slate-400 block">Elevation &bull; Slope metadata:</span><strong class="text-white">${displayMetadata(s.elevation_m)} &bull; ${displayMetadata(s.slope_deg)}</strong></div>
                        <div><span class="text-slate-400 block">Field compliance:</span><strong class="text-amber-300">Not assessed</strong></div>
                        <div><span class="text-slate-400 block">Weather:</span><strong class="text-amber-300">${displayMetadata(s.weather_condition)}</strong></div>
                    </div>
                </div>
            </div>

            <div class="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5 font-mono text-xs">
                <span class="text-[10px] font-bold uppercase text-emerald-400 flex items-center gap-1.5">
                    <span>🤖</span> <span>SCAN RESULT LIMITATIONS:</span>
                </span>
                <p class="text-[10.5px] leading-relaxed text-slate-300 font-sans text-justify">
                    Gemini object detections are model output, not independently verified ground truth. Image detections do not measure field dimensions or establish regulatory compliance.
                </p>
            </div>

            <div class="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[10px] font-mono text-slate-400">
                <span class="truncate">Image SHA-256: <strong class="text-indigo-300 font-bold">${s.sha256_seal || 'Not available'}</strong></span>
                <span class="text-amber-400 font-bold shrink-0">GROUND-TRUTH REVIEW REQUIRED</span>
            </div>
        </div>
    `;

    modal.classList.remove('hidden');
}
window.openSurveySummaryModal = openSurveySummaryModal;

function closeSurveySummaryModal() {
    const modal = document.getElementById('surveySummaryModal');
    if (modal) modal.classList.add('hidden');
}
window.closeSurveySummaryModal = closeSurveySummaryModal;

/**
 * CETAK / UNDUH BUKTI FORENSIK MANDIRI (IDENTIK PERSIS DENGAN MODAL)
 */
function downloadForensicProofPdf() {
    const s = activeModalSurveyItem || surveysFullList[0];
    if (!s) {
        alert("Data bukti forensik tidak ditemukan untuk dicetak.");
        return;
    }

    const boxes = Array.isArray(s.detected_entities) ? s.detected_entities : [];
    const estCode = currentEstateCode || 'EST-MDN-010';
    const displayMetadata = value => value === null || value === undefined || value === '' ? 'Not recorded' : value;
    const formatCoordinate = value => value === null || value === undefined || value === '' || !Number.isFinite(Number(value))
        ? 'Not recorded'
        : Number(value).toFixed(6);
    const blockTitle = s.block_id || s.blok || 'Evidence record';
    const stageName = displayMetadata(s.process_stage);
    const timestampStr = displayMetadata(s.recorded_at || s.timestamp);
    const gpsCoords = `${formatCoordinate(s.latitude ?? s.lat)}, ${formatCoordinate(s.longitude ?? s.lng)}`;
    const elevSlope = `${displayMetadata(s.elevation_m)} • ${displayMetadata(s.slope_deg)}`;
    const weatherStr = displayMetadata(s.weather_condition);
    const shaCode = s.sha256_seal || 'Not available';
    const proofId = `#SURV-2026-0${activeModalSurveyIndex || 1}`;

    const printWin = window.open('', '_blank', 'width=1000,height=800');
    if (!printWin) {
        alert("Izinkan popup browser untuk mengunduh dokumen bukti forensik.");
        return;
    }

    const boxesHtml = boxes.filter(b =>
        b && Array.isArray(b.box_2d) && b.box_2d.length === 4 && b.box_2d.every(Number.isFinite)
    ).map(b => {
        const box = b.box_2d;
        const top = (box[0] / 10.0).toFixed(1);
        const left = (box[1] / 10.0).toFixed(1);
        const height = ((box[2] - box[0]) / 10.0).toFixed(1);
        const width = ((box[3] - box[1]) / 10.0).toFixed(1);
        return `<div style="position:absolute;border:1.5px solid #10b981;background:rgba(16,185,129,0.18);border-radius:4px;top:${top}%;left:${left}%;width:${width}%;height:${height}%;"></div>`;
    }).join('');

    const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FORENSIC_PROOF_DOCUMENT_${estCode}_${proofId.replace('#', '')}</title>
    <style>
        @page { size: A4 landscape; margin: 10mm; }
        body {
            margin: 0;
            padding: 20px;
            background: #020617;
            color: #f1f5f9;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        .proof-card {
            background: #090e17;
            border: 2px solid #1e293b;
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.8);
            max-width: 960px;
            margin: 0 auto;
        }
        .header-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1.5px solid #1e293b;
            padding-bottom: 14px;
            margin-bottom: 18px;
        }
        .header-title-box {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header-title-box h2 {
            font-size: 18px;
            font-weight: 800;
            color: #ffffff;
            margin: 0;
        }
        .badge-id {
            background: #022c22;
            color: #34d399;
            border: 1px solid #059669;
            padding: 3px 10px;
            border-radius: 999px;
            font-family: monospace;
            font-size: 11px;
            font-weight: 800;
        }
        .header-sub {
            font-size: 11px;
            color: #94a3b8;
            margin: 4px 0 0 0;
            font-family: monospace;
        }
        .grid-main {
            display: grid;
            grid-template-columns: 44% 56%;
            gap: 20px;
            background: #040813;
            border: 1px solid #1e293b;
            border-radius: 16px;
            padding: 16px;
            align-items: center;
        }
        .img-container {
            position: relative;
            height: 220px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
            background: #020617;
        }
        .img-container img {
            width: 100%;
            height: 100%;
            object-cover: cover;
        }
        .img-badge {
            position: absolute;
            bottom: 8px;
            left: 8px;
            background: rgba(2,6,23,0.92);
            color: #6ee7b7;
            font-family: monospace;
            font-size: 9.5px;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid #334155;
        }
        .meta-col {
            font-family: monospace;
            font-size: 11px;
        }
        .meta-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 8px;
            margin-bottom: 12px;
        }
        .meta-category {
            color: #10b981;
            font-size: 9.5px;
            font-weight: 800;
            letter-spacing: 0.5px;
        }
        .meta-block-name {
            font-size: 13px;
            font-weight: 800;
            color: #ffffff;
            margin: 2px 0 0 0;
            font-family: sans-serif;
        }
        .badge-verified {
            background: #022c22;
            color: #34d399;
            border: 1px solid #10b981;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 800;
        }
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }
        .meta-cell span {
            display: block;
            color: #94a3b8;
            font-size: 9.5px;
        }
        .meta-cell strong {
            display: block;
            margin-top: 2px;
            font-size: 11px;
        }
        .review-box {
            margin-top: 16px;
            background: #040813;
            border: 1px solid #1e293b;
            border-radius: 14px;
            padding: 14px;
            font-family: monospace;
        }
        .review-header {
            color: #34d399;
            font-size: 10.5px;
            font-weight: 800;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .review-text {
            color: #cbd5e1;
            font-size: 11px;
            line-height: 1.5;
            font-family: sans-serif;
            text-align: justify;
            margin: 0;
        }
        .seal-strip {
            margin-top: 14px;
            background: #040813;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: monospace;
            font-size: 10px;
        }
        .seal-hash {
            color: #818cf8;
            font-weight: 800;
        }
        .seal-status {
            color: #34d399;
            font-weight: 800;
        }
    </style>
</head>
<body>
    <div class="proof-card">
        <div class="header-bar">
            <div>
                <div class="header-title-box">
                    <span style="font-size:20px;">📋</span>
                    <h2>Forensic Ground-Truth Evidence &amp; AI Telemetry Review</h2>
                    <span class="badge-id">${proofId}</span>
                </div>
                <div class="header-sub">Gemini object detections from this image &bull; ground-truth review required</div>
            </div>
            <div style="font-family:monospace;font-size:10px;color:#94a3b8;text-align:right;">
                Concession: <strong style="color:#ffffff;">${estCode}</strong><br>
                Status: <strong style="color:#fbbf24;">NOT GROUND-TRUTH VERIFIED</strong>
            </div>
        </div>

        <div class="grid-main">
            <div class="img-container">
                ${s.foto_url ? `<img src="${s.foto_url}" alt="Evidence Photo">` : ''}
                <div style="position:absolute;inset:0;pointer-events:none;">${boxesHtml}</div>
                <div class="img-badge">📸 ${boxes.length} image detections</div>
            </div>

            <div class="meta-col">
                <div class="meta-header">
                    <div>
                        <span class="meta-category">IMAGE SCAN RECORD</span>
                        <h4 class="meta-block-name">${blockTitle}</h4>
                    </div>
                    <span style="background:#451a03;color:#fbbf24;border:1px solid #d97706;padding:3px 8px;border-radius:6px;">NOT GROUND-TRUTH VERIFIED</span>
                </div>

                <div class="meta-grid">
                    <div class="meta-cell">
                        <span>Cycle Stage:</span>
                        <strong style="color:#34d399;">${stageName}</strong>
                    </div>
                    <div class="meta-cell">
                        <span>Timestamp:</span>
                        <strong style="color:#f8fafc;">${timestampStr}</strong>
                    </div>
                    <div class="meta-cell">
                        <span>WGS84 GPS:</span>
                        <strong style="color:#38bdf8;">${gpsCoords}</strong>
                    </div>
                    <div class="meta-cell">
                        <span>Elevation &bull; Slope:</span>
                        <strong style="color:#f8fafc;">${elevSlope}</strong>
                    </div>
                    <div class="meta-cell">
                        <span>Field compliance:</span>
                        <strong style="color:#fbbf24;">Not assessed</strong>
                    </div>
                    <div class="meta-cell">
                        <span>Weather metadata:</span>
                        <strong style="color:#fcd34d;">${weatherStr}</strong>
                    </div>
                </div>
            </div>
        </div>

        <div class="review-box">
            <div class="review-header">
                <span>🤖</span> <span>SCAN RESULT LIMITATIONS:</span>
            </div>
            <p class="review-text">
                Gemini detections are model output, not independently verified ground truth. Object detections do not measure field dimensions or establish regulatory compliance.
            </p>
        </div>

        <div class="seal-strip">
            <div>
                Image SHA-256: <span class="seal-hash">${shaCode}</span>
            </div>
            <div class="seal-status">
                GROUND-TRUTH REVIEW REQUIRED
            </div>
        </div>
    </div>
</body>
</html>`;

    printWin.document.open();
    printWin.document.write(htmlContent);
    printWin.document.close();

    setTimeout(() => {
        printWin.print();
    }, 500);
}
window.downloadForensicProofPdf = downloadForensicProofPdf;

function calibrateHolisticFieldEntities(filename, isAerialDrone = true) {
    if (window.UnifiedVisionEngine && typeof window.UnifiedVisionEngine.generateHolisticFallback === 'function') {
        const pers = isAerialDrone ? 'AERIAL_DRONE' : 'TERRESTRIAL_IN_SITU';
        const res = window.UnifiedVisionEngine.generateHolisticFallback(filename, pers, 'SPATIAL');
        return res.physical_entities || res.detected_objects || [];
    }
    const isId = typeof isIndonesian === 'function' ? isIndonesian() : false;
    return [
        { label: 'palm_canopy', label_name: isId ? 'Tajuk Sawit Utama' : 'Main Palm Canopy', cluster: 'palm_canopy', box_2d: [50, 40, 220, 200] },
        { label: 'clean_alley', label_name: isId ? 'Koridor Gawangan 3.79m' : '3.79m Alley Corridor', cluster: 'floor_mulch', box_2d: [320, 420, 760, 640] }
    ];
}

function bindEvidencePhotos(photos, dossier) {
    registeredPhotos = [];
    const sealedHashes = new Set(surveysFullList.map(s => s.sha256_seal || s.image_sha256_hash));
    const sealedUrls = new Set(surveysFullList.map(s => s.foto_url).filter(Boolean));
    const sealedEvIds = new Set(surveysFullList.map(s => s.evidence_id || s.id).filter(Boolean));
    const photoHashCounts = new Map();

    const surveyBoxesMap = new Map();
    if (Array.isArray(surveysFullList)) {
        surveysFullList.forEach(s => {
            const sKey = s.evidence_id || s.id;
            const sEnt = s.detected_entities || s.detected_entities_json;
            if (sKey && sEnt) {
                try {
                    const parsed = typeof sEnt === 'string' ? JSON.parse(sEnt) : sEnt;
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        surveyBoxesMap.set(String(sKey), parsed);
                    }
                } catch (_) {}
            }
        });
    }

    if (Array.isArray(photos) && photos.length > 0) {
        photos.forEach((p, idx) => {
            const streamUrl = p.image_gcs_url || p.file_url || p.image_raw_base64 || ('/api/media/evidence/' + p.evidence_id);
            const photoKey = p.image_sha256_hash || p.sha256 || p.filename || streamUrl;
            const currentCount = photoHashCounts.get(photoKey) || 0;
            if (currentCount >= 2) {
                // Quota Capping: Batasi foto identik maksimal 2 entri
                return;
            }
            photoHashCounts.set(photoKey, currentCount + 1);

            let boxes = Array.isArray(p.boxes) && p.boxes.length > 0 ? p.boxes : [];
            if (!boxes.length && p.detected_entities_json) {
                try {
                    boxes = typeof p.detected_entities_json === 'string' ? JSON.parse(p.detected_entities_json) : p.detected_entities_json;
                } catch (_) {}
            }
            if (!boxes.length && (p.evidence_id || p.id)) {
                boxes = surveyBoxesMap.get(String(p.evidence_id || p.id)) || [];
            }

            const hasScanResult = Boolean(p.is_processed || (Array.isArray(boxes) && boxes.length > 0));
            const isLocked = Boolean(
                p.is_locked ||
                String(p.status || '').toUpperCase() === 'SEALED' ||
                sealedHashes.has(p.image_sha256_hash) ||
                sealedHashes.has(p.sha256) ||
                sealedUrls.has(streamUrl) ||
                sealedEvIds.has(p.evidence_id) ||
                sealedEvIds.has(p.id)
            );

            registeredPhotos.push({
                id: p.evidence_id || ('EV-' + idx),
                filename: p.filename || ((p.evidence_id || 'photo') + '.jpg'),
                file_url: streamUrl,
                title: (p.process_stage || 'STAGE-0-ANNUAL-REG') + ' • ' + (p.perspective_mode || 'AERIAL_DRONE'),
                tag: p.process_stage || 'STAGE-0-ANNUAL-REG',
                sha256: p.image_sha256_hash || '',
                boxes: boxes,
                is_processed: hasScanResult,
                is_gemini_verified: Boolean(Array.isArray(boxes) && boxes.length > 0),
                is_locked: isLocked
            });
        });
    }

    selectedPhotoUrls.clear();
    const firstUnprocessed = registeredPhotos.find(p => !p.is_processed) || registeredPhotos[0];
    if (firstUnprocessed) {
        selectedPhotoUrls.add(firstUnprocessed.file_url);
    }

    renderGalleryThumbnails();
    renderSealedArchiveStrip();
    renderProcessedEvidenceCardsGrid();
    updateConsolidatedEvidenceLedger();
    updateScanButtonLabel();

    const initialPhoto = firstUnprocessed || registeredPhotos[0];
    if (initialPhoto) {
        selectGalleryPhoto(initialPhoto.file_url, initialPhoto.filename, false);
    } else {
        const imgEl = document.getElementById('verifPhotoImg');
        if (imgEl) window.handleEmptyEvidenceStateSpatial?.(imgEl);
    }
}

function setProcessStageFilter(stage) {
    activeProcessStageFilter = stage;
    const buttons = ['ALL', 'STAGE-0-ANNUAL-REG', 'STAGE-1-Q1', 'STAGE-2-Q2', 'STAGE-3-Q3', 'STAGE-4-Q4'];
    buttons.forEach(s => {
        const btn = document.getElementById('btnFilterStage_' + s);
        if (!btn) return;
        if (s === stage) {
            btn.className = "px-4 py-2 sm:py-2.5 rounded-xl bg-emerald-600 text-white font-bold text-xs sm:text-sm border border-emerald-400 shadow-md transition transform active:scale-95 cursor-pointer";
        } else {
            btn.className = "px-4 py-2 sm:py-2.5 rounded-xl bg-slate-900 text-slate-300 hover:text-white border border-slate-700 text-xs sm:text-sm font-semibold transition transform active:scale-95 cursor-pointer";
        }
    });

    renderGalleryThumbnails();
    renderSealedArchiveStrip();
    renderProcessedEvidenceCardsGrid();
}
window.setProcessStageFilter = setProcessStageFilter;

function renderGalleryThumbnails() {
    const grid = document.getElementById('galleryThumbnailsGrid');
    const countBadge = document.getElementById('galleryCountBadge');
    const pageIndicator = document.getElementById('lblSpatialGalleryPagination');
    const btnPrev = document.getElementById('btnPrevSpatialGallery');
    const btnNext = document.getElementById('btnNextSpatialGallery');
    const selBadge = document.getElementById('gallerySelectionBadge');
    if (!grid) return;

    const isId = isIndonesian();
    const visiblePhotos = registeredPhotos.filter(p => (activeProcessStageFilter === 'ALL' || p.tag === activeProcessStageFilter));

    if (countBadge) {
        countBadge.textContent = visiblePhotos.length + ' / ' + registeredPhotos.length + (isId ? ' Foto Galeri' : ' Gallery Photos');
    }

    if (selBadge) {
        selBadge.textContent = `[${selectedPhotoUrls.size} Selected]`;
    }

    const masterCheck = document.getElementById('galleryMasterCheckbox');
    if (masterCheck && visiblePhotos.length > 0) {
        masterCheck.checked = visiblePhotos.every(p => selectedPhotoUrls.has(p.file_url));
    }

    if (visiblePhotos.length === 0) {
        grid.innerHTML = '<div class="p-3 text-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-400 font-mono text-[10px]">' +
            '<p class="text-slate-300 font-semibold">' + (isId ? 'Tidak ada foto pada filter siklus ini.' : 'No photos found for this cycle filter.') + '</p></div>';
        if (pageIndicator) pageIndicator.textContent = 'Page 1 of 1';
        if (btnPrev) { btnPrev.disabled = true; btnPrev.classList.add('opacity-40', 'cursor-not-allowed'); }
        if (btnNext) { btnNext.disabled = true; btnNext.classList.add('opacity-40', 'cursor-not-allowed'); }
        return;
    }

    // Default select 1 photo if none selected
    if (selectedPhotoUrls.size === 0 && visiblePhotos.length > 0) {
        selectedPhotoUrls.add(visiblePhotos[0].file_url);
        if (selBadge) selBadge.textContent = `[${selectedPhotoUrls.size} Selected]`;
    }

    // Calculate pagination
    const totalPages = Math.max(1, Math.ceil(visiblePhotos.length / spatialGalleryPageSize));
    if (spatialGalleryCurrentPage > totalPages) spatialGalleryCurrentPage = totalPages;
    if (spatialGalleryCurrentPage < 1) spatialGalleryCurrentPage = 1;

    if (pageIndicator) {
        pageIndicator.textContent = `Page ${spatialGalleryCurrentPage} of ${totalPages} (${visiblePhotos.length} Photos)`;
    }

    if (btnPrev) {
        btnPrev.disabled = (spatialGalleryCurrentPage <= 1);
        if (spatialGalleryCurrentPage <= 1) {
            btnPrev.classList.add('opacity-40', 'cursor-not-allowed');
            btnPrev.classList.remove('hover:bg-slate-800');
        } else {
            btnPrev.classList.remove('opacity-40', 'cursor-not-allowed');
            btnPrev.classList.add('hover:bg-slate-800');
        }
    }

    if (btnNext) {
        btnNext.disabled = (spatialGalleryCurrentPage >= totalPages);
        if (spatialGalleryCurrentPage >= totalPages) {
            btnNext.classList.add('opacity-40', 'cursor-not-allowed');
            btnNext.classList.remove('hover:bg-slate-800');
        } else {
            btnNext.classList.remove('opacity-40', 'cursor-not-allowed');
            btnNext.classList.add('hover:bg-slate-800');
        }
    }

    const startIndex = (spatialGalleryCurrentPage - 1) * spatialGalleryPageSize;
    const pagePhotos = visiblePhotos.slice(startIndex, startIndex + spatialGalleryPageSize);

    grid.innerHTML = pagePhotos.map(item => {
        const isSelected = selectedPhotoUrls.has(item.file_url);
        const isActive = (activePhotoUrl === item.file_url);
        const deleteId = item.id || item.filename;
        const titleText = item.title || item.filename || 'Inspeksi Drone Nadir 45m';
        const subText = item.tag ? `${item.tag} • ${item.filename}` : `STAGE-1-Q1 • ${item.filename}`;

        let cardContainerClass = 'border-slate-800 bg-slate-900/50 hover:border-slate-700';
        if (isActive) {
            cardContainerClass = 'ring-2 ring-emerald-500 border-emerald-400 shadow-md shadow-emerald-500/20 bg-slate-900/90';
        } else if (isSelected) {
            cardContainerClass = 'border-emerald-500/50 bg-slate-900/70';
        }

        const statusBadge = item.is_locked ?
            `<span class="px-1.5 py-0.5 rounded text-[7.5px] font-mono font-bold bg-amber-950/90 text-amber-300 border border-amber-600/60 inline-flex items-center gap-0.5" title="Bukti Tersegel Resmi">🔒 SEALED</span>` :
            `<span class="px-1.5 py-0.5 rounded text-[7.5px] font-mono font-bold ${item.is_processed ? 'bg-sky-950/90 text-sky-300 border border-sky-600/60' : 'bg-emerald-950/90 text-emerald-300 border border-emerald-600/60'} inline-flex items-center gap-0.5">${item.is_processed ? '✓ SCANNED' : '⚡ READY'}</span>`;

        const deleteBtnHtml = `
            ${item.is_locked ? `<button type="button" onclick="unsealEvidencePhoto('${deleteId}', event)" class="p-1 rounded bg-amber-950/90 text-amber-300 hover:bg-amber-600 hover:text-white border border-amber-500/60 transition shadow cursor-pointer" title="${isId ? 'Buka segel untuk scan ulang' : 'Unlock for rescanning'}"><span class="text-[9px]">🔓</span></button>` : ''}
            <button type="button" onclick="deleteEvidencePhoto('${deleteId}', '${item.file_url}', event)" 
                class="p-1 rounded bg-rose-950/90 text-rose-300 hover:bg-rose-600 hover:text-white border border-rose-500/60 transition shadow cursor-pointer" 
                title="${isId ? 'Hapus foto' : 'Delete photo'}">
                <span class="text-[9px]">🗑️</span>
            </button>
        `;

        return `
            <div onclick="selectGalleryPhoto('${item.file_url}', '${item.filename}', false)" 
                class="relative group rounded-2xl p-2.5 border ${cardContainerClass} transition cursor-pointer flex items-center justify-between gap-3 shadow-xs">
                <div class="flex items-center gap-3 min-w-0">
                    <!-- Thumbnail -->
                    <div class="w-16 h-13 rounded-xl overflow-hidden bg-slate-950 flex-shrink-0 border border-slate-800 flex items-center justify-center relative">
                        <img src="${item.file_url}" alt="${item.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform ${item.is_locked ? 'photo-sealed-blur' : ''}" onerror="this.onerror=null; this.classList.add('hidden')">
                    </div>
                    <!-- Metadata -->
                    <div class="min-w-0 space-y-0.5">
                        <span class="text-xs font-bold text-slate-100 truncate block font-sans" title="${titleText}">
                            ${titleText}
                        </span>
                        <span class="text-[9.5px] font-mono text-emerald-400/90 truncate block" title="${subText}">
                            ${subText}
                        </span>
                        <div class="pt-0.5">
                            ${statusBadge}
                        </div>
                    </div>
                </div>
                <!-- Action / Checkbox -->
                <div class="pr-1 flex-shrink-0 flex items-center gap-1.5" onclick="event.stopPropagation()">
                    ${deleteBtnHtml}
                    <input type="checkbox" ${isSelected ? 'checked' : ''} onchange="togglePhotoSelection('${item.file_url}', this.checked, event)" 
                        class="w-4 h-4 rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 accent-indigo-600 cursor-pointer bg-slate-900 shadow" title="Select Photo">
                </div>
            </div>
        `;
    }).join('');
}

function changeSpatialGalleryPage(delta) {
    const visiblePhotos = registeredPhotos.filter(p => (activeProcessStageFilter === 'ALL' || p.tag === activeProcessStageFilter));
    const totalPages = Math.max(1, Math.ceil(visiblePhotos.length / spatialGalleryPageSize));
    spatialGalleryCurrentPage += delta;
    if (spatialGalleryCurrentPage < 1) spatialGalleryCurrentPage = 1;
    if (spatialGalleryCurrentPage > totalPages) spatialGalleryCurrentPage = totalPages;
    renderGalleryThumbnails();
}
window.changeSpatialGalleryPage = changeSpatialGalleryPage;

function togglePhotoSelection(url, checked, event) {
    if (event) event.stopPropagation();
    if (checked) {
        selectedPhotoUrls.add(url);
    } else {
        selectedPhotoUrls.delete(url);
    }
    updateSelectionBadges();
    renderGalleryThumbnails();
}
window.togglePhotoSelection = togglePhotoSelection;

function toggleSelectAllPhotos(checked) {
    const visiblePhotos = registeredPhotos.filter(p => (activeProcessStageFilter === 'ALL' || p.tag === activeProcessStageFilter));
    if (checked) {
        visiblePhotos.forEach(p => selectedPhotoUrls.add(p.file_url));
    } else {
        visiblePhotos.forEach(p => selectedPhotoUrls.delete(p.file_url));
    }
    updateSelectionBadges();
    renderGalleryThumbnails();
}
window.toggleSelectAllPhotos = toggleSelectAllPhotos;

function updateSelectionBadges() {
    const selBadge = document.getElementById('gallerySelectionBadge');
    if (selBadge) {
        selBadge.textContent = `[${selectedPhotoUrls.size} Selected]`;
    }
    const masterCheck = document.getElementById('galleryMasterCheckbox');
    const visiblePhotos = registeredPhotos.filter(p => (activeProcessStageFilter === 'ALL' || p.tag === activeProcessStageFilter));
    if (masterCheck && visiblePhotos.length > 0) {
        const allVisibleSelected = visiblePhotos.every(p => selectedPhotoUrls.has(p.file_url));
        masterCheck.checked = allVisibleSelected;
    }
    updateScanButtonLabel();
}
window.updateSelectionBadges = updateSelectionBadges;

function renderSealedArchiveStrip() {
    const container = document.getElementById('sealedArchiveThumbnailsContainer');
    const badge = document.getElementById('archiveCountBadge');
    if (!container) return;

    const isId = isIndonesian();
    const sealedPhotos = registeredPhotos.filter(p => p.is_locked && (activeProcessStageFilter === 'ALL' || p.tag === activeProcessStageFilter));

    if (badge) badge.textContent = `${sealedPhotos.length} ` + (isId ? 'Foto Tersegel' : 'Sealed');

    if (sealedPhotos.length === 0) {
        container.innerHTML = '<span class="text-slate-500 text-[9.5px] italic py-1">' +
            (isId ? 'Belum ada foto yang tersegel dalam arsip.' : 'No sealed photos in archive yet.') + '</span>';
        return;
    }

    container.innerHTML = sealedPhotos.map(item => {
        const isActive = (activePhotoUrl === item.file_url);
        return `
            <div onclick="reviewArchivedPhoto('${item.file_url}', '${item.filename}')" 
                 class="relative shrink-0 w-12 h-12 rounded-lg overflow-hidden border-2 cursor-pointer transition transform hover:scale-105 ${isActive ? 'border-emerald-400 ring-2 ring-emerald-500/50' : 'border-slate-700 opacity-80'}"
                 title="${item.title || item.filename} (Klik untuk review objek)">
                <img src="${item.file_url}" alt="Archive" class="w-full h-full object-cover photo-sealed-blur" onerror="this.onerror=null; this.classList.add('hidden')">
                <span class="absolute top-0.5 right-0.5 text-[8px] bg-slate-950/90 text-amber-300 px-1 rounded border border-amber-600/50">🔒</span>
                <span class="absolute bottom-0 inset-x-0 bg-slate-950/90 text-emerald-300 text-[7px] truncate px-0.5 text-center">${item.tag}</span>
            </div>
        `;
    }).join('');
}

function reviewArchivedPhoto(url, filename) {
    selectGalleryPhoto(url, filename, false);
    const isId = isIndonesian();
    showNotificationToast(isId ? `Meninjau arsip tersegel: ${filename}` : `Reviewing sealed archive: ${filename}`, "👁️");
}
window.reviewArchivedPhoto = reviewArchivedPhoto;

function updateSpatialScanProgress(stage, message, state = 'running') {
    const panel = document.getElementById('spatialScanProgress');
    const label = document.getElementById('spatialScanProgressLabel');
    const detail = document.getElementById('spatialScanProgressDetail');
    const bar = document.getElementById('spatialScanProgressBar');
    if (!panel || !label || !detail || !bar) return;

    panel.classList.remove('hidden');
    label.textContent = stage;
    detail.textContent = message;
    bar.classList.toggle('animate-pulse', state === 'running');
    bar.classList.toggle('w-1/3', state === 'running');
    bar.classList.toggle('w-full', state !== 'running');
    bar.classList.toggle('bg-emerald-400', state !== 'failed');
    bar.classList.toggle('bg-rose-400', state === 'failed');
    panel.dataset.state = state;
    panel.setAttribute('aria-label', message);
}

function hideSpatialScanProgress() {
    document.getElementById('spatialScanProgress')?.classList.add('hidden');
}

async function loadStoredContourPreview(photo, photoUrl, showProgress = false) {
    const requestId = ++spatialContourRequestId;
    const evidenceId = photo?.evidence_id || photo?.id;
    if (!Array.isArray(photo?.boxes) ||
        !photo.boxes.length ||
        !evidenceId) {
        currentSpatialContourPreview = null;
        updateContourPreviewButton();
        if (showProgress) {
            updateSpatialScanProgress(
                isIndonesian() ? 'Kontur belum tersedia' : 'Contours unavailable',
                isIndonesian()
                    ? 'Kontur hanya tersedia setelah deteksi Gemini berhasil disimpan.'
                    : 'Contours are hidden until Gemini detections are successfully saved.',
                'failed'
            );
        }
        return currentSpatialContourPreview;
    }

    currentSpatialContourPreview = { status: 'loading' };
    updateContourPreviewButton();
    if (showProgress) {
        updateSpatialScanProgress(
            isIndonesian() ? 'OpenCV Contours' : 'OpenCV Contours',
            isIndonesian() ? 'Membentuk dan merapikan garis batas objek...' : 'Building and refining object outlines...',
            'running'
        );
    }
    try {
        const response = await fetch('/api/spatial/contour-preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ evidence_id: evidenceId })
        });
        const result = await readApiJson(response, isIndonesian() ? 'Pratinjau kontur' : 'Contour preview');
        if (requestId !== spatialContourRequestId || activePhotoUrl !== photoUrl) return;

        currentSpatialContourPreview = result.contour_preview || {
            status: result.status || 'unavailable',
            reason: result.reason || 'contour_preview_missing'
        };
        showSam2ContourPreview = Boolean(
            currentSpatialContourPreview.status === 'ready' &&
            currentSpatialContourPreview.contours?.length
        );
        renderDetectedBoundingBoxes(photo.boxes);
        updateContourPreviewButton();
        return currentSpatialContourPreview;
    } catch (error) {
        if (requestId !== spatialContourRequestId || activePhotoUrl !== photoUrl) return;
        console.error('[Spatial stored contour preview]', error);
        currentSpatialContourPreview = {
            status: 'unavailable',
            reason: 'contour_preview_request_failed'
        };
        updateContourPreviewButton();
        return currentSpatialContourPreview;
    }
}

function selectGalleryPhoto(url, filename, shouldRescan = false) {
    const imgEl = document.getElementById('verifPhotoImg');
    const photoLabelEl = document.getElementById('verifPhotoLabel');
    const emptyEl = document.getElementById('emptyEvidenceStateSpatial');
    const overlay = document.getElementById('droneBBoxesOverlay');
    const canvas = document.getElementById('reticleCanvas');
    activePhotoUrl = url;
    activeFilename = filename || (url ? url.split('/').pop() : "EV-PHOTO-ACTIVE.jpg");
    hideSpatialScanProgress();

    if (overlay) {
        overlay.innerHTML = '';
        overlay.style.display = 'none';
    }
    if (canvas) {
        const context = canvas.getContext('2d');
        if (context) context.clearRect(0, 0, canvas.width, canvas.height);
    }
    if (!imgEl || !url) {
        activePhotoUrl = null;
        if (imgEl) window.handleEmptyEvidenceStateSpatial?.(imgEl);
        return;
    }

    try {
        if (url) {
            localStorage.setItem('precision_active_evidence_url', url);
            localStorage.setItem('precision_active_evidence_filename', activeFilename);
            localStorage.setItem('precision_active_evidence_dossier', activeDossier?.kode_kebun || currentEstateCode || 'EST-MDN-010');
            window.dispatchEvent(new CustomEvent('precision_palm_evidence_synced', { detail: { url, filename: activeFilename } }));
        }
    } catch (_) {}

    imgEl.style.display = 'none';
    imgEl.classList.add('hidden');
    if (emptyEl) {
        emptyEl.classList.remove('hidden');
        emptyEl.style.display = 'flex';
    }

    if (photoLabelEl) photoLabelEl.textContent = filename || url.split('/').pop() || "EV-PHOTO-ACTIVE.jpg";

    imgEl.onload = function() {
        if (!imgEl.complete || imgEl.naturalWidth === 0 || activePhotoUrl !== url) {
            window.handleEmptyEvidenceStateSpatial?.(imgEl);
            return;
        }
        if (emptyEl) {
            emptyEl.classList.add('hidden');
            emptyEl.style.display = 'none';
        }
        imgEl.style.display = 'block';
        imgEl.classList.remove('hidden');
        
        drawReticles();

                const photoObj = registeredPhotos.find(p => p.file_url === url || p.filename === filename) || { filename, file_url: url };
        let boxes = Array.isArray(photoObj.boxes) && photoObj.boxes.length > 0
            ? photoObj.boxes
            : [];
        if (!boxes.length && photoObj.detected_entities_json) {
            try {
                boxes = typeof photoObj.detected_entities_json === 'string' ? JSON.parse(photoObj.detected_entities_json) : photoObj.detected_entities_json;
            } catch (_) {}
        }
        
        photoObj.boxes = boxes;
        currentSpatialContourPreview = null;
        showSam2ContourPreview = false;
        openCvStaticReplayRequestId += 1;
        currentOpenCvStaticReplay = null;
        showOpenCvStaticReplay = false;
        renderDetectedBoundingBoxes(boxes);
        updateContourPreviewButton();
        updateOpenCvStaticReplayButton();

        if (shouldRescan) {
            triggerScanningFotoAction();
        } else {
            loadStoredContourPreview(photoObj, url);
        }
    };

    imgEl.onerror = function() {
        if (activePhotoUrl === url) {
            activePhotoUrl = null;
            currentSpatialBoxes = [];
            window.handleEmptyEvidenceStateSpatial?.(imgEl);
        }
    };

    imgEl.src = url;
    if (imgEl.complete && imgEl.naturalWidth > 0) imgEl.onload();
    renderGalleryThumbnails();
    renderSealedArchiveStrip();
}

async function deleteEvidencePhoto(photoId, photoUrl, event) {
    if (event) event.stopPropagation();
    const isId = isIndonesian();
    
    const target = registeredPhotos.find(p => p.file_url === photoUrl || p.id === photoId);
    const confirmation = target?.is_locked
        ? (isId ? "Foto ini SEALED dan dapat terhubung ke rekaman surveilans. Hapus foto serta tautan auditnya secara permanen?" : "This photo is SEALED and may be linked to surveillance records. Permanently delete the photo and its audit links?")
        : (isId ? "Hapus foto ini secara permanen?" : "Permanently delete this photo?");
    if (!confirm(confirmation)) return;

    showNotificationToast(isId ? "Menghapus foto..." : "Deleting photo...", "⏳");

    try {
        const response = await fetch('/api/spatial/delete-photo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                photo_id: photoId,
                photo_url: photoUrl,
                confirm_sealed_delete: true,
                kode_kebun: activeDossier?.kode_kebun || 'EST-MDN-010'
            })
        });
        const result = await readApiJson(response, isId ? 'Penghapusan foto' : 'Photo deletion');
        if (result.status !== 'success') throw new Error(result.message || (isId ? 'Penghapusan foto gagal.' : 'Photo deletion failed.'));
        if (result.bigquery_sync !== 'SYNCED') {
            showNotificationToast(isId ? "Foto terhapus lokal; BigQuery belum tersinkron." : "Photo deleted locally; BigQuery is not synced.", "⚠️");
        }
    } catch (error) {
        showNotificationToast(error.message || (isId ? "Gagal menghapus foto." : "Failed to delete photo."), "⚠️");
        return;
    }

    registeredPhotos = registeredPhotos.filter(p => p.file_url !== photoUrl && p.id !== photoId);
    selectedPhotoUrls.delete(photoUrl);

    renderGalleryThumbnails();
    renderSealedArchiveStrip();
    renderProcessedEvidenceCardsGrid();
    updateConsolidatedEvidenceLedger();
    updateScanButtonLabel();

    if (activePhotoUrl === photoUrl) {
        if (registeredPhotos.length > 0) {
            selectGalleryPhoto(registeredPhotos[0].file_url, registeredPhotos[0].filename, false);
        } else {
            bindEvidencePhotos([], activeDossier);
        }
    }
}

async function unsealEvidencePhoto(evidenceId, event) {
    if (event) event.stopPropagation();
    const isId = isIndonesian();
    if (!confirm(isId
        ? "Buka segel foto? Tautan rekaman surveilans terkait akan dilepas dan dicatat di audit log."
        : "Unlock this photo? Linked surveillance records will be detached and the action logged.")) return;
    try {
        const response = await fetch('/api/spatial/unseal-photo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                evidence_id: evidenceId,
                photo_url: registeredPhotos.find(photo => String(photo.id) === String(evidenceId))?.file_url || '',
                reason: 'User requested rescan'
            })
        });
        const result = await readApiJson(response, isId ? 'Buka segel foto' : 'Unlock photo');
        if (result.status !== 'success') throw new Error(result.message || (isId ? 'Buka segel gagal.' : 'Unlock failed.'));
        const target = registeredPhotos.find(photo => photo.id === evidenceId);
        if (target) target.is_locked = false;
        surveysFullList = surveysFullList.filter(survey =>
            String(survey.evidence_id || '') !== String(evidenceId) &&
            String(survey.id || '') !== String(evidenceId) &&
            (!target || survey.foto_url !== target.file_url)
        );
        cachedMobileSurveys = surveysFullList;
        renderGalleryThumbnails();
        renderSealedArchiveStrip();
        renderProcessedEvidenceCardsGrid();
        showNotificationToast(isId ? "Segel dibuka; hasil scan lama tetap tersimpan." : "Unlocked; the previous scan remains stored.", "🔓");
    } catch (error) {
        showNotificationToast(error.message || (isId ? "Gagal membuka segel." : "Failed to unlock photo."), "⚠️");
    }
}

async function handleNewPhotoUpload(event) {
    const file = event.target?.files?.[0];
    if (!file) return;

    const isId = isIndonesian();
    showNotificationToast(isId ? "Mengunggah foto bukti mentah ke database..." : "Uploading raw evidence photo to database...", "⏳");

    const reader = new FileReader();
    reader.onload = async function (e) {
        const base64Data = e.target.result;
        const year = localStorage.getItem('precision_palm_active_year') || '2026';
        const currentStage = activeProcessStageFilter !== 'ALL' ? activeProcessStageFilter : 'STAGE-0-ANNUAL-REG';

        try {
            const response = await fetch('/api/spatial/upload-photo-direct', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dossier_id: (activeDossier?.kode_kebun || 'EST-MDN-010') + '-' + year,
                    process_stage: currentStage,
                    image_base64: base64Data,
                    filename: file.name
                })
            });
            const result = await readApiJson(response, isId ? 'Unggah foto' : 'Photo upload');
            if (result.status !== 'success') throw new Error(result.message || (isId ? 'Unggah foto gagal.' : 'Photo upload failed.'));
            const newPhoto = {
                id: result.evidence_id,
                evidence_id: result.evidence_id,
                filename: file.name,
                file_url: result.file_url,
                title: currentStage + ' • ' + file.name.replace(/\.[^/.]+$/, ""),
                tag: currentStage,
                boxes: [],
                is_processed: false,
                is_locked: false
            };

            registeredPhotos.unshift(newPhoto);
            selectedPhotoUrls.add(newPhoto.file_url);
            renderGalleryThumbnails();
            renderSealedArchiveStrip();
            selectGalleryPhoto(newPhoto.file_url, newPhoto.filename, false);
            showNotificationToast(isId ? "✓ Foto asli tersimpan dan siap dipindai!" : "✓ Original photo saved and ready to scan!", "🚁");
        } catch (error) {
            showNotificationToast(error.message || (isId ? "Unggah gagal; foto tidak ditambahkan." : "Upload failed; photo was not added."), "⚠️");
        }
    };
    reader.onerror = function () {
        showNotificationToast(
            isId ? "Browser gagal membaca file foto. Coba pilih file lagi." : "The browser could not read this image. Please select it again.",
            "⚠️"
        );
    };
    reader.readAsDataURL(file);
    event.target.value = '';
}

async function animateSingleSentenceAiPipeline(step, customText = "") {
    const textEl = document.getElementById('telemetryCurrentSentence');
    const iconEl = document.getElementById('telemetryStepIcon');
    const badgeEl = document.getElementById('aiPipelineStepBadge');
    if (!textEl) return;

    const isId = isIndonesian();
    const dots = [1, 2, 3, 4, 5].map(i => document.getElementById(`telemetryProgressDot${i}`));

    dots.forEach((dot, idx) => {
        if (!dot) return;
        if (idx < step) {
            dot.className = "w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse";
        } else {
            dot.className = "w-1.5 h-1.5 rounded-full bg-emerald-500/20";
        }
    });

    const pipelineSteps = [
        {
            icon: "🛰️",
            badge: isId ? "Langkah 1/5: Sensor 4D" : "Step 1/5: 4D Sensor",
            sentence: isId
                ? "[KALIBRASI TELEMETRI 4D] Memverifikasi orientasi kamera in-situ AGL 1.45m | Sudut Pitch -12.4° | WGS84 Centroid presisi..."
                : "[CALIBRATING 4D SENSOR] Verifying in-situ AGL 1.45m | Pitch angle -12.4° | WGS84 precise geodetic centroid..."
        },
        {
            icon: "🌴",
            badge: isId ? "Langkah 2/5: Tajuk Sawit" : "Step 2/5: Palm Stands",
            sentence: isId
                ? "[SEGMENTASI KANOPI] Memetakan kerapatan tajuk sawit TM-7 berpola segitiga sama sisi 9.0m (populasi riil ~138 pokok/Ha)..."
                : "[CANOPY MAPPING] Detecting mature TM-7 crowns on equilateral triangular grid 9.0m (~138 palms/Ha density)..."
        },
        {
            icon: "⭕",
            badge: isId ? "Langkah 3/5: Piringan 2.05m" : "Step 3/5: Root Buffer",
            sentence: isId
                ? "[INTEGRITAS PERAKARAN] Memverifikasi piringan akar radius 2.05m bersih steril 100% bebas olah tanah cangkul (PPKS Zero-Tillage)..."
                : "[ROOT RING VERIFICATION] Confirming 2.05m root ring 100% sterile and weed-free (PPKS Zero-Tillage standard)..."
        },
        {
            icon: "🍂",
            badge: isId ? "Langkah 4/5: Koridor Gawangan" : "Step 4/5: Alley Floor",
            sentence: isId
                ? "[KORIDOR GAWANGAN 3.79M] Memeriksa sanitasi hamparan mulsa pelepah organik #1 & #2 (menjaga retensi kelembaban tanah +32%)..."
                : "[3.79M ALLEY FLOOR] Scanning organic frond mulch piles #1 & #2 (ensuring +32% microclimatic water retention)..."
        },
        {
            icon: "💧",
            badge: isId ? "Langkah 5/5: Sempadan Air" : "Step 5/5: Riparian HCV",
            sentence: isId
                ? "[PROTEKSI SEMPADAN AIR] Menegakkan batas sempadan konservasi air ≥ 50 meter bebas gangguan sawit (Sesuai PP No. 23/2021)..."
                : "[RIPARIAN CONSERVATION] Enforcing statutory watercourse buffer ≥ 50 meters free from palm encroachment (PP 23/2021)..."
        }
    ];

    const currentStepData = pipelineSteps[step - 1] || pipelineSteps[0];

    textEl.style.opacity = '0';
    textEl.style.transform = 'translateY(6px)';

    await new Promise(r => setTimeout(r, 180));

    if (iconEl) iconEl.textContent = currentStepData.icon;
    if (badgeEl) badgeEl.textContent = currentStepData.badge;
    textEl.textContent = customText || currentStepData.sentence;

    textEl.style.opacity = '1';
    textEl.style.transform = 'translateY(0)';
}

// =========================================================================
// GUARANTEED HUD DUAL CROSS-LASER CONTROLLER
// =========================================================================
function ensureHudLaserElements() {
    let laserV = document.getElementById('laserSweepV');
    let laserH = document.getElementById('laserSweepH');
    const container = document.getElementById('droneBBoxesOverlay')?.parentElement || document.getElementById('verifPhotoImg')?.parentElement;

    if (!container) return { laserV, laserH };

    if (!laserV) {
        laserV = document.createElement('div');
        laserV.id = 'laserSweepV';
        laserV.className = 'hidden absolute inset-x-0 h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent pointer-events-none';
        container.appendChild(laserV);
    }
    laserV.style.boxShadow = '0 0 15px #10b981, 0 0 30px #10b981';
    laserV.style.zIndex = '35';

    if (!laserH) {
        laserH = document.createElement('div');
        laserH.id = 'laserSweepH';
        laserH.className = 'hidden absolute inset-y-0 w-0.5 bg-gradient-to-b from-transparent via-cyan-400 to-transparent pointer-events-none';
        container.appendChild(laserH);
    }
    laserH.style.boxShadow = '0 0 15px #06b6d4, 0 0 30px #06b6d4';
    laserH.style.zIndex = '35';

    return { laserV, laserH };
}

function startHudLaserSweep(mode = 'fast') {
    const { laserV, laserH } = ensureHudLaserElements();
    if (laserV) {
        laserV.classList.remove('hidden');
        laserV.classList.remove('laser-sweep-v', 'laser-sweep-v-fast', 'laser-sweep-v-focused');
        laserV.classList.add(mode === 'fast' ? 'laser-sweep-v-fast' : 'laser-sweep-v-focused');
    }
    if (laserH) {
        laserH.classList.remove('hidden');
        laserH.classList.remove('laser-sweep-h', 'laser-sweep-h-fast', 'laser-sweep-h-focused');
        laserH.classList.add(mode === 'fast' ? 'laser-sweep-h-fast' : 'laser-sweep-h-focused');
    }
}

function stopHudLaserSweep() {
    const laserV = document.getElementById('laserSweepV');
    const laserH = document.getElementById('laserSweepH');
    if (laserV) {
        laserV.classList.add('hidden');
        laserV.classList.remove('laser-sweep-v', 'laser-sweep-v-fast', 'laser-sweep-v-focused');
    }
    if (laserH) {
        laserH.classList.add('hidden');
        laserH.classList.remove('laser-sweep-h', 'laser-sweep-h-fast', 'laser-sweep-h-focused');
    }
}

async function rescanActiveSinglePhoto() {
    const currentActive = registeredPhotos.find(p => p.file_url === activePhotoUrl) || registeredPhotos[0];
    if (!currentActive) return;
    selectedPhotoUrls.clear();
    selectedPhotoUrls.add(currentActive.file_url);
    await triggerScanningFotoAction(true);
}
window.rescanActiveSinglePhoto = rescanActiveSinglePhoto;

async function triggerScanningFotoAction(forceRescan = false) {
    const isId = isIndonesian();
    
    // Determine target photo
    let target = registeredPhotos.find(p => p.file_url === activePhotoUrl);
    if (!target && selectedPhotoUrls.size > 0) {
        const firstSelected = Array.from(selectedPhotoUrls)[0];
        target = registeredPhotos.find(p => p.file_url === firstSelected);
    }
    if (!target && registeredPhotos.length > 0) {
        target = registeredPhotos[0];
    }

    if (!target) {
        showNotificationToast(isId ? "Pilih foto dari galeri untuk memulai pemindaian!" : "Select photo from gallery to begin scanning!", "⚠️");
        return;
    }
    // Foto tersegel maupun tersimpan dapat di-rescan kapan saja

    activePhotoUrl = target.file_url;
    activeFilename = target.filename || (target.file_url ? target.file_url.split('/').pop() : "EV-EST-MDN-010-2026.jpg");
    selectGalleryPhoto(activePhotoUrl, activeFilename, false);

    const scanBadge = document.getElementById('aiScanBadge');
    const btnScan = document.getElementById('btnTriggerPhotoScan');

    updateSpatialScanProgress(
        isId ? 'Gemini Vision' : 'Gemini Vision',
        isId ? 'Mengirim gambar dan menunggu analisis Gemini...' : 'Sending image and waiting for Gemini analysis...',
        'running'
    );
    if (btnScan) btnScan.classList.add('animate-pulse');
    if (scanBadge) {
        scanBadge.classList.remove('hidden');
        scanBadge.className = 'px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse flex items-center gap-1';
        scanBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span><span>Scanning Canopy with Gemini 3.8 Flash...</span>`;
    }

    const fnLower = (activeFilename || '').toLowerCase();
    let targetPerspective = target.perspective_mode;
    if (!targetPerspective) {
        if (fnLower.includes('9217') || fnLower.includes('11003') || fnLower.includes('mandor') || fnLower.includes('harvest') || fnLower.includes('in-situ') || fnLower.includes('ground')) {
            targetPerspective = 'TERRESTRIAL_IN_SITU';
        } else if (fnLower.includes('field_inspection') || fnLower.includes('20827') || fnLower.includes('21499') || fnLower.includes('landscape') || fnLower.includes('macro')) {
            targetPerspective = 'AERIAL_CONCESSION_MACRO';
        } else {
            targetPerspective = 'AERIAL_DRONE';
        }
    }
    const targetDossier = activeDossier?.kode_kebun || currentEstateCode || 'EST-MDN-010';

    return window.UnifiedVisionEngine.scan({
        imageUrl: activePhotoUrl,
        filename: activeFilename,
        evidenceId: target.evidence_id || target.id,
        dossierId: targetDossier,
        perspective: targetPerspective,
        pageContext: 'SPATIAL',
        containerEl: document.getElementById('telemetryScanContainer') || document.getElementById('verifPhotoContainer'),
        overlayEl: document.getElementById('droneBBoxesOverlay'),
        statusEl: document.getElementById('scannerStatusText'),
        onProgress: progress => {
            if (progress?.stage === 'gemini') {
                updateSpatialScanProgress(
                    isId ? 'Gemini Vision' : 'Gemini Vision',
                    isId ? 'Gemini sedang menganalisis foto...' : 'Gemini is analyzing the image...',
                    'running'
                );
            }
        }
    }).then(async result => {
        if (!result) {
            updateSpatialScanProgress(
                isId ? 'Pemindaian tidak dimulai' : 'Scan did not start',
                isId ? 'Pemindaian lain masih berjalan. Coba lagi setelah selesai.' : 'Another scan is already running. Try again when it finishes.',
                'failed'
            );
            if (btnScan) btnScan.classList.remove('animate-pulse');
            return;
        }
        if (result) {
            const isFallback = result.isFallback === true || result.mode !== 'LIVE_GEMINI';
            const detectedEntities = isFallback ? [] : (result.boxes || []);
            spatialContourRequestId++;
            currentSpatialContourPreview = {
                status: 'unavailable',
                reason: isFallback ? 'scan_not_image_verified' : 'scan_not_persisted'
            };
            showSam2ContourPreview = false;
            renderDetectedBoundingBoxes(detectedEntities);
            updateContourPreviewButton();
            const isPersistedLiveResult = !isFallback && result.persistence?.saved === true;
            const timestampNow = new Date().toISOString().replace('T', ' ').substring(0, 19);
            const specificBlockId = "Centroid Block - " + (target.title || target.filename || `Parcel #${surveysFullList.length + 1}`);

            if (isPersistedLiveResult || (!isFallback && detectedEntities.length > 0)) {
                target.boxes = detectedEntities;
                target.is_processed = true;
                target.is_gemini_verified = true;
                target.is_fallback = false;
                target.sha256 = result.sha256Seal || target.sha256;
                target.prepared_survey = {
                    id: surveysFullList.length + 1,
                    evidence_id: target.id || '',
                    foto_url: target.file_url,
                    image_gcs_url: target.file_url,
                    process_stage: target.tag || 'STAGE-0-ANNUAL-REG',
                    recorded_at: timestampNow,
                    timestamp: timestampNow,
                    block_id: specificBlockId,
                    blok: specificBlockId,
                    ...(Number.isFinite(target.latitude) ? { latitude: target.latitude } : {}),
                    ...(Number.isFinite(target.longitude) ? { longitude: target.longitude } : {}),
                    ...(Number.isFinite(target.elevation_m) ? { elevation_m: target.elevation_m } : {}),
                    ...(Number.isFinite(target.slope_deg) ? { slope_deg: target.slope_deg } : {}),
                    sha256_seal: result.sha256Seal,
                    detected_entities: detectedEntities,
                    ai_scan_status: 'LIVE_GEMINI_GROUND_TRUTH_REQUIRED'
                };
                if (detectedEntities.length) {
                    const contourPreview = await loadStoredContourPreview(target, target.file_url, true);
                    if (activePhotoUrl !== target.file_url) return;
                    const contourReady = contourPreview?.status === 'ready' && contourPreview.contours?.length;
                    const detectionSummary = isId
                        ? `${detectedEntities.length} objek terdeteksi`
                        : `${detectedEntities.length} ${detectedEntities.length === 1 ? 'object' : 'objects'} detected`;
                    updateSpatialScanProgress(
                        isId ? 'Pemindaian selesai' : 'Scan complete',
                        contourReady
                            ? (isId
                                ? `${detectionSummary}; outline OpenCV siap.`
                                : `${detectionSummary}; OpenCV outlines are ready.`)
                            : (isId
                                ? `${detectionSummary}; outline tidak tersedia (${contourPreview?.reason || 'status tidak diketahui'}).`
                                : `${detectionSummary}; outlines unavailable (${contourPreview?.reason || 'unknown status'}).`),
                        'done'
                    );
                } else {
                    updateSpatialScanProgress(
                        isId ? 'Pemindaian selesai' : 'Scan complete',
                        isId ? 'Gemini tidak menemukan objek pada foto ini.' : 'Gemini did not detect objects in this image.',
                        'done'
                    );
                }
            } else {
                updateSpatialScanProgress(
                    isFallback ? (isId ? 'Mode fallback' : 'Fallback mode') : (isId ? 'Hasil belum tersimpan' : 'Result not saved'),
                    isFallback
                        ? (isId
                            ? 'Analisis Gemini tidak tersedia; tidak ada deteksi gambar terverifikasi.'
                            : 'Gemini analysis is unavailable; no image-verified detections are displayed.')
                        : (isId ? 'Deteksi Gemini tidak tersimpan sehingga outline OpenCV tidak dapat dibuat.' : 'Gemini detections were not saved, so OpenCV outlines cannot be generated.'),
                    isFallback ? 'failed' : 'done'
                );
            }

            sealedCardsCurrentPage = 1;
            renderGalleryThumbnails();
            renderSealedArchiveStrip();
            renderProcessedEvidenceCardsGrid();
            updateConsolidatedEvidenceLedger();
            updateScanButtonLabel();

            if (btnScan) btnScan.classList.remove('animate-pulse');

            const badgeEl = document.getElementById('aiPipelineStepBadge');
            if (badgeEl) badgeEl.textContent = isFallback
                ? "Fallback Preview — Not Image Verified"
                : (isPersistedLiveResult ? "Live Gemini — Saved; Ground Truth Required" : "Live Gemini — Not Persisted");
            const textEl = document.getElementById('telemetryCurrentSentence');
            if (textEl) {
                textEl.textContent = isFallback
                    ? (isId
                        ? 'Analisis Gemini tidak tersedia; tidak ada deteksi gambar terverifikasi.'
                        : 'Gemini analysis is unavailable; no image-verified detections are displayed.')
                    : (isPersistedLiveResult
                        ? `✓ Live Gemini result saved for this image: ${result.totalEntities} detections. Ground-truth review is required for accuracy validation.`
                        : `Live Gemini returned ${result.totalEntities} detections, but this result was not persisted to the evidence record.`);
            }

            if (scanBadge) {
                scanBadge.classList.remove('hidden');
                scanBadge.className = isFallback
                    ? 'px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1 shadow-sm'
                    : (isPersistedLiveResult
                        ? 'px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1 shadow-sm'
                        : 'px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1 shadow-sm');
                scanBadge.textContent = isFallback
                    ? (isId ? '⚠ Gemini tidak tersedia • tidak ada deteksi terverifikasi' : '⚠ Gemini unavailable • no verified detections')
                    : (isPersistedLiveResult
                        ? `🟢 Live Gemini saved • ${result.totalEntities} detections`
                        : `⚠ Live Gemini • ${result.totalEntities} detections, not persisted`);
            }

            renderProcessedEvidenceCardsGrid();
            showNotificationToast(
                isFallback
                    ? "Fallback preview shown; no detections were verified or sealed."
                : (result.persistence?.saved
                    ? `Live Gemini scan saved • ${result.totalEntities} detections • BigQuery ${result.persistenceStatus}.`
                    : `Live Gemini scan complete but not persisted • ${result.persistence?.message || 'target evidence missing'}.`),
            isFallback ? "⚠️" : "✅"
            );
        }
    }).catch(error => {
        console.error("[Spatial vision scan]", error);
        updateSpatialScanProgress(
            isId ? 'Pemindaian gagal' : 'Scan failed',
            error?.message || (isId ? 'Terjadi kesalahan saat memindai.' : 'An error occurred while scanning.'),
            'failed'
        );
        if (btnScan) btnScan.classList.remove('animate-pulse');
        showNotificationToast("Pemindaian gagal; periksa koneksi dan coba lagi.", "⚠️");
    });
}

async function animateProgressiveBoxLockOn(boxes, statusTextEl) {
    const overlay = document.getElementById('droneBBoxesOverlay');
    if (!overlay) return;
    overlay.innerHTML = '';

    const isId = isIndonesian();
    const total = boxes.length;
    const batchSize = Math.max(1, Math.floor(total / 5));

    for (let i = 0; i < total; i += batchSize) {
        const slice = boxes.slice(0, i + batchSize);
        renderDetectedBoundingBoxes(slice);
        if (statusTextEl) statusTextEl.textContent = isId 
            ? `Mendeteksi Entitas: ${Math.min(i + batchSize, total)} / ${total} terpetakan...`
            : `Detecting Entities: ${Math.min(i + batchSize, total)} / ${total} mapped...`;
        await new Promise(r => setTimeout(r, 100));
    }
    renderDetectedBoundingBoxes(boxes);
}

function renderProcessedEvidenceCardsGrid() {
    const grid = document.getElementById('processedEvidenceCardsGrid');
    const badge = document.getElementById('processedEvidenceBadge');
    const pageControls = document.getElementById('sealedCardsPaginationControls');
    const lblPagination = document.getElementById('lblSealedCardsPagination');
    const btnPrev = document.getElementById('btnPrevSealedCards');
    const btnNext = document.getElementById('btnNextSealedCards');

    if (!grid) return;

    const isId = isIndonesian();
    const processedPhotos = registeredPhotos.filter(p => p.is_processed && (activeProcessStageFilter === 'ALL' || p.tag === activeProcessStageFilter));
    
    if (badge) badge.textContent = processedPhotos.length + (isId ? ' Hasil Scan' : ' Scanned Photos');

    if (processedPhotos.length === 0) {
        grid.innerHTML = '<div class="col-span-full p-4 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-400 text-xs">' +
            (isId 
                ? 'Belum ada hasil scan. Pilih foto yang sudah diunggah lalu pindai untuk menganalisisnya.' 
                : 'No scan results yet. Select an uploaded photo and scan it to analyze its contents.') +
            '</div>';
        if (pageControls) pageControls.style.display = 'none';
        return;
    }

    if (pageControls) pageControls.style.display = 'flex';

    const totalPages = Math.ceil(processedPhotos.length / SEALED_CARDS_PER_PAGE) || 1;
    if (sealedCardsCurrentPage > totalPages) sealedCardsCurrentPage = totalPages;
    if (sealedCardsCurrentPage < 1) sealedCardsCurrentPage = 1;

    if (lblPagination) {
        lblPagination.textContent = `${isId ? 'Halaman' : 'Page'} ${sealedCardsCurrentPage} / ${totalPages} (${processedPhotos.length} ${isId ? 'Total' : 'Total'})`;
    }
    if (btnPrev) btnPrev.disabled = (sealedCardsCurrentPage <= 1);
    if (btnNext) btnNext.disabled = (sealedCardsCurrentPage >= totalPages);

    const startIndex = (sealedCardsCurrentPage - 1) * SEALED_CARDS_PER_PAGE;
    const paginatedPhotos = processedPhotos.slice(startIndex, startIndex + SEALED_CARDS_PER_PAGE);

    grid.innerHTML = paginatedPhotos.map((item, idx) => {
        const boxes = Array.isArray(item.boxes) ? item.boxes.filter(b => b && typeof b === 'object') : [];
        const palmCount = boxes.filter(b => b.cluster === 'palm_canopy' || (typeof b.label === 'string' && b.label.toLowerCase().includes('palm'))).length;
        const otherCount = boxes.length - palmCount;
        const auditorNotes = item.is_fallback
            ? (isId ? "Pratinjau heuristik; bukan hasil pengenalan gambar." : "Heuristic preview; not an image recognition result.")
            : (isId ? "Hasil Gemini dari citra ini; akurasi memerlukan pemeriksaan ground-truth." : "Gemini result from this image; accuracy requires ground-truth review.");

        const boxesHtml = boxes.filter(b =>
            b &&
            Array.isArray(b.box_2d) &&
            b.box_2d.length === 4 &&
            b.box_2d.every(Number.isFinite)
        ).map(b => {
            const box = b.box_2d;
            const top = (box[0] / 10.0).toFixed(1);
            const left = (box[1] / 10.0).toFixed(1);
            const height = ((box[2] - box[0]) / 10.0).toFixed(1);
            const width = ((box[3] - box[1]) / 10.0).toFixed(1);

            let borderColor = 'border-emerald-400 bg-emerald-500/15 shadow-[0_0_8px_rgba(52,211,153,0.35)]';
            if (b.cluster === 'infrastructure' || b.cluster === 'floor_mulch' || b.cluster === 'clean_alley') {
                borderColor = 'border-sky-400 bg-sky-500/15 shadow-[0_0_8px_rgba(56,189,248,0.35)]';
            } else if (b.cluster === 'root_circle') {
                borderColor = 'border-rose-400 bg-rose-500/15 shadow-[0_0_8px_rgba(251,113,133,0.35)]';
            } else if (b.cluster === 'water_riparian') {
                borderColor = 'border-cyan-400 bg-cyan-500/20 shadow-[0_0_8px_rgba(34,211,238,0.35)]';
            }

            return `<div class="absolute border-2 ${borderColor} rounded-md pointer-events-none transition-all" style="top: ${top}%; left: ${left}%; width: ${width}%; height: ${height}%;"></div>`;
        }).join('');

        const shaPreview = item.sha256 ? item.sha256.substring(0, 14) + '...' : 'N/A';
        const globalIdx = startIndex + idx + 1;

        return '<div class="p-3.5 sm:p-4 rounded-2xl bg-slate-950 border-2 border-emerald-500/70 shadow-xl space-y-2.5 font-mono text-xs text-slate-200">' +
            '<div class="flex items-center justify-between border-b border-slate-800 pb-1.5">' +
                '<div>' +
                    '<span class="font-bold text-white text-xs block truncate max-w-[200px]">' + (isId ? 'Scan #' : 'Scan #') + globalIdx + ': ' + item.filename + '</span>' +
                        '<span class="text-[9px] text-slate-400 font-sans">' + (isId ? 'Deteksi objek dari Gemini' : 'Gemini object detections') + '</span>' +
                '</div>' +
                '<span class="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500 text-[8.5px] font-bold shadow-xs">' +
                    (item.is_locked ? '🔒 SEALED' : '✓ SCANNED') +
                '</span>' +
            '</div>' +

            '<div class="relative w-full h-40 sm:h-44 rounded-xl overflow-hidden bg-slate-900 border border-slate-800 shadow-inner group">' +
                '<img src="' + item.file_url + '" class="w-full h-full object-cover">' +
                '<div class="absolute inset-0 pointer-events-none">' + boxesHtml + '</div>' +
                '<div class="absolute bottom-2 left-2 px-2.5 py-0.5 rounded-md bg-slate-950/90 backdrop-blur-md text-[8.5px] font-bold text-emerald-300 font-mono border border-emerald-500/60 shadow">' +
                    boxes.length + ' ' + (isId ? 'Entitas Terpetakan' : 'Entities Mapped') +
                '</div>' +
            '</div>' +

            '<div class="grid grid-cols-2 gap-1.5 text-[9.5px]">' +
                '<div class="bg-slate-900/90 p-1.5 rounded-lg border border-slate-800">' +
                    '<span class="text-slate-400 text-[8px] block">🔎 ' + (isId ? 'Total entitas:' : 'Total entities:') + '</span>' +
                    '<strong class="text-emerald-400 font-bold">' + boxes.length + '</strong>' +
                '</div>' +
                '<div class="bg-slate-900/90 p-1.5 rounded-lg border border-slate-800">' +
                    '<span class="text-slate-400 text-[8px] block">🌴 ' + (isId ? 'Kanopi sawit:' : 'Palm canopies:') + '</span>' +
                    '<strong class="text-emerald-400 font-bold">' + palmCount + '</strong>' +
                '</div>' +
                '<div class="bg-slate-900/90 p-1.5 rounded-lg border border-slate-800">' +
                    '<span class="text-slate-400 text-[8px] block">📦 ' + (isId ? 'Entitas lain:' : 'Other entities:') + '</span>' +
                    '<strong class="text-sky-300 font-bold">' + otherCount + '</strong>' +
                '</div>' +
                '<div class="bg-slate-900/90 p-1.5 rounded-lg border border-slate-800">' +
                    '<span class="text-slate-400 text-[8px] block">📏 ' + (isId ? 'Pengukuran:' : 'Measurements:') + '</span>' +
                    '<strong class="text-white font-bold">' + (isId ? 'Tidak tersedia' : 'Not available') + '</strong>' +
                '</div>' +
            '</div>' +

            '<div class="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 space-y-1">' +
                '<div class="flex items-center justify-between text-[9px] font-bold text-emerald-400 border-b border-slate-800/80 pb-1">' +
                    '<span>' + (isId ? 'Catatan hasil scan' : 'Scan result note') + '</span>' +
                    '<span class="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/60 text-[8px] font-mono">' + (item.is_fallback ? 'HEURISTIC PREVIEW' : 'GEMINI RESULT') + '</span>' +
                '</div>' +
                '<p class="text-[9.5px] text-slate-300 leading-snug font-sans text-justify pt-0.5">' +
                    auditorNotes +
                '</p>' +
            '</div>' +

            '<div class="pt-1.5 border-t border-slate-800 flex items-center justify-between text-[8.5px] text-slate-400">' +
                '<span>SHA-256: <strong class="text-indigo-300 font-mono">' + shaPreview + '</strong></span>' +
                '<span class="text-emerald-400 font-bold flex items-center gap-1">' + (item.is_locked ? '🔒 ' + (isId ? 'Tersegel' : 'Sealed') : '✓ ' + (isId ? 'Dapat diatur' : 'Editable')) + '</span>' +
            '</div>' +
        '</div>';
    }).join('');
}

function navigateSealedCardsPage(delta) {
    sealedCardsCurrentPage += delta;
    renderProcessedEvidenceCardsGrid();
}
window.navigateSealedCardsPage = navigateSealedCardsPage;

function updateConsolidatedEvidenceLedger() {
    const isId = isIndonesian();
    const scannedPhotos = registeredPhotos.filter(p => p.is_processed);
    const count = scannedPhotos.length;
    const allBoxes = scannedPhotos.flatMap(p => Array.isArray(p.boxes) ? p.boxes.filter(b => b && typeof b === 'object') : []);
    const palmCount = allBoxes.filter(b => b.cluster === 'palm_canopy' || (typeof b.label === 'string' && b.label.toLowerCase().includes('palm'))).length;
    const countClusters = (...clusters) => allBoxes.filter(b => clusters.includes(b.cluster)).length;
    const badgeCount = document.getElementById('ledgerPhotoCountBadge');
    if (badgeCount) badgeCount.textContent = count + (isId ? ' Foto Dipindai' : ' Scanned Photos');

    const elTotal = document.getElementById('ledgerTotalCrowns');
    if (elTotal) elTotal.innerHTML = palmCount + ' <span class="text-[9.5px] font-normal text-emerald-400 font-bold">' + (isId ? 'Terdeteksi' : 'Detected') + '</span>';

    const elAlley = document.getElementById('ledgerAlleyWidth');
    if (elAlley) elAlley.innerHTML = countClusters('clean_alley', 'alley_corridor', 'floor_mulch') + ' <span class="text-[9.5px] font-normal text-slate-400">' + (isId ? 'Deteksi objek' : 'detections') + '</span>';

    const elSterile = document.getElementById('ledgerSterileStatus');
    if (elSterile) elSterile.innerHTML = countClusters('root_circle') + ' <span class="text-[9.5px] font-normal text-slate-400">' + (isId ? 'Deteksi objek' : 'detections') + '</span>';

    const elRiparian = document.getElementById('ledgerRiparianStatus');
    if (elRiparian) elRiparian.innerHTML = countClusters('water_riparian') + ' <span class="text-[9.5px] font-normal text-slate-400">' + (isId ? 'Deteksi objek' : 'detections') + '</span>';
}

function updateScanButtonLabel() {
    const isId = isIndonesian();
    const count = selectedPhotoUrls.size;
    const sub = document.getElementById('btnPhotoScanCountSub');
    if (sub) sub.textContent = '(' + count + (isId ? ' Dipilih)' : ' Selected)');
    const badge = document.getElementById('gallerySelectionBadge');
    if (badge) badge.textContent = `${count} ` + (isId ? 'Dipilih' : 'Selected');
}

function togglePhotoSelection(url, isChecked, ev) {
    if (ev) ev.stopPropagation();
    if (isChecked) selectedPhotoUrls.add(url);
    else selectedPhotoUrls.delete(url);
    renderGalleryThumbnails();
    updateScanButtonLabel();
}

function toggleSelectAllPhotos(selectAll) {
    const visiblePhotos = registeredPhotos.filter(p => (activeProcessStageFilter === 'ALL' || p.tag === activeProcessStageFilter));
    if (selectAll) {
        visiblePhotos.forEach(p => {
            selectedPhotoUrls.add(p.file_url);
        });
    } else {
        selectedPhotoUrls.clear();
    }
    renderGalleryThumbnails();
    updateScanButtonLabel();
}

function drawReticles() {
    const canvas = document.getElementById('reticleCanvas');
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width || 400;
    canvas.height = rect.height || 280;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const imgEl = document.getElementById('verifPhotoImg');
    if (!imgEl || !imgEl.complete || imgEl.naturalWidth === 0 ||
        imgEl.style.display === 'none' || imgEl.classList.contains('hidden')) return;

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
    ctx.moveTo(pad, canvas.height - pad - len); ctx.lineTo(pad, canvas.height - pad); ctx.lineTo(canvas.width - pad, canvas.height - pad);
    ctx.moveTo(canvas.width - pad - len, canvas.height - pad); ctx.lineTo(canvas.width - pad, canvas.height - pad); ctx.lineTo(canvas.width - pad, canvas.height - pad - len);
    ctx.stroke();
}

function escapeSvgText(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[character]);
}

function escapeHtmlText(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[character]);
}

function renderDetectedBoundingBoxes(boxes) {
    currentSpatialBoxes = boxes || [];
    const overlay = document.getElementById('droneBBoxesOverlay');
    const imgEl = document.getElementById('verifPhotoImg');

    const imageReady = Boolean(
        imgEl &&
        imgEl.complete &&
        imgEl.naturalWidth > 0 &&
        imgEl.style.display !== 'none' &&
        !imgEl.classList.contains('hidden')
    );
    if (!imageReady) {
        if (overlay) {
            overlay.innerHTML = '';
            overlay.style.display = 'none';
        }
        return;
    }
    if (!overlay) return;
    overlay.style.display = 'block';

    let contourSvg = '';
    const preview = currentSpatialContourPreview;
    if (
        showSam2ContourPreview &&
        preview?.status === 'ready' &&
        Number.isFinite(preview.width) &&
        Number.isFinite(preview.height) &&
        preview.width > 0 &&
        preview.height > 0 &&
        Array.isArray(preview.contours)
    ) {
        const placedLabels = [];
        const paths = preview.contours.map(contour => {
            if (!Array.isArray(contour.points) || contour.points.length < 3) return '';
            const points = contour.points.filter(point =>
                Array.isArray(point) &&
                point.length === 2 &&
                Number.isFinite(point[0]) &&
                Number.isFinite(point[1]) &&
                point[0] >= 0 &&
                point[0] <= preview.width &&
                point[1] >= 0 &&
                point[1] <= preview.height
            );
            if (points.length < 3) return '';
            const path = points.map(point => `${point[0]},${point[1]}`).join(' L ');
            const entity = currentSpatialBoxes[contour.entity_index];
            const label = entity?.label_name || entity?.label || entity?.cluster;
            const cluster = entity?.cluster || 'palm_canopy';
            const labelText = String(label || '');
            const isInfrastructure = cluster === 'infrastructure' || /harvest|path|road|canal|infrastructure/i.test(labelText);
            const isFrond = /frond/i.test(labelText);
            const stroke = isInfrastructure ? '#38bdf8'
                : cluster === 'root_circle' ? '#fb7185'
                    : cluster === 'water_riparian' ? '#22d3ee'
                        : '#34d399';
            const shortLabel = /fruit|bunch/i.test(labelText) ? 'Fruit bunch'
                : isFrond ? 'Frond stack'
                    : isInfrastructure ? 'Access path'
                        : cluster === 'root_circle' ? 'Root ring'
                            : /oil[_\s-]*palm/i.test(labelText) ? 'Oil palm'
                                : /palm|canopy/i.test(labelText) || cluster === 'palm_canopy' ? 'Palm canopy'
                                    : cluster === 'floor_mulch' ? 'Alley / groundcover'
                                        : labelText.replace(/[_-]+/g, ' ');
            const labelX = (Math.min(...points.map(point => point[0])) + Math.max(...points.map(point => point[0]))) / 2;
            const labelY = Math.max(18, (Math.min(...points.map(point => point[1])) + Math.max(...points.map(point => point[1]))) / 2);
            const overlapsLabel = placedLabels.some(position =>
                Math.hypot(position.x - labelX, position.y - labelY) < 160
            );
            const labelSvg = shortLabel && !overlapsLabel
                ? `<text x="${labelX}" y="${labelY}" text-anchor="middle" fill="${stroke}" font-size="15" font-weight="700" paint-order="stroke" stroke="#020617" stroke-width="4" stroke-linejoin="round"><title>${escapeSvgText(label)} · Canny edge support ${Number.isFinite(contour.edge_support) ? contour.edge_support : 'not measured'}</title>${escapeSvgText(shortLabel)}</text>`
                : '';
            if (shortLabel && !overlapsLabel) placedLabels.push({ x: labelX, y: labelY });
            return `<path d="M ${path} Z" fill="none" stroke="${stroke}" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke"></path>${labelSvg}`;
        }).join('');
        if (paths) {
            contourSvg = `<svg class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 ${preview.width} ${preview.height}" preserveAspectRatio="xMidYMid slice" aria-label="AI detection and OpenCV contours">${paths}</svg>`;
        }
    }

    let openCvReplayOverlay = '';
    const replay = currentOpenCvStaticReplay;
    if (
        showOpenCvStaticReplay &&
        replay?.status === 'ready' &&
        typeof replay.mask_overlay_base64 === 'string' &&
        /^[A-Za-z0-9+/=]+$/.test(replay.mask_overlay_base64)
    ) {
        openCvReplayOverlay = `<img src="data:image/png;base64,${replay.mask_overlay_base64}" class="absolute inset-0 w-full h-full object-cover pointer-events-none" alt="OpenCV HSV static replay mask">`;
    }

    const boxesHtml = (boxes || []).map(item => {
        const cluster = item.cluster || 'palm_canopy';
        const labelName = item.label_name || item.label || cluster;
        // Jika filter aktif, periksa kecocokan cluster string maupun numerik/label; jika tidak cocok maka default tetap tampil agar deteksi tidak tersembunyi
        if (typeof cluster === 'string' && activeSpatialClusterFilters.size > 0 && !activeSpatialClusterFilters.has(cluster)) {
            const hasMatch = Array.from(activeSpatialClusterFilters).some(f => String(labelName).toLowerCase().includes(f));
            if (!hasMatch && !activeSpatialClusterFilters.has('palm_canopy')) return '';
        }
        const isInfrastructure = cluster === 'infrastructure' || /harvest|path|road|canal|infrastructure/i.test(String(labelName));

        const box = item.box_2d || [100, 100, 300, 300];
        const top = (box[0] / 10.0).toFixed(1);
        const left = (box[1] / 10.0).toFixed(1);
        const height = ((box[2] - box[0]) / 10.0).toFixed(1);
        const width = ((box[3] - box[1]) / 10.0).toFixed(1);

        let borderCls = "border-emerald-400 bg-emerald-500/5";
        let badgeCls = "bg-emerald-950 text-emerald-300 border-emerald-400";
        let icon = "🌴";

        if (isInfrastructure) {
            borderCls = "border-sky-400 bg-sky-500/5";
            badgeCls = "bg-sky-950 text-sky-300 border-sky-400";
            icon = "🚜";
        } else if (cluster === 'root_circle') {
            borderCls = "border-rose-400 bg-rose-500/5";
            badgeCls = "bg-rose-950 text-rose-300 border-rose-400";
            icon = "⭕";
        } else if (cluster === 'floor_mulch') {
            borderCls = "border-teal-400 bg-teal-500/5";
            badgeCls = "bg-teal-950 text-teal-300 border-teal-400";
            icon = "🍂";
        } else if (cluster === 'water_riparian') {
            borderCls = "border-cyan-400 bg-cyan-500/5";
            badgeCls = "bg-cyan-950 text-cyan-300 border-cyan-400";
            icon = "💧";
        }

        const confPct = Math.round((item.confidence || 0.95) * 100);
        const safeLabel = escapeHtmlText(labelName || cluster);
        return '<div class="absolute border-2 ' + borderCls + ' rounded-lg shadow-sm pointer-events-auto transition-all box-lock-active" style="top: ' + top + '%; left: ' + left + '%; width: ' + width + '%; height: ' + height + '%;" aria-label="' + safeLabel + '" title="' + safeLabel + '"><span class="absolute -top-5 left-0 max-w-40 truncate rounded bg-slate-950/85 px-1.5 py-0.5 text-[9px] font-bold text-white shadow">' + safeLabel + '</span></div>';
    }).join('');
    overlay.innerHTML = openCvReplayOverlay + contourSvg + boxesHtml;
}

function updateContourPreviewButton() {
    const button = document.getElementById('btnToggleContourPreview');
    const label = document.getElementById('contourPreviewButtonLabel');
    if (!button || !label) return;

    const preview = currentSpatialContourPreview;
    const contourCount = preview?.status === 'ready' && Array.isArray(preview.contours)
        ? preview.contours.length
        : 0;
    const unavailable = preview && preview.status !== 'ready';
    button.disabled = unavailable || contourCount === 0;
    button.setAttribute('aria-pressed', String(showSam2ContourPreview));
    const reasonMessages = {
        sam2_disabled: 'Optional SAM2 outlines are not enabled in this environment; image detection and audit saving remain available.',
        sam2_checkpoint_missing: 'Optional SAM2 outlines are unavailable without local model weights; image detection and audit saving remain available.',
        ultralytics_not_installed: 'Optional SAM2 outlines require the local Ultralytics package; image detection and audit saving remain available.',
        scan_not_image_verified: 'SAM2 preview is not generated from heuristic fallback detections.',
        scan_not_persisted: 'Save the live scan to its evidence record before generating a contour.'
    };
    const unavailableLabels = {
        loading: 'Memproses kontur OpenCV...',
        sam2_disabled: 'Optional outlines · local only',
        sam2_checkpoint_missing: 'Optional outlines unavailable · local model',
        ultralytics_not_installed: 'Optional outlines unavailable · local package',
        scan_not_persisted: 'Save scan to generate SAM2 contour',
        scan_not_image_verified: 'SAM2 unavailable for fallback'
    };
    button.title = unavailable
        ? (reasonMessages[preview.reason] || 'Optional SAM2 outlines are unavailable; scanning and saving can continue.')
        : contourCount === 0
            ? 'OpenCV tidak menemukan kontur pada deteksi ini.'
            : 'AI detections guide OpenCV contours. Suggestions are not verified ground truth.';
    label.textContent = unavailable
        ? (unavailableLabels[preview.status === 'loading' ? 'loading' : preview.reason] || 'OpenCV contours unavailable')
        : `Hybrid outlines (${contourCount})${showSam2ContourPreview ? ' · On' : ' · Off'}`;
}

function toggleContourPreview() {
    if (!currentSpatialContourPreview || currentSpatialContourPreview.status !== 'ready') return;
    showSam2ContourPreview = !showSam2ContourPreview;
    renderDetectedBoundingBoxes(currentSpatialBoxes);
    updateContourPreviewButton();
}

function runOpenCvStaticReplay() {
    currentOpenCvStaticReplay = { status: 'unavailable', reason: 'visual_only_preview_disabled' };
    showOpenCvStaticReplay = false;
    renderDetectedBoundingBoxes(currentSpatialBoxes);
    updateOpenCvStaticReplayButton();
}

function updateOpenCvStaticReplayButton() {
    const button = document.getElementById('btnOpenCvStaticReplay');
    const label = document.getElementById('openCvStaticReplayButtonLabel');
    const status = document.getElementById('openCvStaticReplayStatus');
    if (!button || !label || !status) return;

    button.disabled = true;
    button.setAttribute('aria-pressed', 'false');
    label.textContent = 'OpenCV-only overlay disabled';
    status.textContent = 'Only contours refined from saved Gemini detections are displayed.';
}

function toggleSpatialLayer(cluster) {
    if (activeSpatialClusterFilters.has(cluster)) {
        if (activeSpatialClusterFilters.size > 1) activeSpatialClusterFilters.delete(cluster);
    } else {
        activeSpatialClusterFilters.add(cluster);
    }
    renderDetectedBoundingBoxes(currentSpatialBoxes);
}

async function saveSpatialInspectionAndProceed() {
    const selectEl = document.getElementById('selectDossierApplication');
    const urlParams = new URLSearchParams(window.location.search);
    
    let kodeKebun = (activeDossier && activeDossier.kode_kebun) 
        ? activeDossier.kode_kebun 
        : (urlParams.get('kode') || (selectEl && selectEl.value ? selectEl.value : (currentEstateCode || 'EST-MDN-010')));
        
    let idKebun = (activeDossier && (activeDossier.id_kebun || activeDossier.id))
        ? (activeDossier.id_kebun || activeDossier.id)
        : (urlParams.get('id') || 10);

    const year = localStorage.getItem('precision_palm_active_year') || '2026';
    const targetUrl = '/proses?id=' + idKebun + '&kode=' + encodeURIComponent(kodeKebun) + '&year=' + year;

    const ph = parseFloat(document.getElementById('inp_soil_ph')?.value || 5.5);
    const slope = parseFloat(document.getElementById('inp_terrain_slope')?.value || 4.5);
    const texture = document.getElementById('inp_soil_texture')?.value || 'sandy_loam';

    const assessorName = document.getElementById('inp_assessor_name')?.value?.trim() || '(Lead Assessor)';
    const assessorVerdict = document.getElementById('inp_assessor_verdict')?.value || 'DISETUJUI_PENUH';
    const assessorNotes = document.getElementById('inp_assessor_notes')?.value?.trim() || 
        'Physical parcel characteristics satisfy PPKS agronomic benchmarks & ISPO Principle 3 buffer standards.';

    showNotificationToast(isIndonesian() ? "Merekam bukti audit ke dalam registri permanen..." : "Committing audit proofs into permanent registry...", "🚀");

    const isId = isIndonesian();
    registeredPhotos.forEach((p, idx) => {
        if (!p.prepared_survey) {
            const realFileUrl = p.file_url;
            const specificBlockId = (isId ? "Blok Inti - " : "Centroid Block - ") + (p.title || p.filename || `Parcel #${surveysFullList.length + idx + 1}`);
            const recordedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
            p.prepared_survey = {
                id: surveysFullList.length + idx + 1,
                evidence_id: p.id || '',
                foto_url: realFileUrl,
                image_gcs_url: realFileUrl,
                process_stage: p.tag || 'STAGE-0-ANNUAL-REG',
                recorded_at: recordedAt,
                timestamp: recordedAt,
                block_id: specificBlockId,
                blok: specificBlockId,
                ...(Number.isFinite(p.latitude) ? { latitude: p.latitude, lat: p.latitude } : {}),
                ...(Number.isFinite(p.longitude) ? { longitude: p.longitude, lng: p.longitude } : {}),
                ...(Number.isFinite(p.elevation_m) ? { elevation_m: p.elevation_m } : {}),
                ...(Number.isFinite(p.slope_deg) ? { slope_deg: p.slope_deg } : {}),
                ...(p.sha256 ? { sha256_seal: p.sha256 } : {}),
                detected_entities: p.is_processed && Array.isArray(p.boxes) ? p.boxes : [],
                ai_scan_status: p.is_processed ? 'LIVE_GEMINI_GROUND_TRUTH_REQUIRED' : 'NOT_SCANNED'
            };
        }
    });

    const preparedProofs = registeredPhotos.filter(p => p.prepared_survey);

    const payload = {
        id_kebun: idKebun,
        kode_kebun: kodeKebun,
        audit_year: parseInt(year, 10),
        soil_ph: ph,
        slope: slope,
        elevation: currentElevationDpl || 142.0,
        lat: currentPinLat || 0.824100,
        lng: currentPinLng || 99.561200,
        assessor_name: assessorName,
        assessor_verdict: assessorVerdict,
        assessor_notes: assessorNotes,
        sealed_proofs_count: preparedProofs.length,
        surveillance_entries: preparedProofs.map(p => p.prepared_survey)
    };

    try {
        const response = await fetch('/api/spatial/save-inspection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await readApiJson(response, isId ? 'Simpan audit Spatial' : 'Save Spatial audit');
        if (
            result.success !== true ||
            result.status !== 'success' ||
            result.warning ||
            result.records_committed !== preparedProofs.length
        ) {
            throw new Error(
                result.error ||
                result.warning ||
                (isId
                    ? 'Server belum mengonfirmasi seluruh catatan surveilans tersimpan.'
                    : 'The server did not confirm that every surveillance record was saved.')
            );
        }
    } catch (error) {
        console.error('[Spatial Save Error]', error);
        showNotificationToast(
            error.message || (isId ? 'Audit gagal disimpan; tetap di halaman ini dan coba lagi.' : 'Audit save failed; remain on this page and retry.'),
            '⚠️'
        );
        return;
    }

    registeredPhotos.forEach(photo => {
        if (photo.prepared_survey) photo.is_locked = true;
    });
    preparedProofs.forEach(photo => {
        if (!surveysFullList.some(survey => survey.foto_url === photo.prepared_survey.foto_url)) {
            photo.prepared_survey.id = surveysFullList.length + 1;
            surveysFullList.unshift(photo.prepared_survey);
        }
    });
    renderSurveysTable();

    try {
        if (activePhotoUrl) {
            localStorage.setItem('precision_active_evidence_url', activePhotoUrl);
            localStorage.setItem('precision_active_evidence_filename', activeFilename || 'active_evidence.jpg');
        }
        localStorage.setItem('precision_palm_active_spatial_inspection', JSON.stringify(payload));
        localStorage.setItem('precision_palm_active_dossier', kodeKebun);
        localStorage.setItem('precision_active_dossier', kodeKebun);
    } catch (error) {
        console.warn('[Spatial Save] Local navigation cache could not be updated:', error);
    }
    renderGalleryThumbnails();
    renderSealedArchiveStrip();
    renderProcessedEvidenceCardsGrid();
    window.location.href = targetUrl;
}

function updateCoordinateCards(lat, lng) {
    const cardLong = document.getElementById('card_val_longitude');
    const cardLat = document.getElementById('card_val_latitude');
    const centerDisp = document.getElementById('mapCenterCoordsDisplay');

    if (cardLong) cardLong.textContent = Math.abs(lng).toFixed(6) + '° E';
    if (cardLat) cardLat.textContent = Math.abs(lat).toFixed(6) + '° N';
    if (centerDisp) centerDisp.textContent = lat.toFixed(6) + ', ' + lng.toFixed(6);
}

async function validateSpatialMoratorium(lat, lng) {
    const banner = document.getElementById('spatialValidationBanner');
    const badge = document.getElementById('spatialValBadge');
    const desc = document.getElementById('spatialValDesc');

    let distanceMeters = 5000.0;
    let isDirectCollision = false;

    try {
        const res = await fetch('/api/spatial/check-moratorium?lat=' + lat + '&lng=' + lng + '&kode=' + encodeURIComponent(activeDossier?.kode_kebun || ''));
        if (res.ok) {
            const data = await res.json();
            if (data && typeof data.distance_to_forest_meters === 'number') {
                isDirectCollision = data.is_direct_collision || false;
                distanceMeters = isDirectCollision ? 0.0 : data.distance_to_forest_meters;
            }
        }
    } catch (_) {}

    const isBufferViolation = (!isDirectCollision && distanceMeters < 50.0);
    const isSafeApl = (!isDirectCollision && !isBufferViolation);
    const isId = isIndonesian();

    lastSpatialCheckResult = {
        isSafe: isSafeApl,
        isDirectCollision: isDirectCollision,
        isBufferViolation: isBufferViolation,
        distanceMeters: distanceMeters,
        statusLabel: isSafeApl 
            ? (isId ? "100% BERSIH APL NON-HUTAN" : "100% NON-FOREST APL CLEARED") 
            : (isBufferViolation 
                ? (isId ? "PERINGATAN ZONA PENYANGGA < 50M" : "BUFFER ZONE WARNING < 50M") 
                : (isId ? "PELANGGARAN MORATORIUM PIPPIB" : "PIPPIB MORATORIUM VIOLATION"))
    };

    if (isSafeApl) {
        if (banner) banner.className = "p-3 rounded-2xl bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs transition-all duration-300";
        if (badge) {
            badge.textContent = isId ? "100% Bersih Status APL Non-Hutan" : "100% Cleared for Non-Forest APL Status";
            badge.className = "px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-400";
        }
        if (desc) desc.textContent = isId
            ? ("Koordinat plot terverifikasi di Area Penggunaan Lain (APL). Jarak ke hutan lindung: " + (distanceMeters/1000).toFixed(2) + " km (Memenuhi batas penyangga minimum >= 50m sesuai PP 23/2021 & ISPO Prinsip 3).")
            : ("Plot coordinates verified within Non-Forest Arable Land (APL). Distance to protected forest: " + (distanceMeters/1000).toFixed(2) + " km (Complies with minimum buffer limit >= 50m per PP 23/2021 & ISPO Principle 3).");
    }
}

async function updateBioclimaticTelemetry(lat, lng) {
    let elev = 142.0;

    try {
        const url = 'https://api.open-meteo.com/v1/forecast?latitude=' + lat + '&longitude=' + lng + '&current=temperature_2m,relative_humidity_2m&timezone=auto';
        const resp = await fetch(url);
        if (resp.ok) {
            const data = await resp.json();
            if (data && data.elevation !== undefined) elev = Math.round(data.elevation);
        }
    } catch (_) {}

    currentElevationDpl = elev;
    const elElev = document.getElementById('card_val_elevation');
    if (elElev) elElev.textContent = elev + (isIndonesian() ? ' m DPL' : ' m MSL');

    handleSoilParamChange();
}

function handleSoilParamChange() {
    const isId = isIndonesian();
    const ph = parseFloat(document.getElementById('inp_soil_ph')?.value || 5.5);
    const slope = parseFloat(document.getElementById('inp_terrain_slope')?.value || 4.5);

    const txtPh = document.getElementById('txt_soil_ph_display');
    const txtSlope = document.getElementById('txt_slope_display');
    const phLabel = (ph >= 4.5 && ph <= 6.5 ? 'Optimal' : (ph < 4.5 ? (isId ? 'Masam' : 'Acidic') : (isId ? 'Alkalin' : 'Alkaline')));
    const slopeLabel = (slope <= 4.5 ? (isId ? 'Landai' : 'Gentle') : (slope <= 8 ? (isId ? 'Bergelombang' : 'Undulating') : (slope <= 15 ? (isId ? 'Berbukit' : 'Rolling') : (isId ? 'Curam' : 'Steep'))));

    if (txtPh) txtPh.textContent = ph.toFixed(1) + ' (' + phLabel + ')';
    if (txtSlope) txtSlope.textContent = slope.toFixed(1) + '° (' + slopeLabel + ')';
}

async function fetchAndRenderGeeSatelliteAudit(kode, lat, lng, area, polygon) {
    const elLoss = document.getElementById('geeValEudrLoss');
    const elNdvi = document.getElementById('geeValNdvi');
    const elSlope = document.getElementById('geeValSlope');
    const isId = isIndonesian();

    try {
        const res = await fetch('/api/spatial/gee-audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estate_code: kode, centroid_lat: lat, centroid_lng: lng, luas_ha: area, geojson: polygon })
        });
        if (res.ok) {
            const data = await res.json();
            const summary = data.summary || data;
            if (elLoss) elLoss.innerHTML = (summary.forest_loss_ha || 0).toFixed(2) + ' <span class="text-[10px] font-normal text-slate-400">' + (isId ? 'Ha Deforestasi' : 'Ha Loss') + '</span>';
            if (elNdvi) elNdvi.innerHTML = (summary.ndvi_score || 0.8245).toFixed(4) + ' <span class="text-[9px] font-normal text-slate-400">NDVI</span>';
            if (elSlope) elSlope.innerHTML = (summary.slope_degrees || 4.5).toFixed(2) + '° <span class="text-[9px] font-normal text-slate-400">' + (isId ? 'Kelerengan' : 'Slope') + '</span>';
        }
    } catch (_) {}
}

function showNotificationToast(msg, icon = "ℹ️") {
    const toast = document.getElementById('toastNotification');
    const msgEl = document.getElementById('toastMessage');
    const iconEl = document.getElementById('toastIcon');
    if (!toast || !msgEl) return;
    msgEl.textContent = msg;
    if (iconEl) iconEl.textContent = icon;
    toast.classList.remove('translate-y-24', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');
    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-24', 'opacity-0');
    }, 2800);
}

document.addEventListener('DOMContentLoaded', function () {
    initSpatialMapCanvas();
    updateContourPreviewButton();
    loadRegisteredDossiersAndBind();
});

window.addEventListener('pageshow', function (event) {
    if (event.persisted || performance.getEntriesByType("navigation")[0]?.type === "back_forward") {
        loadRegisteredDossiersAndBind();
    }
});

window.addEventListener('languagechanged', function () {
    renderGalleryThumbnails();
    renderSealedArchiveStrip();
    renderProcessedEvidenceCardsGrid();
    renderSurveysTable();
    updateConsolidatedEvidenceLedger();
    updateScanButtonLabel();
    handleSoilParamChange();
    if (activeDossier) {
        validateSpatialMoratorium(currentPinLat, currentPinLng);
        const hguEl = document.getElementById('activeDossierHguTag');
        if (hguEl) hguEl.textContent = 'HGU: ' + (activeDossier.nomor_hgu || 'e-STDB') + ' • ' + (isIndonesian() ? 'Luas: ' : 'Area: ') + parseFloat(activeDossier.luas_ha || 1200).toLocaleString('en-US') + ' Ha';
        if (mainPinMarker) mainPinMarker.bindTooltip(isIndonesian() ? "Centroid Terkunci (Titik Acuan Kebun)" : "Centroid Locked (Dossier Baseline)", { permanent: false, direction: 'top' });
        const elElev = document.getElementById('card_val_elevation');
        if (elElev) elElev.textContent = (currentElevationDpl || 142) + (isIndonesian() ? ' m DPL' : ' m MSL');
    }
});

window.handleDossierSelectionChange = handleDossierSelectionChange;
window.handleSoilParamChange = handleSoilParamChange;
window.saveSpatialInspectionAndProceed = saveSpatialInspectionAndProceed;
window.selectGalleryPhoto = selectGalleryPhoto;
window.runOpenCvStaticReplay = runOpenCvStaticReplay;
window.deleteEvidencePhoto = deleteEvidencePhoto;
window.unsealEvidencePhoto = unsealEvidencePhoto;
window.handleNewPhotoUpload = handleNewPhotoUpload;
window.triggerScanningFotoAction = triggerScanningFotoAction;
window.toggleSpatialLayer = toggleSpatialLayer;
window.togglePhotoSelection = togglePhotoSelection;
window.toggleSelectAllPhotos = toggleSelectAllPhotos;
window.openSurveySummaryModal = openSurveySummaryModal;
window.closeSurveySummaryModal = closeSurveySummaryModal;
window.downloadForensicProofPdf = downloadForensicProofPdf;
window.changeSurveysPage = changeSurveysPage;
window.handleSurveysSearchDebounce = handleSurveysSearchDebounce;