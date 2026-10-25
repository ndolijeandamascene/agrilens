/**
 * AgriLens Public Agricultural Map Engine
 * Dynamic Interactive GIS Choropleth & Localized District Details Dossier
 * Fully synchronized with official database indicators and verified survey records.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAgriLensMapPage();
});

/* ==========================================================================
   1. GEOGRAPHIC REFERENCE DATA & TAXONOMY
   ========================================================================== */
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
    'Burera': 'Northern Province', 'Gakenke': 'Northern Province', 'Gicumbi': 'Northern Province', 'Musanze': 'Northern Province', 'Rulindo': 'Northern Province',
    'Gisagara': 'Southern Province', 'Huye': 'Southern Province', 'Kamonyi': 'Southern Province', 'Muhanga': 'Southern Province', 'Nyamagabe': 'Southern Province', 'Nyanza': 'Southern Province', 'Nyaruguru': 'Southern Province', 'Ruhango': 'Southern Province',
    'Bugesera': 'Eastern Province', 'Gatsibo': 'Eastern Province', 'Kayonza': 'Eastern Province', 'Kirehe': 'Eastern Province', 'Ngoma': 'Eastern Province', 'Nyagatare': 'Eastern Province', 'Rwamagana': 'Eastern Province',
    'Karongi': 'Western Province', 'Ngororero': 'Western Province', 'Nyabihu': 'Western Province', 'Nyamasheke': 'Western Province', 'Rubavu': 'Western Province', 'Rusizi': 'Western Province', 'Rutsiro': 'Western Province',
    'Gasabo': 'City of Kigali', 'Kicukiro': 'City of Kigali', 'Nyarugenge': 'City of Kigali'
};

const DISTRICT_ID_MAP = {
    'Nyarugenge': 1, 'Gasabo': 2, 'Kicukiro': 3, 'Nyanza': 4, 'Gisagara': 5,
    'Nyaruguru': 6, 'Huye': 7, 'Nyamagabe': 8, 'Ruhango': 9, 'Muhanga': 10,
    'Kamonyi': 11, 'Karongi': 12, 'Rutsiro': 13, 'Rubavu': 14, 'Nyabihu': 15,
    'Ngororero': 16, 'Rusizi': 17, 'Nyamasheke': 18, 'Rulindo': 19, 'Gakenke': 20,
    'Musanze': 21, 'Burera': 22, 'Gicumbi': 23, 'Rwamagana': 24, 'Nyagatare': 25,
    'Gatsibo': 26, 'Kayonza': 27, 'Kirehe': 28, 'Ngoma': 29, 'Bugesera': 30
};

const DISTRICT_AGRO_ZONES = {
    'Western Province': {
        zone: 'Western Volcanic Highlands & Lake Kivu Basin',
        elevation: 'High altitude volcanic slopes (1,800m – 2,500m)',
        climate: 'Bimodal rainfall pattern, 1,300mm – 1,600mm / year',
        staples: 'Irish Potato, Maize, Climbing Beans, Tea & Pyrethrum',
        security: 'Surplus Producer / Strategic Food Basket',
        focus: 'Radical terracing, soil erosion mitigation, post-harvest drying'
    },
    'Northern Province': {
        zone: 'Northern Volcanic Highlands & Buberuka Ridge',
        elevation: 'High altitude volcanic & metamorphic ridges (1,900m – 2,800m)',
        climate: 'Cool temperate mountain climate, 1,400mm – 1,800mm / year',
        staples: 'Irish Potato, High-yield Maize, Wheat, Vegetables',
        security: 'Premier National Grain & Seed Potato Breadbasket',
        focus: 'Certified seed distribution, lime application, cold storage facilities'
    },
    'Southern Province': {
        zone: 'Central Plateau & Southern Granitic Ridge',
        elevation: 'Mid-to-high plateau (1,500m – 1,900m)',
        climate: 'Tropical sub-humid, 1,100mm – 1,350mm / year',
        staples: 'Cassava, Climbing Beans, Maize, Marshland Rice, Coffee',
        security: 'Major Staple Cereal & Tuber Food Security Anchor',
        focus: 'Marshland irrigation schemes, clean cassava cuttings distribution'
    },
    'Eastern Province': {
        zone: 'Eastern Agro-Pastoral Lowland Savannas',
        elevation: 'Lowland to mid-elevation undulating plains (1,300m – 1,550m)',
        climate: 'Semi-arid to sub-humid, 800mm – 1,100mm / year',
        staples: 'Maize, Bush Beans, Banana, Rice, Livestock & Dairy',
        security: 'Commercial Grain Breadbasket & Extensive Consolidated Farmland',
        focus: 'Valley dam irrigation, drought-tolerant crop varieties, solar pumping'
    },
    'City of Kigali': {
        zone: 'Central Dissected Hills & Peri-Urban Agricultural Corridor',
        elevation: 'Central hills and valleys (1,400m – 1,650m)',
        climate: 'Sub-humid tropical, 1,000mm – 1,200mm / year',
        staples: 'Intensive Vegetables, Fruits, Poultry & Peri-Urban Horticulture',
        security: 'High-Value Fresh Market Supply Hub',
        focus: 'Greenhouse farming, urban food logistics, cold-chain transport'
    }
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

let liveDistrictData = {};

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
            liveDistrictData = {};
            if (callback) callback();
        });
}

function getDistrictMetrics(districtName) {
    const item = liveDistrictData[districtName];
    if (item) {
        return {
            yield: (item.yield_tha !== undefined && item.yield_tha !== null) ? Number(item.yield_tha) : null,
            area: (item.area_ha !== undefined && item.area_ha !== null) ? Number(item.area_ha) : null,
            prod: (item.production_mt !== undefined && item.production_mt !== null) ? Number(item.production_mt) : null,
            plots: item.plots_sampled || 0
        };
    }
    return { yield: null, area: null, prod: null, plots: 0 };
}

function getIndicatorValue(districtName) {
    const metrics = getDistrictMetrics(districtName);
    if (!metrics) return null;
    if (currentIndicator === 'production') {
        return metrics.prod;
    } else if (currentIndicator === 'area') {
        return metrics.area;
    }
    return metrics.yield;
}

function formatIndicatorValue(val) {
    if (val === null || val === undefined || isNaN(val)) {
        return 'No data';
    }
    if (currentIndicator === 'production') {
        return Number(val).toLocaleString(undefined, {maximumFractionDigits: 0}) + ' t';
    } else if (currentIndicator === 'area') {
        return Number(val).toLocaleString(undefined, {maximumFractionDigits: 0}) + ' ha';
    }
    return Number(val).toFixed(1) + ' t/ha';
}

function getDistrictColor(val) {
    if (val === null || val === undefined || isNaN(val)) {
        return '#cbd5e1'; // Slate gray (No observations)
    }
    if (currentIndicator === 'production') {
        if (val > 5000) return '#166534'; // Primary Green (> 5,000)
        if (val >= 3500) return '#15803D'; // Action Green (3,500 - 5,000)
        if (val >= 2000) return '#84CC16'; // Agriculture Lime (2,000 - 3,500)
        if (val >= 1000) return '#FACC15'; // Harvest Yellow (1,000 - 2,000)
        if (val > 0) return '#2563EB';     // Information Blue (< 1,000)
        return '#CBD5E1';
    } else if (currentIndicator === 'area') {
        if (val > 2000) return '#166534'; // Primary Green (> 2,000)
        if (val >= 1500) return '#15803D'; // Action Green (1,500 - 2,000)
        if (val >= 1000) return '#84CC16'; // Agriculture Lime (1,000 - 1,500)
        if (val >= 500) return '#FACC15';  // Harvest Yellow (500 - 1,000)
        if (val > 0) return '#2563EB';     // Information Blue (< 500)
        return '#CBD5E1';
    } else {
        // Yield (t/ha)
        if (val > 4.0) return '#166534';   // Primary Green (> 4.0)
        if (val >= 3.0) return '#15803D';  // Action Green (3.0 – 4.0)
        if (val >= 2.0) return '#84CC16';  // Agriculture Lime (2.0 – 3.0)
        if (val >= 1.0) return '#FACC15';  // Harvest Yellow (1.0 – 2.0)
        if (val > 0) return '#2563EB';     // Information Blue (< 1.0)
        return '#CBD5E1';                  // No data
    }
}

/* ==========================================================================
   3. INITIALIZE LEAFLET CHOROPLETH MAP
   ========================================================================== */
function initAgriLensMapPage() {
    const mapElement = document.getElementById('rwanda-leaflet-map');
    if (!mapElement) return;

    if (typeof L === 'undefined') {
        setTimeout(initAgriLensMapPage, 100);
        return;
    }

    if (map) return;

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('crop')) currentCrop = urlParams.get('crop');
    if (urlParams.has('season')) currentSeason = urlParams.get('season');
    if (urlParams.has('indicator')) currentIndicator = urlParams.get('indicator');
    if (urlParams.has('district')) pinnedDistrictName = urlParams.get('district');

    const cropSel = document.getElementById('map-filter-crop');
    const seasonSel = document.getElementById('map-filter-season');
    const indicatorSel = document.getElementById('map-filter-indicator');
    if (cropSel && urlParams.has('crop')) cropSel.value = currentCrop;
    if (seasonSel && urlParams.has('season')) seasonSel.value = currentSeason;
    if (indicatorSel && urlParams.has('indicator')) indicatorSel.value = currentIndicator;

    map = L.map('rwanda-leaflet-map', {
        zoomControl: false,
        scrollWheelZoom: false
    }).setView([-1.9403, 29.8739], 8.5);

    const tileLayer = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16
    }).addTo(map);

    tileLayer.on('tileerror', () => {
        if (!map._fallbackAdded) {
            map._fallbackAdded = true;
            L.tileLayer('https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', {
                maxZoom: 18
            }).addTo(map);
        }
    });

    setTimeout(() => { if (map) map.invalidateSize(); }, 150);
    setTimeout(() => { if (map) map.invalidateSize(); }, 500);
    window.addEventListener('resize', () => { if (map) map.invalidateSize(); });

    const neighbors = [
        { name: 'UGANDA', lat: -1.08, lng: 30.08 },
        { name: 'DRC', lat: -1.90, lng: 28.70 },
        { name: 'BURUNDI', lat: -2.80, lng: 29.85 },
        { name: 'TANZANIA', lat: -1.95, lng: 31.15 }
    ];
    neighbors.forEach(n => {
        L.marker([n.lat, n.lng], {
            icon: L.divIcon({
                className: 'country-watermark-label',
                html: n.name,
                iconSize: [80, 20],
                iconAnchor: [40, 10]
            }),
            interactive: false
        }).addTo(map);
    });

    setupCustomControls();
    setupToolbarSelectors();
    setupLegendInteractivity();
    setupHeaderSearchIntegration();

    // Fetch live district data and GeoJSON
    fetchLiveDistrictData(() => {
        fetch('/static/data/rwanda_districts.geojson')
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(geojson => {
                geoLayer = L.geoJSON(geojson, {
                    style: feature => {
                        const dName = feature.properties.shapeName || feature.properties.name || '';
                        const val = getIndicatorValue(dName);
                        const isPinned = (dName === pinnedDistrictName);
                        return {
                            color: isPinned ? '#0f172a' : '#ffffff',
                            weight: isPinned ? 3.0 : 1.2,
                            fillColor: getDistrictColor(val),
                            fillOpacity: isPinned ? 0.98 : 0.88
                        };
                    },
                    onEachFeature: (feature, layer) => {
                        const dName = feature.properties.shapeName || feature.properties.name || 'District';

                        layer.on('click', e => {
                            L.DomEvent.stopPropagation(e);
                            selectDistrict(dName, false);
                        });

                        layer.on('mouseover', () => {
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
                                }
                            }
                        });
                    }
                }).addTo(map);

                try {
                    map.fitBounds(geoLayer.getBounds(), { padding: [16, 16] });
                } catch (e) {
                    map.setView([-1.9403, 29.8739], 8.5);
                }

                setTimeout(() => { if (map) map.invalidateSize(); }, 150);

                updateLegendDisplay();
                updateBottomKpis();
                selectDistrict(pinnedDistrictName || 'Nyabihu', false);
            })
            .catch(err => {
                console.error("Error loading Rwanda GeoJSON:", err);
            });
    });
}

/* ==========================================================================
   4. DISTRICT SELECTION & SIDEBAR UPDATES
   ========================================================================== */
function selectDistrict(dName, panTo = false) {
    if (!dName) return;
    pinnedDistrictName = dName;
    const center = DISTRICT_CENTROIDS[dName] || [-1.6687, 29.5115];

    if (panTo && map) {
        map.panTo(center, { animate: true, duration: 0.5 });
    }

    showPinnedDistrictPopup(center, dName);
    highlightSelectedDistrict(dName);
    updateDistrictDetailsCard(dName);
    updateUrlQueryState();
}

function showPinnedDistrictPopup(latlng, dName) {
    if (pinnedMarker) {
        map.removeLayer(pinnedMarker);
        pinnedMarker = null;
    }

    const val = getIndicatorValue(dName);
    const formattedVal = formatIndicatorValue(val);
    const indLabel = currentIndicator === 'production' ? 'Production' : (currentIndicator === 'area' ? 'Area' : 'Yield');

    const html = `
        <div class="district-dark-callout">
            <div class="callout-title">${dName} District</div>
            <div class="callout-value">${indLabel}: ${formattedVal}</div>
        </div>
    `;

    const customIcon = L.divIcon({
        className: 'custom-leaflet-callout-wrap',
        html: html,
        iconSize: [140, 52],
        iconAnchor: [70, 60]
    });

    pinnedMarker = L.marker(latlng, {
        icon: customIcon,
        interactive: false,
        zIndexOffset: 1000
    }).addTo(map);
}

function highlightSelectedDistrict(dName) {
    if (!geoLayer) return;
    geoLayer.eachLayer(layer => {
        const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
        const val = getIndicatorValue(name);
        if (name === dName) {
            layer.setStyle({
                weight: 3.2,
                color: '#0f172a',
                fillColor: getDistrictColor(val),
                fillOpacity: 0.98
            });
            layer.bringToFront();
        } else {
            layer.setStyle({
                weight: 1.2,
                color: '#ffffff',
                fillColor: getDistrictColor(val),
                fillOpacity: 0.88
            });
        }
    });
}

function updateDistrictDetailsCard(dName) {
    const province = DISTRICT_PROVINCE_MAP[dName] || '';
    const metrics = getDistrictMetrics(dName);
    const seasonEl_text = document.querySelector('#map-filter-season option:checked')?.textContent || currentSeason;

    const nameEl = document.getElementById('card-district-name');
    const provEl = document.getElementById('card-province-name');
    if (nameEl) nameEl.textContent = `${dName} District`;
    if (provEl) provEl.textContent = province;

    const cropEl = document.getElementById('card-crop-name');
    const seasonEl = document.getElementById('card-season-name');
    const yieldEl = document.getElementById('card-yield-val');
    const areaEl = document.getElementById('card-area-val');
    const prodEl = document.getElementById('card-prod-val');

    if (cropEl) cropEl.textContent = currentCrop;
    if (seasonEl) seasonEl.textContent = seasonEl_text;
    if (yieldEl) yieldEl.textContent = metrics.yield !== null ? `${metrics.yield.toFixed(1)} t/ha` : '—';
    if (areaEl) areaEl.textContent = metrics.area !== null ? `${metrics.area.toLocaleString()} ha` : '—';
    if (prodEl) prodEl.textContent = metrics.prod !== null ? `${metrics.prod.toLocaleString()} t` : '—';

    const reportBtn = document.getElementById('btn-view-district-report');
    if (reportBtn) {
        reportBtn.setAttribute('title', `Open ${dName} District Agricultural Dossier`);
        reportBtn.onclick = () => openDistrictReportModal(dName);
    }

    const modal = document.getElementById('district-report-modal');
    if (modal && modal.classList.contains('open')) {
        populateDistrictReportModal(dName);
    }
}

function updateUrlQueryState() {
    const params = new URLSearchParams();
    if (currentCrop) params.set('crop', currentCrop);
    if (currentSeason) params.set('season', currentSeason);
    if (currentIndicator) params.set('indicator', currentIndicator);
    if (pinnedDistrictName) params.set('district', pinnedDistrictName);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
}

/* ==========================================================================
   5. TOOLBAR SELECTORS & RESET CONTROLS
   ========================================================================== */
function setupToolbarSelectors() {
    const cropSel = document.getElementById('map-filter-crop');
    const seasonSel = document.getElementById('map-filter-season');
    const indicatorSel = document.getElementById('map-filter-indicator');
    const resetBtn = document.getElementById('btn-map-reset');

    if (cropSel) {
        cropSel.addEventListener('change', e => {
            currentCrop = e.target.value;
            fetchLiveDistrictData(() => {
                applyDataRefresh();
                updateBottomKpis();
                updateUrlQueryState();
            });
        });
    }

    if (seasonSel) {
        seasonSel.addEventListener('change', e => {
            currentSeason = e.target.value;
            fetchLiveDistrictData(() => {
                applyDataRefresh();
                updateBottomKpis();
                updateUrlQueryState();
            });
        });
    }

    if (indicatorSel) {
        indicatorSel.addEventListener('change', e => {
            currentIndicator = e.target.value;
            updateLegendDisplay();
            applyDataRefresh();
            updateUrlQueryState();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            currentCrop = 'Maize';
            currentSeason = '2025A';
            currentIndicator = 'yield';
            pinnedDistrictName = 'Nyabihu';

            if (cropSel) cropSel.value = 'Maize';
            if (seasonSel) seasonSel.value = '2025A';
            if (indicatorSel) indicatorSel.value = 'yield';

            if (map && geoLayer) {
                map.fitBounds(geoLayer.getBounds(), { padding: [16, 16] });
            } else if (map) {
                map.setView([-1.9403, 29.8739], 8.5);
            }

            fetchLiveDistrictData(() => {
                updateLegendDisplay();
                updateBottomKpis();
                applyDataRefresh();
                selectDistrict('Nyabihu', false);
                updateUrlQueryState();
            });
        });
    }
}

function applyDataRefresh() {
    if (!geoLayer) return;
    geoLayer.eachLayer(layer => {
        const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
        const val = getIndicatorValue(name);
        const isPinned = (name === pinnedDistrictName);
        layer.setStyle({
            fillColor: getDistrictColor(val),
            color: isPinned ? '#0f172a' : '#ffffff',
            weight: isPinned ? 3.2 : 1.2,
            fillOpacity: isPinned ? 0.98 : 0.88
        });
    });

    if (pinnedDistrictName) {
        const center = DISTRICT_CENTROIDS[pinnedDistrictName] || [-1.6687, 29.5115];
        showPinnedDistrictPopup(center, pinnedDistrictName);
        updateDistrictDetailsCard(pinnedDistrictName);
    }
}

function updateLegendDisplay() {
    const titleEl = document.getElementById('legend-indicator-title');
    const listEl = document.getElementById('legend-scales-list');
    if (!titleEl || !listEl) return;

    if (currentIndicator === 'production') {
        titleEl.textContent = 'PRODUCTION (T)';
        listEl.innerHTML = `
            <div class="legend-scale-item" data-range="gt5k"><span class="legend-color-box" style="background: #166534;"></span><span>> 5,000</span></div>
            <div class="legend-scale-item" data-range="35k-5k"><span class="legend-color-box" style="background: #15803D;"></span><span>3,500 – 5,000</span></div>
            <div class="legend-scale-item" data-range="2k-35k"><span class="legend-color-box" style="background: #84CC16;"></span><span>2,000 – 3,500</span></div>
            <div class="legend-scale-item" data-range="1k-2k"><span class="legend-color-box" style="background: #FACC15;"></span><span>1,000 – 2,000</span></div>
            <div class="legend-scale-item" data-range="lt1k"><span class="legend-color-box" style="background: #2563EB;"></span><span>< 1,000</span></div>
            <div class="legend-scale-item" data-range="nodata"><span class="legend-color-box" style="background: #CBD5E1;"></span><span>No data</span></div>
        `;
    } else if (currentIndicator === 'area') {
        titleEl.textContent = 'CULTIVATED AREA (HA)';
        listEl.innerHTML = `
            <div class="legend-scale-item" data-range="gt2k"><span class="legend-color-box" style="background: #166534;"></span><span>> 2,000</span></div>
            <div class="legend-scale-item" data-range="15k-2k"><span class="legend-color-box" style="background: #15803D;"></span><span>1,500 – 2,000</span></div>
            <div class="legend-scale-item" data-range="1k-15k"><span class="legend-color-box" style="background: #84CC16;"></span><span>1,000 – 1,500</span></div>
            <div class="legend-scale-item" data-range="500-1k"><span class="legend-color-box" style="background: #FACC15;"></span><span>500 – 1,000</span></div>
            <div class="legend-scale-item" data-range="lt500"><span class="legend-color-box" style="background: #2563EB;"></span><span>< 500</span></div>
            <div class="legend-scale-item" data-range="nodata"><span class="legend-color-box" style="background: #CBD5E1;"></span><span>No data</span></div>
        `;
    } else {
        titleEl.textContent = 'YIELD (T/HA)';
        listEl.innerHTML = `
            <div class="legend-scale-item" data-range="gt4"><span class="legend-color-box" style="background: #166534;"></span><span>> 4.0</span></div>
            <div class="legend-scale-item" data-range="3-4"><span class="legend-color-box" style="background: #15803D;"></span><span>3.0 – 4.0</span></div>
            <div class="legend-scale-item" data-range="2-3"><span class="legend-color-box" style="background: #84CC16;"></span><span>2.0 – 3.0</span></div>
            <div class="legend-scale-item" data-range="1-2"><span class="legend-color-box" style="background: #FACC15;"></span><span>1.0 – 2.0</span></div>
            <div class="legend-scale-item" data-range="lt1"><span class="legend-color-box" style="background: #2563EB;"></span><span>< 1.0</span></div>
            <div class="legend-scale-item" data-range="nodata"><span class="legend-color-box" style="background: #CBD5E1;"></span><span>No data</span></div>
        `;
    }
}

function updateBottomKpis() {
    let year = 2025;
    let sCode = 'A';
    if (currentSeason && currentSeason.length >= 5) {
        year = currentSeason.slice(0, 4);
        sCode = currentSeason.slice(4);
    }
    const url = `/indicators/api/summary/?crop=${encodeURIComponent(currentCrop)}&year=${year}&season=${sCode}&source=official`;
    fetch(url)
        .then(r => r.json())
        .then(res => {
            if (res && res.data) {
                const d = res.data;
                const cropsEl = document.getElementById('kpi-tracked-crops');
                const recordsEl = document.getElementById('kpi-validated-records');
                const geoEl = document.getElementById('kpi-geographic-coverage');
                const prodEl = document.getElementById('kpi-total-production');

                if (cropsEl && d.crops_count !== undefined) cropsEl.textContent = d.crops_count;
                if (recordsEl && d.total_plots !== undefined) recordsEl.textContent = Number(d.total_plots).toLocaleString();
                if (geoEl && d.districts_covered !== undefined) geoEl.textContent = d.districts_covered;
                if (prodEl && d.total_production_mt !== undefined) {
                    prodEl.textContent = Number(d.total_production_mt).toLocaleString(undefined, {maximumFractionDigits: 0}) + ' t';
                }
            }
        })
        .catch(err => {
            console.warn('Could not update bottom KPIs from API:', err);
        });
}

/* ==========================================================================
   6. INTERACTIVE LEGEND HOVER
   ========================================================================== */
function setupLegendInteractivity() {
    const legendEl = document.getElementById('map-legend');
    if (!legendEl) return;

    legendEl.addEventListener('mouseover', e => {
        const item = e.target.closest('.legend-scale-item');
        if (!item || !geoLayer) return;

        const colorBox = item.querySelector('.legend-color-box');
        if (!colorBox) return;
        const targetColorHex = colorBox.style.backgroundColor;

        geoLayer.eachLayer(layer => {
            const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
            const val = getIndicatorValue(name);
            const dColor = getDistrictColor(val);
            if (isColorMatch(dColor, targetColorHex)) {
                layer.setStyle({
                    fillOpacity: 1.0,
                    weight: 3.0,
                    color: '#0f172a'
                });
            } else {
                layer.setStyle({
                    fillOpacity: 0.22,
                    weight: 0.8,
                    color: '#ffffff'
                });
            }
        });
    });

    legendEl.addEventListener('mouseout', e => {
        if (!legendEl.contains(e.relatedTarget)) {
            applyDataRefresh();
        }
    });
}

function isColorMatch(hexColor, rgbOrHex) {
    if (!hexColor || !rgbOrHex) return false;
    const tempDiv = document.createElement('div');
    tempDiv.style.color = hexColor;
    const hexAsRgb = tempDiv.style.color;
    tempDiv.style.color = rgbOrHex;
    const targetAsRgb = tempDiv.style.color;
    return hexAsRgb === targetAsRgb;
}

/* ==========================================================================
   7. NAVBAR GLOBAL SEARCH BAR INTEGRATION
   ========================================================================== */
function setupHeaderSearchIntegration() {
    const searchInput = document.querySelector('.header-search-pill input');
    if (!searchInput) return;

    searchInput.addEventListener('input', e => {
        const query = (e.target.value || '').trim().toLowerCase();
        if (!query || query.length < 2) return;

        const match = Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase().startsWith(query)) ||
                      Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase().includes(query));
        if (match) {
            selectDistrict(match, true);
        }
    });

    searchInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = (e.target.value || '').trim().toLowerCase();
            const match = Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase() === query) ||
                          Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase().includes(query));
            if (match) {
                selectDistrict(match, true);
            }
        }
    });
}

/* ==========================================================================
   8. CUSTOM MAP CONTROLS
   ========================================================================== */
function setupCustomControls() {
    const inBtn = document.getElementById('ctrl-zoom-in');
    const outBtn = document.getElementById('ctrl-zoom-out');
    const centerBtn = document.getElementById('ctrl-recenter');

    if (inBtn) inBtn.addEventListener('click', () => map && map.zoomIn());
    if (outBtn) outBtn.addEventListener('click', () => map && map.zoomOut());
    if (centerBtn) centerBtn.addEventListener('click', () => {
        if (map && geoLayer) {
            map.fitBounds(geoLayer.getBounds(), { padding: [16, 16] });
        } else if (map) {
            map.setView([-1.9403, 29.8739], 8.5);
        }
    });

    const modalBackdrop = document.getElementById('district-report-modal');
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', e => {
            if (e.target === modalBackdrop) {
                closeDistrictReportModal();
            }
        });
    }

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            closeDistrictReportModal();
        }
    });
}

/* ==========================================================================
   9. PUBLIC DISTRICT REPORT DOSSIER MODAL CONTROLLER
   ========================================================================== */
function populateDistrictReportModal(districtName) {
    const dName = districtName || pinnedDistrictName || 'Nyabihu';
    const province = DISTRICT_PROVINCE_MAP[dName] || '';
    const metrics = getDistrictMetrics(dName);
    const seasonLabel = document.querySelector('#map-filter-season option:checked')?.textContent || currentSeason;

    const titleEl = document.getElementById('modal-district-title');
    const provEl = document.getElementById('modal-province-name');
    const seasonEl = document.getElementById('modal-season-label');
    const cropEl = document.getElementById('modal-crop-label');
    const tableSeasonEl = document.getElementById('modal-table-season');

    if (titleEl) titleEl.textContent = `${dName} District Report`;
    if (provEl) provEl.textContent = province;
    if (seasonEl) seasonEl.textContent = seasonLabel;
    if (cropEl) cropEl.textContent = currentCrop;
    if (tableSeasonEl) tableSeasonEl.textContent = seasonLabel;

    document.querySelectorAll('.modal-active-crop-text').forEach(el => {
        el.textContent = currentCrop;
    });

    const kpiYieldEl = document.getElementById('modal-kpi-yield');
    const kpiAreaEl = document.getElementById('modal-kpi-area');
    const kpiProdEl = document.getElementById('modal-kpi-prod');
    const kpiRankEl = document.getElementById('modal-kpi-rank');
    const yieldBadgeEl = document.getElementById('modal-yield-badge');
    const rankSubEl = document.getElementById('modal-rank-sub');

    if (kpiYieldEl) kpiYieldEl.innerHTML = metrics.yield !== null ? `${metrics.yield.toFixed(1)} <span class="unit">t/ha</span>` : `— <span class="unit">t/ha</span>`;
    if (kpiAreaEl) kpiAreaEl.innerHTML = metrics.area !== null ? `${metrics.area.toLocaleString()} <span class="unit">ha</span>` : `— <span class="unit">ha</span>`;
    if (kpiProdEl) kpiProdEl.innerHTML = metrics.prod !== null ? `${metrics.prod.toLocaleString()} <span class="unit">t</span>` : `— <span class="unit">t</span>`;

    // Dynamic Rank Computation across all districts with observations
    const distList = Object.entries(liveDistrictData)
        .filter(([name, data]) => data.yield_tha !== undefined && data.yield_tha !== null)
        .map(([name, data]) => ({ name, yield: Number(data.yield_tha) }));
    distList.sort((a, b) => b.yield - a.yield);
    const rankIdx = distList.findIndex(d => d.name === dName);
    const rankNum = rankIdx !== -1 ? (rankIdx + 1) : null;

    if (kpiRankEl) {
        kpiRankEl.innerHTML = rankNum !== null ? `#${rankNum} <span class="unit">/ ${distList.length}</span>` : `— <span class="unit">/ ${distList.length}</span>`;
    }
    if (rankSubEl) {
        if (rankNum === null) {
            rankSubEl.textContent = 'No observations recorded in this period';
        } else if (rankNum <= 5) {
            rankSubEl.textContent = 'Top tier productivity nationwide';
        } else if (rankNum <= 15) {
            rankSubEl.textContent = 'Above average national productivity';
        } else {
            rankSubEl.textContent = 'Developing agricultural territory';
        }
    }

    // Benchmark comparison (against observed national mean)
    const totalYield = distList.reduce((sum, d) => sum + d.yield, 0);
    const natAvg = distList.length > 0 ? (totalYield / distList.length) : null;

    if (yieldBadgeEl) {
        if (metrics.yield !== null && natAvg !== null && natAvg > 0) {
            const diffPct = ((metrics.yield - natAvg) / natAvg) * 100;
            yieldBadgeEl.style.display = 'inline-block';
            if (diffPct >= 0) {
                yieldBadgeEl.textContent = `+${diffPct.toFixed(0)}% vs Nat'l Avg`;
                yieldBadgeEl.style.background = '#DCFCE7';
                yieldBadgeEl.style.color = '#15803d';
            } else {
                yieldBadgeEl.textContent = `${diffPct.toFixed(0)}% vs Nat'l Avg`;
                yieldBadgeEl.style.background = '#FEF3C7';
                yieldBadgeEl.style.color = '#B45309';
            }
        } else {
            yieldBadgeEl.style.display = 'none';
        }
    }

    // Multi-Crop Portfolio Table
    const tbody = document.getElementById('modal-crops-tbody');
    if (tbody) {
        const cropOrder = ['Maize', 'Beans', 'Irish Potato', 'Rice', 'Cassava'];
        let rowsHtml = '';

        cropOrder.forEach(cName => {
            const isCurrent = (cName === currentCrop);
            const rowClass = isCurrent ? 'highlight-active-row' : '';

            if (isCurrent && metrics.yield !== null) {
                let badgeClass = 'normal';
                let badgeText = 'Observed Harvest';
                if (metrics.yield >= 3.5) { badgeClass = 'high'; badgeText = 'High Yield Zone'; }
                else if (metrics.yield < 1.5) { badgeClass = 'moderate'; badgeText = 'Moderate Output'; }

                rowsHtml += `
                    <tr class="${rowClass}">
                        <td>
                            <strong>${cName}</strong>
                            <span style="font-size: 0.70rem; color: #16a34a; font-weight: 700; margin-left: 6px;">● Active Selection</span>
                        </td>
                        <td>${metrics.yield.toFixed(1)} t/ha</td>
                        <td>${metrics.area !== null ? metrics.area.toLocaleString() + ' ha' : '—'}</td>
                        <td>${metrics.prod !== null ? metrics.prod.toLocaleString() + ' t' : '—'}</td>
                        <td><span class="crop-status-badge ${badgeClass}">${badgeText}</span></td>
                    </tr>
                `;
            } else if (isCurrent) {
                rowsHtml += `
                    <tr class="${rowClass}">
                        <td>
                            <strong>${cName}</strong>
                            <span style="font-size: 0.70rem; color: #16a34a; font-weight: 700; margin-left: 6px;">● Active Selection</span>
                        </td>
                        <td><span style="color: #94a3b8;">—</span></td>
                        <td><span style="color: #94a3b8;">—</span></td>
                        <td><span style="color: #94a3b8;">—</span></td>
                        <td><span class="crop-status-badge normal">No Observations</span></td>
                    </tr>
                `;
            } else {
                rowsHtml += `
                    <tr>
                        <td><strong>${cName}</strong></td>
                        <td><span style="color: #94a3b8;">—</span></td>
                        <td><span style="color: #94a3b8;">—</span></td>
                        <td><span style="color: #94a3b8;">—</span></td>
                        <td><span class="crop-status-badge normal" style="opacity: 0.7;">Select crop to inspect</span></td>
                    </tr>
                `;
            }
        });
        tbody.innerHTML = rowsHtml;
    }

    // Regional Agro-Ecological Characteristics
    const zoneInfo = DISTRICT_AGRO_ZONES[province] || DISTRICT_AGRO_ZONES['Western Province'];
    const zoneEl = document.getElementById('modal-profile-zone');
    const elevEl = document.getElementById('modal-profile-elevation');
    const climEl = document.getElementById('modal-profile-climate');
    const stapEl = document.getElementById('modal-profile-staples');
    const secuEl = document.getElementById('modal-profile-security');
    const focuEl = document.getElementById('modal-profile-focus');

    if (zoneEl) zoneEl.textContent = zoneInfo.zone;
    if (elevEl) elevEl.textContent = zoneInfo.elevation;
    if (climEl) climEl.textContent = zoneInfo.climate;
    if (stapEl) stapEl.textContent = zoneInfo.staples;
    if (secuEl) secuEl.textContent = zoneInfo.security;
    if (focuEl) focuEl.textContent = zoneInfo.focus;

    // Multi-Season Inter-Season Trend
    const trendStatsEl = document.getElementById('modal-trend-stats');
    if (trendStatsEl) {
        trendStatsEl.innerHTML = `
            <div class="trend-stat-chip">
                <span>Selected Season:</span>
                <strong>${metrics.yield !== null ? metrics.yield.toFixed(1) + ' t/ha' : '—'}</strong>
            </div>
            <div class="trend-stat-chip">
                <span>Surveillance Status:</span>
                <strong>${metrics.plots > 0 ? metrics.plots + ' plots surveyed' : 'No records'}</strong>
            </div>
        `;
    }
}

function openDistrictReportModal(districtName) {
    const dName = districtName || pinnedDistrictName || 'Nyabihu';
    populateDistrictReportModal(dName);

    const modal = document.getElementById('district-report-modal');
    if (!modal) return;

    modal.style.display = 'flex';
    requestAnimationFrame(() => {
        modal.classList.add('open');
    });
    document.body.style.overflow = 'hidden';
}

function closeDistrictReportModal() {
    const modal = document.getElementById('district-report-modal');
    if (!modal) return;

    modal.classList.remove('open');
    setTimeout(() => {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }, 220);
}

window.openDistrictReportModal = openDistrictReportModal;
window.closeDistrictReportModal = closeDistrictReportModal;
