#!/usr/bin/env python3
"""
Extract energy data from WORLDBAL.TXT for ternary chart visualization.

Extracts TFC (Total Final Consumption) data and calculates percentages for:
- Electrons: ELECTR + HEAT
- Fossil Molecules: COAL + NATGAS + MTOTOIL
- Bio Molecules: COMRENEW
"""

import json
from collections import defaultdict
import os

# Countries to include
COUNTRIES = [
    'USA', 'CHINA', 'GERMANY', 'UK', 'INDIA', 'BRAZIL', 'JAPAN', 'FRANCE',
    'ITALY', 'SPAIN', 'CANADA', 'AUSTRALI', 'MEXICO', 'KOREA', 'INDONESI'
]

# Products by category
ELECTRONS = ['ELECTR']
FOSSIL = ['COAL', 'NATGAS', 'MTOTOIL']
BIO = ['COMRENEW', 'HEAT']

# Years of interest (every 5 years from 1970 to 2023)
YEARS = list(range(1970, 2024, 5)) + [2023]

def parse_line(line):
    """Parse a fixed-width line from WORLDBAL.TXT"""
    if len(line) < 80:
        return None
    
    # Fixed-width columns (estimated from data)
    country = line[0:16].strip()
    product = line[16:32].strip()
    year = line[32:48].strip()
    flow = line[48:64].strip()
    unit = line[64:80].strip()
    value_str = line[80:].strip()
    
    # Skip if missing data
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

def main():
    data_file = '/Users/daanwalter/Documents/EnergyPaths/WORLDBAL.TXT'
    output_file = '/Users/daanwalter/Documents/EnergyPaths/energy_data.json'
    
    # Storage: country -> year -> product -> value
    energy_data = defaultdict(lambda: defaultdict(dict))
    
    all_products = set(ELECTRONS + FOSSIL + BIO)
    
    print("Reading WORLDBAL.TXT...")
    with open(data_file, 'r', encoding='latin-1') as f:
        line_count = 0
        matched = 0
        for line in f:
            line_count += 1
            if line_count % 1000000 == 0:
                print(f"  Processed {line_count:,} lines...")
            
            parsed = parse_line(line)
            if not parsed:
                continue
            
            # Filter for our criteria
            if (parsed['country'] in COUNTRIES and
                parsed['product'] in all_products and
                parsed['flow'] == 'TFC' and
                parsed['unit'] == 'KTOE'):
                
                energy_data[parsed['country']][parsed['year']][parsed['product']] = parsed['value']
                matched += 1
    
    print(f"Processed {line_count:,} lines, found {matched:,} matching records")
    
    # Calculate percentages for each country/year
    results = []
    
    for country in COUNTRIES:
        country_data = energy_data.get(country, {})
        
        for year in sorted(country_data.keys()):
            year_data = country_data[year]
            
            # Sum by category
            electrons = sum(year_data.get(p, 0) for p in ELECTRONS)
            fossil = sum(year_data.get(p, 0) for p in FOSSIL)
            bio = sum(year_data.get(p, 0) for p in BIO)
            
            total = electrons + fossil + bio
            
            if total > 0:
                results.append({
                    'country': country,
                    'year': year,
                    'electrons': electrons,
                    'fossil': fossil,
                    'bio': bio,
                    'total': total,
                    'electrons_pct': round(electrons / total * 100, 2),
                    'fossil_pct': round(fossil / total * 100, 2),
                    'bio_pct': round(bio / total * 100, 2)
                })
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved {len(results)} records to {output_file}")
    
    # Print sample
    print("\nSample data (USA, latest years):")
    usa_data = [r for r in results if r['country'] == 'USA'][-5:]
    for r in usa_data:
        print(f"  {r['year']}: Electrons={r['electrons_pct']:.1f}%, Fossil={r['fossil_pct']:.1f}%, Bio={r['bio_pct']:.1f}%")

if __name__ == '__main__':
    main()
