
import json
import os
import csv
from collections import defaultdict

# Paths (from generate_all_charts.py)
BASE_DIR = '/Users/daanwalter/Library/CloudStorage/OneDrive-SharedLibraries-Ember/ember-futures - Documents/03 Research/2026/97 Ideas/Ternary Chart Playground'
DATA_DIR = os.path.join(BASE_DIR, 'data')
IIASA_FILE = os.path.join(DATA_DIR, 'IIASA_dataset.csv')

REGION_CONFIG = {
    'OECD (1990 Members)': {'iiasa': 'OECD-90'},
    'Europe': {'iiasa_calc': (['OECD-90'], ['United States', 'Canada', 'Japan', 'Australia'])},
}

IIASA_TO_DISPLAY = {v['iiasa']: k for k, v in REGION_CONFIG.items() if 'iiasa' in v}
IIASA_CALC_REGIONS = {k: v['iiasa_calc'] for k, v in REGION_CONFIG.items() if 'iiasa_calc' in v}

IIASA_ELECTRONS = ['Electricity']
IIASA_FOSSIL = ['Coal Products', 'Natural Gas', 'Petroleum Products']
IIASA_TOTAL = ['All Fuels']

iiasa_final = defaultdict(lambda: defaultdict(dict))
iiasa_useful = defaultdict(lambda: defaultdict(dict))

print(f"Reading {IIASA_FILE}...")
with open(IIASA_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Sector'] != 'All Sectors': continue
        region = row['Region']
        if region not in IIASA_TO_DISPLAY: continue
        display_name = IIASA_TO_DISPLAY[region]
        fuel = row['Fuel']
        
        cat = None
        if fuel in IIASA_ELECTRONS: cat = 'electrons'
        elif fuel in IIASA_FOSSIL: cat = 'fossil'
        elif fuel in IIASA_TOTAL: cat = 'total'
        else: continue
        
        target_dict = None
        if row['Type'] == 'Final Energy': target_dict = iiasa_final
        elif row['Type'] == 'Useful Energy': target_dict = iiasa_useful
        else: continue
        
        for year_str, val in row.items():
            if year_str.isdigit() and val:
                try:
                    year = int(year_str)
                    value = float(val)
                    if cat not in target_dict[display_name][year]: target_dict[display_name][year][cat] = 0
                    target_dict[display_name][year][cat] += value
                except ValueError: pass

# Calculate Bio
for region_dict in [iiasa_final, iiasa_useful]:
    for country in region_dict:
        for year in region_dict[country]:
            rec = region_dict[country][year]
            total = rec.get('total', 0)
            elec = rec.get('electrons', 0)
            foss = rec.get('fossil', 0)
            rec['bio'] = max(0, total - elec - foss)

# Calculate Factors
eff_factors_map = defaultdict(lambda: defaultdict(dict))
for country in REGION_CONFIG.keys():
    for cat in ['electrons', 'fossil', 'bio']:
        known_years = []
        known_factors = []
        possible_years = sorted(list(set(iiasa_final[country].keys()) | set(iiasa_useful[country].keys())))
        for y in possible_years:
            fin = iiasa_final[country][y].get(cat, 0)
            use = iiasa_useful[country][y].get(cat, 0)
            if fin > 0 and use > 0:
                ratio = use / fin
                if 0 < ratio < 5: 
                    known_years.append(y)
                    known_factors.append(ratio)
        
        if not known_years:
            eff_factors_map[country][cat] = defaultdict(lambda: 1.0)
            continue
            
        full_series = {}
        min_y, max_y = known_years[0], known_years[-1]
        for y in range(1900, 2024):
            if y in known_years:
                full_series[y] = known_factors[known_years.index(y)]
            elif y < min_y:
                full_series[y] = known_factors[0]
            elif y > max_y:
                full_series[y] = known_factors[-1]
            else:
                prev_y = max([ky for ky in known_years if ky < y])
                next_y = min([ky for ky in known_years if ky > y])
                prev_val = known_factors[known_years.index(prev_y)]
                next_val = known_factors[known_years.index(next_y)]
                frac = (y - prev_y) / (next_y - prev_y)
                full_series[y] = prev_val + frac * (next_val - prev_val)
        eff_factors_map[country][cat] = full_series

print("\nFactors for OECD (1990 Members):")
for cat in ['electrons', 'fossil', 'bio']:
    f = eff_factors_map['OECD (1990 Members)'][cat].get(2020, "N/A")
    print(f"  {cat}: {f}")

print("\nFactors for Europe (before proxy):")
for cat in ['electrons', 'fossil', 'bio']:
    f = eff_factors_map['Europe'][cat].get(2020, "N/A")
    print(f"  {cat}: {f}")
