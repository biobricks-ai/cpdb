#!/usr/bin/env python3
"""
Download Carcinogenic Potency Database (CPDB) from NLM FTP.
Source: https://ftp.nlm.nih.gov/projects/SISFTP/CPDB/Data%20Files/
"""

from pathlib import Path
import urllib.request
import ssl

def main():
    download_path = Path("download")
    download_path.mkdir(exist_ok=True)

    base_url = "https://ftp.nlm.nih.gov/projects/SISFTP/CPDB/Data%20Files/"

    files = [
        "CPDBChemical.xls",      # Chemical identifiers
        "cpdb.ncintp.xls",       # NCI/NTP bioassay data
        "cpdb.lit.xls",          # Literature data
        "cpdb.chemname.xls",     # Chemical names
    ]

    # Create SSL context
    ctx = ssl.create_default_context()

    for filename in files:
        url = base_url + filename
        output_file = download_path / filename

        if output_file.exists():
            print(f"Already exists: {filename}")
            continue

        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, output_file)
            print(f"  Saved: {output_file} ({output_file.stat().st_size:,} bytes)")
        except Exception as e:
            print(f"  Error downloading {filename}: {e}")
            raise

    print("Download complete")

if __name__ == "__main__":
    main()
