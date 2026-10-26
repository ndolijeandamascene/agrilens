/**
 * AgriLens Machine Learning & Decision Intelligence Frontend Engine
 * Controls:
 * 1. Farm-Level Crop Yield What-If Simulator & Scenario Modeler
 * 2. District Agro-Ecological Typology ML Map Layer
 * 3. Seasonal Harvest Production Forecasting & Deficit Early Warning Chart
 * 4. Model Explainability & Transparency Sync
 */

let mlSimulatorMode = 'single'; // 'single' or 'scenario'
let mlForecastChartInstance = null;
let liveDistrictTypologies = {};
let liveDistrictVulnerabilities = {};
let currentMapLayerMode = 'yield';
let isTypologyMapActive = false;

document.addEventListener('DOMContentLoaded', () => {
    initMLIntelligenceSuite();
});

function initMLIntelligenceSuite() {
    // 1. Initial prediction run on default parameters
    triggerMLPrediction();

    // 2. Fetch and render seasonal production forecast
    fetchMLForecast('Maize');

    // 3. Preload district clusters for the Leaflet map layer
    preloadDistrictTypologyClusters();

    // 4. Preload district vulnerability index (AVI)
    preloadDistrictVulnerabilities();
}

/* ==========================================================================
   1. CROP YIELD WHAT-IF SIMULATOR & SCENARIO COMPARISON
   ========================================================================== */

function switchSimulatorMode(mode) {
    mlSimulatorMode = mode;
    const btnSingle = document.getElementById('mlModeSingleBtn');
    const btnScenario = document.getElementById('mlModeScenarioBtn');
    const singleContainer = document.getElementById('mlSinglePracticesContainer');
    const scenarioContainer = document.getElementById('mlScenarioPracticesContainer');
    const scenarioResultCard = document.getElementById('mlScenarioResultCard');

    if (mode === 'scenario') {
        if (btnSingle) btnSingle.classList.remove('active');
        if (btnScenario) btnScenario.classList.add('active');
        if (singleContainer) singleContainer.style.display = 'none';
        if (scenarioContainer) scenarioContainer.style.display = 'grid';
        if (scenarioResultCard) scenarioResultCard.style.display = 'block';
    } else {
        if (btnSingle) btnSingle.classList.add('active');
        if (btnScenario) btnScenario.classList.remove('active');
        if (singleContainer) singleContainer.style.display = 'flex';
        if (scenarioContainer) scenarioContainer.style.display = 'none';
        if (scenarioResultCard) scenarioResultCard.style.display = 'none';
    }
    triggerMLPrediction();
}

function updatePlotAreaDisplay(val) {
    const badge = document.getElementById('mlSimPlotAreaBadge');
    if (badge) {
        badge.textContent = `${parseFloat(val).toFixed(2)} ha`;
    }
    triggerMLPrediction();
}

async function triggerMLPrediction() {
    const districtElem = document.getElementById('mlSimDistrict');
    const cropElem = document.getElementById('mlSimCrop');
    const areaElem = document.getElementById('mlSimPlotArea');

    const district = districtElem ? districtElem.value : 'Musanze';
    const crop = cropElem ? cropElem.value : 'Maize';
    const area = areaElem ? parseFloat(areaElem.value) || 0.5 : 0.5;

    const btn = document.getElementById('mlRunPredictionBtn');
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running ML Model...';
        btn.disabled = true;
    }

    try {
        if (mlSimulatorMode === 'scenario') {
            await runScenarioComparison(district, crop, area);
        } else {
            await runSinglePrediction(district, crop, area);
        }
    } catch (err) {
        console.error('ML Prediction error:', err);
    } finally {
        if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-play"></i> Run Real-Time ML Simulation';
            btn.disabled = false;
        }
    }
}

async function runSinglePrediction(district, crop, area) {
    const seed = document.getElementById('mlSimSeed')?.checked || false;
    const inorg = document.getElementById('mlSimInorgFert')?.checked || false;
    const org = document.getElementById('mlSimOrgFert')?.checked || false;
    const pest = document.getElementById('mlSimPesticide')?.checked || false;
    const irrig = document.getElementById('mlSimIrrig')?.checked || false;

    const payload = {
        district: district,
        crop: crop,
        plot_area_ha: area,
        is_improved_seed: seed,
        uses_inorganic_fertilizer: inorg,
        uses_organic_fertilizer: org,
        uses_pesticide: pest,
        is_irrigated: irrig,
        has_anti_erosion: false,
        uses_mechanization: false
    };

    const resp = await fetch('/api/v1/ml/predict-yield/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!resp.ok) {
        throw new Error(`Inference API error: ${resp.status}`);
    }

    const data = await resp.json();
    renderSinglePredictionOutputs(data);
}

function renderSinglePredictionOutputs(data) {
    // 1. Predicted Yield
    const yieldValElem = document.getElementById('mlOutputYieldVal');
    const yieldKgElem = document.getElementById('mlOutputYieldKg');
    if (yieldValElem) {
        yieldValElem.innerHTML = `${data.predicted_yield_tha.toFixed(2)} <small style="font-size: 12px;">t/ha</small>`;
    }
    if (yieldKgElem) {
        yieldKgElem.textContent = `${data.predicted_yield_kg_per_ha.toLocaleString()} kg/ha`;
    }

    // 1b. 80% Confidence Interval Band
    const confElem = document.getElementById('mlOutputConfBand');
    if (confElem && data.confidence_interval_80) {
        const ci = data.confidence_interval_80;
        confElem.innerHTML = `80% CI: <strong>${ci.lower_p10_tha.toFixed(2)}</strong> &ndash; <strong>${ci.upper_p90_tha.toFixed(2)}</strong> t/ha <span style="font-size: 9px; padding: 1px 5px; border-radius: 3px; background: #E0F2FE; color: #0369A1; margin-left: 4px; font-weight: 700;">&plusmn;${ci.downside_risk_tha.toFixed(2)} t</span>`;
    }

    // 1c. Submodel Badge
    const submodelBadge = document.getElementById('mlSubmodelBadge');
    if (submodelBadge && data.model_info && data.model_info.crop_submodel_applied) {
        submodelBadge.textContent = `Submodel: ${data.model_info.crop_submodel_applied}`;
    }

    // 1d. Local Waterfall Attributions
    const attrList = document.getElementById('mlLocalAttributionList');
    if (attrList && Array.isArray(data.local_attributions)) {
        attrList.innerHTML = '';
        data.local_attributions.forEach(item => {
            const isAdopted = item.is_adopted;
            const sign = item.marginal_contribution_tha >= 0 ? '+' : '';
            const badgeBg = isAdopted ? '#ECFDF5' : '#F8FAFC';
            const badgeColor = isAdopted ? '#065F46' : '#64748B';
            const tagBorder = isAdopted ? 'border: 1px solid #A7F3D0;' : 'border: 1px dashed #E2E8F0;';
            const valColor = isAdopted ? '#15803D' : '#0284C7';

            const row = document.createElement('div');
            row.style.cssText = `display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: ${badgeBg}; border-radius: 6px; ${tagBorder} font-size: 11px;`;
            row.innerHTML = `
                <div style="display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid ${isAdopted ? 'fa-circle-check' : 'fa-circle-plus'}" style="color: ${isAdopted ? '#10B981' : '#94A3B8'};"></i>
                    <span style="font-weight: 600; color: ${badgeColor};">${item.practice_name}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 10px; color: #64748B;">${isAdopted ? 'Active Impact:' : 'Untapped:'}</span>
                    <strong style="color: ${valColor};">${sign}${item.marginal_contribution_tha.toFixed(2)} t/ha</strong>
                </div>
            `;
            attrList.appendChild(row);
        });
    }

    // 2. Production
    const prodValElem = document.getElementById('mlOutputProdVal');
    const prodKgElem = document.getElementById('mlOutputProdKg');
    if (prodValElem) {
        prodValElem.innerHTML = `${data.predicted_production_tonnes.toFixed(2)} <small style="font-size: 12px;">t</small>`;
    }
    if (prodKgElem) {
        prodKgElem.textContent = `${data.predicted_production_kg.toLocaleString()} kg harvest`;
    }

    // 3. Uplift vs Baseline
    const upliftElem = document.getElementById('mlOutputUpliftVal');
    const baselineSubElem = document.getElementById('mlOutputBaselineSub');
    if (upliftElem) {
        const sign = data.yield_difference_percentage >= 0 ? '+' : '';
        upliftElem.textContent = `${sign}${data.yield_difference_percentage.toFixed(1)}%`;
        upliftElem.style.color = data.yield_difference_percentage >= 0 ? '#16A34A' : '#DC2626';
    }
    if (baselineSubElem) {
        baselineSubElem.textContent = `vs ${data.district} baseline (${data.baseline_yield_tha.toFixed(2)} t/ha)`;
    }

    // 4. Latency
    const latencyBadge = document.getElementById('mlInferenceLatencyBadge');
    if (latencyBadge && data.latency_ms) {
        latencyBadge.textContent = `Latency: ${data.latency_ms.toFixed(0)}ms`;
    }

    // 5. Model badge
    if (data.model_info) {
        const algBadge = document.getElementById('mlModelAlgBadge');
        const r2Badge = document.getElementById('mlModelR2Badge');
        const maeBadge = document.getElementById('mlModelMaeBadge');

        if (algBadge) algBadge.textContent = `${data.model_info.algorithm} (${data.model_info.version})`;
        if (r2Badge && data.model_info.r2_score !== null) r2Badge.textContent = `${data.model_info.r2_score}`;
        if (maeBadge && data.model_info.mae_kg_per_ha !== null) maeBadge.textContent = `${data.model_info.mae_kg_per_ha} kg/ha`;
    }
}

async function runScenarioComparison(district, crop, area) {
    const currSeed = document.getElementById('scenCurrSeed')?.checked || false;
    const currInorg = document.getElementById('scenCurrInorg')?.checked || false;
    const currOrg = document.getElementById('scenCurrOrg')?.checked || false;
    const currPest = document.getElementById('scenCurrPest')?.checked || false;

    const recSeed = document.getElementById('scenRecSeed')?.checked || false;
    const recInorg = document.getElementById('scenRecInorg')?.checked || false;
    const recOrg = document.getElementById('scenRecOrg')?.checked || false;
    const recPest = document.getElementById('scenRecPest')?.checked || false;

    const payload = {
        district: district,
        crop: crop,
        plot_area_ha: area,
        current_practices: {
            is_improved_seed: currSeed,
            uses_inorganic_fertilizer: currInorg,
            uses_organic_fertilizer: currOrg,
            uses_pesticide: currPest
        },
        recommended_practices: {
            is_improved_seed: recSeed,
            uses_inorganic_fertilizer: recInorg,
            uses_organic_fertilizer: recOrg,
            uses_pesticide: recPest
        }
    };

    const resp = await fetch('/api/v1/ml/simulate-scenario/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!resp.ok) {
        throw new Error(`Scenario simulation API error: ${resp.status}`);
    }

    const data = await resp.json();
    renderScenarioComparisonOutputs(data);
}

function renderScenarioComparisonOutputs(data) {
    renderSinglePredictionOutputs(data.recommended_scenario);

    const currYieldElem = document.getElementById('scenResCurrYield');
    const recYieldElem = document.getElementById('scenResRecYield');
    const netUpliftElem = document.getElementById('scenResNetUplift');
    const revenueBadge = document.getElementById('mlRevenueGainBadge');

    if (currYieldElem) {
        currYieldElem.textContent = `${data.current_scenario.predicted_yield_tha.toFixed(2)} t/ha`;
    }
    if (recYieldElem) {
        recYieldElem.textContent = `${data.recommended_scenario.predicted_yield_tha.toFixed(2)} t/ha`;
    }
    if (netUpliftElem) {
        const uplift = data.comparison.yield_uplift_tha;
        const pct = data.comparison.yield_uplift_percentage;
        const sign = uplift >= 0 ? '+' : '';
        netUpliftElem.textContent = `${sign}${uplift.toFixed(2)} t/ha (${sign}${pct}%)`;
    }
    if (revenueBadge) {
        const rev = data.comparison.indicative_revenue_gain_rwf;
        revenueBadge.textContent = `+${Math.round(rev).toLocaleString()} RWF Uplift`;
    }
}

/* ==========================================================================
   2. DISTRICT AGRO-ECOLOGICAL TYPOLOGY CLUSTERING (LEAFLET LAYER)
   ========================================================================== */

async function preloadDistrictTypologyClusters() {
    try {
        const resp = await fetch('/api/v1/ml/district-clusters/');
        if (!resp.ok) return;
        const res = await resp.json();
        if (Array.isArray(res.clusters)) {
            res.clusters.forEach(c => {
                liveDistrictTypologies[c.district_name] = c;
            });
        }
    } catch (err) {
        console.warn('Could not load district typologies:', err);
    }
}

async function preloadDistrictVulnerabilities() {
    try {
        const resp = await fetch('/api/v1/ml/vulnerability/');
        if (!resp.ok) return;
        const data = await resp.json();
        if (data.status === 'SUCCESS' && Array.isArray(data.districts)) {
            data.districts.forEach(d => {
                liveDistrictVulnerabilities[d.district_name] = d;
            });
        }
    } catch (err) {
        console.warn('Could not load district vulnerabilities:', err);
    }
}

function setMapLayerMode(layerMode) {
    currentMapLayerMode = layerMode;
    isTypologyMapActive = (layerMode === 'typology');
    const isVulnerability = (layerMode === 'vulnerability');
    
    // Update legend UI
    const yieldLegend = document.getElementById('dashboard-legend-entries');
    const typologyLegend = document.getElementById('dashboard-typology-legend-entries');
    const aviLegend = document.getElementById('dashboard-avi-legend-entries');
    const legendHead = document.querySelector('.legend-head');

    if (yieldLegend) yieldLegend.style.display = (layerMode === 'yield') ? 'block' : 'none';
    if (typologyLegend) typologyLegend.style.display = isTypologyMapActive ? 'block' : 'none';
    if (aviLegend) aviLegend.style.display = isVulnerability ? 'block' : 'none';

    if (legendHead) {
        if (isTypologyMapActive) {
            legendHead.textContent = 'Agro-Ecological Typology (ML)';
        } else if (isVulnerability) {
            legendHead.textContent = 'Vulnerability Index (AVI)';
        } else {
            legendHead.textContent = 'Yield (t/ha)';
        }
    }

    // Trigger map restyle if Leaflet layer is available
    if (typeof geojsonLayer !== 'undefined' && geojsonLayer) {
        geojsonLayer.eachLayer(layer => {
            const dName = layer.feature.properties.shapeName;
            if (isTypologyMapActive && liveDistrictTypologies[dName]) {
                const style = liveDistrictTypologies[dName].style;
                layer.setStyle({
                    fillColor: style.fillColor,
                    color: '#FFFFFF',
                    weight: 1.5,
                    fillOpacity: 0.90
                });
            } else if (isVulnerability && liveDistrictVulnerabilities[dName]) {
                const v = liveDistrictVulnerabilities[dName];
                layer.setStyle({
                    fillColor: v.color || '#EAB308',
                    color: '#FFFFFF',
                    weight: 1.5,
                    fillOpacity: 0.90
                });
            } else if (typeof getDistrictChoroplethColor === 'function') {
                layer.setStyle({
                    fillColor: getDistrictChoroplethColor(dName),
                    color: '#FFFFFF',
                    weight: 1.2,
                    fillOpacity: 0.88
                });
            }
        });
    }
}

/* ==========================================================================
   3. SEASONAL PRODUCTION FORECASTING & DEFICIT EARLY WARNING CHART
   ========================================================================== */

async function fetchMLForecast(crop = 'Maize') {
    try {
        const resp = await fetch(`/api/v1/ml/forecast/?crop=${encodeURIComponent(crop)}`);
        if (!resp.ok) throw new Error(`Forecast API error: ${resp.status}`);
        const data = await resp.json();

        renderMLForecastChart(data);
        renderMLEarlyWarning(data);
        renderMLProductionDecomposition(data);
    } catch (err) {
        console.warn('Failed to load ML production forecast:', err);
    }
}

function renderMLForecastChart(data) {
    const canvas = document.getElementById('mlForecastChart');
    if (!canvas || typeof Chart === 'undefined') return;

    if (mlForecastChartInstance) {
        mlForecastChartInstance.destroy();
    }

    const labels = [];
    const productionData = [];
    const backgroundColors = [];
    const borderColors = [];

    // Historical series
    if (Array.isArray(data.historical_series)) {
        data.historical_series.forEach(h => {
            labels.push(h.period);
            productionData.push(h.production_tonnes);
            backgroundColors.push('rgba(4, 120, 87, 0.85)');
            borderColors.push('#047857');
        });
    }

    // Forecast series point
    if (data.projected_production_tonnes) {
        labels.push(`${data.forecast_period} (ML Forecast)`);
        productionData.push(data.projected_production_tonnes);
        backgroundColors.push('rgba(2, 132, 199, 0.85)');
        borderColors.push('#0284C7');
    }

    const ctx = canvas.getContext('2d');
    mlForecastChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `${data.crop} Harvest (MT)`,
                data: productionData,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y.toLocaleString()} Metric Tons`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value >= 1000 ? (value / 1000).toFixed(0) + 'k t' : value + ' t';
                        },
                        font: { size: 10 }
                    },
                    grid: { color: '#F1F5F9' }
                },
                x: {
                    ticks: { font: { size: 10.5, weight: '600' } },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderMLEarlyWarning(data) {
    const badge = document.getElementById('mlEarlyWarningBadge');
    const msg = document.getElementById('mlEarlyWarningMessage');
    const banner = document.getElementById('mlEarlyWarningBanner');

    if (data.early_warning) {
        const ew = data.early_warning;
        if (badge) {
            badge.textContent = ew.badge || ew.level;
            badge.style.backgroundColor = ew.severity_color || '#15803D';
        }
        if (msg) {
            msg.textContent = ew.message;
        }
        if (banner) {
            if (ew.level === 'HIGH_DEFICIT_ALERT') {
                banner.style.background = '#FEF2F2';
                banner.style.borderColor = '#FCA5A5';
            } else if (ew.level === 'MODERATE_CONTRACTION') {
                banner.style.background = '#FFFBEB';
                banner.style.borderColor = '#FDE68A';
            } else {
                banner.style.background = '#F0FDF4';
                banner.style.borderColor = '#86EFAC';
            }
        }
    }

    // Render top district forecast breakdown with structural growth driver
    const tbody = document.getElementById('mlDistrictForecastBody');
    if (tbody && Array.isArray(data.district_breakdown)) {
        tbody.innerHTML = '';
        data.district_breakdown.forEach(d => {
            const tr = document.createElement('tr');
            const sign = d.difference_tonnes >= 0 ? '+' : '';
            const color = d.difference_tonnes >= 0 ? '#059669' : '#DC2626';
            const isYieldLed = d.primary_driver === 'YIELD_INTENSIFICATION';
            const badgeBg = isYieldLed ? '#ECFDF5' : '#EFF6FF';
            const badgeColor = isYieldLed ? '#047857' : '#1D4ED8';
            const driverShort = isYieldLed ? 'Yield' : (d.primary_driver === 'LAND_EXTENSIFICATION' ? 'Area' : 'Balanced');

            tr.innerHTML = `
                <td><strong>${d.district_name}</strong></td>
                <td>${d.historical_tonnes.toLocaleString()} t</td>
                <td><strong>${d.forecast_tonnes.toLocaleString()} t</strong></td>
                <td style="color: ${color}; font-weight: 700;">${sign}${d.difference_tonnes.toLocaleString()} t</td>
                <td><span style="background: ${badgeBg}; color: ${badgeColor}; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">${driverShort}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
}

function renderMLProductionDecomposition(data) {
    if (!data.production_decomposition || !data.production_decomposition.forecast) return;

    const decomp = data.production_decomposition.forecast;

    const yieldEffectEl = document.getElementById('mlDecompYieldEffect');
    const yieldShareEl = document.getElementById('mlDecompYieldShare');
    const areaEffectEl = document.getElementById('mlDecompAreaEffect');
    const areaShareEl = document.getElementById('mlDecompAreaShare');
    const interactionEffectEl = document.getElementById('mlDecompInteractionEffect');
    const interactionShareEl = document.getElementById('mlDecompInteractionShare');
    const badgeEl = document.getElementById('mlDecompPrimaryBadge');
    const narrativeEl = document.getElementById('mlDecompNarrative');

    const fmtSign = (val) => (val >= 0 ? `+${val.toLocaleString()}` : `${val.toLocaleString()}`);

    if (yieldEffectEl) yieldEffectEl.textContent = `${fmtSign(decomp.yield_effect_tonnes)} MT`;
    if (yieldShareEl) yieldShareEl.textContent = `${decomp.intensification_share_pct}%`;

    if (areaEffectEl) areaEffectEl.textContent = `${fmtSign(decomp.area_effect_tonnes)} MT`;
    if (areaShareEl) areaShareEl.textContent = `${decomp.extensification_share_pct}%`;

    if (interactionEffectEl) interactionEffectEl.textContent = `${fmtSign(decomp.interaction_effect_tonnes)} MT`;
    if (interactionShareEl) interactionShareEl.textContent = `${decomp.interaction_share_pct}%`;

    if (badgeEl) {
        badgeEl.textContent = decomp.primary_driver_label;
        if (decomp.primary_driver === 'YIELD_INTENSIFICATION') {
            badgeEl.style.background = '#ECFDF5';
            badgeEl.style.color = '#065F46';
            badgeEl.style.borderColor = '#A7F3D0';
        } else if (decomp.primary_driver === 'LAND_EXTENSIFICATION') {
            badgeEl.style.background = '#EFF6FF';
            badgeEl.style.color = '#1E40AF';
            badgeEl.style.borderColor = '#BFDBFE';
        } else {
            badgeEl.style.background = '#F8FAFC';
            badgeEl.style.color = '#334155';
            badgeEl.style.borderColor = '#CBD5E1';
        }
    }

    if (narrativeEl && decomp.narrative) {
        narrativeEl.textContent = decomp.narrative;
    }
}

