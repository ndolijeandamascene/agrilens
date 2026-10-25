/**
 * AgriLens Public Portal JavaScript
 * Dynamic National Agricultural Intelligence Map & Verified Microdata Engine
 * Synchronized with official SAS multi-season dataset (2025A / 2024A)
 */

document.addEventListener('DOMContentLoaded', () => {
    initAgriLensPublicMap();
});

/* ==========================================================================
   1. LIVE DISTRICT MICRODATA ENGINE (DATABASE-DRIVEN)
   ========================================================================== */
let liveDistrictData = {};

/* District Centroids for Map Centering & Pinned Dark Popup */
const DISTRICT_CENTROIDS = {
    "Nyarugenge": [-1.9977, 30.022], "Gasabo": [-1.8879, 30.119], "Kicukiro": [-2.0297, 30.1413],
    "Nyanza": [-2.3203, 29.7702], "Gisagara": [-2.6446, 29.8371], "Nyaruguru": [-2.6934, 29.5077],
    "Huye": [-2.5186, 29.7034], "Nyamagabe": [-2.3994, 29.4701], "Ruhango": [-2.1897, 29.7294],
    "Muhanga": [-1.9764, 29.7144], "Kamonyi": [-2.0052, 29.9139], "Karongi": [-2.1669, 29.4665],
    "Rutsiro": [-1.9116, 29.4399], "Rubavu": [-1.6829, 29.3625], "Nyabihu": [-1.6687, 29.5115],
    "Ngororero": [-1.893, 29.5612], "Rusizi": [-2.5759, 29.1192], "Rulindo": [-1.7482, 29.9844],
    "Gakenke": [-1.6974, 29.7774], "Musanze": [-1.5134, 29.631], "Burera": [-1.4811, 29.8543],
    "Gicumbi": [-1.6023, 30.091], "Rwamagana": [-1.9819, 30.3297], "Nyagatare": [-1.2955, 30.3303],
    "Gatsibo": [-1.6126, 30.3387], "Kayonza": [-1.9541, 30.5903], "Kirehe": [-2.2368, 30.6972],
    "Ngoma": [-2.2045, 30.439], "Bugesera": [-2.1734, 30.1726], "Nyamasheke": [-2.4116, 29.1805]
};

const DISTRICT_PROVINCE_MAP = {
    'Burera': 'Northern', 'Gakenke': 'Northern', 'Gicumbi': 'Northern', 'Musanze': 'Northern', 'Rulindo': 'Northern',
    'Gisagara': 'Southern', 'Huye': 'Southern', 'Kamonyi': 'Southern', 'Muhanga': 'Southern', 'Nyamagabe': 'Southern', 'Nyanza': 'Southern', 'Nyaruguru': 'Southern', 'Ruhango': 'Southern',
    'Bugesera': 'Eastern', 'Gatsibo': 'Eastern', 'Kayonza': 'Eastern', 'Kirehe': 'Eastern', 'Ngoma': 'Eastern', 'Nyagatare': 'Eastern', 'Rwamagana': 'Eastern',
    'Karongi': 'Western', 'Ngororero': 'Western', 'Nyabihu': 'Western', 'Nyamasheke': 'Western', 'Rubavu': 'Western', 'Rusizi': 'Western', 'Rutsiro': 'Western',
    'Gasabo': 'Kigali', 'Kicukiro': 'Kigali', 'Nyarugenge': 'Kigali'
};

/* ==========================================================================
   2. MAP CONTROLLER & STATE
   ========================================================================== */
let map = null;
let geoLayer = null;
let currentSeason = '2025A';
let currentCrop = 'Maize';
let currentIndicator = 'yield';
let pinnedDistrictName = 'Nyabihu';
let pinnedMarker = null;
let pinnedPopup = null;

function fetchLiveDistrictData(callback) {
    let year = 2025;
    let sCode = 'A';
    if (currentSeason && currentSeason.length >= 5) {
        year = currentSeason.slice(0, 4);
        sCode = currentSeason.slice(4);
    }
    const url = `/indicators/api/districts/?crop=${encodeURIComponent(currentCrop)}&year=${year}&season=${sCode}&source=official`;
    fetch(url)
        .then(r => r.json())
        .then(res => {
            liveDistrictData = {};
            if (res && res.data && Array.isArray(res.data)) {
                res.data.forEach(item => {
                    liveDistrictData[item.district_name] = item;
                });
            }
            if (callback) callback();
        })
        .catch(err => {
            console.warn('Failed to load live district rankings:', err);
            if (callback) callback();
        });
}

function getIndicatorValue(districtName) {
    const item = liveDistrictData[districtName];
    if (!item) return null;
    if (currentIndicator === 'production') {
        return item.production_mt !== undefined && item.production_mt !== null ? item.production_mt : null;
    } else if (currentIndicator === 'area') {
        return item.area_ha !== undefined && item.area_ha !== null ? item.area_ha : null;
    }
    return item.yield_tha !== undefined && item.yield_tha !== null ? item.yield_tha : null;
}

function formatIndicatorValue(val) {
    if (val === null || val === undefined) return 'No data';
    if (currentIndicator === 'production') {
        return Number(val).toLocaleString() + ' MT';
    } else if (currentIndicator === 'area') {
        return Number(val).toLocaleString() + ' ha';
    }
    return Number(val).toFixed(1) + ' t/ha';
}

function getDistrictColor(val) {
    if (val === null || val === undefined) return '#cbd5e1';
    if (currentIndicator === 'production') {
        if (val > 40000) return '#15803d';
        if (val >= 25000) return '#22c55e';
        if (val >= 15000) return '#84cc16';
        if (val >= 5000) return '#eab308';
        if (val > 0) return '#0284c7';
        return '#cbd5e1';
    } else if (currentIndicator === 'area') {
        if (val > 15000) return '#15803d';
        if (val >= 10000) return '#22c55e';
        if (val >= 5000) return '#84cc16';
        if (val >= 2000) return '#eab308';
        if (val > 0) return '#0284c7';
        return '#cbd5e1';
    } else {
        if (val > 3.5) return '#15803d';
        if (val >= 2.5) return '#22c55e';
        if (val >= 1.8) return '#84cc16';
        if (val >= 1.0) return '#eab308';
        if (val > 0) return '#0284c7';
        return '#cbd5e1';
    }
}

/* ==========================================================================
   3. LEAFLET INITIALIZATION
   ========================================================================== */
function initAgriLensPublicMap() {
    const mapElement = document.getElementById('rwanda-leaflet-map');
    if (!mapElement || typeof L === 'undefined') return;

    // Center map on Rwanda
    map = L.map('rwanda-leaflet-map', {
        attributionControl: false,
        zoomControl: false,
        scrollWheelZoom: false
    }).setView([-1.9403, 29.8739], 8.5);

    // Light Canvas basemap
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16
    }).addTo(map);

    // Surrounding country watermark labels matching reference
    const neighbors = [
        { name: 'UGANDA', lat: -1.08, lng: 30.08 },
        { name: 'DRC', lat: -1.90, lng: 28.70 },
        { name: 'BURUNDI', lat: -2.80, lng: 29.85 },
        { name: 'TANZANIA', lat: -1.95, lng: 31.15 }
    ];
    neighbors.forEach(n => {
        L.marker([n.lat, n.lng], {
            icon: L.divIcon({
                className: 'country-watermark',
                html: n.name,
                iconSize: [80, 20],
                iconAnchor: [40, 10]
            }),
            interactive: false
        }).addTo(map);
    });

    // Custom Map Controls (+, -, Recenter)
    setupCustomControls();

    // Hook up Dropdown Selectors (Crop, Season, Indicator)
    setupToolbarSelectors();

    // Fetch live verified data first, then GeoJSON
    fetchLiveDistrictData(() => {
        fetch('/static/data/rwanda_districts.geojson')
            .then(res => res.json())
            .then(geojson => {
                geoLayer = L.geoJSON(geojson, {
                    style: feature => {
                        const dName = feature.properties.shapeName || feature.properties.name || '';
                        const val = getIndicatorValue(dName);
                        const isPinned = (dName === pinnedDistrictName);
                        return {
                            color: isPinned ? '#0f172a' : '#ffffff',
                            weight: isPinned ? 2.8 : 1.2,
                            fillColor: getDistrictColor(val),
                            fillOpacity: isPinned ? 0.95 : 0.88
                        };
                    },
                    onEachFeature: (feature, layer) => {
                        const dName = feature.properties.shapeName || feature.properties.name || 'District';

                        layer.on('click', e => {
                            L.DomEvent.stopPropagation(e);
                            pinnedDistrictName = dName;
                            const center = DISTRICT_CENTROIDS[dName] || layer.getBounds().getCenter();
                            showPinnedDistrictPopup(center, dName);
                            highlightSelectedDistrict(dName);
                            updateKpiStrip(dName);
                        });

                        layer.on('mouseover', () => {
                            const center = DISTRICT_CENTROIDS[dName] || layer.getBounds().getCenter();
                            showPinnedDistrictPopup(center, dName);
                            layer.setStyle({
                                weight: 2.8,
                                color: '#0f172a',
                                fillOpacity: 0.96
                            });
                            layer.bringToFront();
                        });

                        layer.on('mouseout', () => {
                            if (geoLayer) {
                                geoLayer.resetStyle(layer);
                                if (pinnedDistrictName) {
                                    highlightSelectedDistrict(pinnedDistrictName);
                                    const center = DISTRICT_CENTROIDS[pinnedDistrictName] || [-1.6687, 29.5115];
                                    showPinnedDistrictPopup(center, pinnedDistrictName);
                                }
                            }
                        });
                    }
                }).addTo(map);

                // Fit bounds cleanly
                map.fitBounds(geoLayer.getBounds(), { padding: [20, 20] });

                // Initialize pinned badge on Nyabihu District matching reference specification
                showPinnedDistrictPopup(DISTRICT_CENTROIDS['Nyabihu'], 'Nyabihu');
                highlightSelectedDistrict('Nyabihu');
                updateLegend(currentIndicator);
                updateKpiStrip('Nyabihu');
            })
            .catch(err => console.error('Error loading Rwanda GeoJSON:', err));
    });
}

/* ==========================================================================
   4. PINNED DISTRICT BADGE (REAL LEAFLET POPUP + WHITE DOT MARKER)
   ========================================================================== */
function showPinnedDistrictPopup(latlng, dName) {
    if (!map || !latlng) return;

    const val = getIndicatorValue(dName);
    const labelStr = (currentIndicator === 'production') ? 'Production' : (currentIndicator === 'area' ? 'Area' : 'Yield');

    // Small white dot on district center
    if (!pinnedMarker) {
        pinnedMarker = L.circleMarker(latlng, {
            radius: 4,
            fillColor: '#ffffff',
            color: '#0f172a',
            weight: 2.5,
            fillOpacity: 1,
            zIndexOffset: 1200
        }).addTo(map);
    } else {
        pinnedMarker.setLatLng(latlng);
        if (!map.hasLayer(pinnedMarker)) pinnedMarker.addTo(map);
    }

    // Sleek Dark Badge Tooltip
    const contentHtml = `
        <div class="nyabihu-badge-title">${dName} District</div>
        <div class="nyabihu-badge-yield">${labelStr}: ${formatIndicatorValue(val)}</div>
    `;

    if (!pinnedPopup) {
        pinnedPopup = L.popup({
            className: 'custom-dark-popup',
            closeButton: false,
            autoClose: false,
            closeOnClick: false,
            offset: [0, -4]
        })
        .setLatLng(latlng)
        .setContent(contentHtml)
        .openOn(map);
    } else {
        pinnedPopup.setLatLng(latlng)
            .setContent(contentHtml)
            .openOn(map);
    }
}

function highlightSelectedDistrict(dName) {
    if (!geoLayer) return;
    geoLayer.eachLayer(layer => {
        const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
        const val = getIndicatorValue(name);
        const isSelected = (name === dName);
        layer.setStyle({
            color: isSelected ? '#0f172a' : '#ffffff',
            weight: isSelected ? 2.8 : 1.2,
            fillColor: getDistrictColor(val),
            fillOpacity: isSelected ? 0.95 : 0.88
        });
        if (isSelected) layer.bringToFront();
    });
}

/* ==========================================================================
   5. DYNAMIC REFRESH & SYNCHRONIZATION
   ========================================================================== */
function refreshMapChoropleth() {
    fetchLiveDistrictData(() => {
        if (!geoLayer) return;
        geoLayer.eachLayer(layer => {
            const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
            const val = getIndicatorValue(name);
            const isSelected = (name === pinnedDistrictName);
            layer.setStyle({
                fillColor: getDistrictColor(val),
                color: isSelected ? '#0f172a' : '#ffffff',
                weight: isSelected ? 2.8 : 1.2,
                fillOpacity: isSelected ? 0.95 : 0.88
            });
        });

        // Update pinned popup with new value
        const center = DISTRICT_CENTROIDS[pinnedDistrictName] || [-1.6687, 29.5115];
        showPinnedDistrictPopup(center, pinnedDistrictName);

        // Update KPI strip cards dynamically for the selected district
        updateKpiStrip(pinnedDistrictName);
    });
}

function updateKpiStrip(targetDistrict) {
    const dName = targetDistrict || pinnedDistrictName;
    const item = liveDistrictData[dName];

    const kpiCrops = document.getElementById('kpi-crops');
    const kpiCropsSub = document.getElementById('kpi-crops-sub');
    const kpiRecords = document.getElementById('kpi-records');
    const kpiRecordsSub = document.getElementById('kpi-records-sub');
    const kpiDistricts = document.getElementById('kpi-districts');
    const kpiDistrictsLabel = document.getElementById('kpi-districts-label');
    const kpiDistrictsSub = document.getElementById('kpi-districts-sub');
    const kpiProd = document.getElementById('kpi-prod');
    const kpiProdLabel = document.getElementById('kpi-prod-label');
    const kpiProdSub = document.getElementById('kpi-prod-sub');
    const kpiYield = document.getElementById('kpi-yield');
    const kpiYieldLabel = document.getElementById('kpi-yield-label');
    const kpiYieldSub = document.getElementById('kpi-yield-sub');

    if (item && item.yield_tha !== undefined && item.yield_tha !== null) {
        const prov = item.province_name || DISTRICT_PROVINCE_MAP[dName] || '';
        const yVal = item.yield_tha;
        const distProdMt = item.production_mt || 0;
        const prodDisplay = (distProdMt >= 1000) ? (distProdMt / 1000).toFixed(1) + 'K t' : distProdMt.toLocaleString() + ' t';
        const sampleCount = item.plots_sampled || 0;

        if (kpiCropsSub) kpiCropsSub.textContent = `Priority crops tracked in ${dName}`;
        if (kpiRecords) kpiRecords.textContent = sampleCount.toLocaleString();
        if (kpiRecordsSub) kpiRecordsSub.textContent = `Verified plots in ${dName}`;
        if (kpiDistricts) kpiDistricts.textContent = dName;
        if (kpiDistrictsLabel) kpiDistrictsLabel.textContent = 'Selected District';
        if (kpiDistrictsSub) kpiDistrictsSub.textContent = prov ? `${prov} Province` : 'Rwanda';
        if (kpiProd) kpiProd.textContent = prodDisplay;
        if (kpiProdLabel) kpiProdLabel.textContent = `${currentCrop} Production`;
        if (kpiProdSub) kpiProdSub.textContent = `Estimated (${dName} District)`;
        if (kpiYield) kpiYield.textContent = Number(yVal).toFixed(1) + ' t/ha';
        if (kpiYieldLabel) kpiYieldLabel.textContent = `${currentCrop} Yield`;
        if (kpiYieldSub) kpiYieldSub.textContent = `${dName} District`;
    }
}

function updateLegend(indicator) {
    const titleEl = document.getElementById('legend-dynamic-title');
    const listEl = document.getElementById('legend-swatch-list');
    if (!titleEl || !listEl) return;

    const seasonObj = AGRI_SEASON_DATA[currentSeason] || AGRI_SEASON_DATA['2025A'];
    const cropObj = seasonObj.crops[currentCrop] || seasonObj.crops['Maize'];
    const b = cropObj.yieldBenchmark;

    if (indicator === 'production') {
        titleEl.textContent = 'Production (t)';
        listEl.innerHTML = `
            <div class="swatch-row"><span class="swatch-box" style="background: #15803d;"></span> <span>&gt; 40,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #22c55e;"></span> <span>25,000 &ndash; 40,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #84cc16;"></span> <span>15,000 &ndash; 25,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #eab308;"></span> <span>5,000 &ndash; 15,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #0284c7;"></span> <span>&lt; 5,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #cbd5e1;"></span> <span>No data</span></div>
        `;
    } else if (indicator === 'area') {
        titleEl.textContent = 'Planted Area (ha)';
        listEl.innerHTML = `
            <div class="swatch-row"><span class="swatch-box" style="background: #15803d;"></span> <span>&gt; 15,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #22c55e;"></span> <span>10,000 &ndash; 15,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #84cc16;"></span> <span>5,000 &ndash; 10,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #eab308;"></span> <span>2,000 &ndash; 5,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #0284c7;"></span> <span>&lt; 2,000</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #cbd5e1;"></span> <span>No data</span></div>
        `;
    } else {
        // Yield matching reference specification
        titleEl.textContent = 'Yield (t/ha)';
        let r1 = '&gt; 4.0', r2 = '3.0 &ndash; 4.0', r3 = '2.0 &ndash; 3.0', r4 = '1.0 &ndash; 2.0', r5 = '&lt; 1.0';
        if (currentCrop !== 'Maize') {
            const t1 = (b * 1.05).toFixed(1);
            const t2 = (b * 0.85).toFixed(1);
            const t3 = (b * 0.60).toFixed(1);
            const t4 = (b * 0.35).toFixed(1);
            r1 = `&gt; ${t1}`;
            r2 = `${t2} &ndash; ${t1}`;
            r3 = `${t3} &ndash; ${t2}`;
            r4 = `${t4} &ndash; ${t3}`;
            r5 = `&lt; ${t4}`;
        }
        listEl.innerHTML = `
            <div class="swatch-row"><span class="swatch-box" style="background: #15803d;"></span> <span>${r1}</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #22c55e;"></span> <span>${r2}</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #84cc16;"></span> <span>${r3}</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #eab308;"></span> <span>${r4}</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #0284c7;"></span> <span>${r5}</span></div>
            <div class="swatch-row"><span class="swatch-box" style="background: #cbd5e1;"></span> <span>No data</span></div>
        `;
    }
}

/* ==========================================================================
   6. TOOLBAR SELECTORS & CONTROLS
   ========================================================================== */
function setupToolbarSelectors() {
    const cropSelect = document.getElementById('map-select-crop');
    const seasonSelect = document.getElementById('map-select-season');
    const indSelect = document.getElementById('map-select-indicator');

    if (cropSelect) {
        cropSelect.addEventListener('change', () => {
            currentCrop = cropSelect.value;
            updateLegend(currentIndicator);
            refreshMapChoropleth();
        });
    }

    if (seasonSelect) {
        seasonSelect.addEventListener('change', () => {
            currentSeason = seasonSelect.value;
            updateLegend(currentIndicator);
            refreshMapChoropleth();
        });
    }

    if (indSelect) {
        indSelect.addEventListener('change', () => {
            currentIndicator = indSelect.value;
            updateLegend(currentIndicator);
            refreshMapChoropleth();
        });
    }
}

function setupCustomControls() {
    const zoomInBtn = document.getElementById('btn-map-zoom-in');
    const zoomOutBtn = document.getElementById('btn-map-zoom-out');
    const recenterBtn = document.getElementById('btn-map-recenter');

    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', () => {
            if (map) map.zoomIn();
        });
    }

    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', () => {
            if (map) map.zoomOut();
        });
    }

    if (recenterBtn) {
        recenterBtn.addEventListener('click', () => {
            if (map && geoLayer) {
                map.fitBounds(geoLayer.getBounds(), { padding: [20, 20] });
                pinnedDistrictName = 'Nyabihu';
                highlightSelectedDistrict('Nyabihu');
                showPinnedDistrictPopup(DISTRICT_CENTROIDS['Nyabihu'], 'Nyabihu');
                updateKpiStrip('Nyabihu');
            }
        });
    }
}
