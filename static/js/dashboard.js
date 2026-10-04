/**
 * AgriLens National Dashboard Visualizations & Analytics
 * Brand Identity: Official National Institute of Statistics of Rwanda (NISR)
 * Colors:
 *   - Pantone 2728 C (Royal Blue): #005CAB
 *   - Pantone Cyan (Cyan):         #00AEEF
 *   - Pantone 362 C (Green):       #46962B
 *   - Pantone 3965 C (Yellow):     #F3EA00
 */

document.addEventListener('DOMContentLoaded', () => {
    initDashboardMiniMap();
    initMarketPriceChart();
    initLossStageChart();
});

/* ==========================================================================
   1. REAL RWANDA LEAFLET MINI-MAP FOR DASHBOARD
   ========================================================================== */
let dashMap = null;
let dashGeojsonLayer = null;
let currentDashLayer = 'yield';

const DASH_DISTRICT_DATA = {
    'Musanze':    { yieldNum: 4200, yield: '4,200 kg/ha', irrig: 32, loss: 7.2,  crops: 'Irish Potato, Maize' },
    'Nyabihu':    { yieldNum: 4100, yield: '4,100 kg/ha', irrig: 26, loss: 9.1,  crops: 'Irish Potato, Tea' },
    'Burera':     { yieldNum: 3500, yield: '3,500 kg/ha', irrig: 21, loss: 6.8,  crops: 'Climbing Beans, Wheat' },
    'Gicumbi':    { yieldNum: 3100, yield: '3,100 kg/ha', irrig: 12, loss: 17.8, crops: 'Beans, Maize, Tea' },
    'Rulindo':    { yieldNum: 3300, yield: '3,300 kg/ha', irrig: 24, loss: 11.2, crops: 'Coffee, Vegetables' },
    'Rwamagana':  { yieldNum: 5100, yield: '5,100 kg/ha', irrig: 88, loss: 5.4,  crops: 'Marshland Rice, Maize' },
    'Bugesera':   { yieldNum: 2700, yield: '2,700 kg/ha', irrig: 14, loss: 16.4, crops: 'Cassava, Beans' },
    'Nyagatare':  { yieldNum: 3400, yield: '3,400 kg/ha', irrig: 42, loss: 10.5, crops: 'Maize, Soya, Dairy' },
    'Kayonza':    { yieldNum: 2900, yield: '2,900 kg/ha', irrig: 22, loss: 14.1, crops: 'Maize, Bananas' },
    'Kirehe':     { yieldNum: 2600, yield: '2,600 kg/ha', irrig: 9,  loss: 14.5, crops: 'Bananas, Maize' },
    'Gatsibo':    { yieldNum: 3000, yield: '3,000 kg/ha', irrig: 18, loss: 12.3, crops: 'Rice, Maize' },
    'Ngoma':      { yieldNum: 2800, yield: '2,800 kg/ha', irrig: 16, loss: 13.9, crops: 'Bananas, Beans' },
    'Huye':       { yieldNum: 3300, yield: '3,300 kg/ha', irrig: 28, loss: 10.9, crops: 'Coffee, Cassava' },
    'Nyanza':     { yieldNum: 3100, yield: '3,100 kg/ha', irrig: 22, loss: 12.4, crops: 'Cassava, Maize' },
    'Gisagara':   { yieldNum: 2900, yield: '2,900 kg/ha', irrig: 15, loss: 14.2, crops: 'Rice, Soya' },
    'Nyamagabe':  { yieldNum: 3000, yield: '3,000 kg/ha', irrig: 18, loss: 13.1, crops: 'Tea, Wheat, Beans' },
    'Nyaruguru':  { yieldNum: 2950, yield: '2,950 kg/ha', irrig: 16, loss: 13.8, crops: 'Tea, Coffee' },
    'Muhanga':    { yieldNum: 3200, yield: '3,200 kg/ha', irrig: 24, loss: 11.5, crops: 'Coffee, Cassava' },
    'Kamonyi':    { yieldNum: 3400, yield: '3,400 kg/ha', irrig: 35, loss: 9.8,  crops: 'Vegetables, Rice' },
    'Ruhango':    { yieldNum: 3050, yield: '3,050 kg/ha', irrig: 20, loss: 12.8, crops: 'Cassava, Beans' },
    'Rubavu':     { yieldNum: 3900, yield: '3,900 kg/ha', irrig: 29, loss: 8.7,  crops: 'Vegetables, Beans' },
    'Rusizi':     { yieldNum: 3600, yield: '3,600 kg/ha', irrig: 62, loss: 12.1, crops: 'Marshland Rice, Tea' },
    'Rutsiro':    { yieldNum: 3100, yield: '3,100 kg/ha', irrig: 14, loss: 14.1, crops: 'Coffee, Beans' },
    'Karongi':    { yieldNum: 3200, yield: '3,200 kg/ha', irrig: 20, loss: 12.5, crops: 'Coffee, Tea' },
    'Nyamasheke': { yieldNum: 3000, yield: '3,000 kg/ha', irrig: 19, loss: 13.5, crops: 'Coffee, Tea' },
    'Ngororero':  { yieldNum: 3250, yield: '3,250 kg/ha', irrig: 17, loss: 13.0, crops: 'Beans, Maize' },
    'Nyarugenge': { yieldNum: 3100, yield: '3,100 kg/ha', irrig: 25, loss: 8.2,  crops: 'Urban Horticulture' },
    'Gasabo':     { yieldNum: 3400, yield: '3,400 kg/ha', irrig: 36, loss: 8.9,  crops: 'Vegetables, Maize' },
    'Kicukiro':   { yieldNum: 3200, yield: '3,200 kg/ha', irrig: 28, loss: 8.5,  crops: 'Horticulture, Poultry' }
};

function getDashDistrictColor(distName) {
    const data = DASH_DISTRICT_DATA[distName];
    if (!data) return '#CBD5E1';

    if (currentDashLayer === 'yield') {
        const y = data.yieldNum;
        return y >= 4000 ? '#46962B' : (y >= 3300 ? '#005CAB' : (y >= 3000 ? '#00AEEF' : '#D4A000'));
    } else if (currentDashLayer === 'irrig') {
        const ir = data.irrig;
        return ir >= 50 ? '#005CAB' : (ir >= 25 ? '#00AEEF' : (ir >= 15 ? '#80D7FA' : '#E6F7FE'));
    } else if (currentDashLayer === 'loss') {
        const l = data.loss;
        return l >= 15 ? '#DC2626' : (l >= 12 ? '#EA580C' : (l >= 9 ? '#F3EA00' : '#46962B'));
    }
    return '#005CAB';
}

async function initDashboardMiniMap() {
    const mapContainer = document.getElementById('dashboard-mini-map');
    if (!mapContainer || typeof L === 'undefined') return;

    dashMap = L.map('dashboard-mini-map', {
        center: [-1.9403, 29.8739],
        zoom: 8.5,
        minZoom: 8,
        maxZoom: 12,
        scrollWheelZoom: false,
        attributionControl: false,
        zoomControl: false
    });

    L.control.zoom({ position: 'bottomright' }).addTo(dashMap);

    // Free ESRI World Canvas tiles (crisp, zero watermarks)
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16
    }).addTo(dashMap);

    try {
        const resp = await fetch('/static/data/rwanda_districts.geojson');
        const geojson = await resp.json();

        dashGeojsonLayer = L.geoJSON(geojson, {
            style: (feature) => {
                const dName = feature.properties.shapeName;
                return {
                    fillColor: getDashDistrictColor(dName),
                    weight: 1.5,
                    opacity: 1,
                    color: '#FFFFFF',
                    fillOpacity: 0.82
                };
            },
            onEachFeature: (feature, layer) => {
                const dName = feature.properties.shapeName;
                const d = DASH_DISTRICT_DATA[dName] || { yield: 'N/A', irrig: 'N/A', crops: 'N/A' };
                layer.bindTooltip(`
                    <div style="font-weight: 800; font-size: 12px; color: #001F3B;">${dName} District</div>
                    <div style="font-size: 11px; margin-top: 2px;">Avg Yield: <strong style="color: #005CAB;">${d.yield}</strong></div>
                    <div style="font-size: 11px;">Irrigation: <strong>${d.irrig}%</strong> &bull; Loss: <strong>${d.loss}%</strong></div>
                `, { sticky: true, className: 'dash-map-tooltip' });

                layer.on({
                    mouseover: (e) => {
                        e.target.setStyle({ weight: 2.5, color: '#001F3B', fillOpacity: 0.95 });
                        e.target.bringToFront();
                    },
                    mouseout: (e) => {
                        dashGeojsonLayer.resetStyle(e.target);
                    }
                });
            }
        }).addTo(dashMap);

        // Layer selector buttons
        const layerButtons = document.querySelectorAll('.dash-map-pill');
        layerButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                layerButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentDashLayer = btn.getAttribute('data-dash-layer');

                if (dashGeojsonLayer) {
                    dashGeojsonLayer.eachLayer(l => {
                        const dName = l.feature.properties.shapeName;
                        l.setStyle({ fillColor: getDashDistrictColor(dName) });
                    });
                }
            });
        });
    } catch (err) {
        console.error('Failed to load dashboard geojson:', err);
    }
}

/* ==========================================================================
   2. INTERACTIVE COMMODITY MARKET PRICE TRENDS (CHART.JS)
   ========================================================================== */
let priceChart = null;

const COMMODITY_PRICE_SERIES = {
    maize: {
        title: 'Maize (Grain) - Weekly Wholesale Market Price',
        weeks: ['Week 34', 'Week 35', 'Week 36', 'Week 37', 'Week 38', 'Week 39'],
        kimironko: [490, 500, 510, 515, 520, 520],
        musanze:   [440, 450, 455, 460, 460, 465],
        huye:      [460, 470, 475, 480, 485, 485]
    },
    potato: {
        title: 'Irish Potato (Kinigi) - Weekly Wholesale Market Price',
        weeks: ['Week 34', 'Week 35', 'Week 36', 'Week 37', 'Week 38', 'Week 39'],
        kimironko: [410, 400, 395, 390, 385, 380],
        musanze:   [310, 300, 290, 285, 280, 280],
        huye:      [360, 355, 350, 345, 340, 340]
    },
    beans: {
        title: 'Climbing Beans - Weekly Wholesale Market Price',
        weeks: ['Week 34', 'Week 35', 'Week 36', 'Week 37', 'Week 38', 'Week 39'],
        kimironko: [700, 715, 725, 730, 740, 745],
        musanze:   [650, 660, 670, 675, 680, 685],
        huye:      [680, 690, 700, 705, 710, 715]
    },
    rice: {
        title: 'Marshland Milled Rice - Weekly Wholesale Market Price',
        weeks: ['Week 34', 'Week 35', 'Week 36', 'Week 37', 'Week 38', 'Week 39'],
        kimironko: [1140, 1145, 1150, 1150, 1150, 1155],
        musanze:   [1080, 1085, 1090, 1090, 1090, 1095],
        huye:      [1100, 1105, 1110, 1110, 1110, 1115]
    }
};

function initMarketPriceChart() {
    const ctx = document.getElementById('marketPriceChart');
    if (!ctx || typeof Chart === 'undefined') return;

    const initial = COMMODITY_PRICE_SERIES.maize;

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: initial.weeks,
            datasets: [
                {
                    label: 'Kigali (Kimironko)',
                    data: initial.kimironko,
                    borderColor: '#005CAB', // NISR Royal Blue
                    backgroundColor: 'rgba(0, 92, 171, 0.08)',
                    borderWidth: 2.5,
                    pointBackgroundColor: '#005CAB',
                    pointRadius: 4,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Musanze Hub',
                    data: initial.musanze,
                    borderColor: '#00AEEF', // NISR Cyan
                    backgroundColor: 'transparent',
                    borderWidth: 2.2,
                    pointBackgroundColor: '#00AEEF',
                    pointRadius: 4,
                    tension: 0.3
                },
                {
                    label: 'Huye Hub',
                    data: initial.huye,
                    borderColor: '#46962B', // NISR Green
                    backgroundColor: 'transparent',
                    borderWidth: 2.2,
                    pointBackgroundColor: '#46962B',
                    pointRadius: 4,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        usePointStyle: true,
                        font: { family: 'Plus Jakarta Sans', size: 11, weight: 600 }
                    }
                },
                tooltip: {
                    backgroundColor: '#001F3B',
                    titleFont: { family: 'Plus Jakarta Sans', size: 12, weight: 700 },
                    bodyFont: { family: 'Plus Jakarta Sans', size: 11 },
                    padding: 10,
                    callbacks: {
                        label: (c) => ` ${c.dataset.label}: ${c.raw.toLocaleString()} RWF / kg`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } }
                },
                y: {
                    grid: { color: '#E2E8F0', drawBorder: false },
                    ticks: {
                        font: { family: 'Plus Jakarta Sans', size: 10 },
                        callback: (v) => v + ' RWF'
                    }
                }
            }
        }
    });

    // Commodity Selector Tabs
    const tabs = document.querySelectorAll('.dash-crop-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const crop = tab.getAttribute('data-crop');
            updatePriceChartData(crop);
        });
    });
}

function updatePriceChartData(cropKey) {
    if (!priceChart) return;
    const series = COMMODITY_PRICE_SERIES[cropKey];
    if (!series) return;

    priceChart.data.datasets[0].data = series.kimironko;
    priceChart.data.datasets[1].data = series.musanze;
    priceChart.data.datasets[2].data = series.huye;
    priceChart.update();
}

/* ==========================================================================
   3. POST-HARVEST LOSS STAGE DONUT CHART (CHART.JS)
   ========================================================================== */
function initLossStageChart() {
    const ctx = document.getElementById('lossStageChart');
    if (!ctx || typeof Chart === 'undefined') return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [
                'On-Farm Storage (4.8%)',
                'Field Harvesting (3.4%)',
                'Transport / Logistics (2.1%)',
                'Market Handling (1.5%)'
            ],
            datasets: [{
                data: [4.8, 3.4, 2.1, 1.5],
                backgroundColor: [
                    '#D4A000', // NISR Yellow/Amber
                    '#46962B', // NISR Green
                    '#00AEEF', // NISR Cyan
                    '#005CAB'  // NISR Royal Blue
                ],
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        usePointStyle: true,
                        font: { family: 'Plus Jakarta Sans', size: 11, weight: 600 },
                        padding: 12
                    }
                },
                tooltip: {
                    backgroundColor: '#001F3B',
                    padding: 8,
                    callbacks: {
                        label: (c) => ` ${c.label}: ${c.raw}% Loss Rate`
                    }
                }
            }
        }
    });
}
