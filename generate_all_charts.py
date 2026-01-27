#!/usr/bin/env python3
"""
Generate ternary charts for all countries by merging IIASA and IEA data.
Matches the exact visual style of the provided example.
"""

import csv
import json
from collections import defaultdict
import os

# Paths
BASE_DIR = '/Users/daanwalter/Library/CloudStorage/OneDrive-SharedLibraries-Ember/ember-futures - Documents/03 Research/2026/97 Ideas/Ternary Chart Playground'
DATA_DIR = os.path.join(BASE_DIR, 'data')
IIASA_FILE = os.path.join(DATA_DIR, 'IIASA_dataset.csv')
IEA_FILE = os.path.join(DATA_DIR, 'WORLDBAL.TXT')
EMBER_FILE = os.path.join(DATA_DIR, 'Ember Electricity Generation Data.xlsx')
NEW_EMBER_FILE = os.path.join(DATA_DIR, 'electricity-prod-source-stacked.csv')
OUTPUT_HTML = os.path.join(BASE_DIR, 'all_countries_ternary_charts.html')

import pandas as pd

# Region configuration with calculation rules for IEA
REGION_CONFIG = {
    'United States': {'color': '#2563eb', 'short': 'USA', 'iiasa': 'United States', 'iea': 'USA', 'ember': 'United States of America'},
    'China': {'color': '#dc2626', 'short': 'CHN', 'iiasa': 'China', 'iea': 'CHINA'},
    'Germany': {'color': '#d97706', 'short': 'DEU', 'iiasa': 'Germany', 'iea': 'GERMANY'},
    'United Kingdom': {'color': '#7c3aed', 'short': 'GBR', 'iiasa': 'United Kingdom', 'iea': 'UK'},
    'Japan': {'color': '#db2777', 'short': 'JPN', 'iiasa': 'Japan', 'iea': 'JAPAN'},
    'France': {'color': '#0891b2', 'short': 'FRA', 'iiasa': 'France', 'iea': 'FRANCE'},
    'India': {'color': '#ea580c', 'short': 'IND', 'iiasa': 'India', 'iea': 'INDIA'},
    'Brazil': {'color': '#16a34a', 'short': 'BRA', 'iiasa': 'Brazil', 'iea': 'BRAZIL'},
    'Australia': {'color': '#0d9488', 'short': 'AUS', 'iiasa': 'Australia', 'iea': 'AUSTRALI'},
    'Canada': {'color': '#9333ea', 'short': 'CAN', 'iiasa': 'Canada', 'iea': 'CANADA'},
    'Italy': {'color': '#65a30d', 'short': 'ITA', 'iiasa': 'Italy', 'iea': 'ITALY'},
    'Poland': {'color': '#4f46e5', 'short': 'POL', 'iiasa': 'Poland', 'iea': 'POLAND'},
    'South Africa': {'color': '#e11d48', 'short': 'ZAF', 'iiasa': 'South Africa', 'iea': 'SOUTHAFRIC'},
    'Nigeria': {'color': '#ca8a04', 'short': 'NGA', 'iiasa': 'Nigeria', 'iea': 'NIGERIA'},
    'World': {'color': '#000000', 'short': 'WLD', 'iiasa': 'World', 'iea': 'WORLD'},
    # Aggregates & Residuals
    'Asia (Total)': {'color': '#fca5a5', 'short': 'ASI', 'iiasa': 'ASIA', 'iea': 'UNASIATOT'},
    'Other Asia': {'color': '#fda4af', 'short': 'ASO', 'iiasa': 'ASIother', 
                   'iea_calc': ('UNASIATOT', ['CHINA', 'INDIA', 'JAPAN'])},
    'Former Soviet Union': {'color': '#818cf8', 'short': 'FSU', 'iiasa': 'Former Soviet Union', 'iea': 'EURASIA'},
    'OECD (1990 Members)': {'color': '#34d399', 'short': 'O90', 'iiasa': 'OECD-90', 'iea': 'OECDTOT'},
    'Eastern Europe & FSU': {'color': '#a78bfa', 'short': 'EEF', 'iiasa': 'REF', 'iea': 'NOECDTOT'}, 
    'Latin America & Caribbean': {'color': '#fbbf24', 'short': 'LAC', 'iiasa': 'LAM', 'iea': 'LATAMER'},
    'Middle East & Africa': {'color': '#f472b6', 'short': 'MEA', 'iiasa': 'MEA', 
                             'iea_calc': (['MIDEAST', 'AFRICA'], [])}, # Sum Mideast+Africa
    'Rest of Latin America': {'color': '#fcd34d', 'short': 'RLA', 'iiasa': 'LAMother', 
                              'iea_calc': ('LATAMER', ['BRAZIL'])},
    'Rest of MEA': {'color': '#f9a8d4', 'short': 'RME', 'iiasa': 'MEAother', 
                    'iea_calc': (['MIDEAST', 'AFRICA'], ['SOUTHAFRIC', 'NIGERIA'])},
    'Rest of EE / FSU': {'color': '#c4b5fd', 'short': 'REF', 'iiasa': 'REFother', 
                         'iea_calc': ('NOECDTOT', ['EURASIA'])}, # NOECDTOT includes FSU(EURASIA) + East Europe. So Sub FSU gives East Eur.
    'Rest of OECD (1990)': {'color': '#6ee7b7', 'short': 'RO9', 'iiasa': 'O90other', 
                            'iea_calc': ('OECDTOT', ['USA', 'GERMANY', 'UK', 'JAPAN', 'FRANCE', 'AUSTRALI', 'CANADA', 'ITALY'])},
}

# Inverse mappings
IIASA_TO_DISPLAY = {v['iiasa']: k for k, v in REGION_CONFIG.items()}
# IEA Loading needs to range over all explicit codes AND all codes mentioned in calcs
IEA_CODES_TO_LOAD = set()
for v in REGION_CONFIG.values():
    if 'iea' in v: IEA_CODES_TO_LOAD.add(v['iea'])
    if 'iea_calc' in v:
        pos, neg = v['iea_calc']
        if isinstance(pos, str): IEA_CODES_TO_LOAD.add(pos)
        else: IEA_CODES_TO_LOAD.update(pos)
        IEA_CODES_TO_LOAD.update(neg)

# IIASA fuel classification
IIASA_ELECTRONS = ['Electricity']
IIASA_FOSSIL = ['Coal Products', 'Natural Gas', 'Petroleum Products']
IIASA_TOTAL = ['All Fuels'] # Used to calculate "Bio and other" as residual

# IEA product classification
IEA_ELECTRONS = ['ELECTR']
IEA_FOSSIL = ['COAL', 'NATGAS', 'MTOTOIL']
IEA_TOTAL = ['TOTAL'] # Used to calculate "Bio and other" as residual

def parse_iea_line(line):
    if len(line) < 80: return None
    country = line[0:16].strip()
    product = line[16:32].strip()
    year = line[32:48].strip()
    flow = line[48:64].strip()
    unit = line[64:80].strip()
    value_str = line[80:].strip()
    if '..' in value_str or not value_str: return None
    try:
        year = int(year)
        value = float(value_str)
    except (ValueError, TypeError): return None
    return {'country': country, 'product': product, 'year': year, 'flow': flow, 'unit': unit, 'value': value}

def load_iiasa_data(filepath):
    energy_data = defaultdict(lambda: defaultdict(dict))
    print(f"Reading {filepath}...")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Type'] != 'Final Energy' or row['Sector'] != 'All Sectors': continue
            iiasa_region = row['Region']
            fuel = row['Fuel']
            if iiasa_region not in IIASA_TO_DISPLAY: continue
            display_name = IIASA_TO_DISPLAY[iiasa_region]
            
            # Load Electrons, Fossil, and Total
            if fuel not in (IIASA_ELECTRONS + IIASA_FOSSIL + IIASA_TOTAL): continue
            
            for year_str, val in row.items():
                if year_str.isdigit():
                    year = int(year_str)
                    if val:
                        try:
                            value = float(val)
                            cat = 'electrons' if fuel in IIASA_ELECTRONS else 'fossil' if fuel in IIASA_FOSSIL else 'total'
                            if cat not in energy_data[display_name][year]: energy_data[display_name][year][cat] = 0
                            energy_data[display_name][year][cat] += value
                        except ValueError: pass
    
    # Calculate "Bio and other" as residual (Total - Electrons - Fossil)
    for country in energy_data:
        for year in energy_data[country]:
            rec = energy_data[country][year]
            total = rec.get('total', 0)
            elec = rec.get('electrons', 0)
            foss = rec.get('fossil', 0)
            # Ensure Bio includes everything else
            bio = max(0, total - elec - foss)
            energy_data[country][year]['bio'] = bio
            
    return energy_data

def load_iea_data(filepath):
    # Raw IEA store: Code -> Year -> Category -> Value
    raw_iea = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    all_products = set(IEA_ELECTRONS + IEA_FOSSIL + IEA_TOTAL)
    
    print(f"Reading {filepath}...")
    with open(filepath, 'r', encoding='latin-1') as f:
        line_count = 0
        for line in f:
            line_count += 1
            if line_count % 10000000 == 0: print(f"  Processed {line_count:,} lines...")
            parsed = parse_iea_line(line)
            if not parsed: continue
            
            if (parsed['country'] in IEA_CODES_TO_LOAD and parsed['product'] in all_products and
                parsed['flow'] == 'TFC' and parsed['unit'] == 'KTOE'):
                
                cat = 'electrons' if parsed['product'] in IEA_ELECTRONS else 'fossil' if parsed['product'] in IEA_FOSSIL else 'total'
                raw_iea[parsed['country']][parsed['year']][cat] += parsed['value']
    
    # Process into Display Names
    energy_data = defaultdict(lambda: defaultdict(dict))
    
    for display_name, config in REGION_CONFIG.items():
        # Direct Mapping
        if 'iea' in config:
            code = config['iea']
            for year, cats in raw_iea[code].items():
                energy_data[display_name][year] = cats.copy()
        
        # Calculated Mapping
        elif 'iea_calc' in config:
            pos_codes, neg_codes = config['iea_calc']
            if isinstance(pos_codes, str): pos_codes = [pos_codes]
            
            # Find all relevant years
            all_years = set()
            for code in pos_codes + neg_codes:
                all_years.update(raw_iea[code].keys())
            
            for year in all_years:
                res = {'electrons': 0, 'fossil': 0, 'total': 0}
                
                # Add positives
                for code in pos_codes:
                    if year in raw_iea[code]:
                        for c in res: res[c] += raw_iea[code][year].get(c, 0)
                
                # Subtract negatives
                for code in neg_codes:
                    if year in raw_iea[code]:
                        for c in res: res[c] -= raw_iea[code][year].get(c, 0)
                
                # Ensure no negatives due to data mismatches (clamp to 0)
                for c in res: res[c] = max(0, res[c])
                
                if sum(res.values()) > 0:
                    energy_data[display_name][year] = res

    # Calculate "Bio and other" as residual
    for country in energy_data:
        for year in energy_data[country]:
            rec = energy_data[country][year]
            total = rec.get('total', 0)
            elec = rec.get('electrons', 0)
            foss = rec.get('fossil', 0)
            bio = max(0, total - elec - foss)
            energy_data[country][year]['bio'] = bio

    return energy_data

def main():
    iiasa_data = load_iiasa_data(IIASA_FILE)
    iea_data = load_iea_data(IEA_FILE)
    
    print("\nMerging datasets...")
    results = []
    source_counts = defaultdict(int)
    overlap_prioritized = []

    for display_name in REGION_CONFIG.keys():
        all_years = set()
        if display_name in iiasa_data: all_years.update(iiasa_data[display_name].keys())
        if display_name in iea_data: all_years.update(iea_data[display_name].keys())
        
        for year in sorted(all_years):
            # PRIORITIZE IEA DATA, BUT CHECK FOR COMPLETENESS (Bioenergy Gap)
            has_iea = year in iea_data.get(display_name, {})
            has_iiasa = year in iiasa_data.get(display_name, {})
            
            use_iea = False
            
            if has_iea:
                iea_rec = iea_data[display_name][year]
                iea_bio = iea_rec.get('bio', 0)
                
                # Checking for completeness:
                # 1. Must have Bioenergy (unless year >= 1990)
                # 2. Must have Fossil Fuels (to avoid "Electrons only" spikes like Other LAM 1971)
                iea_fossil = iea_rec.get('fossil', 0)
                
                # Condition 1: Bioenergy check
                bio_ok = (iea_bio > 0 or year >= 1990)
                if not bio_ok and has_iiasa and iiasa_data[display_name][year].get('bio', 0) > 0:
                    bio_ok = False
                else:
                    bio_ok = True # Either has bio, or trusted 0, or IIASA also has 0
                
                # Condition 2: Fossil check (Must have some fossil energy if IIASA has it)
                fossil_ok = True
                if iea_fossil == 0:
                     if has_iiasa and iiasa_data[display_name][year].get('fossil', 0) > 0:
                         fossil_ok = False
                
                if bio_ok and fossil_ok:
                    use_iea = True
                else:
                    use_iea = False

            if use_iea:
                source_data = iea_data[display_name][year]
                source_name = 'IEA'
                if has_iiasa and not has_iea: # Should not happen with logic above, but for safety
                     pass 
                elif has_iiasa:
                    overlap_prioritized.append((display_name, year))
            elif has_iiasa:
                source_data = iiasa_data[display_name][year]
                source_name = 'IIASA'
            else:
                continue
            
            source_counts[source_name] += 1
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
                    'source': source_name
                })
    
    print(f"Generated {len(results)} merged records.")
    
    # Calculate Useful Energy
    # Strategy: Calculate Efficiency Ratios from IIASA (Useful/Final) and apply to Merged Data
    print("Calculating Useful Energy...")
    
    # Reload IIASA data specifically for Useful Energy to calculate ratios
    # We need a strictly IIASA-only view for this to derive the factors
    iiasa_final = defaultdict(lambda: defaultdict(dict))
    iiasa_useful = defaultdict(lambda: defaultdict(dict))
    
    with open(IIASA_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Sector'] != 'All Sectors': continue
            region = row['Region']
            if region not in IIASA_TO_DISPLAY: continue
            display_name = IIASA_TO_DISPLAY[region]
            fuel = row['Fuel']
            
            # Identify Category
            cat = None
            if fuel in IIASA_ELECTRONS: cat = 'electrons'
            elif fuel in IIASA_FOSSIL: cat = 'fossil'
            elif fuel in IIASA_TOTAL: cat = 'total'
            else: continue
            
            # Determine Flow Type
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

    # Calculate Bio Residuals for Useful Energy Ratios
    for region_dict in [iiasa_final, iiasa_useful]:
        for country in region_dict:
            for year in region_dict[country]:
                rec = region_dict[country][year]
                total = rec.get('total', 0)
                elec = rec.get('electrons', 0)
                foss = rec.get('fossil', 0)
                rec['bio'] = max(0, total - elec - foss)

    # Load Ember Data (Power Generation)
    print(f"Reading {EMBER_FILE}...")
    ember_raw = pd.read_excel(EMBER_FILE)
    ember_data = defaultdict(lambda: defaultdict(dict))
    
    # Map for Ember Areas
    EMBER_MAP = {v.get('ember', k): k for k, v in REGION_CONFIG.items()}
    
    # Filter Relevant Rows (Category=Electricity generation)
    gen_df = ember_raw[
        (ember_raw['Category'] == 'Electricity generation') & 
        (ember_raw['Area'].isin(EMBER_MAP.keys()))
    ]
    
    # Pivot to get variables as columns: Year, Area, Variable -> Value
    # Using 'Variable' column: 'Fossil', 'Wind and Solar', 'Total Generation'
    # 'Other' needs to be calculated: Total - Fossil - Wind&Solar
    
    # We'll group by Area, Year, Variable and sum Value (just in case there are dupes, though likely unique)
    pivoted = gen_df.pivot_table(index=['Area', 'Year'], columns='Variable', values='Value', aggfunc='sum').reset_index()
    
    for _, row in pivoted.iterrows():
        area = row['Area']
        year = int(row['Year'])
        country_key = EMBER_MAP[area]
        
        # Helper to get value
        def get_val(col_name):
            val = row.get(col_name, 0)
            return 0 if pd.isna(val) else val

        # Atomic components mapping
        # Fossil = Coal + Gas + Other Fossil
        # Wind & Solar = Wind + Solar
        # Other = Hydro + Bioenergy + Nuclear + Other Renewables
        
        coal = get_val('Coal')
        gas = get_val('Gas')
        other_fossil = get_val('Other Fossil')
        fossil_sum = coal + gas + other_fossil
        
        wind = get_val('Wind')
        solar = get_val('Solar')
        ws_sum = wind + solar
        
        hydro = get_val('Hydro')
        bio = get_val('Bioenergy')
        nuc = get_val('Nuclear')
        other_ren = get_val('Other Renewables')
        other_sum = hydro + bio + nuc + other_ren
        
        # Calculate strict total from components
        total_calc = fossil_sum + ws_sum + other_sum
        
        if total_calc > 0:
             ember_data[country_key][year] = {
                 'fossil': fossil_sum,
                 'wind_solar': ws_sum,
                 'other': other_sum,
                 'total': total_calc,
                 'fossil_pct': round(fossil_sum / total_calc * 100, 2),
                 'wind_solar_pct': round(ws_sum / total_calc * 100, 2),
                 'other_pct': round(other_sum / total_calc * 100, 2),
                 'source': 'Ember'
             }
             
    # Load NEW Extended Ember Data (1985 onwards)
    print(f"Reading {NEW_EMBER_FILE}...")
    new_ember_raw = pd.read_csv(NEW_EMBER_FILE)
    
    # Map for New Dataset Areas (Direct Match for most)
    # The config keys map to 'Entity' in CSV
    NEW_EMBER_MAP = {k: k for k in REGION_CONFIG.keys()} # Default to direct match
    # Specific Overrides if needed (e.g., US is 'United States' in new vs 'United States of America' in old)
    for k, v in REGION_CONFIG.items():
        if 'ember_new' in v: NEW_EMBER_MAP[v['ember_new']] = k
    
    # Columns in new dataset
    # "Electricity from coal - TWh..." -> 'Coal'
    # "Electricity from gas - TWh..." -> 'Gas'
    # "Electricity from oil - TWh..." -> 'Oil'
    # "Electricity from nuclear - TWh..." -> 'Nuclear'
    # "Electricity from hydro - TWh..." -> 'Hydro'
    # "Electricity from wind - TWh..." -> 'Wind'
    # "Electricity from solar - TWh..." -> 'Solar'
    # "Electricity from bioenergy - TWh..." -> 'Bioenergy'
    # "Other renewables excluding bioenergy - TWh..." -> 'Other Renewables'
    
    col_map = {
        'Electricity from coal - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Coal',
        'Electricity from gas - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Gas',
        'Electricity from oil - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Oil',
        'Electricity from nuclear - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Nuclear',
        'Electricity from hydro - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Hydro',
        'Electricity from wind - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Wind',
        'Electricity from solar - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Solar',
        'Electricity from bioenergy - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Bioenergy',
        'Other renewables excluding bioenergy - TWh (adapted for visualization of chart electricity-prod-source-stacked)': 'Other Renewables'
    }
    
    for _, row in new_ember_raw.iterrows():
        entity = row['Entity']
        if entity not in NEW_EMBER_MAP and entity not in REGION_CONFIG: continue
        
        country_key = entity if entity in REGION_CONFIG else NEW_EMBER_MAP.get(entity)
        if not country_key: continue
        
        year = int(row['Year'])
        
        # Only use if we don't already have better data from main Ember file (prioritize main for recent years, new for older)
        # Actually, let's just overwrite/fill. Since main Ember usually starts 2000, this fills 1985-1999.
        # Check if year exists in ember_data
        if year in ember_data[country_key]: continue 
        
        # Calculate components
        coal = row.get(next(k for k in col_map if 'coal' in k), 0)
        gas = row.get(next(k for k in col_map if 'gas' in k), 0)
        oil = row.get(next(k for k in col_map if 'oil' in k), 0)
        nuc = row.get(next(k for k in col_map if 'nuclear' in k), 0)
        hydro = row.get(next(k for k in col_map if 'hydro' in k), 0)
        wind = row.get(next(k for k in col_map if 'wind' in k), 0)
        solar = row.get(next(k for k in col_map if 'solar' in k), 0)
        bio = row.get(next(k for k in col_map if 'bio' in k and 'excluding' not in k), 0)
        other_ren = row.get(next(k for k in col_map if 'Other renewables' in k), 0)
        
        # Handle NaNs
        def get_val(v): return 0 if pd.isna(v) else v
        coal = get_val(coal); gas = get_val(gas); oil = get_val(oil);
        nuc = get_val(nuc); hydro = get_val(hydro); wind = get_val(wind);
        solar = get_val(solar); bio = get_val(bio); other_ren = get_val(other_ren);
        
        fossil = coal + gas + oil
        wind_solar = wind + solar
        other = nuc + hydro + bio + other_ren
        total_gen = fossil + wind_solar + other
        
        if total_gen > 0:
             ember_data[country_key][year] = {
                 'fossil': fossil,
                 'wind_solar': wind_solar,
                 'other': other,
                 'total': total_gen,
                 'fossil_pct': round(fossil / total_gen * 100, 2),
                 'wind_solar_pct': round(wind_solar / total_gen * 100, 2),
                 'other_pct': round(other / total_gen * 100, 2),
                 'source': 'Ember (History)'
             }

    # Compute Ratios and Apply to Results
    # Result structure: {country: {year: {final: ..., useful: ..., power: ...}}}
    combined_data = defaultdict(lambda: defaultdict(lambda: {'final': {}, 'useful': {}, 'power': {}}))
    
    # Pre-compute Efficiency Factors (Interpolated) for all countries/fuels
    # Structure: eff_factors_map[country][cat] = {year: factor}
    eff_factors_map = defaultdict(lambda: defaultdict(dict))
    
    for country in REGION_CONFIG.keys():
        for cat in ['electrons', 'fossil', 'bio']:
            # Gather known points
            known_years = []
            known_factors = []
            
            # Check years where we have both Final and Useful data in IIASA
            possible_years = sorted(list(set(iiasa_final[country].keys()) | set(iiasa_useful[country].keys())))
            for y in possible_years:
                fin = iiasa_final[country][y].get(cat, 0)
                use = iiasa_useful[country][y].get(cat, 0)
                if fin > 0 and use > 0: # Only use if we have valid non-zero data for Ratio
                    ratio = use / fin
                    # Sanity check: Ratio shouldn't be wildly > 2 or < 0
                    if 0 < ratio < 5: 
                        known_years.append(y)
                        known_factors.append(ratio)
            
            if not known_years:
                # Default to 1.0 if no data ever
                eff_factors_map[country][cat] = defaultdict(lambda: 1.0)
                continue
                
            # Create Interpolation Function
            # We will generate a map for the full range of years (1900-2023)
            # Strategy: Linear Interpolation for gaps, Constant Extrapolation for ends
            full_series = {}
            min_y, max_y = known_years[0], known_years[-1]
            
            for y in range(1900, 2024):
                if y in known_years:
                    idx = known_years.index(y)
                    full_series[y] = known_factors[idx]
                elif y < min_y:
                    full_series[y] = known_factors[0] # Constant Backcast
                elif y > max_y:
                    full_series[y] = known_factors[-1] # Constant Forecast
                else:
                    # Linear Interpolation
                    # Find bounds
                    prev_y = max([ky for ky in known_years if ky < y])
                    next_y = min([ky for ky in known_years if ky > y])
                    prev_val = known_factors[known_years.index(prev_y)]
                    next_val = known_factors[known_years.index(next_y)]
                    
                    frac = (y - prev_y) / (next_y - prev_y)
                    val = prev_val + frac * (next_val - prev_val)
                    full_series[y] = val
            
            eff_factors_map[country][cat] = full_series

    # Pre-fill with Final Energy results we already generated
    for r in results:
        c = r['country']
        y = r['year']
        combined_data[c][y]['final'] = {
            'electrons': round(r['electrons'], 2),
            'fossil': round(r['fossil'], 2),
            'bio': round(r['bio'], 2),
            'total': round(r['total'], 2),
            'electrons_pct': r['electrons_pct'],
            'fossil_pct': r['fossil_pct'],
            'bio_pct': r['bio_pct'],
            'source': r['source']
        }
        
        # Calculate Useful
        # Apply factor to the MERGED final energy (which might be IEA or IIASA)
        useful_rec = {}
        total_useful = 0
        
        for cat in ['electrons', 'fossil', 'bio']:
            final_val = r[cat]
            # Get interpolated factor
            # If map has function (dict), use it. Else default 1.0
            factor = 1.0
            if c in eff_factors_map and cat in eff_factors_map[c]:
                factor = eff_factors_map[c][cat].get(y, 1.0)
            
            # Apply
            useful_val = final_val * factor
            useful_rec[cat] = useful_val
            total_useful += useful_val
            
        # Percents
        if total_useful > 0:
            combined_data[c][y]['useful'] = {
                'electrons': round(useful_rec['electrons'], 2),
                'fossil': round(useful_rec['fossil'], 2),
                'bio': round(useful_rec['bio'], 2),
                'total': round(total_useful, 2),
                'electrons_pct': round(useful_rec['electrons'] / total_useful * 100, 2),
                'fossil_pct': round(useful_rec['fossil'] / total_useful * 100, 2),
                'bio_pct': round(useful_rec['bio'] / total_useful * 100, 2),
                'source': r['source']
            }
        else:
             combined_data[c][y]['useful'] = combined_data[c][y]['final'] # Fallback if 0

        # Inject Ember Power Data if available
        if c in ember_data and y in ember_data[c]:
            combined_data[c][y]['power'] = ember_data[c][y]


    # HTML Template (Reverting to original design + small Toggle)
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Energy Transition - Ternary Chart</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --slate-50: #f8fafc;
            --slate-100: #f1f5f9;
            --slate-200: #e2e8f0;
            --slate-300: #cbd5e1;
            --slate-400: #94a3b8;
            --slate-500: #64748b;
            --slate-600: #475569;
            --slate-700: #334155;
            --slate-800: #1e293b;
            --slate-900: #0f172a;
            --blue-600: #2563eb;
        }

        body { 
            margin: 0; 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background-color: white; 
            color: var(--slate-800);
            -webkit-font-smoothing: antialiased;
        }

        .layout {
            display: grid;
            grid-template-columns: 1fr 320px;
            height: 100vh;
            overflow: hidden;
        }

        /* Chart Area */
        .main-content {
            padding: 40px 60px;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            position: relative;
        }

        .header {
            margin-bottom: 32px;
        }

        h1 { 
            font-size: 32px; 
            font-weight: 800; 
            margin: 0; 
            color: var(--slate-900);
            letter-spacing: -0.025em;
        }

        .subtitle { 
            font-size: 15px; 
            color: var(--slate-500); 
            margin-top: 8px;
            font-weight: 500;
        }

        /* Sidebar */
        .sidebar {
            background-color: var(--slate-50);
            border-left: 1px solid var(--slate-200);
            display: flex;
            flex-direction: column;
            padding: 32px 24px;
            overflow: hidden;
        }

        .section-label {
            font-size: 11px;
            font-weight: 700;
            color: var(--slate-400);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Toggle Button */
        .toggle-group {
            display: flex;
            background: var(--slate-200);
            padding: 4px;
            border-radius: 12px;
            margin-bottom: 32px;
        }

        .toggle-btn {
            flex: 1;
            padding: 8px;
            font-size: 13px;
            font-weight: 600;
            text-align: center;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--slate-500);
        }

        .toggle-btn.active {
            background: white;
            color: var(--slate-900);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* Regions List */
        .regions-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 0;
            margin-bottom: 24px;
        }

        .regions-list {
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding-right: 4px;
        }

        .region-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: var(--slate-600);
            transition: all 0.1s;
        }

        .region-item:hover {
            background: var(--slate-200);
            color: var(--slate-900);
        }

        .region-item.active {
            background: white;
            color: var(--slate-900);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .color-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .select-all-btn {
            font-size: 11px;
            color: var(--blue-600);
            cursor: pointer;
            font-weight: 600;
        }

        /* Controls */
        .playback-controls {
            margin-top: auto;
            background: white;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid var(--slate-100);
        }

        .top-controls {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }

        .play-pause {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--slate-900);
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s;
        }

        .play-pause:active { transform: scale(0.95); }

        .current-year {
            font-size: 24px;
            font-weight: 800;
            color: var(--slate-900);
            font-variant-numeric: tabular-nums;
        }

        #year-slider {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: var(--slate-200);
            outline: none;
            -webkit-appearance: none;
            margin: 20px 0;
        }

        #year-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            background: var(--slate-900);
            border-radius: 50%;
            cursor: pointer;
            transition: transform 0.1s;
        }

        .speed-selector {
            display: flex;
            gap: 4px;
        }

        .speed-btn {
            flex: 1;
            padding: 6px;
            font-size: 11px;
            font-weight: 700;
            background: var(--slate-100);
            border: none;
            border-radius: 6px;
            color: var(--slate-500);
            cursor: pointer;
        }

        .speed-btn.active {
            background: var(--slate-900);
            color: white;
        }

        /* Visualization Elements */
        #viz-container {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .triangle-axis { stroke: var(--slate-300); stroke-width: 1.5; }
        .grid-line { stroke: var(--slate-100); stroke-width: 1; }
        .axis-label { font-size: 14px; font-weight: 700; fill: var(--slate-800); }
        .year-trail { fill: none; stroke-width: 2; opacity: 0.6; stroke-linecap: round; }
        .year-trail.dimmed { opacity: 0.05; }
        
        .tooltip {
            position: absolute;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(8px);
            border: 1px solid var(--slate-200);
            border-radius: 12px;
            padding: 16px;
            font-size: 13px;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            pointer-events: none;
            opacity: 0;
            z-index: 100;
            min-width: 180px;
        }

        .tooltip-title { font-weight: 700; font-size: 14px; margin-bottom: 12px; color: var(--slate-900); border-bottom: 1px solid var(--slate-100); padding-bottom: 8px; }
        .tooltip-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .tooltip-label { color: var(--slate-500); font-weight: 500; }
        .tooltip-value { font-weight: 700; color: var(--slate-900); }
        .tooltip-source { font-size: 10px; color: var(--slate-400); margin-top: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
    </style>
</head>
<body>
    <div class="layout">
        <main class="main-content">
            <header class="header">
                <h1>Global Energy Transition</h1>
                <div class="subtitle">Historical & Projected Transition Path (1900 – 2023)</div>
                <div class="subtitle" id="data-source-label" style="font-size:11px; opacity:0.8;">Source: IIASA / IEA</div>
            </header>

            <div id="viz-container">
                <div id="tooltip" class="tooltip"></div>
            </div>
        </main>

        <aside class="sidebar">
            <div class="section-label">Energy Type</div>
            <div class="toggle-group">
                <div class="toggle-btn active" id="btn-final" onclick="setEnergyMode('final')">Final</div>
                <div class="toggle-btn" id="btn-useful" onclick="setEnergyMode('useful')">Useful</div>
                <div class="toggle-btn" id="btn-power" onclick="setEnergyMode('power')">Power Generation</div>
            </div>

            <div class="section-label">Trailing Line</div>
            <div class="toggle-group">
                <div class="toggle-btn active" id="btn-annual" onclick="setSmoothingMode(false)">Annual</div>
                <div class="toggle-btn" id="btn-smooth" onclick="setSmoothingMode(true)">5-Year Average</div>
            </div>

            <div class="regions-wrapper">
                <div class="section-label">
                    <span>Regions</span>
                    <span class="select-all-btn" onclick="toggleAll()">SELECT ALL</span>
                </div>
                <div class="regions-list" id="regions-list"></div>
            </div>

            <div class="playback-controls">
                <div class="top-controls">
                    <button class="play-pause" id="play-pause-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" id="play-icon"><path d="M8 5v14l11-7z"/></svg>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" id="pause-icon" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                    </button>
                    <div class="current-year" id="year-display">2023</div>
                    <div class="speed-selector">
                        <button class="speed-btn active" onclick="setSpeed(1)">1x</button>
                        <button class="speed-btn" onclick="setSpeed(2)">2x</button>
                        <button class="speed-btn" onclick="setSpeed(5)">5x</button>
                    </div>
                </div>
                <input type="range" id="year-slider" min="1900" max="2023" value="2023" step="1">
            </div>
        </aside>
    </div>

    <script>
        const COUNTRY_CONFIG = %COUNTRIES%;
        const RAW_DATA = %DATA%;
        
        let selectedCountries = new Set(['United States', 'China', 'Germany', 'India', 'Brazil', 'World']);
        let currentYear = 2023;
        let isPlaying = false;
        let playInterval = null;
        let playSpeed = 1;
        let energyMode = 'final';
        let isSmoothed = false;

        const width = 800;
        const height = 700;
        const margin = { top: 60, right: 80, bottom: 80, left: 80 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        
        const triangleHeight = innerWidth * Math.sqrt(3) / 2;
        
        // Final Orientation: Left (Bio), Right (Electrons), Bottom (Fossil) [Center Pointing Down]
        const cornerBio = { x: 0, y: 0 };
        const cornerElec = { x: innerWidth, y: 0 };
        const cornerFoss = { x: innerWidth / 2, y: triangleHeight };

        function ternToXY(bio, elec, foss) {
            const xPos = bio * cornerBio.x + elec * cornerElec.x + foss * cornerFoss.x;
            const yPos = bio * cornerBio.y + elec * cornerElec.y + foss * cornerFoss.y;
            return { x: xPos, y: yPos };
        }

        const svg = d3.select('#viz-container').append('svg')
            .attr('viewBox', `0 0 ${width} ${height}`)
            .style('width', '100%')
            .style('height', 'auto')
            .style('max-height', '75vh')
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        function drawTriangle() {
            // Grid lines (subtle)
            [0.2, 0.4, 0.6, 0.8].forEach(t => {
                let b1 = ternToXY(t, 1-t, 0), b2 = ternToXY(t, 0, 1-t);
                svg.append('line').attr('x1', b1.x).attr('y1', b1.y).attr('x2', b2.x).attr('y2', b2.y).attr('class', 'grid-line');
                let e1 = ternToXY(0, t, 1-t), e2 = ternToXY(1-t, t, 0);
                svg.append('line').attr('x1', e1.x).attr('y1', e1.y).attr('x2', e2.x).attr('y2', e2.y).attr('class', 'grid-line');
                let f1 = ternToXY(0, 1-t, t), f2 = ternToXY(1-t, 0, t);
                svg.append('line').attr('x1', f1.x).attr('y1', f1.y).attr('x2', f2.x).attr('y2', f2.y).attr('class', 'grid-line');
            });
            
            // Triangle Main Border
            svg.append('path')
                .attr('d', `M${cornerBio.x},${cornerBio.y} L${cornerElec.x},${cornerElec.y} L${cornerFoss.x},${cornerFoss.y} Z`)
                .attr('class', 'triangle-axis')
                .attr('fill', 'none');

            // Corner Labels (Dynamic IDs for updating)
            svg.append('text').attr('id', 'label-bio').attr('x', cornerBio.x - 15).attr('y', cornerBio.y - 15).attr('text-anchor', 'end').attr('class', 'axis-label').text('Bio and other');
            svg.append('text').attr('id', 'label-elec').attr('x', cornerElec.x + 15).attr('y', cornerElec.y - 15).attr('text-anchor', 'start').attr('class', 'axis-label').text('Electricity');
            svg.append('text').attr('id', 'label-foss').attr('x', cornerFoss.x).attr('y', cornerFoss.y + 35).attr('text-anchor', 'middle').attr('class', 'axis-label').text('Fossil Fuels');
        }

        function updateChart() {
            const currentData = [];
            selectedCountries.forEach(country => {
                const countryData = RAW_DATA[country];
                if (countryData) {
                    // Find latest year <= currentYear
                    const years = Object.keys(countryData).map(Number).sort((a,b)=>a-b);
                    let displayYear = null;
                    for (let y of years) {
                        if (y <= currentYear) displayYear = y;
                        else break;
                    }

                    if (displayYear !== null) {
                    const d = countryData[displayYear][energyMode];
                    if (d) {
                        // Map fields based on mode
                        let bio, elec, foss, absolute;
                        if (energyMode === 'power') {
                            bio = (d.other_pct || 0)/100; // Left Axis -> Other
                            elec = (d.wind_solar_pct || 0)/100; // Right Axis -> Wind & Solar
                            foss = (d.fossil_pct || 0)/100; // Bottom Axis -> Fossil
                            absolute = d.total;
                        } else {
                            bio = (d.bio_pct || 0)/100;
                            elec = (d.electrons_pct || 0)/100;
                            foss = (d.fossil_pct || 0)/100;
                            absolute = d.total;
                        }
                        
                        currentData.push({ 
                            country, 
                            year: displayYear, // Store actual year
                            bio: bio, 
                            elec: elec, 
                            foss: foss,
                            source: d.source,
                            absolute: absolute
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
                const years = Object.keys(RAW_DATA[country] || {}).map(y => parseInt(y)).sort((a,b)=>a-b);
                
                // Precompile points for smoothing if needed
                let rawPoints = [];
                years.forEach(y => {
                     const d = RAW_DATA[country][y][energyMode];
                     if(d) {
                         let bio, elec, foss;
                         if (energyMode === 'power') {
                             bio = d.other_pct/100;
                             elec = d.wind_solar_pct/100;
                             foss = d.fossil_pct/100;
                         } else {
                             bio = d.bio_pct/100;
                             elec = d.electrons_pct/100;
                             foss = d.fossil_pct/100;
                         }
                         rawPoints.push({ y, bio, elec, foss });
                     }
                });

                // Calculate path data
                rawPoints.forEach((pt, i) => {
                    const y = pt.y;
                    if (energyMode === 'power' && y < 1985) return;
                    if (y <= currentYear) {
                        let finalBio = pt.bio, finalElec = pt.elec, finalFoss = pt.foss;
                        
                        if (isSmoothed) {
                            // 5-year average (current year + 4 previous available years)
                            // Actually, let's just take the last 5 points including this one if they are consecutive-ish
                            // But simpler: just take average of up to 5 points ending at i
                            let start = Math.max(0, i - 4);
                            let subset = rawPoints.slice(start, i + 1);
                            
                            // Check if years are somewhat continuous (optional, but good for gaps)
                            // For simplicity, just average the components
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
                .on('mouseover', function(event, d) {
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
                        .style('left', (event.offsetX + 20) + 'px')
                        .style('top', (event.offsetY - 20) + 'px')
                        .html(`
                            <div class="tooltip-title">${d.country} (${d.year})</div>
                            <div class="tooltip-row"><span class="tooltip-label">${labels.elec}</span><span class="tooltip-value">${(d.elec*100).toFixed(1)}%</span></div>
                            <div class="tooltip-row"><span class="tooltip-label">${labels.foss}</span><span class="tooltip-value">${(d.foss*100).toFixed(1)}%</span></div>
                            <div class="tooltip-row"><span class="tooltip-label">${labels.bio}</span><span class="tooltip-value">${(d.bio*100).toFixed(1)}%</span></div>
                            <div class="tooltip-row" style="margin-top:8px; padding-top:8px; border-top:1px solid #f1f5f9;">
                                <span class="tooltip-label">${labels.total}</span><span class="tooltip-value">${d.absolute.toLocaleString()} ${energyMode === 'power' ? 'TWh' : 'Mtoe'}</span>
                            </div>
                            <div class="tooltip-source">Source: ${d.source}</div>
                        `);
                    d3.selectAll('.year-trail').classed('dimmed', true);
                    d3.select(this).attr('r', 8);
                })
                .on('mousemove', function(event) {
                    d3.select('#tooltip')
                        .style('left', (event.offsetX + 20) + 'px')
                        .style('top', (event.offsetY - 20) + 'px');
                })
                .on('mouseout', function() {
                    d3.select('#tooltip').style('opacity', 0);
                    d3.selectAll('.year-trail').classed('dimmed', false);
                    d3.select(this).attr('r', 6);
                });
                
            let sources = new Set(currentData.map(d => d.source));
            document.getElementById('data-source-label').innerText = "Source: " + Array.from(sources).join(' & ');
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
            document.getElementById('btn-power').classList.toggle('active', mode === 'power');
            
            // Update Axis Labels and Slider
            const slider = document.getElementById('year-slider');
            if (mode === 'power') {
                slider.min = 1985;
                if (currentYear < 1985) {
                     currentYear = 1985;
                     slider.value = 1985;
                     document.getElementById('year-display').innerText = 1985;
                }
                d3.select('#label-bio').text('Other (Hydro, Bio, Nuc)');
                d3.select('#label-elec').text('Wind & Solar');
                d3.select('#label-foss').text('Fossil Fuels');
            } else {
                slider.min = 1900;
                d3.select('#label-bio').text('Bio and other');
                d3.select('#label-elec').text('Electricity');
                d3.select('#label-foss').text('Fossil Fuels');
            }
            
            updateChart();
        }

        function renderList() {
            const container = document.getElementById('regions-list');
            container.innerHTML = '';
            Object.keys(COUNTRY_CONFIG).sort().forEach(country => {
                const item = document.createElement('div');
                item.className = 'region-item ' + (selectedCountries.has(country) ? 'active' : '');
                item.innerHTML = `
                    <div class="color-dot" style="background:${COUNTRY_CONFIG[country].color}"></div>
                    <span>${country}</span>
                `;
                item.onclick = () => {
                    if (selectedCountries.has(country)) selectedCountries.delete(country);
                    else selectedCountries.add(country);
                    renderList(); updateChart();
                };
                container.appendChild(item);
            });
        }
        
        function toggleAll() {
            if (selectedCountries.size === Object.keys(COUNTRY_CONFIG).length) selectedCountries.clear();
            else selectedCountries = new Set(Object.keys(COUNTRY_CONFIG));
            renderList(); updateChart();
        }

        const slider = document.getElementById('year-slider');
        const yearDisplay = document.getElementById('year-display');
        const playBtn = document.getElementById('play-pause-btn');

        function updateUI() {
            yearDisplay.innerText = currentYear;
            slider.value = currentYear;
            updateChart();
        }

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
        
        function setSpeed(speed) {
            playSpeed = speed;
            document.querySelectorAll('.speed-btn').forEach(btn => {
                btn.classList.toggle('active', parseFloat(btn.innerText) === speed);
            });
            if (isPlaying) { playBtn.click(); playBtn.click(); }
        }

        drawTriangle(); renderList(); updateUI();
    </script>
</body>
</html>"""

    # Prepare config for JS
    js_config = {k: {'color': v['color'], 'short': v['short']} for k, v in REGION_CONFIG.items()}
    
    print(f"Generated {len(results)} data records with Final and Useful energy.")
    print(f"Source breakdown: {dict(source_counts)}")

    # Inject data (combined_data is the new structure)
    # Convert defaultdict to regular dict for JSON serialization
    json_data = json.loads(json.dumps(combined_data))
    
    final_html = html_template.replace('%COUNTRIES%', json.dumps(js_config)).replace('%DATA%', json.dumps(json_data))
    
    with open(OUTPUT_HTML, 'w') as f:
        f.write(final_html)
    print(f"Saved exact replica visualization to {OUTPUT_HTML}")

if __name__ == '__main__':
    main()
