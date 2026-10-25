(function (window) {
    'use strict';

    const previews = new Map();

    function escapeXml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;'
        })[character]);
    }

    function getState(channel) {
        if (!previews.has(channel)) {
            previews.set(channel, { requestId: 0, preview: null, options: null, visible: true });
        }
        return previews.get(channel);
    }

    function setProgress(options, state, title, detail) {
        const panel = document.getElementById(options.progressPanelId);
        const label = document.getElementById(options.progressLabelId);
        const description = document.getElementById(options.progressDetailId);
        const bar = document.getElementById(options.progressBarId);
        if (!panel || !label || !description || !bar) return;

        panel.classList.remove('hidden');
        panel.dataset.state = state;
        label.textContent = title;
        description.textContent = detail;
        bar.classList.toggle('animate-pulse', state === 'running');
        bar.classList.toggle('w-1/3', state === 'running');
        bar.classList.toggle('w-full', state !== 'running');
        bar.classList.toggle('bg-emerald-500', state !== 'failed');
        bar.classList.toggle('bg-rose-500', state === 'failed');
    }

    function render(channel) {
        const state = getState(channel);
        const options = state.options;
        if (!options) return;

        const layer = document.getElementById(options.layerId);
        const button = document.getElementById(options.toggleButtonId);
        const buttonLabel = document.getElementById(options.toggleLabelId);
        if (!layer || !button || !buttonLabel) return;

        const preview = state.preview;
        const contours = preview?.status === 'ready' && Array.isArray(preview.contours)
            ? preview.contours
            : [];
        const drawable = contours.filter(contour =>
            Array.isArray(contour.points) &&
            contour.points.length >= 3 &&
            contour.points.every(point =>
                Array.isArray(point) &&
                Number.isFinite(point[0]) &&
                Number.isFinite(point[1])
            )
        );

        if (!state.visible || !drawable.length || !Number.isFinite(preview.width) || !Number.isFinite(preview.height)) {
            layer.innerHTML = '';
        } else {
            const boxes = Array.isArray(options.boxes) ? options.boxes : [];
            const paths = drawable.map((contour, index) => {
                const color = ['#34d399', '#38bdf8', '#fb7185', '#fbbf24', '#a78bfa'][index % 5];
                const points = contour.points.map(point => `${point[0]},${point[1]}`).join(' ');
                const entity = boxes[contour.entity_index] || {};
                const label = entity.label_name || entity.label || entity.cluster || `Object ${index + 1}`;
                const firstPoint = contour.points.reduce((top, point) => point[1] < top[1] ? point : top, contour.points[0]);
                const support = Number.isFinite(contour.edge_support)
                    ? ` · edge support ${contour.edge_support}`
                    : '';
                return `<g><title>${escapeXml(label + support)}</title><polyline points="${points}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/><text x="${firstPoint[0]}" y="${Math.max(14, firstPoint[1] - 7)}" fill="${color}" font-size="16" font-weight="700" paint-order="stroke" stroke="#020617" stroke-width="4" stroke-linejoin="round">${escapeXml(label)}</text></g>`;
            }).join('');
            layer.innerHTML = `<svg class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 ${preview.width} ${preview.height}" preserveAspectRatio="xMidYMid slice" aria-label="SAM2 segmentation refined with OpenCV">${paths}</svg>`;
        }

        const unavailable = !preview || preview.status !== 'ready' || drawable.length === 0;
        button.disabled = unavailable;
        button.setAttribute('aria-pressed', String(state.visible));
        buttonLabel.textContent = unavailable
            ? 'Optional outlines · local only'
            : `SAM2 + OpenCV outline (${drawable.length}) · ${state.visible ? 'On' : 'Off'}`;
    }

    function reset(channel, options) {
        const state = getState(channel);
        state.requestId += 1;
        state.preview = null;
        state.options = options || state.options;
        state.visible = true;

        if (state.options) {
            const panel = document.getElementById(state.options.progressPanelId);
            const button = document.getElementById(state.options.toggleButtonId);
            const layer = document.getElementById(state.options.layerId);
            if (panel) panel.classList.add('hidden');
            if (button) {
                button.disabled = true;
                button.setAttribute('aria-pressed', 'false');
            }
            if (layer) layer.innerHTML = '';
        }
    }

    function report(channel, options, state, title, detail) {
        if (typeof options.isCurrent === 'function' && !options.isCurrent()) return;
        const previewState = getState(channel);
        previewState.options = options;
        setProgress(options, state, title, detail);
    }

    async function load(options) {
        if (typeof options.isCurrent === 'function' && !options.isCurrent()) return null;
        const state = getState(options.channel);
        const requestId = ++state.requestId;
        state.options = options;
        state.preview = { status: 'loading' };
        state.visible = true;
        render(options.channel);
        setProgress(options, 'running', 'Gemini detections → SAM2 + OpenCV', 'Generating object outlines from the saved scan…');

        const isCurrent = () => requestId === state.requestId &&
            (typeof options.isCurrent !== 'function' || options.isCurrent());
        if (!options.isLive || !options.isPersisted || !options.evidenceId) {
            state.preview = {
                status: 'unavailable',
                reason: !options.evidenceId
                    ? 'evidence_id_missing'
                    : (!options.isPersisted ? 'scan_not_persisted' : 'scan_not_image_verified')
            };
            if (isCurrent()) {
                render(options.channel);
                setProgress(options, 'done', 'SAM2 + OpenCV outline skipped', !options.evidenceId
                    ? 'This image is not linked to a saved evidence record.'
                    : (!options.isPersisted
                        ? 'The live Gemini scan was not saved; no stored detections are available for segmentation.'
                        : 'Only live image detections saved to evidence can be used as SAM2 prompts.'));
            }
            return state.preview;
        }

        try {
            const response = await fetch('/api/spatial/contour-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ evidence_id: options.evidenceId })
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || `Contour preview failed (${response.status})`);
            }

            const preview = result.contour_preview || {
                status: 'unavailable',
                reason: result.reason || (result.status === 'not_run' ? 'scan_not_persisted' : 'contour_preview_missing')
            };
            if (!isCurrent()) return preview;

            state.preview = preview;
            render(options.channel);
            if (preview.status === 'ready' && Array.isArray(preview.contours) && preview.contours.length > 0) {
                setProgress(options, 'done', 'SAM2 + OpenCV complete', `${preview.contours.length} outline(s) refined from the saved Gemini detections.`);
            } else {
                const reason = preview.reason || 'no_contours';
                const messages = {
                    sam2_disabled: 'Optional SAM2 outlines are not enabled here; scanning and certification can continue.',
                    sam2_checkpoint_missing: 'Optional SAM2 outlines need local model weights; scanning and certification can continue.',
                    ultralytics_not_installed: 'Optional SAM2 outlines need the local Ultralytics package; scanning and certification can continue.',
                    scan_not_image_verified: 'The saved detections are not verified live image results.',
                    scan_not_persisted: 'No saved image detections are available for this evidence.',
                    no_contours: 'SAM2 did not return an outline for the detected objects.'
                };
                setProgress(options, 'done', 'Optional outlines skipped', messages[reason] || `No outline was returned (${reason}); scanning and certification can continue.`);
            }
            return preview;
        } catch (error) {
            if (!isCurrent()) return null;
            console.error(`[${options.channel} contour preview]`, error);
            state.preview = { status: 'unavailable', reason: 'contour_preview_request_failed' };
            render(options.channel);
            setProgress(options, 'done', 'Optional outlines skipped', `${error.message || 'The contour preview request failed.'} Scanning and certification can continue.`);
            return state.preview;
        }
    }

    function toggle(channel) {
        const state = getState(channel);
        if (state.preview?.status !== 'ready') return;
        state.visible = !state.visible;
        render(channel);
    }

    window.HybridContourPreview = { load, report, reset, toggle };
})(window);
