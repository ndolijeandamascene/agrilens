/**
 * AgriLens Public Home JavaScript
 * - Interactive Productivity Gap Simulator
 * - Real Rwanda Administrative Map with Official GeoJSON Polygons (30 Districts)
 * - Cascading Geographic Filters (Province -> District -> Sector)
 * - Free ESRI / OSM Basemaps with Zero Watermarks
 */

document.addEventListener('DOMContentLoaded', () => {
    initProductivitySimulator();
    initRealRwandaMap();
});

/* ==========================================================================
   1. PRODUCTIVITY GAP SIMULATOR (CONNECTED TO LIVE MICRODATA API)
   ========================================================================== */
const CROP_NAME_MAP = {
    maize: 'Maize',
    potato: 'Irish Potato',
    beans: 'Bush Beans',
    rice: 'Marshland Rice'
};

function initProductivitySimulator() {
    const tabs = document.querySelectorAll('.crop-tab');
    if (!tabs.length) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const cropKey = tab.getAttribute('data-crop');
            await updateSimulatorView(cropKey);
        });
    });

    // Initial load for active tab
    const activeTab = document.querySelector('.crop-tab.active');
    if (activeTab) {
        updateSimulatorView(activeTab.getAttribute('data-crop'));
    }
}

const simulatorClientCache = {};

function renderSimulatorData(data, subtextEl) {
    if (data.is_sufficient_data && data.benchmark && data.lagging) {
        const b = data.benchmark;
        const l = data.lagging;

        // District A (Benchmark)
        const distAName = document.getElementById('dist-a-name');
        if (distAName) distAName.textContent = `${b.district_name} District`;
        const distAProv = document.getElementById('dist-a-prov');
        if (distAProv) distAProv.textContent = b.province_name;
        const distAYield = document.getElementById('dist-a-yield');
        if (distAYield) distAYield.textContent = b.yield_kg_per_ha.toLocaleString();

        setBarAndValue('dist-a-irrig-val', 'dist-a-irrig-bar', b.irrigation_rate);
        setBarAndValue('dist-a-seed-val', 'dist-a-seed-bar', b.improved_seed_rate);
        setBarAndValue('dist-a-fert-val', 'dist-a-fert-bar', b.fertilizer_rate);
        setBarAndValue('dist-a-loss-val', 'dist-a-loss-bar', b.loss_rate);

        // Center Gap
        const gapPercent = document.getElementById('gap-percent-val');
        if (gapPercent) gapPercent.textContent = `${data.gap_percentage}%`;
        if (subtextEl) {
            subtextEl.textContent = `Observed empirical gap: ${b.district_name} vs ${l.district_name} (${data.yield_difference_kg_per_ha.toLocaleString()} kg/ha spread)`;
        }

        // District B (Lagging)
        const distBName = document.getElementById('dist-b-name');
        if (distBName) distBName.textContent = `${l.district_name} District`;
        const distBProv = document.getElementById('dist-b-prov');
        if (distBProv) distBProv.textContent = l.province_name;
        const distBYield = document.getElementById('dist-b-yield');
        if (distBYield) distBYield.textContent = l.yield_kg_per_ha.toLocaleString();

        setBarAndValue('dist-b-irrig-val', 'dist-b-irrig-bar', l.irrigation_rate);
        setBarAndValue('dist-b-seed-val', 'dist-b-seed-bar', l.improved_seed_rate);
        setBarAndValue('dist-b-fert-val', 'dist-b-fert-bar', l.fertilizer_rate);
        setBarAndValue('dist-b-loss-val', 'dist-b-loss-bar', l.loss_rate);
    } else {
        // Insufficient data state (Strict statistical policy)
        const gapPercent = document.getElementById('gap-percent-val');
        if (gapPercent) gapPercent.textContent = 'N/A';
        if (subtextEl) {
            subtextEl.textContent = data.reason || 'Insufficient observations for a reliable benchmark comparison.';
        }
    }
}

async function updateSimulatorView(cropKey) {
    const cropName = CROP_NAME_MAP[cropKey] || 'Maize';
    const subtextEl = document.getElementById('gap-subtext-val');

    // 1. Instant Cache Hit: 0ms UI switch
    if (simulatorClientCache[cropKey]) {
        renderSimulatorData(simulatorClientCache[cropKey], subtextEl);
        return;
    }

    if (subtextEl) {
        subtextEl.textContent = `Fetching verified microdata for ${cropName}...`;
    }

    try {
        const resp = await fetch(`/indicators/api/productivity-gap/?crop=${encodeURIComponent(cropName)}&year=2025&season=A`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const result = await resp.json();

        if (result.status === 'success' && result.data) {
            simulatorClientCache[cropKey] = result.data;
            renderSimulatorData(result.data, subtextEl);
        }
    } catch (err) {
        console.warn('Could not fetch productivity gap from API:', err);
        if (subtextEl) {
            subtextEl.textContent = 'API unavailable. Please check connectivity or try another crop.';
        }
    }
}

function setBarAndValue(valId, barId, num) {
    const valEl = document.getElementById(valId);
    const barEl = document.getElementById(barId);
    const formatted = (num !== null && num !== undefined) ? `${num}%` : '—';
    if (valEl) valEl.textContent = formatted;
    if (barEl) barEl.style.width = (num !== null && num !== undefined) ? `${Math.min(100, Math.max(0, num))}%` : '0%';
}


/* ==========================================================================
   2. RWANDA ADMINISTRATIVE HIERARCHY & METADATA
   ========================================================================== */
const DISTRICT_ADMIN = {
    // KIGALI (3)
    'Gasabo': { province: 'Kigali', provName: 'City of Kigali', market: 'Kimironko Wholesale Market' },
    'Kicukiro': { province: 'Kigali', provName: 'City of Kigali', market: 'Zinia Modern Market' },
    'Nyarugenge': { province: 'Kigali', provName: 'City of Kigali', market: 'Nyabugogo Wholesale Market' },

    // NORTH (5)
    'Burera': { province: 'North', provName: 'Northern Province', market: 'Kirambo Market' },
    'Gakenke': { province: 'North', provName: 'Northern Province', market: 'Gakenke Ag Market' },
    'Gicumbi': { province: 'North', provName: 'Northern Province', market: 'Byumba Central Market' },
    'Musanze': { province: 'North', provName: 'Northern Province', market: 'Musanze Modern Market' },
    'Rulindo': { province: 'North', provName: 'Northern Province', market: 'Tare Agro Market' },

    // SOUTH (8)
    'Gisagara': { province: 'South', provName: 'Southern Province', market: 'Ndora Market' },
    'Huye': { province: 'South', provName: 'Southern Province', market: 'Huye Modern Market' },
    'Kamonyi': { province: 'South', provName: 'Southern Province', market: 'Ruyenzi Agribusiness Hub' },
    'Muhanga': { province: 'South', provName: 'Southern Province', market: 'Muhanga Central Market' },
    'Nyamagabe': { province: 'South', provName: 'Southern Province', market: 'Gasarenda Market' },
    'Nyanza': { province: 'South', provName: 'Southern Province', market: 'Nyanza Modern Market' },
    'Nyaruguru': { province: 'South', provName: 'Southern Province', market: 'Kibeho Market' },
    'Ruhango': { province: 'South', provName: 'Southern Province', market: 'Ruhango Ag Market' },

    // EAST (7)
    'Bugesera': { province: 'East', provName: 'Eastern Province', market: 'Nyamata Market' },
    'Gatsibo': { province: 'East', provName: 'Eastern Province', market: 'Kabarore Central Market' },
    'Kayonza': { province: 'East', provName: 'Eastern Province', market: 'Mukarange Market' },
    'Kirehe': { province: 'East', provName: 'Eastern Province', market: 'Nyakarambi Market' },
    'Ngoma': { province: 'East', provName: 'Eastern Province', market: 'Kibungo Modern Market' },
    'Nyagatare': { province: 'East', provName: 'Eastern Province', market: 'Nyagatare Grain Market' },
    'Rwamagana': { province: 'East', provName: 'Eastern Province', market: 'Rwamagana Agribusiness Market' },

    // WEST (7)
    'Karongi': { province: 'West', provName: 'Western Province', market: 'Rubengera Market' },
    'Ngororero': { province: 'West', provName: 'Western Province', market: 'Ngororero Central Market' },
    'Nyabihu': { province: 'West', provName: 'Western Province', market: 'Mukamira Modern Market' },
    'Nyamasheke': { province: 'West', provName: 'Western Province', market: 'Ntendezi Market' },
    'Rubavu': { province: 'West', provName: 'Western Province', market: 'Gisenyi Cross-Border Market' },
    'Rusizi': { province: 'West', provName: 'Western Province', market: 'Kamembe Central Market' },
    'Rutsiro': { province: 'West', provName: 'Western Province', market: 'Gihango Market' }
};

// Official NISR Brand Colors Palette (Pantone 2728 C, Pantone Cyan, Pantone 362 C, Pantone 3965 C)
const PROVINCE_COLORS = {
    'East': '#D4A000',    // NISR Gold/Amber (Pantone 3965 C tone)
    'North': '#46962B',   // NISR Green (Pantone 362 C)
    'West': '#00AEEF',    // NISR Cyan (Pantone Cyan)
    'South': '#005CAB',   // NISR Royal Blue (Pantone 2728 C)
    'Kigali': '#002B54'   // NISR Deep Navy
};

const PROVINCE_DISPLAY_NAMES = {
    'East': 'Eastern Province',
    'North': 'Northern Province',
    'South': 'Southern Province',
    'West': 'Western Province',
    'Kigali': 'City of Kigali'
};

/* ==========================================================================
   3. REAL RWANDA LEAFLET MAP & VECTOR POLYGONS
   ========================================================================== */
let map = null;
let geojsonLayer = null;
let rawGeojsonData = null;
let rawHierarchyData = null;
let liveDistrictMetrics = {};
let nationalSummaryData = null;
let currentLayer = 'province';
let activeDistrictName = null;
let sectorMarker = null;

async function initRealRwandaMap() {
    const mapElement = document.getElementById('rwanda-leaflet-map');
    if (!mapElement || typeof L === 'undefined') return;

    // Centered on Rwanda (Kigali / Central coordinates)
    map = L.map('rwanda-leaflet-map', {
        center: [-1.9403, 29.8739],
        zoom: 9,
        minZoom: 8,
        maxZoom: 14,
        scrollWheelZoom: false,
        attributionControl: false
    });

    // 100% Free ESRI Light Gray Canvas basemap with OpenStreetMap tiles (ZERO watermarks!)
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16,
        subdomains: ['server', 'services']
    }).addTo(map);

    // Fetch GeoJSON polygons, hierarchy, and live microdata indicators in parallel
    try {
        const [geoResp, hierResp, distResp, sumResp] = await Promise.all([
            fetch('/static/data/rwanda_districts.geojson'),
            fetch('/static/data/rwanda_hierarchy.json'),
            fetch('/indicators/api/districts/?year=2025&season=A'),
            fetch('/indicators/api/summary/?year=2025&season=A')
        ]);
        rawGeojsonData = await geoResp.json();
        rawHierarchyData = await hierResp.json();

        const distData = await distResp.json();
        if (distData.status === 'success' && Array.isArray(distData.data)) {
            distData.data.forEach(item => {
                liveDistrictMetrics[item.district_name] = item;
            });
        }

        const sumData = await sumResp.json();
        if (sumData.status === 'success' && sumData.data) {
            nationalSummaryData = sumData.data;
        }

        renderVectorPolygons();
        setupCascadingFilters();
        setupLayerToggles();
        resetToRwandaOverview();
    } catch (err) {
        console.error('Failed to load Rwanda spatial and survey datasets:', err);
    }
}

function getDistrictFillColor(distName) {
    const admin = DISTRICT_ADMIN[distName];
    if (!admin) return '#cbd5e1';

    if (currentLayer === 'province') {
        return PROVINCE_COLORS[admin.province] || '#005CAB';
    }

    const metrics = liveDistrictMetrics[distName];
    if (!metrics || !metrics.plots_sampled) {
        return '#cbd5e1'; // Neutral grey for unobserved districts
    }

    if (currentLayer === 'yield') {
        const y = metrics.yield_kg_per_ha;
        return y >= 4000 ? '#46962B' : (y >= 3000 ? '#68B84D' : (y >= 2000 ? '#9BD485' : '#FDF8A6'));
    } else if (currentLayer === 'irrigation') {
        const ir = metrics.irrigation_rate;
        return ir >= 40 ? '#005CAB' : (ir >= 20 ? '#00AEEF' : (ir > 0 ? '#7DD7FA' : '#E6F7FE'));
    } else if (currentLayer === 'fertilizer') {
        const f = metrics.fertilizer_rate;
        return f >= 60 ? '#265C14' : (f >= 40 ? '#46962B' : (f >= 20 ? '#83C56D' : '#E8F6E4'));
    } else if (currentLayer === 'loss') {
        const l = metrics.loss_rate;
        return l >= 15 ? '#DC2626' : (l >= 10 ? '#EA580C' : (l >= 5 ? '#F3EA00' : '#46962B'));
    }
    return '#005CAB';
}

function styleDistrictFeature(feature) {
    const distName = feature.properties.shapeName;
    const isSelected = activeDistrictName === distName;

    return {
        fillColor: getDistrictFillColor(distName),
        weight: isSelected ? 3.5 : 1.5,
        opacity: 1,
        color: isSelected ? '#0f172a' : '#ffffff',
        fillOpacity: isSelected ? 0.9 : 0.75
    };
}

function renderVectorPolygons() {
    if (geojsonLayer) {
        map.removeLayer(geojsonLayer);
    }

    geojsonLayer = L.geoJSON(rawGeojsonData, {
        style: styleDistrictFeature,
        onEachFeature: (feature, layer) => {
            const distName = feature.properties.shapeName;
            const admin = DISTRICT_ADMIN[distName] || {};
            const metrics = liveDistrictMetrics[distName];
            const yieldStr = metrics ? `${metrics.yield_kg_per_ha.toLocaleString()} kg/ha` : 'Not sampled';
            const plotsStr = metrics ? `${metrics.plots_sampled} plots` : '0 plots';

            // Hover tooltip
            layer.bindTooltip(`
                <div style="font-weight: 800; font-size: 13px;">${distName} District</div>
                <div style="font-size: 11px; opacity: 0.9;">${admin.provName || ''}</div>
                <div style="font-size: 11px; margin-top: 2px;">Avg Yield: <strong>${yieldStr}</strong></div>
                <div style="font-size: 10px; color: #64748B;">Sampled: ${plotsStr}</div>
            `, {
                className: 'district-map-tooltip',
                sticky: true,
                direction: 'top'
            });

            layer.on({
                mouseover: (e) => {
                    const l = e.target;
                    l.setStyle({
                        weight: 3,
                        color: '#0f172a',
                        fillOpacity: 0.9
                    });
                    l.bringToFront();
                },
                mouseout: (e) => {
                    geojsonLayer.resetStyle(e.target);
                    if (activeDistrictName) {
                        highlightSelectedDistrict(activeDistrictName);
                    }
                },
                click: () => {
                    selectDistrict(distName, true);
                }
            });
        }
    }).addTo(map);
}

function highlightSelectedDistrict(distName) {
    if (!geojsonLayer) return;
    geojsonLayer.eachLayer(layer => {
        if (layer.feature && layer.feature.properties.shapeName === distName) {
            layer.setStyle({
                weight: 4,
                color: '#0f172a',
                fillOpacity: 0.95
            });
            layer.bringToFront();
        } else {
            layer.setStyle({
                weight: 1.2,
                color: '#ffffff',
                fillOpacity: 0.65
            });
        }
    });
}

/* ==========================================================================
   4. CASCADING GEOGRAPHIC FILTERS (PROVINCE -> DISTRICT -> SECTOR)
   ========================================================================== */
function setupCascadingFilters() {
    const provSelect = document.getElementById('filter-province');
    const distSelect = document.getElementById('filter-district');
    const secSelect = document.getElementById('filter-sector');
    const resetBtn = document.getElementById('btn-reset-filters');

    // Populate all 30 districts initially in district dropdown
    populateDistrictsDropdown('');

    // Province Change
    provSelect.addEventListener('change', () => {
        const provKey = provSelect.value;
        populateDistrictsDropdown(provKey);
        resetSectorDropdown();

        if (provKey) {
            zoomToProvince(provKey);
            updateInspectorForProvince(provKey);
        } else {
            resetToRwandaOverview();
        }
    });

    // District Change
    distSelect.addEventListener('change', () => {
        const distName = distSelect.value;
        if (distName) {
            const info = DISTRICT_ADMIN[distName];
            if (info && provSelect.value !== info.province) {
                provSelect.value = info.province;
            }
            selectDistrict(distName, true);
            populateSectorsDropdown(distName);
        } else {
            resetSectorDropdown();
            if (provSelect.value) {
                zoomToProvince(provSelect.value);
                updateInspectorForProvince(provSelect.value);
            } else {
                resetToRwandaOverview();
            }
        }
    });

    // Sector Change
    secSelect.addEventListener('change', () => {
        const secName = secSelect.value;
        const distName = distSelect.value;
        if (secName && distName) {
            selectSector(distName, secName);
        }
    });

    // Reset button
    resetBtn.addEventListener('click', () => {
        provSelect.value = '';
        distSelect.value = '';
        populateDistrictsDropdown('');
        resetSectorDropdown();
        resetToRwandaOverview();
    });
}

function populateDistrictsDropdown(provKey) {
    const distSelect = document.getElementById('filter-district');
    distSelect.innerHTML = '<option value="">All Districts</option>';

    Object.keys(DISTRICT_ADMIN).sort().forEach(distName => {
        const info = DISTRICT_ADMIN[distName];
        if (!provKey || info.province === provKey) {
            const opt = document.createElement('option');
            opt.value = distName;
            opt.textContent = `${distName} (${info.provName})`;
            distSelect.appendChild(opt);
        }
    });
}

function populateSectorsDropdown(distName) {
    const secSelect = document.getElementById('filter-sector');
    secSelect.innerHTML = '<option value="">All Sectors in ' + distName + '</option>';
    secSelect.disabled = false;

    if (!rawHierarchyData) return;
    const info = DISTRICT_ADMIN[distName];
    if (!info) return;

    const provHierarchy = rawHierarchyData[info.province];
    if (provHierarchy && provHierarchy[distName]) {
        const sectors = Object.keys(provHierarchy[distName]).sort();
        sectors.forEach(secName => {
            const opt = document.createElement('option');
            opt.value = secName;
            opt.textContent = secName;
            secSelect.appendChild(opt);
        });

        const sectorRow = document.getElementById('inspect-sector-count-row');
        if (sectorRow) {
            document.getElementById('inspect-sectors').textContent = `${sectors.length} Sectors`;
        }
    }
}

function resetSectorDropdown() {
    const secSelect = document.getElementById('filter-sector');
    secSelect.innerHTML = '<option value="">Select District first</option>';
    secSelect.disabled = true;
    if (sectorMarker) {
        map.removeLayer(sectorMarker);
        sectorMarker = null;
    }
}

function selectDistrict(distName, shouldZoom) {
    activeDistrictName = distName;
    const admin = DISTRICT_ADMIN[distName];
    if (!admin) return;

    // Sync Dropdowns
    const provSelect = document.getElementById('filter-province');
    const distSelect = document.getElementById('filter-district');
    if (provSelect.value !== admin.province) {
        provSelect.value = admin.province;
        populateDistrictsDropdown(admin.province);
    }
    distSelect.value = distName;
    populateSectorsDropdown(distName);

    // Highlight polygon
    highlightSelectedDistrict(distName);

    // Zoom map to district bounds
    if (shouldZoom && geojsonLayer) {
        geojsonLayer.eachLayer(layer => {
            if (layer.feature && layer.feature.properties.shapeName === distName) {
                map.fitBounds(layer.getBounds(), { padding: [50, 50], maxZoom: 12 });
            }
        });
    }

    // Update Inspector UI with live metrics
    const m = liveDistrictMetrics[distName];
    document.getElementById('inspect-level').textContent = 'District Level';
    document.getElementById('inspect-province').textContent = admin.provName;
    document.getElementById('inspect-title').textContent = distName + ' District';
    document.getElementById('inspect-desc').textContent = m 
        ? `${distName} District under the Seasonal Agricultural Survey monitoring grid (${m.plots_sampled} verified survey plots).`
        : `${distName} District had no survey plots recorded in the 2025A sample.`;
    document.getElementById('inspect-crops').textContent = 'Priority Crops (Maize, Beans, Irish Potato, Rice, etc.)';
    document.getElementById('inspect-yield').textContent = m ? `${m.yield_kg_per_ha.toLocaleString()} kg/ha (Weighted)` : 'Not sampled in 2025A';
    document.getElementById('inspect-irrig').textContent = m ? (m.irrigation_rate > 0 ? `${m.irrigation_rate}%` : '0.0% (Unmapped in pilot batch)') : '—';
    document.getElementById('inspect-fert').textContent = m ? `${m.fertilizer_rate}% (Inorganic adoption)` : '—';
    document.getElementById('inspect-mech').textContent = '0.0% (Unmapped in pilot batch)';
    document.getElementById('inspect-loss').textContent = m ? `${m.loss_rate}% (Reported loss)` : '—';
    document.getElementById('inspect-market').textContent = admin.market || `${distName} Ag Market`;
    const sectorCountEl = document.getElementById('inspect-sectors');
    if (sectorCountEl) {
        sectorCountEl.textContent = m ? `${m.plots_sampled} Survey Plots` : '0 Plots';
    }
}

function selectSector(distName, secName) {
    const admin = DISTRICT_ADMIN[distName];
    if (!admin) return;
    const m = liveDistrictMetrics[distName];

    // Zoom into district and drop a marker
    if (geojsonLayer) {
        geojsonLayer.eachLayer(layer => {
            if (layer.feature && layer.feature.properties.shapeName === distName) {
                const center = layer.getBounds().getCenter();
                map.setView(center, 12);

                if (sectorMarker) map.removeLayer(sectorMarker);

                const icon = L.divIcon({
                    className: 'custom-sector-pin',
                    html: `<div style="
                        background: #0f172a;
                        color: #4ade80;
                        font-weight: 800;
                        font-size: 11px;
                        padding: 5px 10px;
                        border-radius: 9999px;
                        border: 2px solid #ffffff;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    "><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> ${secName} Sector</div>`,
                    iconSize: [120, 30],
                    iconAnchor: [60, 15]
                });

                sectorMarker = L.marker(center, { icon: icon }).addTo(map);
            }
        });
    }

    // Update Inspector to Sector Profile
    document.getElementById('inspect-level').textContent = 'Sector Profile';
    document.getElementById('inspect-province').textContent = `${admin.provName} &bull; ${distName}`;
    document.getElementById('inspect-title').textContent = `${secName} Sector`;
    document.getElementById('inspect-desc').textContent = `Administrative sector in ${distName} District under the Seasonal Agricultural Survey monitoring grid.`;
    document.getElementById('inspect-crops').textContent = 'Sub-district Survey Area';
    document.getElementById('inspect-yield').textContent = m ? `${m.yield_kg_per_ha.toLocaleString()} kg/ha (District Baseline)` : 'Not sampled';
    document.getElementById('inspect-irrig').textContent = m ? (m.irrigation_rate > 0 ? `${m.irrigation_rate}%` : '0.0% (Unmapped in pilot batch)') : '—';
    document.getElementById('inspect-fert').textContent = m ? `${m.fertilizer_rate}% (District baseline)` : '—';
    document.getElementById('inspect-mech').textContent = '0.0% (Unmapped in pilot batch)';
    document.getElementById('inspect-loss').textContent = m ? `${m.loss_rate}%` : '—';
    document.getElementById('inspect-market').textContent = `${secName} Cooperative Collection Center`;
}

function zoomToProvince(provKey) {
    activeDistrictName = null;
    if (!geojsonLayer) return;

    const bounds = L.latLngBounds([]);
    geojsonLayer.eachLayer(layer => {
        const dName = layer.feature.properties.shapeName;
        const dAdmin = DISTRICT_ADMIN[dName];
        if (dAdmin && dAdmin.province === provKey) {
            bounds.extend(layer.getBounds());
            layer.setStyle({
                weight: 2,
                color: '#0f172a',
                fillOpacity: 0.9
            });
        } else {
            layer.setStyle({
                weight: 1,
                color: '#ffffff',
                fillOpacity: 0.35
            });
        }
    });

    if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [30, 30] });
    }
}

function updateInspectorForProvince(provKey) {
    const provName = PROVINCE_DISPLAY_NAMES[provKey] || provKey;
    const distList = Object.keys(DISTRICT_ADMIN).filter(k => DISTRICT_ADMIN[k].province === provKey);
    const sampledDistricts = distList.map(k => liveDistrictMetrics[k]).filter(Boolean);
    const totalPlots = sampledDistricts.reduce((acc, d) => acc + (d.plots_sampled || 0), 0);
    const avgYield = sampledDistricts.length > 0 
        ? Math.round(sampledDistricts.reduce((acc, d) => acc + (d.yield_kg_per_ha || 0), 0) / sampledDistricts.length)
        : 0;
    const avgFert = sampledDistricts.length > 0 
        ? (sampledDistricts.reduce((acc, d) => acc + (d.fertilizer_rate || 0), 0) / sampledDistricts.length).toFixed(1)
        : '0.0';

    document.getElementById('inspect-level').textContent = 'Province Level';
    document.getElementById('inspect-province').textContent = 'Republic of Rwanda';
    document.getElementById('inspect-title').textContent = provName;
    document.getElementById('inspect-desc').textContent = `Consists of ${distList.length} monitored administrative districts (${sampledDistricts.length} sampled in 2025A).`;
    document.getElementById('inspect-crops').textContent = 'Regional Grain & Food Crop Systems';
    document.getElementById('inspect-yield').textContent = avgYield > 0 ? `${avgYield.toLocaleString()} kg/ha (Provincial Mean)` : '—';
    document.getElementById('inspect-irrig').textContent = '0.0% (Unmapped in pilot batch)';
    document.getElementById('inspect-fert').textContent = `${avgFert}% Adoption`;
    document.getElementById('inspect-mech').textContent = '0.0% (Unmapped in pilot batch)';
    document.getElementById('inspect-loss').textContent = 'Survey Variable Aggregation';
    document.getElementById('inspect-market').textContent = `${provName} Central Trade Hubs`;
    document.getElementById('inspect-sectors').textContent = `${sampledDistricts.length} / ${distList.length} Districts (${totalPlots} Plots)`;
}

function resetToRwandaOverview() {
    activeDistrictName = null;
    if (geojsonLayer) {
        geojsonLayer.eachLayer(layer => {
            geojsonLayer.resetStyle(layer);
        });
    }
    if (sectorMarker) {
        map.removeLayer(sectorMarker);
        sectorMarker = null;
    }

    map.setView([-1.9403, 29.8739], 9);

    document.getElementById('inspect-level').textContent = 'National Overview';
    document.getElementById('inspect-province').textContent = 'Republic of Rwanda';
    document.getElementById('inspect-title').textContent = 'National Agricultural Grid';
    document.getElementById('inspect-desc').textContent = 'Official NISR Seasonal Agricultural Survey monitoring 30 districts across all 5 provinces.';
    document.getElementById('inspect-crops').textContent = 'Maize, Irish Potato, Bush Beans, Rice, Cassava';

    if (nationalSummaryData) {
        const s = nationalSummaryData;
        document.getElementById('inspect-yield').textContent = `${s.weighted_yield_kg_per_ha.toLocaleString()} kg/ha (Weighted National Mean)`;
        document.getElementById('inspect-irrig').textContent = `${s.adoption_rates.irrigation}% (Pilot batch unmapped)`;
        document.getElementById('inspect-fert').textContent = `${s.adoption_rates.inorganic_fertilizer}% (Inorganic Adoption)`;
        document.getElementById('inspect-mech').textContent = `${s.adoption_rates.mechanization}% (Pilot batch unmapped)`;
        document.getElementById('inspect-loss').textContent = `${s.loss_rate_percentage}% (Seasonal Loss Rate)`;
        document.getElementById('inspect-market').textContent = 'National Wholesale & Cross-Border Hubs';
        document.getElementById('inspect-sectors').textContent = `${s.districts_covered} Districts Sampled (${s.total_plots.toLocaleString()} Plots)`;
    } else {
        document.getElementById('inspect-yield').textContent = '1,959.9 kg/ha (Weighted National Mean)';
        document.getElementById('inspect-irrig').textContent = '0.0% (Pilot batch unmapped)';
        document.getElementById('inspect-fert').textContent = '36.6% (Inorganic Adoption)';
        document.getElementById('inspect-mech').textContent = '0.0% (Pilot batch unmapped)';
        document.getElementById('inspect-loss').textContent = '2.2% (Seasonal Loss Rate)';
        document.getElementById('inspect-market').textContent = 'National Wholesale & Cross-Border Hubs';
        document.getElementById('inspect-sectors').textContent = '27 Districts Sampled';
    }
}

/* ==========================================================================
   5. LAYER MODE TOGGLES (PROVINCE / YIELD / IRRIGATION / FERTILIZER / LOSS)
   ========================================================================== */
function setupLayerToggles() {
    const buttons = document.querySelectorAll('.map-pill-btn');
    const legendTitle = document.getElementById('legend-title');
    const legendItems = document.getElementById('legend-items');

    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentLayer = btn.getAttribute('data-layer');

            // Re-render polygons with new color scale
            if (geojsonLayer) {
                geojsonLayer.eachLayer(layer => {
                    const dName = layer.feature.properties.shapeName;
                    layer.setStyle({
                        fillColor: getDistrictFillColor(dName)
                    });
                });
            }

            // Update Legend Bar
            updateLegendBar(currentLayer, legendTitle, legendItems);
        });
    });
}

function updateLegendBar(layer, titleEl, itemsEl) {
    if (layer === 'province') {
        titleEl.textContent = '5 Provinces of Rwanda (NISR Palette):';
        itemsEl.innerHTML = `
            <span class="legend-chip"><span class="legend-color-box" style="background: #D4A000;"></span> Eastern</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #46962B;"></span> Northern</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #00AEEF;"></span> Western</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #005CAB;"></span> Southern</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #002B54;"></span> Kigali</span>
        `;
    } else if (layer === 'yield') {
        titleEl.textContent = 'Crop Yield Scale (kg/ha):';
        itemsEl.innerHTML = `
            <span class="legend-chip"><span class="legend-color-box" style="background: #46962B;"></span> 4,000+ (High)</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #68B84D;"></span> 3,300 - 3,999</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #9BD485;"></span> 3,000 - 3,299</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #FDF8A6;"></span> &lt; 3,000 (Lagging)</span>
        `;
    } else if (layer === 'irrigation') {
        titleEl.textContent = 'Irrigation Adoption Rate:';
        itemsEl.innerHTML = `
            <span class="legend-chip"><span class="legend-color-box" style="background: #005CAB;"></span> 60%+</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #00AEEF;"></span> 30% - 59%</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #7DD7FA;"></span> 20% - 29%</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #E6F7FE;"></span> &lt; 20%</span>
        `;
    } else if (layer === 'fertilizer') {
        titleEl.textContent = 'Fertilizer Adoption Rate:';
        itemsEl.innerHTML = `
            <span class="legend-chip"><span class="legend-color-box" style="background: #265C14;"></span> 65%+</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #46962B;"></span> 50% - 64%</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #83C56D;"></span> 45% - 49%</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #E8F6E4;"></span> &lt; 45%</span>
        `;
    } else if (layer === 'loss') {
        titleEl.textContent = 'Post-Harvest Loss Rate:';
        itemsEl.innerHTML = `
            <span class="legend-chip"><span class="legend-color-box" style="background: #DC2626;"></span> High Alert (&gt;15%)</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #EA580C;"></span> Moderate (12% - 15%)</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #F3EA00;"></span> Low (9% - 12%)</span>
            <span class="legend-chip"><span class="legend-color-box" style="background: #46962B;"></span> Minimal (&lt;9%)</span>
        `;
    }
}
