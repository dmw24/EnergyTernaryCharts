import json
import csv
import os

def main():
    base_path = '/Users/daanwalter/Documents/EnergyPaths'
    json_file = f'{base_path}/combined_energy_data.json'
    csv_file = f'{base_path}/energy_data.csv'

    print(f"Reading {json_file}...")
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found.")
        return

    if not data:
        print("Error: No data found in JSON.")
        return

    # Extract headers from the first record
    headers = list(data[0].keys())
    
    # Ensure specific order if desired, or just use keys
    # Preferred order: country, year, electrons, fossil, bio, total, percentages, source
    preferred_order = ['country', 'year', 'electrons', 'fossil', 'bio', 'total', 'electrons_pct', 'fossil_pct', 'bio_pct', 'source']
    
    # usage intersection to keep only valid keys if data structure changes
    headers = [h for h in preferred_order if h in headers]
    
    print(f"Writing to {csv_file}...")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Success! CSV file created at: {csv_file}")

if __name__ == '__main__':
    main()
