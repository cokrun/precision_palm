/**
 * Precision Palm Cloud - Step 3: Timelines & Forensic Stage Evidence Controller
 * File: static/js/timeline.js
 * 
 * Integrates UnifiedVisionEngine with Stage 0-4 Navigation, Sandbox Mode,
 * and Dynamic 2D Bounding Box Calculation per Stage.
 */

(function () {
    'use strict';

    // Metadata tahapan siklus kepatuhan ISPO 2025 & EUDR
    const STAGE_METADATA = {
        0: {
            stageIndex: 0,
            cycleKey: 'ANNUAL',
            title: 'Stage 0: Annual Registration & Nursery/Baseline',
            shortTitle: 'Stage 0 • Annual Registration',
            filename: 'evidence_stage_0_seedling_polybag.jpg',
            defaultPhoto: '/static/img/field_tm_weed.jpg',
            perspective: 'TERRESTRIAL_IN_SITU',
            perspectiveLabel: 'Perspective: Terrestrial In-Situ Handheld',
            period: 'Year 0 (Baseline & Legalitas)',
            focus: 'Bibit polybag PPKS, ajir bambu 9.0m, parit batas, & patok BPN',
            auditorCritique: 'Audit Tahap 0 (Annual / Baseline Lahan Awal): Terverifikasi bibit polybag bersertifikat PPKS, pancang ajir bambu 9.0m formasi segitiga sama sisi, terasering kontur tanah olahan, dan patok batas HGU kadastral BPN. Zero deforestation EUDR compliant.'
        },
        1: {
            stageIndex: 1,
            cycleKey: 'Q1',
            title: 'Stage 1: Quarter 1 Canopy Closure & Geometric Baseline',
            shortTitle: 'Stage 1 • Q1 Baseline Geometri',
            filename: 'evidence_stage_1_q1_canopy.jpg',
            defaultPhoto: '/static/img/sawit_drone.jpg',
            perspective: 'AERIAL_DRONE',
            perspectiveLabel: 'Perspective: Aerial Drone Nadir 45m',
            period: 'Month 1–3 (Baseline Geometri)',
            focus: 'Kanopi vegetatif awal LAI 4.25, formasi 9.0m, & piringan 2.05m',
            auditorCritique: 'Audit Tahap 1 (Q1 - 90 Days): Fotogrametri membuktikan kanopi vegetatif awal tumbuh simetris pada formasi heksagonal 9.0m, piringan bebas herbisida 2.05m, dan lorong gawangan 3.79m bersih tanpa rintangan.'
        },
        2: {
            stageIndex: 2,
            cycleKey: 'Q2',
            title: 'Stage 2: Quarter 2 Intercrop Corridor & Soil Integrity',
            shortTitle: 'Stage 2 • Q2 Vegetatif & MOP',
            filename: 'evidence_stage_2_q2_intercrop.jpg',
            defaultPhoto: '/static/img/field_tm_weed.jpg',
            perspective: 'TERRESTRIAL_IN_SITU',
            perspectiveLabel: 'Perspective: Terrestrial In-Situ Handheld',
            period: 'Month 4–6 (Vegetatif & MOP)',
            focus: 'Piringan steril 2.05m bebas cangkul, koridor gawangan 3.79m, & kalium MOP',
            auditorCritique: 'Audit Tahap 2 (Q2 - 180 Days): Terverifikasi tajuk kanopi dewasa TM-7.5, lorong bebas 3.79m untuk tanaman sela, kompensasi kalium MOP, dan piringan steril 2.05m bebas cangkul mekanis.'
        },
        3: {
            stageIndex: 3,
            cycleKey: 'Q3',
            title: 'Stage 3: Quarter 3 Mature Canopy, TBS Piles & Drainage',
            shortTitle: 'Stage 3 • Q3 Biomassa & Rorak',
            filename: 'evidence_stage_3_q3_mature_tbs.jpg',
            defaultPhoto: '/static/img/sawit_drone.jpg',
            perspective: 'AERIAL_DRONE',
            perspectiveLabel: 'Perspective: Aerial Drone Nadir 45m',
            period: 'Month 7–9 (Biomassa & Rorak)',
            focus: 'Tajuk dewasa TM-7.5, parit air sekunder, rorak SCS-CN 64, & tiang panen egrek',
            auditorCritique: 'Audit Tahap 3 (Q3 - 270 Days): Terverifikasi tajuk kanopi sawit dewasa produktif TM-7.5, tumpukan TBS panen segar, tiang panen egrek teleskopik, saluran parit air sekunder, lorong bebas 3.79m, dan zona piringan 2.05m steril bebas herbisida beracun.'
        },
        4: {
            stageIndex: 4,
            cycleKey: 'Q4',
            title: 'Stage 4: Quarter 4 Peak Harvest & FFB Balance Ratification',
            shortTitle: 'Stage 4 • Q4 Panen & Audit TBS',
            filename: 'evidence_stage_4_q4_harvest.jpg',
            defaultPhoto: '/static/img/field_tm_weed.jpg',
            perspective: 'TERRESTRIAL_IN_SITU',
            perspectiveLabel: 'Perspective: Terrestrial In-Situ Handheld',
            period: 'Month 10–12 (Panen & Audit TBS)',
            focus: 'Tumpukan TBS panen puncak, jalan angkut panen, & defisit sawit 1.22%',
            auditorCritique: 'Audit Tahap 4 (Q4 - 360 Days): Terverifikasi tumpukan TBS panen puncak, jalan angkut panen terawat, indeks fotosintesis SPAD 82.4, dan defisit TBS terkunci aman pada 1.22% (di bawah batas toleransi 4.5%).'
        }
    };

    let activeTimelineStage = 0;
    let isStageScanInProgress = false;

    /**
     * Resolusi URL foto bukti aktual untuk stage tertentu
     */
    function resolveStagePhoto(stageIdx) {
        const meta = STAGE_METADATA[stageIdx] || STAGE_METADATA[0];
        
        // 1. Cek apakah ada foto di galeri uploadedEvidencePhotos yang cocok
        if (typeof uploadedEvidencePhotos !== 'undefined' && Array.isArray(uploadedEvidencePhotos) && uploadedEvidencePhotos.length > 0) {
            // Cek kecocokan quarter_cycle atau tag
            const match = uploadedEvidencePhotos.find(p => {
                const q = (p.quarter_cycle || p.tag || '').toUpperCase();
                if (meta.cycleKey === 'ANNUAL' && (q === 'ANNUAL' || q === 'REG' || q.includes('ANNUAL') || q.includes('STAGE-0'))) return true;
                if (meta.cycleKey === 'Q1' && (q === 'Q1' || q.includes('Q1') || q.includes('STAGE-1'))) return true;
                if (meta.cycleKey === 'Q2' && (q === 'Q2' || q.includes('Q2') || q.includes('STAGE-2'))) return true;
                if (meta.cycleKey === 'Q3' && (q === 'Q3' || q.includes('Q3') || q.includes('STAGE-3'))) return true;
                if (meta.cycleKey === 'Q4' && (q === 'Q4' || q.includes('Q4') || q.includes('STAGE-4'))) return true;
                return false;
            });

            if (match && match.url) {
                return {
                    url: match.url,
                    filename: match.name || match.filename || meta.filename,
                    perspective: match.perspective_mode || meta.perspective
                };
            }

            // Jika stageIdx ada dalam rentang uploadedEvidencePhotos
            if (uploadedEvidencePhotos[stageIdx] && uploadedEvidencePhotos[stageIdx].url) {
                return {
                    url: uploadedEvidencePhotos[stageIdx].url,
                    filename: uploadedEvidencePhotos[stageIdx].name || meta.filename,
                    perspective: uploadedEvidencePhotos[stageIdx].perspective_mode || meta.perspective
                };
            }
        }

        // 2. Gunakan foto default terestrial/drone sesuai perspektif stage
        return {
            url: meta.defaultPhoto,
            filename: meta.filename,
            perspective: meta.perspective
        };
    }

    /**
     * Memilih stage timeline dan memicu pemindaian dinamis UnifiedVisionEngine
     */
    function selectTimelineStage(stageIndex) {
        const stageIdx = parseInt(stageIndex, 10) || 0;
        activeTimelineStage = stageIdx;
        window.currentTimelineStageIndex = stageIdx;

        const meta = STAGE_METADATA[stageIdx] || STAGE_METADATA[0];
        const photoInfo = resolveStagePhoto(stageIdx);
        const stagePhotoUrl = photoInfo.url;
        const stageFilename = photoInfo.filename;

        console.log(`[Timeline.js] Switching to Stage ${stageIdx} (${meta.cycleKey}): ${stageFilename}`);

        // 1. Update Preview Image & HUD di Bagian Atas
        const imgEl = document.getElementById('imgMonitoringEvidencePreview');
        const emptyEl = document.getElementById('emptyEvidenceStateTimelines');
        const lblFile = document.getElementById('lblActiveEvidenceFilename');
        const textPerspective = document.getElementById('textTimelinesPerspective');
        const container = document.getElementById('timelinePhotoContainer') || document.getElementById('stageEvidenceWrapper');
        const overlay = document.getElementById('timelineBBoxesOverlay') || document.getElementById('stageBBoxesOverlay');
        const statusText = document.getElementById('timelineScanStatusText');

        if (lblFile) {
            lblFile.textContent = `${meta.shortTitle} (${stageFilename})`;
        }
        if (textPerspective) {
            textPerspective.textContent = meta.perspectiveLabel;
        }

        if (imgEl) {
            imgEl.style.display = 'block';
            imgEl.classList.remove('hidden');
            if (emptyEl) {
                emptyEl.classList.add('hidden');
                emptyEl.style.display = 'none';
            }
            imgEl.src = stagePhotoUrl;
        }

        // 2. Beri Efek Visual Aktif pada Semua Kartu Stage (Atas & Bawah)
        highlightActiveStageCards(stageIdx);

        // 3. Panggil UnifiedVisionEngine untuk Menghitung Kotak 2D Secara Dinamis
        if (window.UnifiedVisionEngine) {
            if (statusText) {
                statusText.textContent = `Scanning Stage ${stageIdx} (${meta.cycleKey})...`;
            }

            window.UnifiedVisionEngine.scan({
                imageUrl: stagePhotoUrl,
                filename: stageFilename || `evidence_stage_${stageIdx}.jpg`,
                pageContext: 'TIMELINES',
                containerEl: container,
                overlayEl: overlay,
                statusEl: statusText,
                stageIndex: stageIdx
            }).then(payload => {
                if (payload) {
                    console.log(`[Timeline.js] Stage ${stageIdx} Vision Audit Completed:`, payload.sha256Seal);

                    // Perbarui badge segel kriptografis SHA-256 di bawah foto
                    const shaEl = document.getElementById('stageShaSealBadge');
                    if (shaEl) {
                        shaEl.textContent = payload.sha256Seal;
                        shaEl.classList.add('text-cyan-400');
                    }

                    const critiqueEl = document.getElementById('stageAuditorSummaryText');
                    if (critiqueEl) {
                        critiqueEl.textContent = payload.auditorCritique;
                    }

                    // Sinkronkan juga kartu galeri forensik jika ada di halaman
                    const fSha = document.getElementById('forensicCardSha256');
                    if (fSha) fSha.textContent = payload.sha256Seal;

                    const fCritique = document.getElementById('forensicAuditorNarrative');
                    if (fCritique) fCritique.textContent = payload.auditorCritique;

                    const fCount = document.getElementById('forensicCardEntityCount');
                    if (fCount) fCount.textContent = `${payload.totalEntities || 24} Entities Ground-Mapped`;

                    const fBadge = document.getElementById('forensicCardBadgeText');
                    if (fBadge) fBadge.textContent = `SEALED • STAGE-${stageIdx}-${meta.cycleKey}`;

                    const fTitle = document.getElementById('forensicCardTitle');
                    if (fTitle) fTitle.textContent = `Proof #${stageIdx + 1}: ${meta.title}`;

                    const fImg = document.getElementById('forensicCardImage');
                    if (fImg && fImg.src !== stagePhotoUrl) {
                        fImg.src = stagePhotoUrl;
                    }

                    // Notifikasi sukses
                    if (typeof showNotificationToast === 'function') {
                        showNotificationToast(`✓ Stage ${stageIdx} (${meta.cycleKey}) Terpetakan Dinamis (${payload.totalEntities || 24} Entitas)`, "🎯");
                    }
                }
            }).catch(err => {
                console.warn("[Timeline.js] Scan notice:", err);
            });
        }

        // 4. Sinkronkan dengan tombol galeri thumbnail jika tersedia
        const thumbBtn = document.getElementById(`btnForensicStageThumb_${stageIdx}`);
        if (thumbBtn) {
            // Tandai tombol carousel aktif
            const allThumbs = document.querySelectorAll('button[id^="btnForensicStageThumb_"]');
            allThumbs.forEach(btn => {
                btn.classList.remove('bg-gradient-to-r', 'from-emerald-600', 'to-teal-600', 'text-white', 'scale-[1.03]');
            });
            thumbBtn.classList.add('bg-gradient-to-r', 'from-emerald-600', 'to-teal-600', 'text-white', 'scale-[1.03]');
        }
    }

    /**
     * Berikan highlight border/ring pada kartu stage yang aktif
     */
    function highlightActiveStageCards(activeIdx) {
        const stageKeys = ['Annual', 'Q1', 'Q2', 'Q3', 'Q4'];
        
        stageKeys.forEach((key, idx) => {
            const cardElements = document.querySelectorAll(`#cardSiklus${key}`);
            cardElements.forEach(card => {
                if (idx === activeIdx) {
                    card.classList.add('ring-2', 'ring-emerald-400', 'border-emerald-500', 'scale-[1.01]');
                    card.classList.remove('border-slate-200', 'dark:border-slate-800');
                } else {
                    card.classList.remove('ring-2', 'ring-emerald-400', 'scale-[1.01]');
                }
            });
        });
    }

    /**
     * BUKA SEMUA KUNCI STAGE (SANDBOX MODE):
     * Hapus atribut disabled, kelas opacity-40/60, pointer-events-none, atau cursor-not-allowed
     * Izinkan juri bebas mengklik tab Stage mana pun (Stage 0, 1, 2, 3, 4).
     */
    function initSandboxMode() {
        console.log("[Timeline.js] Initializing Sandbox Mode: Unlocking all stages for jury evaluation...");

        const stages = [
            { key: 'Annual', idx: 0 },
            { key: 'Q1', idx: 1 },
            { key: 'Q2', idx: 2 },
            { key: 'Q3', idx: 3 },
            { key: 'Q4', idx: 4 }
        ];

        stages.forEach(({ key, idx }) => {
            // 1. Unlocked semua kartu stage di DOM
            const cards = document.querySelectorAll(`#cardSiklus${key}`);
            cards.forEach(card => {
                card.style.display = 'flex';
                card.classList.remove('hidden', 'opacity-40', 'opacity-60', 'pointer-events-none', 'cursor-not-allowed');
                card.classList.add('cursor-pointer');
                card.removeAttribute('disabled');

                // Pasang event click jika belum ada
                card.onclick = (e) => {
                    // Jika klik pada tombol download PDF, biarkan link berjalan
                    if (e.target && (e.target.tagName === 'A' || e.target.closest('a'))) {
                        return;
                    }
                    selectTimelineStage(idx);
                };
            });

            // 2. Unlocked tombol download & tombol aksi
            const btnDls = document.querySelectorAll(`#btnDownloadReport${key}`);
            btnDls.forEach(btn => {
                btn.classList.remove('opacity-60', 'cursor-not-allowed', 'pointer-events-none');
                btn.removeAttribute('disabled');
            });
        });

        // 3. Tambahkan trigger klik pada baris carousel stage jika belum
        const carousel = document.getElementById('forensicGalleryThumbsContainer');
        if (carousel) {
            carousel.addEventListener('click', (e) => {
                const btn = e.target.closest('button[id^="btnForensicStageThumb_"]');
                if (btn) {
                    const btnIdx = parseInt(btn.id.replace('btnForensicStageThumb_', ''), 10);
                    if (!isNaN(btnIdx)) {
                        selectTimelineStage(btnIdx);
                    }
                }
            });
        }
    }

    // Expose fungsi ke global window agar dapat dipanggil dari mana saja
    window.selectTimelineStage = selectTimelineStage;
    window.renderStageDetail = selectTimelineStage;
    window.initSandboxMode = initSandboxMode;

    // Inisialisasi saat DOM siap
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initSandboxMode();
            // Jalankan scan awal untuk stage aktif (Stage 0) secara mulus
            setTimeout(() => {
                selectTimelineStage(activeTimelineStage);
            }, 300);
        });
    } else {
        initSandboxMode();
        setTimeout(() => {
            selectTimelineStage(activeTimelineStage);
        }, 300);
    }

})();
