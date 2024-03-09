import pandas as pd
import os
import yaml

download_dir = 'download/processed'
output_dir = 'brick'
os.makedirs(output_dir, exist_ok=True)

for file_name in os.listdir(download_dir):
    if file_name.endswith('.xls'):
        xls_path = os.path.join(download_dir, file_name)
        parquet_path = os.path.join(output_dir, file_name.replace('.xls', '.parquet'))
        parquet_path = parquet_path.replace('cpdb.', '')

        # Read the Excel file
        df = pd.read_excel(xls_path)

        # Check each column's data types
        for col in df.columns:
            if df[col].apply(type).nunique() > 1:  # More than one data type in the column
                df[col] = df[col].astype(str)

        # Save as Parquet
        df.to_parquet(parquet_path)

print(f"Converted files to Parquet format.")

# read the dvc.yaml
dvc = {}
with open('dvc.yaml', 'r') as file:
    dvc = yaml.safe_load(file)

process_outs = dvc['stages']['process']['outs']
brick_files = [f'brick/{o}' for o in os.listdir(output_dir)]
intersect = set(process_outs).intersection(set(brick_files))

# check that the outs are right
assert len(intersect) == len(process_outs)
assert len(intersect) == len(brick_files)

