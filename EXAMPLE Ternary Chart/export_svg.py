import json
import math

def main():
    # Dimensions - High resolution
    width = 1000
    height = 900
    margin = {'top': 50, 'right': 50, 'bottom': 50, 'left': 50}
    
    # Calculate triangle dimensions
    side = min(width - margin['left'] - margin['right'], height - margin['top'] - margin['bottom'])
    h = side * math.sqrt(3) / 2
    
    # Center the triangle vertically within the available space
    # The actual height often computed is 'h'.
    # Top Y = margin['top']
    # Bottom Y = margin['top'] + h
    
    # Vertices (INVERTED TRIANGLE: Point Down to match JS)
    # bio: Top Left
    # ele: Top Right
    # fos: Bottom
    
    # Logic from JS:
    # v.bio: x: width/2 - side/2, y: margin.top
    # v.ele: x: width/2 + side/2, y: margin.top
    # v.fos: x: width/2,          y: margin.top + h
    
    v_bio = {'x': width / 2 - side / 2, 'y': margin['top']}
    v_ele = {'x': width / 2 + side / 2, 'y': margin['top']}
    v_fos = {'x': width / 2,            'y': margin['top'] + h}

    def ternary_to_cartesian(e, f, b):
        total = e + f + b
        if total == 0: return {'x': 0, 'y': 0}
        E = e / total
        F = f / total
        B = b / total
        
        x = v_ele['x'] * E + v_fos['x'] * F + v_bio['x'] * B
        y = v_ele['y'] * E + v_fos['y'] * F + v_bio['y'] * B
        return {'x': x, 'y': y}

    # Load data
    with open('combined_energy_data.json', 'r') as f:
        data = json.load(f)

    countries_to_export = {
        'India': '#EE7309',
        'China': '#BF3100',
        'United States': '#1E6DA9'
    }

    combined_svg_elements = ""

    for country, color in countries_to_export.items():
        # Filter and sort data
        c_data = [d for d in data if d['country'] == country]
        c_data.sort(key=lambda x: x['year'])
        
        if not c_data:
            print(f"No data for {country}")
            continue

        # Generate Path string
        path_d = ""
        points = []
        for i, d in enumerate(c_data):
            # JS uses d.electrons_pct, d.fossil_pct, d.bio_pct
            p = ternary_to_cartesian(d['electrons_pct'], d['fossil_pct'], d['bio_pct'])
            points.append(p)
            
            # Use 2 decimal precision
            px = f"{p['x']:.2f}"
            py = f"{p['y']:.2f}"
            
            cmd = "M" if i == 0 else "L"
            path_d += f"{cmd} {px} {py} "

        if not points:
            continue

        # Latest point for the circle
        latest = points[-1]
        lx = f"{latest['x']:.2f}"
        ly = f"{latest['y']:.2f}"
        
        # SVG Content for Individual File
        # No background rect -> transparent background by default
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <!-- Path for {country} -->
    <path d="{path_d}" fill="none" stroke="{color}" stroke-width="4" stroke-opacity="0.8" stroke-linecap="round" stroke-linejoin="round"/>
    <!-- End Point -->
    <circle cx="{lx}" cy="{ly}" r="8" fill="{color}" stroke="#fff" stroke-width="3"/>
</svg>'''
        
        filename = f"{country.replace(' ', '_')}_chart.svg"
        with open(filename, 'w') as f:
            f.write(svg_content)
        print(f"Exported {filename}")

        # Add to combined SVG elements
        combined_svg_elements += f'''
    <!-- {country} -->
    <path d="{path_d}" fill="none" stroke="{color}" stroke-width="4" stroke-opacity="0.8" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="{lx}" cy="{ly}" r="8" fill="{color}" stroke="#fff" stroke-width="3"/>'''

    # Generate Combined SVG (No Triangle)
    combined_svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
{combined_svg_elements}
</svg>'''

    with open('combined_chart.svg', 'w') as f:
        f.write(combined_svg_content)
    print("Exported combined_chart.svg")

    # Generate Combined SVG (With Triangle Outline)
    # Triangle path: v_bio -> v_ele -> v_fos -> z
    triangle_path = f"M {v_bio['x']:.2f} {v_bio['y']:.2f} L {v_ele['x']:.2f} {v_ele['y']:.2f} L {v_fos['x']:.2f} {v_fos['y']:.2f} Z"
    
    combined_with_triangle_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <!-- Triangle Outline -->
    <path d="{triangle_path}" fill="none" stroke="#ccc" stroke-width="2" stroke-linejoin="round"/>
{combined_svg_elements}
</svg>'''

    with open('combined_chart_with_triangle.svg', 'w') as f:
        f.write(combined_with_triangle_content)
    print("Exported combined_chart_with_triangle.svg")

if __name__ == "__main__":
    main()
