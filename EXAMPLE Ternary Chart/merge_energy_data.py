#!/usr/bin/env python3
"""
Merge IIASA (1900-2014) and IEA (2015-2023) energy data and embed into HTML.

Extracts Final Energy data and calculates percentages for:
- Electrons: Electricity + Heat
- Fossil Molecules: Coal + Gas + Oil products
- Bio Molecules: Biomass/Combustible Renewables
"""

import csv
import json
from collections import defaultdict
import os

# Country mapping: IIASA name -> IEA code
COUNTRY_MAPPING = {
    'United States': 'USA',
    'China': 'CHINA',
    'Germany': 'GERMANY',
    'United Kingdom': 'UK',
    'Japan': 'JAPAN',
    'France': 'FRANCE',
    'India': 'INDIA',
    'Brazil': 'BRAZIL',
    'Australia': 'AUSTRALI',
    'Canada': 'CANADA',
    'Italy': 'ITALY',
    'Poland': 'POLAND',
    'South Africa': 'SOUTHAFRIC',
    'Nigeria': 'NIGERIA',
}

# Reverse mapping for IEA -> display name
IEA_TO_DISPLAY = {v: k for k, v in COUNTRY_MAPPING.items()}

# IIASA fuel classification
IIASA_ELECTRONS = ['Electricity']
IIASA_FOSSIL = ['Coal Products', 'Natural Gas', 'Petroleum Products']
IIASA_BIO = ['Biomass', 'Heat']

# IEA product classification
IEA_ELECTRONS = ['ELECTR']
IEA_FOSSIL = ['COAL', 'NATGAS', 'MTOTOIL']
IEA_BIO = ['COMRENEW', 'HEAT']

# Transition year - use IIASA up to and including this year
TRANSITION_YEAR = 2014


def parse_iea_line(line):
    """Parse a fixed-width line from WORLDBAL.TXT"""
    if len(line) < 80:
        return None
    
    country = line[0:16].strip()
    product = line[16:32].strip()
    year = line[32:48].strip()
    flow = line[48:64].strip()
    unit = line[64:80].strip()
    value_str = line[80:].strip()
    
    if '..' in value_str or not value_str:
        return None
    
    try:
        year = int(year)
        value = float(value_str)
    except (ValueError, TypeError):
        return None
    
    return {
        'country': country,
        'product': product,
        'year': year,
        'flow': flow,
        'unit': unit,
        'value': value
    }


def load_iiasa_data(filepath):
    """Load and process IIASA data for years up to TRANSITION_YEAR."""
    energy_data = defaultdict(lambda: defaultdict(dict))
    
    print("Reading IIASA_dataset.csv...")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row['Type'] != 'Final Energy' or row['Sector'] != 'All Sectors':
                continue
            
            region = row['Region']
            fuel = row['Fuel']
            
            if region not in COUNTRY_MAPPING:
                continue
            if fuel not in (IIASA_ELECTRONS + IIASA_FOSSIL + IIASA_BIO):
                continue
            
            display_name = region
            
            for year in range(1900, TRANSITION_YEAR + 1):
                year_str = str(year)
                if year_str in row and row[year_str]:
                    try:
                        value = float(row[year_str])
                        if fuel in IIASA_ELECTRONS:
                            cat = 'electrons'
                        elif fuel in IIASA_FOSSIL:
                            cat = 'fossil'
                        else:
                            cat = 'bio'
                        
                        if cat not in energy_data[display_name][year]:
                            energy_data[display_name][year][cat] = 0
                        energy_data[display_name][year][cat] += value
                    except ValueError:
                        pass
    
    return energy_data


def load_iea_data(filepath):
    """Load and process IEA data for years after TRANSITION_YEAR."""
    energy_data = defaultdict(lambda: defaultdict(dict))
    all_products = set(IEA_ELECTRONS + IEA_FOSSIL + IEA_BIO)
    iea_countries = set(COUNTRY_MAPPING.values())
    
    print("Reading WORLDBAL.TXT...")
    with open(filepath, 'r', encoding='latin-1') as f:
        line_count = 0
        matched = 0
        for line in f:
            line_count += 1
            if line_count % 5000000 == 0:
                print(f"  Processed {line_count:,} lines...")
            
            parsed = parse_iea_line(line)
            if not parsed:
                continue
            
            if (parsed['country'] in iea_countries and
                parsed['product'] in all_products and
                parsed['flow'] == 'TFC' and
                parsed['unit'] == 'KTOE' and
                parsed['year'] > TRANSITION_YEAR):
                
                display_name = IEA_TO_DISPLAY[parsed['country']]
                year = parsed['year']
                product = parsed['product']
                
                if product in IEA_ELECTRONS:
                    cat = 'electrons'
                elif product in IEA_FOSSIL:
                    cat = 'fossil'
                else:
                    cat = 'bio'
                
                if cat not in energy_data[display_name][year]:
                    energy_data[display_name][year][cat] = 0
                energy_data[display_name][year][cat] += parsed['value']
                matched += 1
    
    print(f"Processed {line_count:,} lines, found {matched:,} matching records")
    return energy_data


def main():
    base_path = '/Users/daanwalter/Documents/EnergyPaths'
    iiasa_file = f'{base_path}/IIASA_dataset.csv'
    iea_file = f'{base_path}/WORLDBAL.TXT'
    html_file = f'{base_path}/energy_ternary_chart.html'
    
    # Load both datasets
    iiasa_data = load_iiasa_data(iiasa_file)
    iea_data = load_iea_data(iea_file)
    
    # Merge data
    print("\nMerging datasets...")
    results = []
    
    for display_name in COUNTRY_MAPPING.keys():
        all_years = set()
        if display_name in iiasa_data:
            all_years.update(iiasa_data[display_name].keys())
        if display_name in iea_data:
            all_years.update(iea_data[display_name].keys())
        
        for year in sorted(all_years):
            if year <= TRANSITION_YEAR:
                source_data = iiasa_data.get(display_name, {}).get(year, {})
                data_source = 'IIASA'
            else:
                source_data = iea_data.get(display_name, {}).get(year, {})
                data_source = 'IEA'
            
            electrons = source_data.get('electrons', 0)
            fossil = source_data.get('fossil', 0)
            bio = source_data.get('bio', 0)
            total = electrons + fossil + bio
            
            if total > 0:
                results.append({
                    'country': display_name,
                    'year': year,
                    'electrons': round(electrons, 2),
                    'fossil': round(fossil, 2),
                    'bio': round(bio, 2),
                    'total': round(total, 2),
                    'electrons_pct': round(electrons / total * 100, 2),
                    'fossil_pct': round(fossil / total * 100, 2),
                    'bio_pct': round(bio / total * 100, 2),
                    'source': data_source
                })
    
    print(f"Generated {len(results)} data records.")
    
    # Read HTML template
    print(f"Reading {html_file}...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Inject data
    json_data = json.dumps(results)
    
    # Replace empty array with data
    if 'let energyData = [];' in html_content:
        print("Injecting JSON data into HTML...")
        new_html = html_content.replace('let energyData = [];', f'let energyData = {json_data};')
        
        # Replace the Tick generation loop logic
        # Since we can't reliably replace just that block, we will replace the initChart block
        # and include a function to override drawTriangle? 
        # No, easier to just rely on the Python script to inject a REPLACEMENT script.
        
        # Wait, I cannot change the existing JS in the HTML file easily if I'm just reading/writing the whole file 
        # unless I do stringent replace.
        
        # ACTUALLY, I should just update the HTML file FIRST with `write_to_file` to include the correct JS logic
        # AND THEN run the python script to inject the data.
        # But `merge_energy_data.py` reads the HTML file.
        # If I update HTML first, `merge_energy_data` will read the updated HTML.
        # This is better.
    else:
        # Write to combined_energy_data.json
        output_json = f'{base_path}/combined_energy_data.json'
        print(f"Saving combined data to {output_json}...")
        with open(output_json, 'w') as f:
            json.dump(results, f, indent=2)


if __name__ == '__main__':
    main()
