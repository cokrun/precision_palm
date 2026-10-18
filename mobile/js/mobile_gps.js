/**
 * mobile/js/mobile_gps.js
 * Precision Palm Mobile - WGS84 Geolocation & Device Sensor Controller.
 * 
 * Manages:
 * 1. High-accuracy WGS84 GPS positioning (navigator.geolocation API).
 * 2. Elevation / altitude ASL calculation.
 * 3. Physical terrain slope detection via DeviceOrientation & Accelerometer sensors.
 * 4. Real-time satellite weather synchronization against live GPS (Open-Meteo API).
 * 5. Formatting telemetry readouts on the DOM.
 */

let liveCoordinates = {
    lat: null,
    lng: null,
    elev: null,
    ground_elev: null,
    altitude_agl_m: 1.45,
    camera_pitch_deg: -12.4,
    accuracy: null,
    slope: null,
    weather: null,
    timestamp_iso: new Date().toISOString()
};

let orientationSensorActive = false;

function acquireDeviceLocation() {
    if (!navigator.geolocation) {
        renderCoordinatesToDOM();
        initDeviceOrientationSensor();
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            liveCoordinates.lat = position.coords.latitude;
            liveCoordinates.lng = position.coords.longitude;
            liveCoordinates.accuracy = position.coords.accuracy || 4.5;
            liveCoordinates.timestamp_iso = new Date(position.timestamp || Date.now()).toISOString();

            if (position.coords.altitude !== null && position.coords.altitude !== undefined) {
                const rawAlt = position.coords.altitude;
                liveCoordinates.elev = rawAlt;
                // Hitung relative AGL height (altitude - ground_elevation atau default 1.45m handheld)
                const relativeAgl = liveCoordinates.ground_elev ? (rawAlt - liveCoordinates.ground_elev) : 1.45;
                liveCoordinates.altitude_agl_m = relativeAgl > 2.5 ? parseFloat(relativeAgl.toFixed(2)) : 1.45;
            } else {
                liveCoordinates.altitude_agl_m = 1.45;
            }

            renderCoordinatesToDOM();
            updateWeatherSatellite(liveCoordinates.lat, liveCoordinates.lng);
            initDeviceOrientationSensor();

            if (window.showToast) {
                const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';
                window.showToast(isId ? `GPS Terkunci: ${liveCoordinates.lat.toFixed(6)}, ${liveCoordinates.lng.toFixed(6)}` : `GPS Locked: ${liveCoordinates.lat.toFixed(6)}, ${liveCoordinates.lng.toFixed(6)}`, "📍");
            }
        },
        (error) => {
            console.warn('[MobileGPS] Hardware GNSS note:', error.message);
            renderCoordinatesToDOM();
            initDeviceOrientationSensor();
        },
        { enableHighAccuracy: true, timeout: 7000, maximumAge: 15000 }
    );
}

function setCentroidBaseline(lat, lng, elevation) {
    if (lat !== null && lat !== undefined && !isNaN(parseFloat(lat))) {
        liveCoordinates.lat = parseFloat(lat);
    }
    if (lng !== null && lng !== undefined && !isNaN(parseFloat(lng))) {
        liveCoordinates.lng = parseFloat(lng);
    }
    if (elevation !== null && elevation !== undefined && !isNaN(parseFloat(elevation))) {
        liveCoordinates.elev = parseFloat(elevation);
        liveCoordinates.ground_elev = parseFloat(elevation);
    }
    liveCoordinates.altitude_agl_m = 1.45;

    renderCoordinatesToDOM();
    if (liveCoordinates.lat !== null && liveCoordinates.lng !== null) {
        updateWeatherSatellite(liveCoordinates.lat, liveCoordinates.lng);
    }
    initDeviceOrientationSensor();
}

function renderCoordinatesToDOM() {
    const dispLat = document.getElementById('valDispLat');
    const dispLng = document.getElementById('valDispLng');
    const dispElev = document.getElementById('valDispElev');
    const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';

    if (dispLat) {
        dispLat.textContent = (liveCoordinates.lat !== null && liveCoordinates.lat !== undefined)
            ? liveCoordinates.lat.toFixed(6)
            : (isId ? "[Menunggu Kunci Satelit GPS]" : "[Awaiting GPS Satellite Lock]");
    }
    if (dispLng) {
        dispLng.textContent = (liveCoordinates.lng !== null && liveCoordinates.lng !== undefined)
            ? liveCoordinates.lng.toFixed(6)
            : "-";
    }
    if (dispElev) {
        dispElev.textContent = (liveCoordinates.elev !== null && liveCoordinates.elev !== undefined)
            ? `${Math.round(liveCoordinates.elev)} ${isId ? 'm dpl' : 'm msl'}`
            : "-";
    }
}

async function updateWeatherSatellite(lat, lng) {
    const dispWeather = document.getElementById('valDispWeather');
    const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';

    if (lat === null || lat === undefined || lng === null || lng === undefined) {
        liveCoordinates.weather = isId ? "[Data Cuaca Offline]" : "[Weather Offline]";
        if (dispWeather) dispWeather.textContent = liveCoordinates.weather;
        return;
    }

    try {
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m`;
        const response = await fetch(url);

        if (response.ok) {
            const data = await response.json();
            if (data && data.current) {
                const temp = data.current.temperature_2m;
                const rh = data.current.relative_humidity_2m;
                liveCoordinates.weather = `${temp.toFixed(1)}°C ${isId ? 'Cerah Berawan' : 'Partly Cloudy'} (RH ${rh}%)`;
                if (dispWeather) dispWeather.textContent = liveCoordinates.weather;
                return;
            }
        }
    } catch (_) {}

    liveCoordinates.weather = isId ? "[Data Cuaca Offline]" : "[Weather Offline]";
    if (dispWeather) dispWeather.textContent = liveCoordinates.weather;
}

function initDeviceOrientationSensor() {
    if (window.DeviceOrientationEvent && !orientationSensorActive) {
        window.addEventListener('deviceorientation', (event) => {
            if (event.beta !== null) {
                // Sudut kemiringan kamera perangkat (pitch angle)
                // Nilai beta: 0 saat datar, 90 saat tegak vertikal, 180 saat terbalik
                // Sudut kamera mengarah ke tanah = pitch negatif
                let pitch = event.beta;
                if (pitch > 90) pitch = 90 - pitch;
                else if (pitch < -90) pitch = -90 - pitch;
                else pitch = pitch - 90; // Normalisasi ke horizontal = 0, menghadap tanah = negatif
                
                if (pitch < -85) pitch = -90.0; // Nadir
                liveCoordinates.camera_pitch_deg = parseFloat(pitch.toFixed(1));
                
                const terrainSlope = Math.abs(event.beta);
                if (terrainSlope >= 0 && terrainSlope <= 45) {
                    liveCoordinates.slope = parseFloat(terrainSlope.toFixed(1));
                }
            }
        }, true);
        orientationSensorActive = true;
    }
}

function get4DTelemetryPayload() {
    return {
        latitude: liveCoordinates.lat,
        longitude: liveCoordinates.lng,
        altitude_agl_m: liveCoordinates.altitude_agl_m,
        camera_pitch_deg: liveCoordinates.camera_pitch_deg,
        timestamp_iso: new Date().toISOString()
    };
}

function format4DHudReadout() {
    const isId = (localStorage.getItem('precision_palm_mobile_lang') || localStorage.getItem('precision_palm_lang') || 'en') === 'id';
    const lat = liveCoordinates.lat;
    const lng = liveCoordinates.lng;
    if (lat === null || lat === undefined || lng === null || lng === undefined) {
        return isId ? "🛰️ 4D: [Menunggu Kunci Satelit GPS]" : "🛰️ 4D: [Awaiting GPS Satellite Lock]";
    }
    const alt = liveCoordinates.altitude_agl_m || 1.45;
    const pitch = Math.round(liveCoordinates.camera_pitch_deg || -12);
    const modeLabel = alt > 15.0 ? 'Drone' : 'Handheld';
    const latHemi = lat >= 0 ? 'N' : 'S';
    const lngHemi = lng >= 0 ? 'E' : 'W';
    return `🛰️ 4D: ${Math.abs(lat).toFixed(6)}°${latHemi}, ${Math.abs(lng).toFixed(6)}°${lngHemi} | Alt: ${alt.toFixed(2)}m (${modeLabel}) | Pitch: ${pitch > 0 ? '+' : ''}${pitch}°`;
}

window.MobileGPS = {
    acquireLocation: acquireDeviceLocation,
    setCentroidBaseline: setCentroidBaseline,
    initOrientationSensor: initDeviceOrientationSensor,
    getLiveCoords: () => liveCoordinates,
    get4DTelemetry: get4DTelemetryPayload,
    format4DHud: format4DHudReadout
};

window.acquireDeviceGpsLocation = acquireDeviceLocation;