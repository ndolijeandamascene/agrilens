/**
 * AgriLens Public Home JavaScript
 * Interactive Productivity Gap Simulator & Rwanda Leaflet Geospatial Hub
 */

document.addEventListener('DOMContentLoaded', () => {
    initProductivitySimulator();
    initRwandaMap();
});

/* ==========================================================================
   1. PRODUCTIVITY GAP SIMULATOR
   ========================================================================== */
const CROP_DATA = {
    maize: {
        cropName: 'Maize',
        distA: {
            name: 'Musanze District',
            province: 'Northern Province',
            yieldVal: '4,200',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 32,
            seed: 71,
            fert: 64,
            mech: 28,
            loss: 7.2
        },
        distB: {
            name: 'Bugesera District',
            province: 'Eastern Province',
            yieldVal: '2,700',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 14,
            seed: 49,
            fert: 41,
            mech: 11,
            loss: 16.4
        },
        gap: '-35.7%',
        subtext: 'Observed difference between Musanze & Bugesera'
    },
    potato: {
        cropName: 'Irish Potato',
        distA: {
            name: 'Nyabihu District',
            province: 'Western Province',
            yieldVal: '18,400',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 26,
            seed: 82,
            fert: 78,
            mech: 19,
            loss: 9.1
        },
        distB: {
            name: 'Gicumbi District',
            province: 'Northern Province',
            yieldVal: '12,100',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 12,
            seed: 54,
            fert: 51,
            mech: 8,
            loss: 17.8
        },
        gap: '-34.2%',
        subtext: 'Observed difference between Nyabihu & Gicumbi'
    },
    beans: {
        cropName: 'Climbing Beans',
        distA: {
            name: 'Burera District',
            province: 'Northern Province',
            yieldVal: '1,950',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 21,
            seed: 74,
            fert: 58,
            mech: 14,
            loss: 6.8
        },
        distB: {
            name: 'Kirehe District',
            province: 'Eastern Province',
            yieldVal: '1,150',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 9,
            seed: 46,
            fert: 37,
            mech: 6,
            loss: 14.5
        },
        gap: '-41.0%',
        subtext: 'Observed difference between Burera & Kirehe'
    },
    rice: {
        cropName: 'Marshland Rice',
        distA: {
            name: 'Rwamagana District',
            province: 'Eastern Province',
            yieldVal: '5,100',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 88,
            seed: 91,
            fert: 85,
            mech: 39,
            loss: 5.4
        },
        distB: {
            name: 'Rusizi (Bugarama)',
            province: 'Western Province',
            yieldVal: '3,600',
            yieldUnit: 'kg / hectare (avg)',
            irrig: 62,
            seed: 68,
            fert: 63,
            mech: 22,
            loss: 12.1
        },
        gap: '-29.4%',
        subtext: 'Observed difference between Rwamagana & Rusizi'
    }
};

function initProductivitySimulator() {
    const tabs = document.querySelectorAll('.crop-tab');
    if (!tabs.length) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const cropKey = tab.getAttribute('data-crop');
            updateSimulatorView(cropKey);
        });
    });
}

function updateSimulatorView(cropKey) {
    const data = CROP_DATA[cropKey];
    if (!data) return;

    // District A
    document.getElementById('dist-a-name').textContent = data.distA.name;
    document.getElementById('dist-a-prov').textContent = data.distA.province;
    document.getElementById('dist-a-yield').textContent = data.distA.yieldVal;
    document.getElementById('dist-a-irrig-val').textContent = data.distA.irrig + '%';
    document.getElementById('dist-a-irrig-bar').style.width = data.distA.irrig + '%';
    document.getElementById('dist-a-seed-val').textContent = data.distA.seed + '%';
    document.getElementById('dist-a-seed-bar').style.width = data.distA.seed + '%';
    document.getElementById('dist-a-fert-val').textContent = data.distA.fert + '%';
    document.getElementById('dist-a-fert-bar').style.width = data.distA.fert + '%';
    document.getElementById('dist-a-mech-val').textContent = data.distA.mech + '%';
    document.getElementById('dist-a-mech-bar').style.width = data.distA.mech + '%';
    document.getElementById('dist-a-loss-val').textContent = data.distA.loss + '%';
    document.getElementById('dist-a-loss-bar').style.width = data.distA.loss + '%';

    // Center Gap
    document.getElementById('gap-percent-val').textContent = data.gap;
    document.getElementById('gap-subtext-val').textContent = data.subtext;

    // District B
    document.getElementById('dist-b-name').textContent = data.distB.name;
    document.getElementById('dist-b-prov').textContent = data.distB.province;
    document.getElementById('dist-b-yield').textContent = data.distB.yieldVal;
    document.getElementById('dist-b-irrig-val').textContent = data.distB.irrig + '%';
    document.getElementById('dist-b-irrig-bar').style.width = data.distB.irrig + '%';
    document.getElementById('dist-b-seed-val').textContent = data.distB.seed + '%';
    document.getElementById('dist-b-seed-bar').style.width = data.distB.seed + '%';
    document.getElementById('dist-b-fert-val').textContent = data.distB.fert + '%';
    document.getElementById('dist-b-fert-bar').style.width = data.distB.fert + '%';
    document.getElementById('dist-b-mech-val').textContent = data.distB.mech + '%';
    document.getElementById('dist-b-mech-bar').style.width = data.distB.mech + '%';
    document.getElementById('dist-b-loss-val').textContent = data.distB.loss + '%';
    document.getElementById('dist-b-loss-bar').style.width = data.distB.loss + '%';
}

/* ==========================================================================
   2. RWANDA LEAFLET MAP
   ========================================================================== */
const DISTRICT_GEO_DATA = [
    {
        name: 'Musanze',
        province: 'Northern Province',
        coords: [-1.4998, 29.6350],
        crops: 'Irish Potato, Maize, Climbing Beans',
        yield: '4,200 kg/ha',
        irrig: '32% (Gravity & Hillside)',
        fert: '64% (DAP & NPK)',
        loss: '7.2%',
        market: 'Musanze Modern Market',
        desc: 'Volcanic highland zone with highest Irish potato & highland maize productivity.'
    },
    {
        name: 'Nyabihu',
        province: 'Western Province',
        coords: [-1.6558, 29.5034],
        crops: 'Irish Potato, Tea, Pyrethrum',
        yield: '3,800 kg/ha',
        irrig: '26% (Small Hillside Schemes)',
        fert: '78% (DAP & Organic Manure)',
        loss: '9.1%',
        market: 'Mukamira Market',
        desc: 'High-altitude zone with heavy organic fertilizer adoption and anti-erosion terraces.'
    },
    {
        name: 'Bugesera',
        province: 'Eastern Province',
        coords: [-2.2166, 30.1500],
        crops: 'Cassava, Maize, Beans',
        yield: '2,700 kg/ha',
        irrig: '14% (Lake water pumping)',
        fert: '41% (DAP / Urea)',
        loss: '16.4%',
        market: 'Nyamata Market',
        desc: 'Eastern plateau with significant irrigation expansion opportunities around marshlands.'
    },
    {
        name: 'Huye',
        province: 'Southern Province',
        coords: [-2.5975, 29.7394],
        crops: 'Coffee, Beans, Maize, Rice',
        yield: '3,100 kg/ha',
        irrig: '22% (Valley Bottom & Marshland)',
        fert: '52% (NPK & Lime for acidic soil)',
        loss: '11.8%',
        market: 'Huye Modern Market',
        desc: 'Central plateau agro-ecological zone with active agricultural research partnerships.'
    },
    {
        name: 'Nyagatare',
        province: 'Eastern Province',
        coords: [-1.2981, 30.3256],
        crops: 'Maize, Soya, Dairy Fodder',
        yield: '3,450 kg/ha',
        irrig: '18% (Center pivot & valley dams)',
        fert: '55% (DAP & Urea)',
        loss: '13.2%',
        market: 'Nyagatare Central Market',
        desc: 'Key grain belt of Rwanda with widespread land consolidation and mechanization adoption.'
    },
    {
        name: 'Rwamagana',
        province: 'Eastern Province',
        coords: [-1.9486, 30.4347],
        crops: 'Rice, Banana, Vegetables',
        yield: '5,100 kg/ha',
        irrig: '88% (Marshland schemes)',
        fert: '85% (Urea & DAP)',
        loss: '5.4%',
        market: 'Rwamagana Agribusiness Market',
        desc: 'Major irrigated rice hub feeding urban markets with high cooperative participation.'
    },
    {
        name: 'Rubavu',
        province: 'Western Province',
        coords: [-1.6775, 29.2614],
        crops: 'Vegetables, Beans, Irish Potato',
        yield: '3,900 kg/ha',
        irrig: '29% (Lake Kivu & stream diversions)',
        fert: '68% (Mineral & manure)',
        loss: '8.7%',
        market: 'Gisenyi Cross-Border Market',
        desc: 'High-intensity vegetable production hub supplying cross-border regional markets.'
    },
    {
        name: 'Gicumbi',
        province: 'Northern Province',
        coords: [-1.6033, 30.0767],
        crops: 'Tea, Irish Potato, Wheat, Beans',
        yield: '3,200 kg/ha',
        irrig: '12% (Spring gravity fed)',
        fert: '51% (NPK & manure)',
        loss: '17.8%',
        market: 'Byumba Market',
        desc: 'Steep highland terrain with intensive terracing and high post-harvest storage needs.'
    },
    {
        name: 'Rusizi',
        province: 'Western Province',
        coords: [-2.4833, 28.9000],
        crops: 'Rice, Oil Palm, Cassava',
        yield: '3,600 kg/ha',
        irrig: '62% (Bugarama marshland)',
        fert: '63% (Urea & DAP)',
        loss: '12.1%',
        market: 'Kamembe Central Market',
        desc: 'Bugarama valley sub-tropical climate supporting intensive marshland rice cultivation.'
    },
    {
        name: 'Gasabo',
        province: 'City of Kigali',
        coords: [-1.8845, 30.1256],
        crops: 'Horticulture, Vegetables, Maize',
        yield: '3,300 kg/ha',
        irrig: '45% (Urban peri-irrigation)',
        fert: '59% (Organic & NPK)',
        loss: '6.5%',
        market: 'Kimironko Wholesale Market',
        desc: 'Peri-urban agricultural zone with direct logistics pipeline into Kigali consumers.'
    }
];

let mapInstance = null;
let currentLayer = 'yield';
let districtMarkers = [];

function initRwandaMap() {
    const mapElement = document.getElementById('rwanda-leaflet-map');
    if (!mapElement || typeof L === 'undefined') return;

    // Centered on Rwanda (Kigali / Central)
    mapInstance = L.map('rwanda-leaflet-map', {
        center: [-1.9403, 29.8739],
        zoom: 9,
        scrollWheelZoom: false,
        attributionControl: false
    });

    // CartoDB Positron tiles for high-clarity cartographic presentation
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 18,
        subdomains: 'abcd'
    }).addTo(mapInstance);

    // Add Rwanda boundary guide
    renderDistrictMarkers();
    initMapLayerButtons();
}

function renderDistrictMarkers() {
    districtMarkers.forEach(m => mapInstance.removeLayer(m));
    districtMarkers = [];

    DISTRICT_GEO_DATA.forEach((d, idx) => {
        let color = '#15803d'; // Default green
        if (currentLayer === 'yield') {
            color = d.yield.startsWith('4') || d.yield.startsWith('5') ? '#15803d' : (d.yield.startsWith('3') ? '#f59e0b' : '#ea580c');
        } else if (currentLayer === 'loss') {
            const lossNum = parseFloat(d.loss);
            color = lossNum > 15 ? '#ef4444' : (lossNum > 10 ? '#f59e0b' : '#15803d');
        } else if (currentLayer === 'irrigation') {
            const irrigNum = parseInt(d.irrig);
            color = irrigNum > 40 ? '#0284c7' : (irrigNum > 20 ? '#10b981' : '#f59e0b');
        }

        const markerIcon = L.divIcon({
            className: 'custom-rwanda-marker',
            html: `<div style="
                background: ${color};
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 9999px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.25);
                border: 2px solid #ffffff;
                display: flex;
                align-items: center;
                gap: 4px;
                white-space: nowrap;
                cursor: pointer;
            ">📍 ${d.name}</div>`,
            iconSize: [80, 24],
            iconAnchor: [40, 12]
        });

        const marker = L.marker(d.coords, { icon: markerIcon }).addTo(mapInstance);

        marker.on('click', () => {
            selectDistrict(d);
            mapInstance.panTo(d.coords, { animate: true });
        });

        districtMarkers.push(marker);
    });
}

function selectDistrict(d) {
    document.getElementById('inspect-province').textContent = d.province;
    document.getElementById('inspect-title').textContent = d.name + ' District';
    document.getElementById('inspect-desc').textContent = d.desc;
    document.getElementById('inspect-crops').textContent = d.crops;
    document.getElementById('inspect-yield').textContent = d.yield;
    document.getElementById('inspect-irrig').textContent = d.irrig;
    document.getElementById('inspect-fert').textContent = d.fert;
    document.getElementById('inspect-loss').textContent = d.loss;
    document.getElementById('inspect-market').textContent = d.market;
}

function initMapLayerButtons() {
    const buttons = document.querySelectorAll('.map-pill-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentLayer = btn.getAttribute('data-layer');
            renderDistrictMarkers();
        });
    });
}
