
import pandas as pd
import json
import os

def process_uk_data():
    file_path = '/Users/daanwalter/Library/CloudStorage/OneDrive-SharedLibraries-Ember/ember-futures - Documents/03 Research/2026/97 Ideas/Ternary Chart Playground/data/UK data Final Energy Consumption.xlsx'
    
    # Read the data starting from the row with headers
    df = pd.read_excel(file_path, header=3)
    
    # Drop rows where year is NaN (if any header noise is left)
    df = df.dropna(subset=['Unnamed: 0'])
    
    # Rename columns for clarity
    # ['Unnamed: 0', 'TOTAL', 'Electricity', 'Gas (Natural and Town)', 'Petroleum ', 'Coal', 'Woodfuel', 'Fodder/Provender', 'Wind Power']
    df = df.rename(columns={
        'Unnamed: 0': 'year',
        'TOTAL': 'total',
        'Electricity': 'electricity',
        'Gas (Natural and Town)': 'gas',
        'Petroleum ': 'oil',
        'Coal': 'coal',
        'Woodfuel': 'wood',
        'Fodder/Provender': 'fodder',
        'Wind Power': 'wind'
    })
    
    # Ensure numeric types
    for col in ['year', 'total', 'electricity', 'gas', 'oil', 'coal', 'wood', 'fodder', 'wind']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['year'] = df['year'].astype(int)
    
    uk_json_data = {}
    
    for _, row in df.iterrows():
        year = int(row['year'])
        total = row['total']
        
        if total == 0: continue
        
        # Mapping to the tool's categories:
        # Electrons: electricity, wind
        # Fossil: gas, oil, coal
        # Bio & other: wood, fodder
        
        electrons = row['electricity'] + row['wind']
        fossil = row['gas'] + row['oil'] + row['coal']
        bio_other = row['wood'] + row['fodder']
        
        # Recalculate total from these components to ensure percentages sum to 100
        sum_components = electrons + fossil + bio_other
        
        uk_json_data[str(year)] = {
            "final": {
                "electrons_pct": (electrons / sum_components * 100) if sum_components > 0 else 0,
                "fossil_pct": (fossil / sum_components * 100) if sum_components > 0 else 0,
                "bio_pct": (bio_other / sum_components * 100) if sum_components > 0 else 0,
                "total": total,
                "source": "Fouquet (2008) with Updates"
            }
        }
    
    # Wrap in the expected top-level structure
    final_data = {"United Kingdom": uk_json_data}
    
    output_path = '/Users/daanwalter/Library/CloudStorage/OneDrive-SharedLibraries-Ember/ember-futures - Documents/03 Research/2026/97 Ideas/Ternary Chart Playground/UK version/uk_data.json'
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=4)
    
    print(f"Processed {len(uk_json_data)} years of UK data. Output saved to {output_path}")

if __name__ == "__main__":
    process_uk_data()
