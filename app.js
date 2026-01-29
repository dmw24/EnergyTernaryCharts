// Regions (aggregates)
const REGIONS_CONFIG = {
    "Asia (Total)": { "color": "#fca5a5", "short": "ASI" },
    "Europe": { "color": "#3b82f6", "short": "EUR" },
    "Former Soviet Union": { "color": "#818cf8", "short": "FSU" },
    "Latin America & Caribbean": { "color": "#fbbf24", "short": "LAC" },
    "Middle East & Africa": { "color": "#f472b6", "short": "MEA" },
    "North America": { "color": "#7c3aed", "short": "NAM" },
    "OECD (1990 Members)": { "color": "#34d399", "short": "O90" },
    "World": { "color": "#000000", "short": "WLD" }
};

// Countries
const COUNTRIES_CONFIG = {
    "Australia": { "color": "#0d9488", "short": "AUS" },
    "Brazil": { "color": "#16a34a", "short": "BRA" },
    "Canada": { "color": "#9333ea", "short": "CAN" },
    "China": { "color": "#dc2626", "short": "CHN" },
    "France": { "color": "#0891b2", "short": "FRA" },
    "Germany": { "color": "#d97706", "short": "DEU" },
    "India": { "color": "#ea580c", "short": "IND" },
    "Italy": { "color": "#65a30d", "short": "ITA" },
    "Japan": { "color": "#db2777", "short": "JPN" },
    "Nigeria": { "color": "#ca8a04", "short": "NGA" },
    "Poland": { "color": "#dc2626", "short": "POL" },
    "South Africa": { "color": "#e11d48", "short": "ZAF" },
    "United States": { "color": "#2563eb", "short": "USA" }
};

// Combined config for backwards compatibility
const COUNTRY_CONFIG = { ...REGIONS_CONFIG, ...COUNTRIES_CONFIG };

// State
let RAW_DATA = {};
let selectedCountries = new Set(['United States', 'China', 'Germany', 'India', 'Brazil', 'World', 'Europe']);
let currentYear = 2023;
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

    // Add gradient tint bands - darkest at opposite corner, fading toward the axis
    const bands = [0, 0.2, 0.4, 0.6, 0.8];
    const opacities = [0.1, 0.05, 0.03, 0.01, 0.005]; // Lighter start, quick dropoff

    bands.forEach((t, i) => {
        const t2 = bands[i + 1] || 1.0;
        let points;

        if (axisType === 'bio') {
            // Bands expanding from opposite corner (Foss corner, where bio=0)
            // t=0 is at Foss corner (darkest), t=1 is at Bio corner (lightest)
            const p1 = ternToXY(t, 1 - t, 0);
            const p2 = ternToXY(t, 0, 1 - t);
            const p3 = ternToXY(t2, 0, 1 - t2);
            const p4 = ternToXY(t2, 1 - t2, 0);
            points = `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`;
        } else if (axisType === 'elec') {
            // Bands expanding from opposite corner (Foss corner, where elec=0)
            const p1 = ternToXY(0, t, 1 - t);
            const p2 = ternToXY(1 - t, t, 0);
            const p3 = ternToXY(1 - t2, t2, 0);
            const p4 = ternToXY(0, t2, 1 - t2);
            points = `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`;
        } else if (axisType === 'foss') {
            // Bands expanding from opposite edge (top edge, where foss=0)
            const p1 = ternToXY(0, 1 - t, t);
            const p2 = ternToXY(1 - t, 0, t);
            const p3 = ternToXY(1 - t2, 0, t2);
            const p4 = ternToXY(0, 1 - t2, t2);
            points = `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`;
        }

        // Reverse opacity - first band (near opposite corner) is darkest
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

    // Remove gradient tint bands
    svg.selectAll('.highlight-band').remove();
}

function drawTriangle() {
    // Add arrowhead marker definition first
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

    // Grid lines with axis-specific classes for hover highlighting
    [0.2, 0.4, 0.6, 0.8].forEach(t => {
        // Bio grid lines
        let b1 = ternToXY(t, 1 - t, 0), b2 = ternToXY(t, 0, 1 - t);
        svg.append('line').attr('x1', b1.x).attr('y1', b1.y).attr('x2', b2.x).attr('y2', b2.y)
            .attr('class', 'grid-line bio-grid');
        // Elec grid lines (horizontal-ish, parallel to top edge)
        let e1 = ternToXY(0, t, 1 - t), e2 = ternToXY(1 - t, t, 0);
        svg.append('line').attr('x1', e1.x).attr('y1', e1.y).attr('x2', e2.x).attr('y2', e2.y)
            .attr('class', 'grid-line elec-grid');
        // Foss grid lines (diagonal, parallel to left edge)
        let f1 = ternToXY(0, 1 - t, t), f2 = ternToXY(1 - t, 0, t);
        svg.append('line').attr('x1', f1.x).attr('y1', f1.y).attr('x2', f2.x).attr('y2', f2.y)
            .attr('class', 'grid-line foss-grid');
    });

    // Triangle edges
    // Left edge (Bio corner to Fossil corner) - for reading Bio values
    svg.append('line')
        .attr('x1', cornerBio.x).attr('y1', cornerBio.y)
        .attr('x2', cornerFoss.x).attr('y2', cornerFoss.y)
        .attr('class', 'axis-edge bio-edge')
        .on('mouseenter', () => highlightAxis('bio'))
        .on('mouseleave', () => unhighlightAxis('bio'));

    // Right edge (Elec corner to Fossil corner) - for reading Fossil values
    svg.append('line')
        .attr('x1', cornerElec.x).attr('y1', cornerElec.y)
        .attr('x2', cornerFoss.x).attr('y2', cornerFoss.y)
        .attr('class', 'axis-edge foss-edge')
        .on('mouseenter', () => highlightAxis('foss'))
        .on('mouseleave', () => unhighlightAxis('foss'));

    // Top edge (Bio corner to Elec corner) - for reading Electron values
    svg.append('line')
        .attr('x1', cornerBio.x).attr('y1', cornerBio.y)
        .attr('x2', cornerElec.x).attr('y2', cornerElec.y)
        .attr('class', 'axis-edge elec-edge')
        .on('mouseenter', () => highlightAxis('elec'))
        .on('mouseleave', () => unhighlightAxis('elec'));

    // Tick marks along each edge (0, 20, 40, 60, 80, 100)
    const tickValues = [0, 0.2, 0.4, 0.6, 0.8, 1.0];

    // LEFT EDGE TICKS (Bio axis) - 100 at top (Bio corner), 0 at bottom
    // Position goes from Bio corner (t=1) down to Fossil corner (t=0)
    tickValues.forEach(t => {
        const pos = ternToXY(t, 0, 1 - t); // t=1 is Bio corner, t=0 is Fossil corner
        const pct = Math.round(t * 100); // Show bio percentage (100 at top, 0 at bottom)
        svg.append('text')
            .attr('x', pos.x - 12)
            .attr('y', pos.y + 4)
            .attr('text-anchor', 'end')
            .attr('class', 'axis-tick bio-tick')
            .text(pct);
    });

    // RIGHT EDGE TICKS (showing fossil % increasing downward) - 0 at top, increasing down
    // Position goes from Electrons corner (t=0 fossil) down to Fossil corner (t=1 fossil)
    tickValues.forEach(t => {
        const pos = ternToXY(0, 1 - t, t); // t=0 at Elec corner, t=1 at Fossil corner
        const pct = Math.round(t * 100); // Show fossil percentage (0 at top, 100 at bottom)
        svg.append('text')
            .attr('x', pos.x + 12)
            .attr('y', pos.y + 4)
            .attr('text-anchor', 'start')
            .attr('class', 'axis-tick foss-tick')
            .text(pct);
    });

    // TOP EDGE TICKS (Electrons %) - 0 at left (Bio corner), 100 at right (Electrons corner)
    tickValues.forEach(t => {
        const pos = ternToXY(1 - t, t, 0); // t=0 at Bio corner, t=1 at Elec corner
        const pct = Math.round(t * 100); // Show electrons percentage
        svg.append('text')
            .attr('x', pos.x)
            .attr('y', pos.y - 10)
            .attr('text-anchor', 'middle')
            .attr('class', 'axis-tick elec-tick')
            .text(pct);
    });

    // Range labels matching reference image
    // Top edge: "Low electrons" on left, arrow pointing right, "High electrons" on right
    // Range labels matching reference image
    // Top edge: "Low electrons" on left, arrow pointing right, "High electrons" on right
    svg.append('text')
        .attr('x', cornerBio.x + 55)
        .attr('y', cornerBio.y - 45)
        .attr('text-anchor', 'start')
        .attr('class', 'axis-range-label elec-range')
        .text('Low electrons');

    svg.append('text')
        .attr('x', cornerElec.x - 55)
        .attr('y', cornerElec.y - 45)
        .attr('text-anchor', 'end')
        .attr('class', 'axis-range-label elec-range')
        .text('High electrons');

    // Arrow positioning constants
    const arrowLengthFactor = 0.6;
    const arrowOffset = 30; // Offset from axis edge

    // TOP EDGE ARROW (Electrons) - Increasing to right
    const elecArrowStartX = cornerBio.x + (innerWidth * (1 - arrowLengthFactor) / 2);
    const elecArrowEndX = cornerBio.x + (innerWidth * (1 + arrowLengthFactor) / 2);
    const elecArrowY = cornerBio.y - arrowOffset;

    svg.append('line')
        .attr('x1', elecArrowStartX)
        .attr('y1', elecArrowY)
        .attr('x2', elecArrowEndX)
        .attr('y2', elecArrowY)
        .attr('stroke', 'var(--slate-400)')
        .attr('stroke-width', 1)
        .attr('marker-end', 'url(#arrowhead)')
        .attr('class', 'axis-range-label elec-range');

    // LEFT EDGE ARROW (Bio) - Increasing towards top
    // 0 is Fossil corner, 1 is Bio corner
    const bioArrowStartT = (1 - arrowLengthFactor) / 2;
    const bioArrowEndT = 1 - bioArrowStartT;
    const bioP1 = ternToXY(bioArrowStartT, 0, 1 - bioArrowStartT);
    const bioP2 = ternToXY(bioArrowEndT, 0, 1 - bioArrowEndT);

    // Perpendicular offset for Bio arrow
    const bioAngle = Math.PI / 3; // 60 degrees
    const bioDx = -Math.sin(bioAngle) * arrowOffset - 50;
    const bioDy = -Math.cos(bioAngle) * arrowOffset + 10;

    svg.append('line')
        .attr('x1', bioP1.x + bioDx)
        .attr('y1', bioP1.y + bioDy)
        .attr('x2', bioP2.x + bioDx)
        .attr('y2', bioP2.y + bioDy)
        .attr('stroke', 'var(--slate-400)')
        .attr('stroke-width', 1)
        .attr('marker-end', 'url(#arrowhead)')
        .attr('class', 'axis-range-label bio-range');

    // RIGHT EDGE ARROW (Fossil) - Increasing towards bottom
    // 0 is Electrons corner, 1 is Fossil corner
    const fossArrowStartT = (1 - arrowLengthFactor) / 2;
    const fossArrowEndT = 1 - fossArrowStartT;
    const fossP1 = ternToXY(0, 1 - fossArrowStartT, fossArrowStartT);
    const fossP2 = ternToXY(0, 1 - fossArrowEndT, fossArrowEndT);

    // Perpendicular offset for Fossil arrow
    const fossAngle = -Math.PI / 3; // -60 degrees
    const fossDx = -Math.sin(fossAngle) * arrowOffset + 50;
    const fossDy = -Math.cos(fossAngle) * arrowOffset + 10;

    svg.append('line')
        .attr('x1', fossP1.x + fossDx)
        .attr('y1', fossP1.y + fossDy)
        .attr('x2', fossP2.x + fossDx)
        .attr('y2', fossP2.y + fossDy)
        .attr('stroke', 'var(--slate-400)')
        .attr('stroke-width', 1)
        .attr('marker-end', 'url(#arrowhead)')
        .attr('class', 'axis-range-label foss-range');

    // Left edge labels: "High bio" near top (100), nothing needed at bottom
    svg.append('text')
        .attr('x', cornerBio.x - 5)
        .attr('y', cornerBio.y + 90)
        .attr('text-anchor', 'end')
        .attr('class', 'axis-range-label bio-range')
        .text('High bio');

    // Right edge labels: "Low fossil" at top (0), "High fossil" implied at bottom
    svg.append('text')
        .attr('x', cornerElec.x - 5)
        .attr('y', cornerElec.y + 90)
        .attr('text-anchor', 'start')
        .attr('class', 'axis-range-label foss-range')
        .text('Low fossil');

    // Bottom labels
    svg.append('text')
        .attr('x', cornerFoss.x - 120)
        .attr('y', cornerFoss.y - 60)
        .attr('text-anchor', 'middle')
        .attr('class', 'axis-range-label bio-range')
        .text('Low bio');

    svg.append('text')
        .attr('x', cornerFoss.x + 120)
        .attr('y', cornerFoss.y - 60)
        .attr('text-anchor', 'middle')
        .attr('class', 'axis-range-label foss-range')
        .text('High fossil');

    // Corner labels with hover interactivity
    svg.append('text')
        .attr('id', 'label-bio')
        .attr('x', cornerBio.x - 20)
        .attr('y', cornerBio.y - 20)
        .attr('text-anchor', 'end')
        .attr('class', 'axis-label bio-label')
        .text('Bio & other')
        .on('mouseenter', () => highlightAxis('bio'))
        .on('mouseleave', () => unhighlightAxis('bio'));

    svg.append('text')
        .attr('id', 'label-elec')
        .attr('x', cornerElec.x + 20)
        .attr('y', cornerElec.y - 20)
        .attr('text-anchor', 'start')
        .attr('class', 'axis-label elec-label')
        .text('Electrons')
        .on('mouseenter', () => highlightAxis('elec'))
        .on('mouseleave', () => unhighlightAxis('elec'));

    svg.append('text')
        .attr('id', 'label-foss')
        .attr('x', cornerFoss.x)
        .attr('y', cornerFoss.y + 40)
        .attr('text-anchor', 'middle')
        .attr('class', 'axis-label foss-label')
        .text('Fossil')
        .on('mouseenter', () => highlightAxis('foss'))
        .on('mouseleave', () => unhighlightAxis('foss'));
}

function updateChart() {
    const currentData = [];
    selectedCountries.forEach(country => {
        const countryData = RAW_DATA[country];
        if (countryData) {
            const years = Object.keys(countryData).map(Number).sort((a, b) => a - b);
            let displayYear = null;
            for (let y of years) {
                if (y <= currentYear) displayYear = y;
                else break;
            }

            if (displayYear !== null) {
                const d = countryData[displayYear][energyMode];
                if (d) {
                    let bio, elec, foss, absolute;
                    if (energyMode === 'power') {
                        bio = (d.other_pct || 0) / 100;
                        elec = (d.wind_solar_pct || 0) / 100;
                        foss = (d.fossil_pct || 0) / 100;
                        absolute = d.total;
                    } else {
                        bio = (d.bio_pct || 0) / 100;
                        elec = (d.electrons_pct || 0) / 100;
                        foss = (d.fossil_pct || 0) / 100;
                        absolute = d.total;
                    }

                    currentData.push({
                        country,
                        year: displayYear,
                        bio, elec, foss,
                        source: d.source,
                        absolute
                    });
                }
            }
        }
    });

    // Trails
    svg.selectAll('.trail-group').remove();
    const trailGroup = svg.append('g').attr('class', 'trail-group');

    selectedCountries.forEach(country => {
        const pathData = [];
        const years = Object.keys(RAW_DATA[country] || {}).map(y => parseInt(y)).sort((a, b) => a - b);

        let rawPoints = [];
        years.forEach(y => {
            const d = RAW_DATA[country][y][energyMode];
            if (d) {
                let bio, elec, foss;
                if (energyMode === 'power') {
                    bio = d.other_pct / 100;
                    elec = d.wind_solar_pct / 100;
                    foss = d.fossil_pct / 100;
                } else {
                    bio = d.bio_pct / 100;
                    elec = d.electrons_pct / 100;
                    foss = d.fossil_pct / 100;
                }
                rawPoints.push({ y, bio, elec, foss });
            }
        });

        rawPoints.forEach((pt, i) => {
            const y = pt.y;
            if (energyMode === 'power' && y < 1985) return;
            if (y <= currentYear) {
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
            trailGroup.append('path')
                .attr('d', lineGen(pathData))
                .attr('class', 'year-trail')
                .attr('stroke', COUNTRY_CONFIG[country].color)
                .attr('fill', 'none');
        }
    });

    // Points
    const points = svg.selectAll('.country-point').data(currentData, d => d.country);
    points.exit().remove();

    const enter = points.enter().append('circle')
        .attr('class', 'country-point')
        .attr('r', 6)
        .attr('stroke', 'white')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer');

    points.merge(enter)
        .attr('cx', d => ternToXY(d.bio, d.elec, d.foss).x)
        .attr('cy', d => ternToXY(d.bio, d.elec, d.foss).y)
        .attr('fill', d => COUNTRY_CONFIG[d.country].color)
        .on('mouseover', function (event, d) {
            const tooltip = d3.select('#tooltip');
            let labels = {
                elec: 'Electricity',
                foss: 'Fossil Fuels',
                bio: 'Bio and other',
                total: 'Total'
            };

            if (energyMode === 'power') {
                labels.elec = 'Wind & Solar';
                labels.foss = 'Fossil Fuels';
                labels.bio = 'Other (Hydro/Bio/Nuc)';
                labels.total = 'Total Generation';
            }

            tooltip.style('opacity', 1)
                .html(`
                    <div class="tooltip-title">${d.country} (${d.year})</div>
                    <div class="tooltip-row"><span class="tooltip-label">${labels.elec}</span><span class="tooltip-value">${(d.elec * 100).toFixed(1)}%</span></div>
                    <div class="tooltip-row"><span class="tooltip-label">${labels.foss}</span><span class="tooltip-value">${(d.foss * 100).toFixed(1)}%</span></div>
                    <div class="tooltip-row"><span class="tooltip-label">${labels.bio}</span><span class="tooltip-value">${(d.bio * 100).toFixed(1)}%</span></div>
                `);

            positionTooltip(event);
            d3.selectAll('.year-trail').classed('dimmed', true);
            d3.select(this).attr('r', 8);
        })
        .on('mousemove', function (event) {
            positionTooltip(event);
        })
        .on('mouseout', function () {
            d3.select('#tooltip').style('opacity', 0);
            d3.selectAll('.year-trail').classed('dimmed', false);
            d3.select(this).attr('r', 6);
        });

    let sources = new Set(currentData.map(d => d.source));
    document.getElementById('data-source-label').innerText = "Source: IIASA, IEA, Electrotech Revolution team analysis";
}

function positionTooltip(event) {
    const tooltip = document.getElementById('tooltip');
    const tooltipRect = tooltip.getBoundingClientRect();
    const padding = 10;

    let x = event.pageX + padding;
    let y = event.pageY + padding;

    // Check if tooltip goes off right edge
    if (x + tooltipRect.width > window.innerWidth) {
        x = event.pageX - tooltipRect.width - padding;
    }

    // Check if tooltip goes off bottom edge
    if (y + tooltipRect.height > window.innerHeight) {
        y = event.pageY - tooltipRect.height - padding;
    }

    // Safety check for top/left
    x = Math.max(padding, x);
    y = Math.max(padding, y);

    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
}

function setSmoothingMode(smooth) {
    isSmoothed = smooth;
    document.getElementById('btn-annual').classList.toggle('active', !smooth);
    document.getElementById('btn-smooth').classList.toggle('active', smooth);
    updateChart();
}

function setEnergyMode(mode) {
    energyMode = mode;
    document.getElementById('btn-final').classList.toggle('active', mode === 'final');
    document.getElementById('btn-useful').classList.toggle('active', mode === 'useful');

    // Update header text based on mode
    const modeLabel = mode.charAt(0).toUpperCase() + mode.slice(1);
    const labelElement = document.getElementById('energy-type-label');
    if (labelElement) {
        labelElement.innerText = modeLabel;
    }

    const slider = document.getElementById('year-slider');
    if (mode === 'power') {
        slider.min = 1985;
        if (currentYear < 1985) {
            currentYear = 1985;
            slider.value = 1985;
            document.getElementById('year-display').innerText = 1985;
        }
        d3.select('#label-bio').text('Other');
        d3.select('#label-elec').text('Wind & Solar');
        d3.select('#label-foss').text('Fossil');
    } else {
        slider.min = 1900;
        d3.select('#label-bio').text('Bio & other');
        d3.select('#label-elec').text('Electrons');
        d3.select('#label-foss').text('Fossil');
    }

    updateChart();
}

function renderList() {
    const regionsContainer = document.getElementById('regions-list');
    const countriesContainer = document.getElementById('countries-list');

    // Render Regions
    regionsContainer.innerHTML = '';
    Object.keys(REGIONS_CONFIG).sort().forEach(region => {
        const item = document.createElement('div');
        item.className = 'region-item ' + (selectedCountries.has(region) ? 'active' : '');
        item.innerHTML = `
            <div class="color-dot" style="background:${REGIONS_CONFIG[region].color}"></div>
            <span>${region}</span>
        `;
        item.onclick = () => {
            if (selectedCountries.has(region)) selectedCountries.delete(region);
            else selectedCountries.add(region);
            renderList(); updateChart(); renderLegend();
        };
        regionsContainer.appendChild(item);
    });

    // Render Countries
    countriesContainer.innerHTML = '';
    Object.keys(COUNTRIES_CONFIG).sort().forEach(country => {
        const item = document.createElement('div');
        item.className = 'region-item ' + (selectedCountries.has(country) ? 'active' : '');
        item.innerHTML = `
            <div class="color-dot" style="background:${COUNTRIES_CONFIG[country].color}"></div>
            <span>${country}</span>
        `;
        item.onclick = () => {
            if (selectedCountries.has(country)) selectedCountries.delete(country);
            else selectedCountries.add(country);
            renderList(); updateChart(); renderLegend();
        };
        countriesContainer.appendChild(item);
    });
}

function renderLegend() {
    const legendContainer = document.getElementById('chart-legend');
    if (!legendContainer) return;

    legendContainer.innerHTML = '';

    // Sort selected countries/regions: Regions first, then Countries, both alphabetical
    const sortedSelection = Array.from(selectedCountries).sort((a, b) => {
        const isARegion = a in REGIONS_CONFIG;
        const isBRegion = b in REGIONS_CONFIG;
        if (isARegion && !isBRegion) return -1;
        if (!isARegion && isBRegion) return 1;
        return a.localeCompare(b);
    });

    sortedSelection.forEach(item => {
        const config = COUNTRY_CONFIG[item];
        if (!config) return;

        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <div class="color-dot" style="background:${config.color}"></div>
            <span>${item}</span>
        `;
        legendContainer.appendChild(legendItem);
    });

    legendContainer.style.display = sortedSelection.length > 0 ? 'flex' : 'none';
}

function toggleAll() {
    if (selectedCountries.size === Object.keys(COUNTRY_CONFIG).length) selectedCountries.clear();
    else selectedCountries = new Set(Object.keys(COUNTRY_CONFIG));
    renderList(); updateChart(); renderLegend();
}

function updateUI() {
    document.getElementById('year-display').innerText = currentYear;
    document.getElementById('year-slider').value = currentYear;

    // Update dynamic title range
    const startYear = energyMode === 'power' ? 1985 : 1900;
    document.getElementById('chart-title-range').innerText = `(${startYear} – ${currentYear})`;

    updateChart();
}

function setSpeed(speed) {
    playSpeed = speed;
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.classList.toggle('active', parseFloat(btn.innerText) === speed);
    });
    if (isPlaying) {
        document.getElementById('play-pause-btn').click();
        document.getElementById('play-pause-btn').click();
    }
}

// Initialize
async function init() {
    // Load data
    const response = await fetch('data.json');
    RAW_DATA = await response.json();

    // Setup UI
    const slider = document.getElementById('year-slider');
    const playBtn = document.getElementById('play-pause-btn');

    slider.addEventListener('input', (e) => {
        currentYear = parseInt(e.target.value);
        updateUI();
    });

    playBtn.addEventListener('click', () => {
        isPlaying = !isPlaying;
        document.getElementById('play-icon').style.display = isPlaying ? 'none' : 'block';
        document.getElementById('pause-icon').style.display = isPlaying ? 'block' : 'none';
        if (isPlaying) {
            playInterval = setInterval(() => {
                currentYear = currentYear >= 2023 ? 1900 : currentYear + 1;
                updateUI();
            }, 1000 / (10 * playSpeed));
        } else clearInterval(playInterval);
    });

    // Draw and render
    drawTriangle();
    renderList();
    renderLegend();
    updateUI();

    // Setup custom tooltips for elements with data-tooltip
    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (target) {
            const tooltip = d3.select('#tooltip');
            tooltip.style('opacity', 1)
                .html(`<div style="max-width: 200px;">${target.getAttribute('data-tooltip')}</div>`);
            positionTooltip(e);
        }
    });

    document.addEventListener('mousemove', (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (target) {
            positionTooltip(e);
        }
    });

    document.addEventListener('mouseout', (e) => {
        if (e.target.closest('[data-tooltip]')) {
            d3.select('#tooltip').style('opacity', 0);
        }
    });
}

// Start the app
init();
