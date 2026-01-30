
import json
import os

def merge_uk_and_global():
    root_dir = '/Users/daanwalter/Library/CloudStorage/OneDrive-SharedLibraries-Ember/ember-futures - Documents/03 Research/2026/97 Ideas/Ternary Chart Playground'
    global_data_path = os.path.join(root_dir, 'data.json')
    uk_hist_path = os.path.join(root_dir, 'UK version', 'uk_data.json')
    output_path = os.path.join(root_dir, 'UK version', 'uk_global_merged.json')

    # Load original global data
    with open(global_data_path, 'r') as f:
        global_data = json.load(f)

    # Load UK historical data (1700-2010)
    with open(uk_hist_path, 'r') as f:
        uk_hist_data = json.load(f).get("United Kingdom", {})

    merged_data = {}

    # 1. Process all countries/regions from global_data
    for entity_name, entity_data in global_data.items():
        if entity_name == "United Kingdom":
            # For UK, merge historical (up to 2010) and global (past 2010)
            uk_merged = {}
            
            # Add historical years
            for year, data in uk_hist_data.items():
                uk_merged[year] = data
            
            # Add global years > 2010
            global_years = sorted([int(y) for y in entity_data.keys()])
            for year in global_years:
                if year > 2010:
                    uk_merged[str(year)] = entity_data[str(year)]
            
            merged_data["United Kingdom"] = uk_merged
        else:
            # For other countries, just keep them as they are
            merged_data[entity_name] = entity_data

    # 2. Add some logic to ensure all countries start from 1900 in the UI? 
    # Actually the UI handles missing years fine.

    with open(output_path, 'w') as f:
        json.dump(merged_data, f, indent=4)

    print(f"Merged data saved to {output_path}")
    print(f"UK years range: 1700 to {max([int(y) for y in merged_data['United Kingdom'].keys()])}")
    print(f"Total entities: {len(merged_data)}")

if __name__ == "__main__":
    merge_uk_and_global()
