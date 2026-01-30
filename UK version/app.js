// UK Data focused configuration
const COUNTRY_CONFIG = {
    "United Kingdom": { "color": "#2563eb", "short": "UKR" }
};

// State
let RAW_DATA = {};
let selectedCountries = new Set(['United Kingdom']);
let currentYear = 2010;
let isPlaying = false;
let playInterval = null;
let playSpeed = 1;
let energyMode = 'final';
let isSmoothed = false;

// Chart dimensions
const width = 800;
const height = 700;
const margin = { top: 60, right: 80, bottom: 80, left: 80 };
const innerWidth = width - margin.left - margin.right;
const innerHeight = height - margin.top - margin.bottom;
const triangleHeight = innerWidth * Math.sqrt(3) / 2;

// Triangle corners: Left (Bio), Right (Electrons), Bottom (Fossil)
const cornerBio = { x: 0, y: 0 };
const cornerElec = { x: innerWidth, y: 0 };
const cornerFoss = { x: innerWidth / 2, y: triangleHeight };

// Convert ternary coordinates to XY
function ternToXY(bio, elec, foss) {
    const xPos = bio * cornerBio.x + elec * cornerElec.x + foss * cornerFoss.x;
    const yPos = bio * cornerBio.y + elec * cornerElec.y + foss * cornerFoss.y;
    return { x: xPos, y: yPos };
}

// Create SVG
const svg = d3.select('#viz-container').append('svg')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .style('width', '100%')
    .style('height', 'auto')
    .style('max-height', '75vh')
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

// Highlight functions for axis interactivity
function highlightAxis(axisType) {
    svg.selectAll(`.grid-line.${axisType}-grid`).classed('highlighted', true);
    svg.selectAll(`.axis-edge.${axisType}-edge`).classed('highlighted', true);
    svg.selectAll(`.axis-tick.${axisType}-tick`).classed('highlighted', true);
    svg.selectAll(`.axis-range-label.${axisType}-range`).classed('highlighted', true);
    svg.selectAll(`.axis-label.${axisType}-label`).classed('highlighted', true);

    const bands = [0, 0.2, 0.4, 0.6, 0.8];
    const opacities = [0.1, 0.05, 0.03, 0.01, 0.005];

    bands.forEach((t, i) => {
        const t2 = bands[i + 1] || 1.0;
        let points;

        if (axisType === 'bio') {
            const p1 = ternToXY(t, 1 - t, 0);
            const p2 = ternToXY(t, 0, 1 - t);
            const p3 = ternToXY(t2, 0, 1 - t2);
            const p4 = ternToXY(t2, 1 - t2, 0);
            points = `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`;
        } else if (axisType === 'elec') {
            const p1 = ternToXY(0, t, 1 - t);
            const p2 = ternToXY(1 - t, t, 0);
            const p3 = ternToXY(1 - t2, t2, 0);
            const p4 = ternToXY(0, t2, 1 - t2);
            points = `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`;
        } else if (axisType === 'foss') {
            const p1 = ternToXY(0, 1 - t, t);
            const p2 = ternToXY(1 - t, 0, t);
            const p3 = ternToXY(1 - t2, 0, t2);
            const p4 = ternToXY(0, 1 - t2, t2);
            points = `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`;
        }

        const reversedOpacity = opacities[bands.length - 1 - i];

        svg.insert('polygon', ':first-child')
            .attr('class', 'highlight-band')
            .attr('points', points)
            .attr('fill', '#000')
            .attr('opacity', reversedOpacity);
    });
}

function unhighlightAxis(axisType) {
    svg.selectAll(`.grid-line.${axisType}-grid`).classed('highlighted', false);
    svg.selectAll(`.axis-edge.${axisType}-edge`).classed('highlighted', false);
    svg.selectAll(`.axis-tick.${axisType}-tick`).classed('highlighted', false);
    svg.selectAll(`.axis-range-label.${axisType}-range`).classed('highlighted', false);
    svg.selectAll(`.axis-label.${axisType}-label`).classed('highlighted', false);
    svg.selectAll('.highlight-band').remove();
}

function drawTriangle() {
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('markerWidth', 10)
        .attr('markerHeight', 7)
        .attr('refX', 9)
        .attr('refY', 3.5)
        .attr('orient', 'auto')
        .append('polygon')
        .attr('points', '0 0, 10 3.5, 0 7')
        .attr('fill', 'var(--slate-400)');

    [0.2, 0.4, 0.6, 0.8].forEach(t => {
        let b1 = ternToXY(t, 1 - t, 0), b2 = ternToXY(t, 0, 1 - t);
        svg.append('line').attr('x1', b1.x).attr('y1', b1.y).attr('x2', b2.x).attr('y2', b2.y).attr('class', 'grid-line bio-grid');
        let e1 = ternToXY(0, t, 1 - t), e2 = ternToXY(1 - t, t, 0);
        svg.append('line').attr('x1', e1.x).attr('y1', e1.y).attr('x2', e2.x).attr('y2', e2.y).attr('class', 'grid-line elec-grid');
        let f1 = ternToXY(0, 1 - t, t), f2 = ternToXY(1 - t, 0, t);
        svg.append('line').attr('x1', f1.x).attr('y1', f1.y).attr('x2', f2.x).attr('y2', f2.y).attr('class', 'grid-line foss-grid');
    });

    svg.append('line').attr('x1', cornerBio.x).attr('y1', cornerBio.y).attr('x2', cornerFoss.x).attr('y2', cornerFoss.y).attr('class', 'axis-edge bio-edge').on('mouseenter', () => highlightAxis('bio')).on('mouseleave', () => unhighlightAxis('bio'));
    svg.append('line').attr('x1', cornerElec.x).attr('y1', cornerElec.y).attr('x2', cornerFoss.x).attr('y2', cornerFoss.y).attr('class', 'axis-edge foss-edge').on('mouseenter', () => highlightAxis('foss')).on('mouseleave', () => unhighlightAxis('foss'));
    svg.append('line').attr('x1', cornerBio.x).attr('y1', cornerBio.y).attr('x2', cornerElec.x).attr('y2', cornerElec.y).attr('class', 'axis-edge elec-edge').on('mouseenter', () => highlightAxis('elec')).on('mouseleave', () => unhighlightAxis('elec'));

    const tickValues = [0, 0.2, 0.4, 0.6, 0.8, 1.0];
    tickValues.forEach(t => {
        const pos = ternToXY(t, 0, 1 - t);
        svg.append('text').attr('x', pos.x - 12).attr('y', pos.y + 4).attr('text-anchor', 'end').attr('class', 'axis-tick bio-tick').text(Math.round(t * 100));
        const pos2 = ternToXY(0, 1 - t, t);
        svg.append('text').attr('x', pos2.x + 12).attr('y', pos2.y + 4).attr('text-anchor', 'start').attr('class', 'axis-tick foss-tick').text(Math.round(t * 100));
        const pos3 = ternToXY(1 - t, t, 0);
        svg.append('text').attr('x', pos3.x).attr('y', pos3.y - 10).attr('text-anchor', 'middle').attr('class', 'axis-tick elec-tick').text(Math.round(t * 100));
    });

    svg.append('text').attr('x', cornerBio.x + 55).attr('y', cornerBio.y - 45).attr('text-anchor', 'start').attr('class', 'axis-range-label elec-range').text('Low electrons');
    svg.append('text').attr('x', cornerElec.x - 55).attr('y', cornerElec.y - 45).attr('text-anchor', 'end').attr('class', 'axis-range-label elec-range').text('High electrons');

    const arrowLengthFactor = 0.6, arrowOffset = 30;
    const elecArrowStartX = cornerBio.x + (innerWidth * (1 - arrowLengthFactor) / 2);
    const elecArrowEndX = cornerBio.x + (innerWidth * (1 + arrowLengthFactor) / 2);
    const elecArrowY = cornerBio.y - arrowOffset;
    svg.append('line').attr('x1', elecArrowStartX).attr('y1', elecArrowY).attr('x2', elecArrowEndX).attr('y2', elecArrowY).attr('stroke', 'var(--slate-400)').attr('stroke-width', 1).attr('marker-end', 'url(#arrowhead)').attr('class', 'axis-range-label elec-range');

    const bioArrowStartT = (1 - arrowLengthFactor) / 2, bioArrowEndT = 1 - bioArrowStartT;
    const bioP1 = ternToXY(bioArrowStartT, 0, 1 - bioArrowStartT), bioP2 = ternToXY(bioArrowEndT, 0, 1 - bioArrowEndT);
    const bioAngle = Math.PI / 3, bioDx = -Math.sin(bioAngle) * arrowOffset - 50, bioDy = -Math.cos(bioAngle) * arrowOffset + 10;
    svg.append('line').attr('x1', bioP1.x + bioDx).attr('y1', bioP1.y + bioDy).attr('x2', bioP2.x + bioDx).attr('y2', bioP2.y + bioDy).attr('stroke', 'var(--slate-400)').attr('stroke-width', 1).attr('marker-end', 'url(#arrowhead)').attr('class', 'axis-range-label bio-range');

    const fossArrowStartT = (1 - arrowLengthFactor) / 2, fossArrowEndT = 1 - fossArrowStartT;
    const fossP1 = ternToXY(0, 1 - fossArrowStartT, fossArrowStartT), fossP2 = ternToXY(0, 1 - fossArrowEndT, fossArrowEndT);
    const fossAngle = -Math.PI / 3, fossDx = -Math.sin(fossAngle) * arrowOffset + 50, fossDy = -Math.cos(fossAngle) * arrowOffset + 10;
    svg.append('line').attr('x1', fossP1.x + fossDx).attr('y1', fossP1.y + fossDy).attr('x2', fossP2.x + fossDx).attr('y2', fossP2.y + fossDy).attr('stroke', 'var(--slate-400)').attr('stroke-width', 1).attr('marker-end', 'url(#arrowhead)').attr('class', 'axis-range-label foss-range');

    svg.append('text').attr('x', cornerBio.x - 5).attr('y', cornerBio.y + 90).attr('text-anchor', 'end').attr('class', 'axis-range-label bio-range').text('High bio');
    svg.append('text').attr('x', cornerElec.x - 5).attr('y', cornerElec.y + 90).attr('text-anchor', 'start').attr('class', 'axis-range-label foss-range').text('Low fossil');
    svg.append('text').attr('x', cornerFoss.x - 120).attr('y', cornerFoss.y - 60).attr('text-anchor', 'middle').attr('class', 'axis-range-label bio-range').text('Low bio');
    svg.append('text').attr('x', cornerFoss.x + 120).attr('y', cornerFoss.y - 60).attr('text-anchor', 'middle').attr('class', 'axis-range-label foss-range').text('High fossil');

    svg.append('text').attr('id', 'label-bio').attr('x', cornerBio.x - 20).attr('y', cornerBio.y - 20).attr('text-anchor', 'end').attr('class', 'axis-label bio-label').text('Bio & other').on('mouseenter', () => highlightAxis('bio')).on('mouseleave', () => unhighlightAxis('bio'));
    svg.append('text').attr('id', 'label-elec').attr('x', cornerElec.x + 20).attr('y', cornerElec.y - 20).attr('text-anchor', 'start').attr('class', 'axis-label elec-label').text('Electrons').on('mouseenter', () => highlightAxis('elec')).on('mouseleave', () => unhighlightAxis('elec'));
    svg.append('text').attr('id', 'label-foss').attr('x', cornerFoss.x).attr('y', cornerFoss.y + 40).attr('text-anchor', 'middle').attr('class', 'axis-label foss-label').text('Fossil').on('mouseenter', () => highlightAxis('foss')).on('mouseleave', () => unhighlightAxis('foss'));
}

function updateChart() {
    const currentData = [];
    selectedCountries.forEach(country => {
        const countryData = RAW_DATA[country];
        if (countryData) {
            const years = Object.keys(countryData).map(Number).sort((a, b) => a - b);
            let displayYear = null;
            for (let y of years) { if (y <= currentYear) displayYear = y; else break; }

            if (displayYear !== null) {
                const d = countryData[displayYear][energyMode];
                if (d) {
                    currentData.push({
                        country,
                        year: displayYear,
                        bio: d.bio_pct / 100,
                        elec: d.electrons_pct / 100,
                        foss: d.fossil_pct / 100,
                        source: d.source,
                        absolute: d.total
                    });
                }
            }
        }
    });

    svg.selectAll('.trail-group').remove();
    const trailGroup = svg.append('g').attr('class', 'trail-group');

    selectedCountries.forEach(country => {
        const pathData = [];
        const years = Object.keys(RAW_DATA[country] || {}).map(y => parseInt(y)).sort((a, b) => a - b);
        let rawPoints = [];
        years.forEach(y => {
            const d = RAW_DATA[country][y][energyMode];
            if (d) rawPoints.push({ y, bio: d.bio_pct / 100, elec: d.electrons_pct / 100, foss: d.fossil_pct / 100 });
        });

        rawPoints.forEach((pt, i) => {
            if (pt.y <= currentYear) {
                let finalBio = pt.bio, finalElec = pt.elec, finalFoss = pt.foss;
                if (isSmoothed) {
                    let start = Math.max(0, i - 4);
                    let subset = rawPoints.slice(start, i + 1);
                    finalBio = d3.mean(subset, d => d.bio);
                    finalElec = d3.mean(subset, d => d.elec);
                    finalFoss = d3.mean(subset, d => d.foss);
                }
                pathData.push(ternToXY(finalBio, finalElec, finalFoss));
            }
        });

        if (pathData.length > 1) {
            const lineGen = d3.line().x(d => d.x).y(d => d.y).curve(d3.curveBundle.beta(1));
            trailGroup.append('path').attr('d', lineGen(pathData)).attr('class', 'year-trail').attr('stroke', COUNTRY_CONFIG[country].color).attr('fill', 'none');
        }
    });

    const points = svg.selectAll('.country-point').data(currentData, d => d.country);
    points.exit().remove();
    const enter = points.enter().append('circle').attr('class', 'country-point').attr('r', 6).attr('stroke', 'white').attr('stroke-width', 2).style('cursor', 'pointer');
    points.merge(enter)
        .attr('cx', d => ternToXY(d.bio, d.elec, d.foss).x)
        .attr('cy', d => ternToXY(d.bio, d.elec, d.foss).y)
        .attr('fill', d => COUNTRY_CONFIG[d.country].color)
        .on('mouseover', function (event, d) {
            const tooltip = d3.select('#tooltip').style('opacity', 1).html(`
                <div class="tooltip-title">${d.country} (${d.year})</div>
                <div class="tooltip-row"><span class="tooltip-label">Electricity</span><span class="tooltip-value">${(d.elec * 100).toFixed(1)}%</span></div>
                <div class="tooltip-row"><span class="tooltip-label">Fossil Fuels</span><span class="tooltip-value">${(d.foss * 100).toFixed(1)}%</span></div>
                <div class="tooltip-row"><span class="tooltip-label">Bio and other</span><span class="tooltip-value">${(d.bio * 100).toFixed(1)}%</span></div>
            `);
            positionTooltip(event);
            d3.selectAll('.year-trail').classed('dimmed', true);
            d3.select(this).attr('r', 8);
        })
        .on('mousemove', function (event) { positionTooltip(event); })
        .on('mouseout', function () { d3.select('#tooltip').style('opacity', 0); d3.selectAll('.year-trail').classed('dimmed', false); d3.select(this).attr('r', 6); });

    document.getElementById('data-source-label').innerText = currentData.length > 0 ? `Source: ${currentData[0].source}` : "";
}

function positionTooltip(event) {
    const tooltip = document.getElementById('tooltip'), rect = tooltip.getBoundingClientRect(), pad = 10;
    let x = event.pageX + pad, y = event.pageY + pad;
    if (x + rect.width > window.innerWidth) x = event.pageX - rect.width - pad;
    if (y + rect.height > window.innerHeight) y = event.pageY - rect.height - pad;
    tooltip.style.left = Math.max(pad, x) + 'px';
    tooltip.style.top = Math.max(pad, y) + 'px';
}

function setSmoothingMode(smooth) {
    isSmoothed = smooth;
    document.getElementById('btn-annual').classList.toggle('active', !smooth);
    document.getElementById('btn-smooth').classList.toggle('active', smooth);
    updateChart();
}

function renderLegend() {
    const legendContainer = document.getElementById('chart-legend');
    if (!legendContainer) return;
    legendContainer.innerHTML = '';
    const legendItem = document.createElement('div');
    legendItem.className = 'legend-item';
    legendItem.innerHTML = `<div class="color-dot" style="background:${COUNTRY_CONFIG["United Kingdom"].color}"></div><span>United Kingdom</span>`;
    legendContainer.appendChild(legendItem);
    legendContainer.style.display = 'flex';
}

function updateUI() {
    document.getElementById('year-display').innerText = currentYear;
    document.getElementById('year-slider').value = currentYear;
    document.getElementById('chart-title-range').innerText = `(1700 – ${currentYear})`;
    updateChart();
}

function setSpeed(speed) {
    playSpeed = speed;
    document.querySelectorAll('.speed-btn').forEach(btn => { btn.classList.toggle('active', parseFloat(btn.innerText) === speed); });
    if (isPlaying) { document.getElementById('play-pause-btn').click(); document.getElementById('play-pause-btn').click(); }
}

async function init() {
    const response = await fetch('uk_data.json');
    RAW_DATA = await response.json();
    const slider = document.getElementById('year-slider'), playBtn = document.getElementById('play-pause-btn');
    slider.addEventListener('input', (e) => { currentYear = parseInt(e.target.value); updateUI(); });
    playBtn.addEventListener('click', () => {
        isPlaying = !isPlaying;
        document.getElementById('play-icon').style.display = isPlaying ? 'none' : 'block';
        document.getElementById('pause-icon').style.display = isPlaying ? 'block' : 'none';
        if (isPlaying) {
            playInterval = setInterval(() => {
                currentYear = currentYear >= 2010 ? 1700 : currentYear + 1;
                updateUI();
            }, 1000 / (10 * playSpeed));
        } else clearInterval(playInterval);
    });
    drawTriangle();
    renderLegend();
    updateUI();
}

init();
