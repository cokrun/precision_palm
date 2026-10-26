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
            const methodLabel = preview.method === 'opencv_hsv_ema_static_replay'
                ? 'OpenCV HSV vegetation-region preview'
                : 'OpenCV contour outlines';
            layer.innerHTML = `<svg class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 ${preview.width} ${preview.height}" preserveAspectRatio="xMidYMid slice" aria-label="${methodLabel}">${paths}</svg>`;
        }

        const unavailable = !preview || preview.status !== 'ready' || drawable.length === 0;
        button.disabled = unavailable;
        button.setAttribute('aria-pressed', String(state.visible));
        buttonLabel.textContent = unavailable
            ? 'OpenCV outlines unavailable'
            : `${preview.method === 'opencv_hsv_ema_static_replay' ? 'OpenCV vegetation regions' : 'OpenCV outline'} (${drawable.length}) · ${state.visible ? 'On' : 'Off'}`;
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
        state.visible = false;
        const hasPersistedGeminiDetections = options.isLive === true &&
            options.isPersisted === true &&
            Array.isArray(options.boxes) &&
            options.boxes.length > 0;
        if (!hasPersistedGeminiDetections) {
            state.preview = { status: 'unavailable', reason: 'saved_gemini_detections_required' };
            render(options.channel);
            setProgress(
                options,
                'failed',
                'Contours unavailable',
                'Contours are hidden until Gemini detections are successfully saved.'
            );
            return state.preview;
        }

        state.preview = { status: 'loading' };
        state.visible = true;
        render(options.channel);
        setProgress(options, 'running', 'OpenCV Contours', 'Refining saved Gemini detections…');

        const isCurrent = () => requestId === state.requestId &&
            (typeof options.isCurrent !== 'function' || options.isCurrent());
        if (!options.evidenceId) {
            state.preview = { status: 'unavailable', reason: 'evidence_id_missing' };
            render(options.channel);
            setProgress(options, 'failed', 'Contours unavailable', 'This image is not linked to a saved Gemini scan.');
            return state.preview;
        }

        let preview = null;
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
            preview = result.contour_preview || null;
        } catch (error) {
            console.error(`[${options.channel} SAM2 contour preview]`, error);
            if (isCurrent()) {
                state.preview = { status: 'unavailable', reason: 'contour_preview_request_failed' };
                render(options.channel);
                setProgress(options, 'failed', 'Contours unavailable', 'OpenCV could not extract contours for the saved Gemini detections.');
            }
            return state.preview;
        }

        if (!isCurrent()) return preview;
        if (preview?.status !== 'ready' || !Array.isArray(preview.contours) || !preview.contours.length) {
            state.preview = preview || { status: 'unavailable', reason: 'contour_preview_unavailable' };
            render(options.channel);
            setProgress(options, 'failed', 'Contours unavailable', 'OpenCV did not return contours for the saved Gemini detections.');
            return state.preview;
        }

        state.preview = preview;
        render(options.channel);
        setProgress(options, 'done', 'OpenCV complete',
            `${preview.contours.length} outline(s) refined from saved Gemini detections.`);
        return state.preview;
    }

    function toggle(channel) {
        const state = getState(channel);
        if (state.preview?.status !== 'ready') return;
        state.visible = !state.visible;
        render(channel);
    }

    window.HybridContourPreview = { load, report, reset, toggle };
})(window);
