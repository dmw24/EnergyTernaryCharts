import json
import os
from collections import defaultdict

# Mock the script behavior to see what's in the merged results
# (I'll just read the generated all_countries_ternary_charts.html and parse the JSON)

with open('all_countries_ternary_charts.html', 'r') as f:
    content = f.read()
    start_marker = 'const RAW_DATA = '
    end_marker = ';'
    start_idx = content.find(start_marker) + len(start_marker)
    # Finding the true end of the JSON object can be tricky if it spans multiple lines or has semicolons
    # But for our case, it's usually on its own line or followed by a newline and then a semicolon
    # Let's try to extract it based on the marker in the generator script
    
    # Actually, the generator script does:
    # final_html = html_template.replace('%DATA%', json.dumps(json_data))
    # And the template has: const RAW_DATA = %DATA%;
    
    end_idx = content.find(';', start_idx)
    raw_json = content[start_idx:end_idx]
    try:
        data = json.loads(raw_json)
        print(f"Data contains keys for {len(data)} countries.")
        for country, entry in data.items():
            years = sorted([int(y) for y in entry.keys()])
            if years:
                latest = years[-1]
                if latest == 2023:
                    print(f"  {country}: Success! Latest is 2023")
                else:
                   pass # print(f"  {country}: Latest is {latest}")
            else:
                print(f"  {country}: No years found")
                
        # Count 2023 specifically
        count_2023 = 0
        for country, entry in data.items():
            if '2023' in entry:
                count_2023 += 1
        print(f"Total 2023 entries: {count_2023}")
        
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        # Try finding 2023 as a string in the whole file
        print(f"Raw 2023 count in file: {content.count('\"2023\":')}")

