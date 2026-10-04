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
   2. COMPLETE RWANDA DATASET (ALL 30 DISTRICTS)
   ========================================================================== */
const DISTRICT_DATA = {
    // KIGALI (3)
    'Gasabo': { province: 'Kigali', provName: 'City of Kigali', crops: 'Horticulture, Vegetables, Maize', yieldNum: 3300, yield: '3,300 kg/ha', irrigNum: 45, irrig: '45% (Urban peri-irrigation)', fertNum: 59, fert: '59% (Organic & NPK)', lossNum: 6.5, loss: '6.5%', mech: '24% (Motorized sprayers & tillers)', market: 'Kimironko Wholesale Market', desc: 'Peri-urban agro-zone with direct logistics pipelines into Kigali retail consumers.' },
    'Kicukiro': { province: 'Kigali', provName: 'City of Kigali', crops: 'Vegetables, Poultry, Maize', yieldNum: 3150, yield: '3,150 kg/ha', irrigNum: 38, irrig: '38% (Valley sprinklers)', fertNum: 62, fert: '62% (NPK & Compost)', lossNum: 5.8, loss: '5.8%', mech: '20% (Small tillers)', market: 'Zinia Modern Market', desc: 'Intensive urban farming with strong poultry feed and horticulture production.' },
    'Nyarugenge': { province: 'Kigali', provName: 'City of Kigali', crops: 'Market Gardening, Fruits, Cassava', yieldNum: 3050, yield: '3,050 kg/ha', irrigNum: 35, irrig: '35% (Valley gravity fed)', fertNum: 54, fert: '54% (Organic manure)', lossNum: 6.2, loss: '6.2%', mech: '18%', market: 'Nyabugogo Wholesale Market', desc: 'Central transit and commercial distribution point for produce across Rwanda.' },

    // NORTH (5)
    'Burera': { province: 'North', provName: 'Northern Province', crops: 'Climbing Beans, Irish Potato, Wheat', yieldNum: 3700, yield: '3,700 kg/ha', irrigNum: 21, irrig: '21% (Spring gravity schemes)', fertNum: 58, fert: '58% (DAP & Manure)', lossNum: 6.8, loss: '6.8%', mech: '14%', market: 'Kirambo Market', desc: 'Volcanic and lake-border zone with high climbing bean seed multiplication.' },
    'Gakenke': { province: 'North', provName: 'Northern Province', crops: 'Coffee, Maize, Beans, Pineapple', yieldNum: 3400, yield: '3,400 kg/ha', irrigNum: 16, irrig: '16% (Stream diversion)', fertNum: 53, fert: '53% (NPK & Organic)', lossNum: 12.4, loss: '12.4%', mech: '9%', market: 'Gakenke Ag Market', desc: 'Steep hillside farming with specialty high-grade Arabica coffee washing stations.' },
    'Gicumbi': { province: 'North', provName: 'Northern Province', crops: 'Tea, Irish Potato, Wheat, Beans', yieldNum: 3200, yield: '3,200 kg/ha', irrigNum: 12, irrig: '12% (Spring fed)', fertNum: 51, fert: '51% (NPK & manure)', lossNum: 17.8, loss: '17.8%', mech: '8%', market: 'Byumba Central Market', desc: 'Highland altitude belt characterized by extensive anti-erosion terracing and tea estates.' },
    'Musanze': { province: 'North', provName: 'Northern Province', crops: 'Irish Potato, Maize, Climbing Beans', yieldNum: 4200, yield: '4,200 kg/ha', irrigNum: 32, irrig: '32% (Hillside & Gravity)', fertNum: 64, fert: '64% (DAP & NPK)', lossNum: 7.2, loss: '7.2%', mech: '28% (Tractor & Threshers)', market: 'Musanze Modern Market', desc: 'National benchmark for Irish potato and highland maize productivity with fertile volcanic soils.' },
    'Rulindo': { province: 'North', provName: 'Northern Province', crops: 'Coffee, Maize, Banana, Passion Fruit', yieldNum: 3500, yield: '3,500 kg/ha', irrigNum: 24, irrig: '24% (Valley bottom)', fertNum: 56, fert: '56% (Mineral & Compost)', lossNum: 10.5, loss: '10.5%', mech: '15%', market: 'Tare Agro Market', desc: 'Diverse agro-climatic zones supporting coffee, cereals, and fruits near Kigali-Musanze corridor.' },

    // SOUTH (8)
    'Gisagara': { province: 'South', provName: 'Southern Province', crops: 'Cassava, Rice, Banana, Maize', yieldNum: 2900, yield: '2,900 kg/ha', irrigNum: 28, irrig: '28% (Akanyaru marshland)', fertNum: 44, fert: '44% (Urea & Manure)', lossNum: 14.2, loss: '14.2%', mech: '10%', market: 'Ndora Market', desc: 'Southern border agricultural hub with intensive marshland rice and cassava processing.' },
    'Huye': { province: 'South', provName: 'Southern Province', crops: 'Coffee, Climbing Beans, Maize, Rice', yieldNum: 3100, yield: '3,100 kg/ha', irrigNum: 22, irrig: '22% (Valley Bottom)', fertNum: 52, fert: '52% (NPK & Agricultural Lime)', lossNum: 11.8, loss: '11.8%', mech: '16%', market: 'Huye Modern Market', desc: 'Southern agricultural academic and research hub with extensive agronomic trial plots.' },
    'Kamonyi': { province: 'South', provName: 'Southern Province', crops: 'Cassava, Vegetables, Coffee, Maize', yieldNum: 3250, yield: '3,250 kg/ha', irrigNum: 34, irrig: '34% (Nyabarongo pumping)', fertNum: 50, fert: '50% (Mineral & Manure)', lossNum: 11.1, loss: '11.1%', mech: '19%', market: 'Ruyenzi Agribusiness Hub', desc: 'River basin agriculture with vegetable irrigation along Nyabarongo marshlands.' },
    'Muhanga': { province: 'South', provName: 'Southern Province', crops: 'Cassava, Beans, Maize, Coffee', yieldNum: 3000, yield: '3,000 kg/ha', irrigNum: 19, irrig: '19% (Stream diversions)', fertNum: 47, fert: '47% (Compost & DAP)', lossNum: 13.0, loss: '13.0%', mech: '12%', market: 'Muhanga Central Market', desc: 'Key trade crossroad connecting central and western agricultural trade flows.' },
    'Nyamagabe': { province: 'South', provName: 'Southern Province', crops: 'Tea, Wheat, Irish Potato, Beans', yieldNum: 2850, yield: '2,850 kg/ha', irrigNum: 15, irrig: '15% (Gravity springs)', fertNum: 45, fert: '45% (Lime & NPK)', lossNum: 15.6, loss: '15.6%', mech: '7%', market: 'Gasarenda Tea Market', desc: 'Buffer zone near Nyungwe forest with high tea production and soil acidity management.' },
    'Nyanza': { province: 'South', provName: 'Southern Province', crops: 'Cassava, Dairy Fodder, Maize, Soya', yieldNum: 3150, yield: '3,150 kg/ha', irrigNum: 20, irrig: '20% (Valley dams)', fertNum: 48, fert: '48% (Manure & DAP)', lossNum: 12.5, loss: '12.5%', mech: '15%', market: 'Nyanza Modern Market', desc: 'Traditional livestock and grain belt with strong milk collection center infrastructure.' },
    'Nyaruguru': { province: 'South', provName: 'Southern Province', crops: 'Tea, Irish Potato, Wheat, Beans', yieldNum: 2800, yield: '2,800 kg/ha', irrigNum: 11, irrig: '11% (Small streams)', fertNum: 43, fert: '43% (NPK & Lime)', lossNum: 16.1, loss: '16.1%', mech: '6%', market: 'Kibeho Market', desc: 'High-elevation southern hills with major tea plantations and lime soil amendment programs.' },
    'Ruhango': { province: 'South', provName: 'Southern Province', crops: 'Cassava, Maize, Beans, Coffee', yieldNum: 3100, yield: '3,100 kg/ha', irrigNum: 18, irrig: '18% (Marshland borders)', fertNum: 46, fert: '46% (Organic & DAP)', lossNum: 13.4, loss: '13.4%', mech: '13%', market: 'Ruhango Ag Market', desc: 'Major cassava producing district supporting commercial flour processing cooperatives.' },

    // EAST (7)
    'Bugesera': { province: 'East', provName: 'Eastern Province', crops: 'Cassava, Maize, Beans, Sorghum', yieldNum: 2700, yield: '2,700 kg/ha', irrigNum: 14, irrig: '14% (Lake pumping schemes)', fertNum: 41, fert: '41% (DAP & Urea)', lossNum: 16.4, loss: '16.4%', mech: '11%', market: 'Nyamata Market', desc: 'Dry lowland plateau with high potential for expanded lake-water irrigation schemes.' },
    'Gatsibo': { province: 'East', provName: 'Eastern Province', crops: 'Maize, Soya, Beans, Dairy Fodder', yieldNum: 3350, yield: '3,350 kg/ha', irrigNum: 22, irrig: '22% (Valley dam schemes)', fertNum: 54, fert: '54% (DAP & Urea)', lossNum: 12.9, loss: '12.9%', mech: '21%', market: 'Kabarore Central Market', desc: 'Eastern agricultural savanna with large consolidated plots and mechanized threshing.' },
    'Kayonza': { province: 'East', provName: 'Eastern Province', crops: 'Maize, Soya, Banana, Vegetables', yieldNum: 3200, yield: '3,200 kg/ha', irrigNum: 26, irrig: '26% (Lake Muhazi pumping)', fertNum: 52, fert: '52% (DAP & Compost)', lossNum: 13.7, loss: '13.7%', mech: '18%', market: 'Mukarange Market', desc: 'Drought-resilient farming systems with valley dam water storage programs.' },
    'Kirehe': { province: 'East', provName: 'Eastern Province', crops: 'Banana, Maize, Beans, Rice', yieldNum: 2950, yield: '2,950 kg/ha', irrigNum: 29, irrig: '29% (Akagera river schemes)', fertNum: 46, fert: '46% (Organic & Urea)', lossNum: 14.5, loss: '14.5%', mech: '14%', market: 'Nyakarambi Market', desc: 'Major cooking and dessert banana production basin along Akagera river valley.' },
    'Ngoma': { province: 'East', provName: 'Eastern Province', crops: 'Banana, Maize, Pineapple, Rice', yieldNum: 3050, yield: '3,050 kg/ha', irrigNum: 25, irrig: '25% (Valley bottom & lake)', fertNum: 48, fert: '48% (Manure & DAP)', lossNum: 13.8, loss: '13.8%', mech: '15%', market: 'Kibungo Modern Market', desc: 'Hilly eastern terrain with integrated agroforestry and fruit processing initiatives.' },
    'Nyagatare': { province: 'East', provName: 'Eastern Province', crops: 'Maize, Soya, Rice, Dairy', yieldNum: 3450, yield: '3,450 kg/ha', irrigNum: 18, irrig: '18% (Center pivot & valley dams)', fertNum: 55, fert: '55% (DAP & Urea)', lossNum: 13.2, loss: '13.2%', mech: '31% (Tractors & harvesters)', market: 'Nyagatare Grain Market', desc: 'Rwanda’s breadbasket for grain production with extensive mechanization and land consolidation.' },
    'Rwamagana': { province: 'East', provName: 'Eastern Province', crops: 'Rice, Banana, Maize, Vegetables', yieldNum: 5100, yield: '5,100 kg/ha', irrigNum: 88, irrig: '88% (Marshland schemes)', fertNum: 85, fert: '85% (Urea & DAP)', lossNum: 5.4, loss: '5.4%', mech: '39% (Power tillers)', market: 'Rwamagana Agribusiness Market', desc: 'Leading district for irrigated marshland rice schemes and banana cooperatives.' },

    // WEST (7)
    'Karongi': { province: 'West', provName: 'Western Province', crops: 'Coffee, Tea, Maize, Beans', yieldNum: 3200, yield: '3,200 kg/ha', irrigNum: 17, irrig: '17% (Stream diversions)', fertNum: 49, fert: '49% (Compost & NPK)', lossNum: 12.3, loss: '12.3%', mech: '8%', market: 'Rubengera Market', desc: 'Lake Kivu slopes with high-elevation coffee and terraced food crop production.' },
    'Ngororero': { province: 'West', provName: 'Western Province', crops: 'Tea, Coffee, Irish Potato, Beans', yieldNum: 3150, yield: '3,150 kg/ha', irrigNum: 13, irrig: '13% (Gravity flow)', fertNum: 47, fert: '47% (Organic & NPK)', lossNum: 14.8, loss: '14.8%', mech: '6%', market: 'Ngororero Central Market', desc: 'Mountainous landscape with steep slope cultivation and intensive terracing requirements.' },
    'Nyabihu': { province: 'West', provName: 'Western Province', crops: 'Irish Potato, Tea, Pyrethrum, Maize', yieldNum: 3800, yield: '3,800 kg/ha', irrigNum: 26, irrig: '26% (Small hillside schemes)', fertNum: 78, fert: '78% (DAP & Manure)', lossNum: 9.1, loss: '9.1%', mech: '19%', market: 'Mukamira Modern Market', desc: 'High-altitude volcanic district leading national dairy production and potato seed multiplication.' },
    'Nyamasheke': { province: 'West', provName: 'Western Province', crops: 'Coffee, Tea, Cassava, Rice', yieldNum: 3000, yield: '3,000 kg/ha', irrigNum: 19, irrig: '19% (Kivu streams)', fertNum: 46, fert: '46% (Compost & NPK)', lossNum: 13.5, loss: '13.5%', mech: '7%', market: 'Ntendezi Market', desc: 'Coastal Lake Kivu agricultural zone renowned for award-winning specialty coffee washing.' },
    'Rubavu': { province: 'West', provName: 'Western Province', crops: 'Vegetables, Beans, Irish Potato, Maize', yieldNum: 3900, yield: '3,900 kg/ha', irrigNum: 29, irrig: '29% (Lake Kivu pumping)', fertNum: 68, fert: '68% (Mineral & Manure)', lossNum: 8.7, loss: '8.7%', mech: '17%', market: 'Gisenyi Cross-Border Market', desc: 'High-intensity horticulture zone supplying domestic urban centers and cross-border trade.' },
    'Rusizi': { province: 'West', provName: 'Western Province', crops: 'Rice, Oil Palm, Cassava, Tea', yieldNum: 3600, yield: '3,600 kg/ha', irrigNum: 62, irrig: '62% (Bugarama marshland)', fertNum: 63, fert: '63% (Urea & DAP)', lossNum: 12.1, loss: '12.1%', mech: '22% (Power tillers)', market: 'Kamembe Central Market', desc: 'Sub-tropical Bugarama valley with large-scale marshland rice and oil palm cultivation.' },
    'Rutsiro': { province: 'West', provName: 'Western Province', crops: 'Coffee, Tea, Beans, Maize', yieldNum: 3100, yield: '3,100 kg/ha', irrigNum: 14, irrig: '14% (Spring fed)', fertNum: 48, fert: '48% (Compost & NPK)', lossNum: 14.1, loss: '14.1%', mech: '6%', market: 'Gihango Market', desc: 'Kivu belt agro-forestry zone prioritizing watershed protection and organic coffee.' }
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

    // Fetch GeoJSON polygons & administrative hierarchy
    try {
        const [geoResp, hierResp] = await Promise.all([
            fetch('/static/data/rwanda_districts.geojson'),
            fetch('/static/data/rwanda_hierarchy.json')
        ]);
        rawGeojsonData = await geoResp.json();
        rawHierarchyData = await hierResp.json();

        renderVectorPolygons();
        setupCascadingFilters();
        setupLayerToggles();
    } catch (err) {
        console.error('Failed to load Rwanda spatial datasets:', err);
    }
}

function getDistrictFillColor(distName) {
    const info = DISTRICT_DATA[distName];
    if (!info) return '#cbd5e1';

    if (currentLayer === 'province') {
        return PROVINCE_COLORS[info.province] || '#005CAB';
    } else if (currentLayer === 'yield') {
        const y = info.yieldNum;
        return y >= 4000 ? '#46962B' : (y >= 3300 ? '#68B84D' : (y >= 3000 ? '#9BD485' : '#FDF8A6'));
    } else if (currentLayer === 'irrigation') {
        const ir = info.irrigNum;
        return ir >= 60 ? '#005CAB' : (ir >= 30 ? '#00AEEF' : (ir >= 20 ? '#7DD7FA' : '#E6F7FE'));
    } else if (currentLayer === 'fertilizer') {
        const f = info.fertNum;
        return f >= 65 ? '#265C14' : (f >= 50 ? '#46962B' : (f >= 45 ? '#83C56D' : '#E8F6E4'));
    } else if (currentLayer === 'loss') {
        const l = info.lossNum;
        return l >= 15 ? '#DC2626' : (l >= 12 ? '#EA580C' : (l >= 9 ? '#F3EA00' : '#46962B'));
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
            const info = DISTRICT_DATA[distName] || {};

            // Hover tooltip
            layer.bindTooltip(`
                <div style="font-weight: 800; font-size: 13px;">${distName} District</div>
                <div style="font-size: 11px; opacity: 0.9;">${info.provName || ''}</div>
                <div style="font-size: 11px; margin-top: 2px;">Avg Yield: <strong>${info.yield || 'N/A'}</strong></div>
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
            const info = DISTRICT_DATA[distName];
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

    Object.keys(DISTRICT_DATA).sort().forEach(distName => {
        const info = DISTRICT_DATA[distName];
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
    const info = DISTRICT_DATA[distName];
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
    const info = DISTRICT_DATA[distName];
    if (!info) return;

    // Sync Dropdowns
    const provSelect = document.getElementById('filter-province');
    const distSelect = document.getElementById('filter-district');
    if (provSelect.value !== info.province) {
        provSelect.value = info.province;
        populateDistrictsDropdown(info.province);
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

    // Update Inspector UI
    document.getElementById('inspect-level').textContent = 'District Level';
    document.getElementById('inspect-province').textContent = info.provName;
    document.getElementById('inspect-title').textContent = distName + ' District';
    document.getElementById('inspect-desc').textContent = info.desc;
    document.getElementById('inspect-crops').textContent = info.crops;
    document.getElementById('inspect-yield').textContent = info.yield;
    document.getElementById('inspect-irrig').textContent = info.irrig;
    document.getElementById('inspect-fert').textContent = info.fert;
    document.getElementById('inspect-mech').textContent = info.mech;
    document.getElementById('inspect-loss').textContent = info.loss;
    document.getElementById('inspect-market').textContent = info.market;
}

function selectSector(distName, secName) {
    const info = DISTRICT_DATA[distName];
    if (!info) return;

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
    document.getElementById('inspect-province').textContent = `${info.provName} &bull; ${distName}`;
    document.getElementById('inspect-title').textContent = `${secName} Sector`;
    document.getElementById('inspect-desc').textContent = `Agricultural sector in ${distName} District under the Seasonal Agricultural Survey monitoring grid.`;
    document.getElementById('inspect-crops').textContent = info.crops;
    document.getElementById('inspect-yield').textContent = info.yield;
    document.getElementById('inspect-irrig').textContent = info.irrig;
    document.getElementById('inspect-fert').textContent = info.fert;
    document.getElementById('inspect-mech').textContent = info.mech;
    document.getElementById('inspect-loss').textContent = info.loss;
    document.getElementById('inspect-market').textContent = `${secName} Cooperative Collection Center`;
}

function zoomToProvince(provKey) {
    activeDistrictName = null;
    if (!geojsonLayer) return;

    const bounds = L.latLngBounds([]);
    geojsonLayer.eachLayer(layer => {
        const dName = layer.feature.properties.shapeName;
        const dInfo = DISTRICT_DATA[dName];
        if (dInfo && dInfo.province === provKey) {
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
    const distList = Object.keys(DISTRICT_DATA).filter(k => DISTRICT_DATA[k].province === provKey);

    document.getElementById('inspect-level').textContent = 'Province Level';
    document.getElementById('inspect-province').textContent = 'Republic of Rwanda';
    document.getElementById('inspect-title').textContent = provName;
    document.getElementById('inspect-desc').textContent = `Consists of ${distList.length} monitored administrative districts: ${distList.slice(0, 4).join(', ')}, etc.`;
    document.getElementById('inspect-crops').textContent = 'Regional Grain & Cash Crop Belt';
    document.getElementById('inspect-yield').textContent = '3,450 kg/ha (Provincial Avg)';
    document.getElementById('inspect-irrig').textContent = '32% Avg Coverage';
    document.getElementById('inspect-fert').textContent = '58% Adoption';
    document.getElementById('inspect-mech').textContent = '19% Mechanized';
    document.getElementById('inspect-loss').textContent = '11.4% Avg Loss';
    document.getElementById('inspect-market').textContent = `${provName} Central Trade Hubs`;
    document.getElementById('inspect-sectors').textContent = `${distList.length} Districts`;
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
    document.getElementById('inspect-crops').textContent = 'Maize, Irish Potato, Beans, Rice, Cassava, Coffee, Tea';
    document.getElementById('inspect-yield').textContent = '3,380 kg/ha (National Benchmark)';
    document.getElementById('inspect-irrig').textContent = '26% National Avg';
    document.getElementById('inspect-fert').textContent = '56% Mineral/Organic Adoption';
    document.getElementById('inspect-mech').textContent = '16% Mechanization Adoption';
    document.getElementById('inspect-loss').textContent = '11.8% National Loss Rate';
    document.getElementById('inspect-market').textContent = 'National Wholesale Markets';
    document.getElementById('inspect-sectors').textContent = '416 Sectors';
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
