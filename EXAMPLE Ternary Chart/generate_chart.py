#!/usr/bin/env python3
"""Generate complete ternary chart HTML with embedded data"""

import json

# Read the data
with open('/Users/daanwalter/Documents/EnergyPaths/ternary_data.json', 'r') as f:
    data = json.load(f)

# JavaScript code template
js_code = f"""
        // Embedded data - {len(data)} records from 1900-2014
        const energyData = {json.dumps(data, indent=2)};

        // Country color palette
        const countryColors = {{
            "United States": "#ef4444",
            "China": "#f59e0b",
            "Germany": "#10b981",
            "Japan": "#3b82f6",
            "India": "#a855f7",
            "Brazil": "#14b8a6",
            "United Kingdom": "#ec4899",
            "France": "#6366f1"
        }};

        // Chart dimensions
        const width = 800;
        const height = 720;
        const margin = {{ top: 70, right: 70, bottom: 90, left: 70 }};
        
        const triangleWidth = width - margin.left - margin.right;
        const triangleHeight = triangleWidth * Math.sqrt(3) / 2;

        // Create SVG
        const svg = d3.select("#chart-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}}, ${{margin.top}})`);

        // Triangle vertices
        const vertices = {{
            fossil: [0, triangleHeight],
            electrons: [triangleWidth, triangleHeight],
            bio: [triangleWidth / 2, 0]
        }};

        // Convert ternary to Cartesian coordinates
        function ternaryToCartesian(electrons, fossil, bio) {{
            const total = electrons + fossil + bio;
            const e = electrons / total;
            const f = fossil / total;
            const b = bio / total;
            
            const x = vertices.fossil[0] * f + vertices.electrons[0] * e + vertices.bio[0] * b;
            const y = vertices.fossil[1] * f + vertices.electrons[1] * e + vertices.bio[1] * b;
            
            return [x, y];
        }}

        // Draw triangle border
        const trianglePath = `M ${{vertices.fossil.join(',')}} L ${{vertices.electrons.join(',')}} L ${{vertices.bio.join(',')}} Z`;
        g.append("path")
            .attr("d", trianglePath)
            .attr("class", "triangle-border");

        // Draw grid lines
        const gridLevels = 10;
        for (let i = 1; i < gridLevels; i++) {{
            const ratio = i / gridLevels;
            
            // Parallel to fossil-electrons (bottom)
            const p1 = ternaryToCartesian(ratio * 100, (1 - ratio) * 100, 0);
            const p2 = ternaryToCartesian(ratio * 100, 0, (1 - ratio) * 100);
            g.append("line")
                .attr("x1", p1[0]).attr("y1", p1[1])
                .attr("x2", p2[0]).attr("y2", p2[1])
                .attr("class", "grid-line");

            // Parallel to fossil-bio (left)
            const p3 = ternaryToCartesian(0, ratio * 100, (1 - ratio) * 100);
            const p4 = ternaryToCartesian((1 - ratio) * 100, ratio * 100, 0);
            g.append("line")
                .attr("x1", p3[0]).attr("y1", p3[1])
                .attr("x2", p4[0]).attr("y2", p4[1])
                .attr("class", "grid-line");

            // Parallel to electrons-bio (right)
            const p5 = ternaryToCartesian((1 - ratio) * 100, 0, ratio * 100);
            const p6 = ternaryToCartesian(0, (1 - ratio) * 100, ratio * 100);
            g.append("line")
                .attr("x1", p5[0]).attr("y1", p5[1])
                .attr("x2", p6[0]).attr("y2[1])
                .attr("class", "grid-line");
        }}

        // Add tick labels
        for (let i = 0; i <= gridLevels; i += 2) {{
            const pct = i * 10;
            
            // Fossil axis (bottom-left)
            const fossilTick = ternaryToCartesian(0, pct, 100 - pct);
            g.append("text")
                .attr("x", fossilTick[0] - 18)
                .attr("y", fossilTick[1] + 5)
                .attr("text-anchor", "end")
                .attr("class", "tick-label")
                .text(`${{pct}}%`);

            // Electrons axis (bottom-right)
            const electronsTick = ternaryToCartesian(pct, 100 - pct, 0);
            g.append("text")
                .attr("x", electronsTick[0])
                .attr("y", electronsTick[1] + 24)
                .attr("text-anchor", "middle")
                .attr("class", "tick-label")
                .text(`${{pct}}%`);

            // Bio axis (right side)
            const bioTick = ternaryToCartesian(100 - pct, 0, pct);
            g.append("text")
                .attr("x", bioTick[0] + 18)
                .attr("y", bioTick[1] + 5)
                .attr("text-anchor", "start")
                .attr("class", "tick-label")
                .text(`${{pct}}%`);
        }}

        // Axis labels
        g.append("text")
            .attr("x", triangleWidth / 2)
            .attr("y", triangleHeight + 65)
            .attr("text-anchor", "middle")
            .attr("class", "axis-label")
            .text("← Fossil Molecules                    Electrons →");

        g.append("text")
            .attr("x", -50)
            .attr("y", triangleHeight / 2)
            .attr("text-anchor", "middle")
            .attr("transform", `rotate(-60, -50, ${{triangleHeight / 2}})`)
            .attr("class", "axis-label")
            .style("fill", "#10b981")
            .text("Bio Molecules →");

        g.append("text")
            .attr("x", triangleWidth + 50)
            .attr("y", triangleHeight / 2)
            .attr("text-anchor", "middle")
            .attr("transform", `rotate(60, ${{triangleWidth + 50}}, ${{triangleHeight / 2}})`)
            .attr("class", "axis-label")
            .style("fill", "#10b981")
            .text("← Bio Molecules");

        // Tooltip
        const tooltip = d3.select("#tooltip");

        // Group data by country
        const countries = [...new Set(energyData.map(d => d.country))];
        let selectedCountry = null;

        // Draw paths and points for each country
        countries.forEach(country => {{
            const countryData = energyData.filter(d => d.country === country)
                .sort((a, b) => a.year - b.year);

            // Convert to Cartesian coordinates
            const points = countryData.map(d => ({{
                ...d,
                coords: ternaryToCartesian(d.electrons_pct, d.fossil_pct, d.bio_pct)
            }}));

            // Create smooth line generator
            const lineGen = d3.line()
                .x(d => d.coords[0])
                .y(d => d.coords[1])
                .curve(d3.curveCardinal.tension(0.5));

            // Draw path
            g.append("path")
                .datum(points)
                .attr("class", `country-path path-${{country.replace(/\\s+/g, '-')}}`)
                .attr("d", lineGen)
                .attr("fill", "none")
                .attr("stroke", countryColors[country])
                .attr("stroke-width", 3)
                .attr("stroke-opacity", 0.7)
                .attr("stroke-linecap", "round")
                .attr("stroke-linejoin", "round");

            // Draw points
            const pointsGroup = g.selectAll(`.point-${{country.replace(/\\s+/g, '-')}}`)
                .data(points)
                .enter()
                .append("g")
                .attr("class", `country-point point-${{country.replace(/\\s+/g, '-')}}`);

            pointsGroup.append("circle")
                .attr("cx", d => d.coords[0])
                .attr("cy", d => d.coords[1])
                .attr("r", d => d.year === 2014 || d.year === 1900 ? 8 : 4)
                .attr("fill", countryColors[country])
                .attr("stroke", "#fff")
                .attr("stroke-width", d => d.year === 2014 || d.year === 1900 ? 2.5 : 1.5)
                .attr("cursor", "pointer")
                .style("filter", d => d.year === 2014 || d.year === 1900 ? "drop-shadow(0 0 8px rgba(0,0,0,0.5))" : "none")
                .on("mouseover", function(event, d) {{
                    d3.select(this)
                        .transition()
                        .duration(150)
                        .attr("r", d.year === 2014 || d.year === 1900 ? 11 : 7);
                    
                    tooltip
                        .style("opacity", 1)
                        .html(`
                            <div class="tooltip-country">${{d.country}}</div>
                            <div class="tooltip-year">${{d.year}}</div>
                            <div class="tooltip-row">
                                <span class="tooltip-label">Electrons:</span>
                                <span class="tooltip-value">${{d.electrons_pct.toFixed(1)}}%</span>
                            </div>
                            <div class="tooltip-row">
                                <span class="tooltip-label">Fossil:</span>
                                <span class="tooltip-value">${{d.fossil_pct.toFixed(1)}}%</span>
                            </div>
                            <div class="tooltip-row">
                                <span class="tooltip-label">Bio:</span>
                                <span class="tooltip-value">${{d.bio_pct.toFixed(1)}}%</span>
                            </div>
                        `)
                        .style("left", (event.pageX + 15) + "px")
                        .style("top", (event.pageY - 10) + "px");
                }})
                .on("mouseout", function(event, d) {{
                    d3.select(this)
                        .transition()
                        .duration(150)
                        .attr("r", d.year === 2014 || d.year === 1900 ? 8 : 4);
                    
                    tooltip.style("opacity", 0);
                }});

            // Add year labels for first and last points
            [points[0], points[points.length - 1]].forEach((d, i) => {{
                const offset = 15;
                const angle = i === 0 ? -Math.PI / 4 : Math.PI / 4;
                const xOffset = Math.cos(angle) * offset;
                const yOffset = Math.sin(angle) * offset;
                
                g.append("text")
                    .attr("class", `year-label label-${{country.replace(/\\s+/g, '-')}}`)
                    .attr("x", d.coords[0] + xOffset)
                    .attr("y", d.coords[1] + yOffset)
                    .attr("text-anchor", "middle")
                    .attr("fill", countryColors[country])
                    .style("font-weight", "bold")
                    .text(d.year);
            }});
        }});

        // Create legend
        const legend = d3.select("#legend");
        countries.forEach(country => {{
            const item = legend.append("div")
                .attr("class", "legend-item")
                .on("click", function() {{
                    if (selectedCountry === country) {{
                        // Deselect
                        selectedCountry = null;
                        d3.selectAll(".legend-item").classed("dimmed", false).classed("active", false);
                        d3.selectAll(".country-path").attr("stroke-opacity", 0.7).attr("stroke-width", 3);
                        d3.selectAll(".country-point circle").attr("opacity", 1);
                        d3.selectAll(".year-label").attr("opacity", 1);
                    }} else {{
                        // Select this country
                        selectedCountry = country;
                        d3.selectAll(".legend-item")
                            .classed("dimmed", function() {{
                                return d3.select(this).select(".legend-text").text() !== country;
                            }})
                            .classed("active", function() {{
                                return d3.select(this).select(".legend-text").text() === country;
                            }});
                        
                        d3.selectAll(".country-path")
                            .attr("stroke-opacity", function() {{
                                return this.classList.contains(`path-${{country.replace(/\\s+/g, '-')}}`) ? 1 : 0.12;
                            }})
                            .attr("stroke-width", function() {{
                                return this.classList.contains(`path-${{country.replace(/\\s+/g, '-')}}`) ? 5 : 2;
                            }});
                        
                        d3.selectAll(".country-point circle")
                            .attr("opacity", function() {{
                                return this.parentNode.classList.contains(`point-${{country.replace(/\\s+/g, '-')}}`) ? 1 : 0.15;
                            }});
                        
                        d3.selectAll(".year-label")
                            .attr("opacity", function() {{
                                return this.classList.contains(`label-${{country.replace(/\\s+/g, '-')}}`) ? 1 : 0.15;
                            }});
                    }}
                }});

            item.append("div")
                .attr("class", "legend-marker")
                .style("background-color", countryColors[country]);

            item.append("div")
                .attr("class", "legend-text")
                .text(country);
        }});
"""

# Read the HTML template
with open('/Users/daanwalter/Documents/EnergyPaths/ternary_chart.html', 'r') as f:
    html_content = f.read()

# Replace the empty script tag with the full JavaScript
html_content = html_content.replace('<script></script>', f'<script>{js_code}</script>')

# Write the complete HTML
with open('/Users/daanwalter/Documents/EnergyPaths/ternary_chart.html', 'w') as f:
    f.write(html_content)

print("✓ Generated complete ternary_chart.html with embedded data and visualization code")
print(f"✓ Includes {len(data)} records from 1900-2014 for 8 countries")
