# cpdb

## 🔍 Overview
carcinogencity potency databse

## 📦 Data Source

- **TODO: data source**  
  URL: [https://example.com](https://example.com)
  <br>Citation: TODO
  <br>License: TODO


## 🔄 Transformations
None – raw data preserved.
TODO: update if processing applied.

## 📁 Assets

- `TODO.ext` (TODO): TODO


## 🧪 Usage
```bash
biobricks install cpdb

import biobricks as bb
import pandas as pd

paths = bb.assets("cpdb")

# Available assets:

df_1 = pd.read_parquet(paths.TODO_ext)


print(df_1.head())      # Preview the first asset

## Additional Information
# Carcinogencity Potency Database
This pulls all the workbooks from https://files.toxplanet.com/cpdb/CPDB-tab.html

