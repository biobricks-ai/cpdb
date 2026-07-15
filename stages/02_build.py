#!/usr/bin/env python3
"""
Process CPDB data into parquet format.
Maps CAS numbers to SMILES via PubChem API.
"""

from pathlib import Path
import pandas as pd
import requests
import time
import json

# Literal placeholder tokens that encode a MISSING structure (not a real SMILES).
# These arise because unmapped CAS -> NaN -> astype(str) -> literal 'nan'.
# Normalized to NULL so validity is computed only over genuine structures.
# Exact-token match (after strip); never a substring -- real SMILES untouched.
_SMILES_MISSING = {'-', '--', '.', 'nan', 'no data', 'none', ''}

def null_smiles_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    """Replace exact missing-value placeholder tokens with None in SMILES columns."""
    for col in df.columns:
        if 'smiles' in col.lower():
            before = df[col].notna().sum()
            df[col] = df[col].map(
                lambda v: None if (v is None or str(v).strip().lower() in _SMILES_MISSING) else v
            )
            after = df[col].notna().sum()
            print(f"  Nulled {before - after} placeholder(s) in column {col}")
    return df

def cas_to_smiles_batch(cas_numbers: list, batch_size: int = 100) -> dict:
    """Convert CAS numbers to SMILES via PubChem API in batches."""
    cas_to_smiles = {}

    for i in range(0, len(cas_numbers), batch_size):
        batch = cas_numbers[i:i+batch_size]
        print(f"  Processing CAS batch {i//batch_size + 1}/{(len(cas_numbers)-1)//batch_size + 1}...")

        for cas in batch:
            if pd.isna(cas) or cas == '' or cas == 'na':
                continue

            try:
                # Try PubChem CAS lookup
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/property/CanonicalSMILES/JSON"
                resp = requests.get(url, timeout=10)

                if resp.status_code == 200:
                    data = resp.json()
                    props = data.get('PropertyTable', {}).get('Properties', [])
                    if props:
                        # PubChem returns ConnectivitySMILES for this endpoint
                        smiles = props[0].get('CanonicalSMILES') or props[0].get('ConnectivitySMILES', '')
                        if smiles:
                            cas_to_smiles[cas] = smiles

                time.sleep(0.2)  # Rate limit

            except Exception as e:
                pass  # Skip failed lookups

    return cas_to_smiles

def main():
    download_path = Path("download")
    brick_path = Path("brick")
    brick_path.mkdir(exist_ok=True)

    # Load chemical names with CAS numbers
    print("Loading chemical data...")
    chem_df = pd.read_excel(download_path / "cpdb.chemname.xls")
    print(f"  {len(chem_df)} chemicals")

    # Get unique CAS numbers
    cas_numbers = chem_df['cas'].dropna().unique().tolist()
    cas_numbers = [c for c in cas_numbers if c and c != 'na']
    print(f"  {len(cas_numbers)} unique CAS numbers")

    # Map CAS to SMILES
    print("Mapping CAS to SMILES via PubChem...")
    cas_smiles_file = download_path / "cas_smiles_cache.json"

    if cas_smiles_file.exists():
        with open(cas_smiles_file) as f:
            cas_to_smiles = json.load(f)
        print(f"  Loaded {len(cas_to_smiles)} cached mappings")
    else:
        cas_to_smiles = cas_to_smiles_batch(cas_numbers)
        with open(cas_smiles_file, 'w') as f:
            json.dump(cas_to_smiles, f)
        print(f"  Mapped {len(cas_to_smiles)} CAS to SMILES")

    # Add SMILES to chemical dataframe
    chem_df['smiles'] = chem_df['cas'].map(cas_to_smiles)

    # Load NCI/NTP bioassay data
    print("Loading NCI/NTP bioassay data...")
    ncintp_df = pd.read_excel(download_path / "cpdb.ncintp.xls")
    ncintp_df['source'] = 'NCI/NTP'
    print(f"  {len(ncintp_df)} NCI/NTP records")

    # Load literature bioassay data
    print("Loading literature bioassay data...")
    lit_df = pd.read_excel(download_path / "cpdb.lit.xls")
    lit_df['source'] = 'Literature'
    print(f"  {len(lit_df)} literature records")

    # Combine bioassay data
    common_cols = ['idnum', 'chemcode', 'species', 'strain', 'sex', 'route',
                   'tissue', 'tumor', 'opinion', 'td50', 'pval', 'source']
    ncintp_subset = ncintp_df[[c for c in common_cols if c in ncintp_df.columns]]
    lit_subset = lit_df[[c for c in common_cols if c in lit_df.columns]]
    bioassay_df = pd.concat([ncintp_subset, lit_subset], ignore_index=True)

    # Merge with chemical info
    print("Merging bioassay data with chemical info...")
    merged_df = bioassay_df.merge(
        chem_df[['chemcode', 'name', 'cas', 'smiles']],
        on='chemcode',
        how='left'
    )

    # Rename columns for clarity
    merged_df = merged_df.rename(columns={
        'name': 'chemical_name',
        'opinion': 'carcinogenicity_opinion'  # +/- for positive/negative
    })

    # Convert object columns to string for parquet compatibility
    for col in merged_df.select_dtypes(include=['object']).columns:
        merged_df[col] = merged_df[col].astype(str)
    merged_df = null_smiles_placeholders(merged_df)

    # Save chemicals table
    print("Saving chemicals table...")
    chem_out = chem_df.copy()
    for col in chem_out.select_dtypes(include=['object']).columns:
        chem_out[col] = chem_out[col].astype(str)
    chem_out = null_smiles_placeholders(chem_out)
    chem_out.to_parquet(brick_path / "chemicals.parquet", index=False)
    print(f"  Saved {len(chem_out)} chemicals")

    # Save bioassays table
    print("Saving bioassays table...")
    merged_df.to_parquet(brick_path / "bioassays.parquet", index=False)
    print(f"  Saved {len(merged_df)} bioassay records")

    # Summary stats
    with_smiles = chem_out['smiles'].notna().sum()
    print(f"\nSummary:")
    print(f"  Total chemicals: {len(chem_out)}")
    print(f"  Chemicals with SMILES: {with_smiles}")
    print(f"  Total bioassay records: {len(merged_df)}")

if __name__ == "__main__":
    main()
