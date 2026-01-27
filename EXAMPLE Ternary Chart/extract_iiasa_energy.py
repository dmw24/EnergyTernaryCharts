#!/usr/bin/env python3
"""
Extract energy data from IIASA_dataset.csv for ternary chart visualization.

Extracts Final Energy data and calculates percentages for:
- Electrons: Electricity + Heat
- Fossil Molecules: Coal Products + Natural Gas + Petroleum Products
- Bio Molecules: Biomass
"""

import csv
import json

# Countries to include (must match IIASA dataset region names)
COUNTRIES = [
    'United States', 'China', 'Germany', 'Japan', 
    'India', 'Brazil', 'United Kingdom', 'France'
]

# Fuel classification
ELECTRONS = ['Electricity', 'Heat']
FOSSIL = ['Coal Products', 'Natural Gas', 'Petroleum Products']
BIO = ['Biomass']

# Years to include - comprehensive historical data
# 1900-1950: every 10 years
# 1950-2014: every 5 years for better granularity
YEARS_OF_INTEREST = (
    list(range(1900, 1950, 10)) + 
    list(range(1950, 2015, 5)) + 
    [2014]
)


def main():
    input_file = '/Users/daanwalter/Documents/EnergyPaths/IIASA_dataset.csv'
    output_file = '/Users/daanwalter/Documents/EnergyPaths/ternary_data.json'
    
    # Storage: country -> year -> fuel -> value
    energy_data = {}
    
    print("Reading IIASA_dataset.csv...")
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Filter for Final Energy, All Sectors
            if row['Type'] != 'Final Energy' or row['Sector'] != 'All Sectors':
                continue
            
            region = row['Region']
            fuel = row['Fuel']
            
            # Filter for our countries and fuels
            if region not in COUNTRIES:
                continue
            if fuel not in (ELECTRONS + FOSSIL + BIO):
                continue
            
            if region not in energy_data:
                energy_data[region] = {}
            
            # Extract year values
            for year in YEARS_OF_INTEREST:
                year_str = str(year)
                if year_str in row and row[year_str]:
                    try:
                        value = float(row[year_str])
                        if year not in energy_data[region]:
                            energy_data[region][year] = {}
                        if fuel not in energy_data[region][year]:
                            energy_data[region][year][fuel] = 0
                        energy_data[region][year][fuel] += value
                    except ValueError:
                        pass
    
    # Calculate percentages
    results = []
    
    for country in COUNTRIES:
        if country not in energy_data:
            print(f"Warning: No data for {country}")
            continue
        
        country_years = sorted(energy_data[country].keys())
        
        for year in country_years:
            year_data = energy_data[country][year]
            
            # Sum by category
            electrons = sum(year_data.get(f, 0) for f in ELECTRONS)
            fossil = sum(year_data.get(f, 0) for f in FOSSIL)
            bio = sum(year_data.get(f, 0) for f in BIO)
            
            total = electrons + fossil + bio
            
            if total > 0:
                results.append({
                    'country': country,
                    'year': year,
                    'electrons': round(electrons, 2),
                    'fossil': round(fossil, 2),
                    'bio': round(bio, 2),
                    'total': round(total, 2),
                    'electrons_pct': round(electrons / total * 100, 2),
                    'fossil_pct': round(fossil / total * 100, 2),
                    'bio_pct': round(bio / total * 100, 2)
                })
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved {len(results)} records to {output_file}")
    
    # Print summary
    for country in COUNTRIES:
        country_data = [r for r in results if r['country'] == country]
        if country_data:
            latest = country_data[-1]
            print(f"\n{country} ({latest['year']}):")
            print(f"  Electrons: {latest['electrons_pct']:.1f}%")
            print(f"  Fossil:    {latest['fossil_pct']:.1f}%")
            print(f"  Bio:       {latest['bio_pct']:.1f}%")


if __name__ == '__main__':
    main()
