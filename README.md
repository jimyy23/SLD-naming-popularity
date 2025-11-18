# SLD Naming Popularity Analysis

Analyzes second-level domain (SLD) and third-level domain naming patterns from the Public Suffix List to determine which component strings are most commonly used across different TLDs.

## Requirements

- Python 3.10+
- No external dependencies (uses only standard library)

## Usage

```bash
python3 main.py
```

## What It Does

1. Downloads the Public Suffix List from `https://psl.hrsn.dev/public_suffix_list.min.dat`
2. Extracts only ICANN domains (between `===BEGIN ICANN DOMAINS===` and `===END ICANN DOMAINS===`)
3. Excludes `.it`, `.jp`, and `.no` TLDs
4. Extracts component strings from 2nd and 3rd level domains (ignoring 1st level TLDs)
5. Calculates two types of frequency counts

## Examples

From entries like:
```
lib.nd.us
lib.ne.us
lib.nh.us
com.ac
org.ac
```

The script extracts components: `lib`, `com`, `org` (ignoring TLDs like `us`, `ac`)

## Output Files

### `sld_popularity_total.csv`
- **Total occurrences** of each component string
- Example: If "lib" appears in `lib.nd.us`, `lib.ne.us`, `lib.nh.us` → counted as 3

### `sld_popularity_unique_tld.csv`
- **Unique TLD count** for each component string
- Example: If "lib" appears in `lib.nd.us`, `lib.ne.us`, `lib.nh.us` → counted as 1 (all under `.us`)

Both CSV files contain:
- `string`: The component name
- `frequency`: Count (sorted descending by frequency, then alphabetically)

## Notes

- Handles internationalized domain names (IDNs) like `hobøl.no`
- Strips wildcard (`*`) and exception (`!`) markers
- Skips comments and empty lines