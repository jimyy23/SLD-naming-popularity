#!/usr/bin/env python3
"""
SLD Naming Popularity Analysis Script
Analyzes second-level and third-level domain strings from the Public Suffix List
"""
import urllib.request
from collections import defaultdict
import csv
import json

def fetch_psl():
    """Fetch the Public Suffix List from the URL using a proper User-Agent header.
    """
    url = "https://psl.hrsn.dev/public_suffix_list.min.dat"
    default_ua = (
        "sld-naming-popularity/1.0 "
    )
    headers = {"User-Agent": default_ua}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def extract_icann_domains(psl_content):
    """Extract only ICANN domains section from PSL"""
    lines = psl_content.split('\n')
    start_marker = "// ===BEGIN ICANN DOMAINS==="
    end_marker = "// ===END ICANN DOMAINS==="
    
    start_idx = None
    end_idx = None
    
    for idx, line in enumerate(lines):
        if start_marker in line:
            start_idx = idx + 1
        elif end_marker in line:
            end_idx = idx
            break
    
    if start_idx is None or end_idx is None:
        raise ValueError("Could not find ICANN domains section markers")
    
    return lines[start_idx:end_idx]

def parse_domains(lines, exclude_tlds={'it', 'jp', 'no'}):
    """
    Parse domain entries and extract SLD/3LD components
    
    Returns:
        tuple: (component_tlds, component_total_count, tld_components)
        - component_tlds: {component: {tld1, tld2, ...}} - tracks which TLDs use each component
        - component_total_count: {component: total_count} - counts every occurrence
        - tld_components: {tld: [component1, component2, ...]} - tracks which components each TLD uses
    """
    component_tlds = defaultdict(set)
    component_total_count = defaultdict(int)
    tld_components = defaultdict(list)
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('//'):
            continue
        
        # Remove wildcard and exception markers
        line = line.lstrip('*').lstrip('!')
        
        # Split into parts
        parts = line.split('.')
        
        # Filter out empty parts (from cases like *.sch.uk -> .sch.uk)
        parts = [p for p in parts if p]
        
        # Skip if it's just a TLD (1 part)
        if len(parts) < 2:
            continue
        
        # Get the TLD (rightmost part)
        tld = parts[-1]
        
        # Skip excluded TLDs
        if tld in exclude_tlds:
            continue
        
        # Extract all components except the TLD (rightmost)
        # We want 2nd level, 3rd level, etc.
        for component in parts[:-1]:
            # Skip empty components (shouldn't happen after filtering, but be safe)
            if not component:
                continue
            # Store which TLD uses this component (for unique TLD count)
            component_tlds[component].add(tld)
            # Count every occurrence (for total count)
            component_total_count[component] += 1
            # Track which components each TLD uses
            tld_components[tld].append(component)
    
    return component_tlds, component_total_count, tld_components

def calculate_frequencies(component_tlds, component_total_count):
    """
    Calculate two types of frequencies:
    1. Total frequency (count all occurrences)
    2. Unique TLD frequency (count once per TLD)
    
    Args:
        component_tlds: {component: {tld1, tld2, ...}}
        component_total_count: {component: total_count}
    
    Returns:
        tuple: (total_freq_dict, unique_tld_freq_dict)
    """
    total_freq = dict(component_total_count)
    unique_tld_freq = {component: len(tlds) for component, tlds in component_tlds.items()}
    
    return total_freq, unique_tld_freq

def write_csv(filename, data):
    """Write frequency data to CSV file"""
    # Sort by frequency (descending), then by string (ascending)
    sorted_data = sorted(data.items(), key=lambda x: (-x[1], x[0]))
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['string', 'frequency'])
        writer.writerows(sorted_data)
    
    print(f"Written {len(sorted_data)} entries to {filename}")


def write_json_string_to_tlds(filename, component_tlds, component_total_count):
    """
    Write JSON file: string -> count and list of TLDs using it
    Format: {
        "string1": {
            "count": 10,
            "tlds": ["tld1", "tld2", ...]
        },
        ...
    }
    Ordered by count (descending), then alphabetically
    """
    # Sort by count descending, then alphabetically
    sorted_components = sorted(
        component_tlds.keys(),
        key=lambda x: (-component_total_count[x], x)
    )
    
    # Use a list of tuples to maintain order, then convert to dict
    data = {}
    for component in sorted_components:
        data[component] = {
            "count": component_total_count[component],
            "tlds": sorted(list(component_tlds[component]))
        }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Written {len(data)} entries to {filename}")


def write_json_tld_to_strings(filename, tld_components, component_total_count):
    """
    Write JSON file: TLD -> list of strings ordered by count
    Format: {
        "tld1": ["string1", "string2", ...],
        ...
    }
    Strings are ordered by their total count (descending)
    """
    data = {}
    for tld in sorted(tld_components.keys()):
        # Get unique components for this TLD
        unique_components = list(set(tld_components[tld]))
        # Sort by count (descending), then alphabetically
        sorted_components = sorted(
            unique_components,
            key=lambda x: (-component_total_count[x], x)
        )
        data[tld] = sorted_components
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Written {len(data)} entries to {filename}")

def main():
    print("Fetching Public Suffix List...")
    psl_content = fetch_psl()
    
    print("Extracting ICANN domains section...")
    icann_lines = extract_icann_domains(psl_content)
    print(f"Found {len(icann_lines)} lines in ICANN section")
    
    print("Parsing domains (excluding .it, .jp, .no)...")
    component_tlds, component_total_count, tld_components = parse_domains(icann_lines)
    print(f"Found {len(component_tlds)} unique components")
    print(f"Found {len(tld_components)} unique TLDs")
    
    print("Calculating frequencies...")
    total_freq, unique_tld_freq = calculate_frequencies(component_tlds, component_total_count)
    
    # Output files
    print("\nWriting output files...")
    write_csv('sld_popularity_total.csv', total_freq)
    write_csv('sld_popularity_unique_tld.csv', unique_tld_freq)
    
    print("\nWriting JSON files...")
    write_json_string_to_tlds('sld_string_to_tlds.json', component_tlds, component_total_count)
    write_json_tld_to_strings('sld_tld_to_strings.json', tld_components, component_total_count)
    
    # Print top 10 most popular
    print("\nTop 10 most popular components (total):")
    sorted_total = sorted(total_freq.items(), key=lambda x: (-x[1], x[0]))
    for component, freq in sorted_total[:10]:
        print(f"  {component}: {freq}")
    
    print("\nTop 10 most popular components (unique TLD):")
    sorted_unique = sorted(unique_tld_freq.items(), key=lambda x: (-x[1], x[0]))
    for component, freq in sorted_unique[:10]:
        print(f"  {component}: {freq}")
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()