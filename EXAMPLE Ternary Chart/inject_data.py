import json
import os

def main():
    base_path = '/Users/daanwalter/Documents/EnergyPaths'
    html_file = f'{base_path}/energy_ternary_chart.html'
    json_file = f'{base_path}/combined_energy_data.json'
    
    print(f"Reading {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    json_str = json.dumps(data)
    
    print(f"Reading {html_file}...")
    with open(html_file, 'r') as f:
        html_content = f.read()
    
    # Check markers
    # if 'let energyData = [];' not in html_content:
    #     print("ERROR: 'let energyData = [];' not found!")
    #     return
        
    # if '// Load data' not in html_content:
    #     print("ERROR: '// Load data' not found!")
    #     return

    # Replace data using regex to handle existing populated data
    print("Injecting data...")
    import re
    # Pattern to match: let energyData = [ ... ];
    # We use dotall to match across newlines
    pattern = r'let energyData = \[.*?\];'
    
    if re.search(pattern, html_content, re.DOTALL):
        new_html = re.sub(pattern, f'let energyData = {json_str};', html_content, flags=re.DOTALL)
    elif 'let energyData = [];' in html_content:
        # Fallback for empty init
        new_html = html_content.replace('let energyData = [];', f'let energyData = {json_str};')
    else:
        print("ERROR: Could not find 'let energyData = [...];' to replace!")
        return
    
    print("Writing updated HTML...")
    with open(html_file, 'w') as f:
        f.write(new_html)
    
    print("Success!")

if __name__ == '__main__':
    main()
