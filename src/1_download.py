import requests
from bs4 import BeautifulSoup
import shutil
import os

# Ensure the download directory exists
download_dir = 'download/processed'
os.makedirs(download_dir, exist_ok=True)

# Download the webpage content
response = requests.get("https://files.toxplanet.com/cpdb/CPDB-tab.html")
response.raise_for_status()  # Ensure the request was successful

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find all 'a' tags with href attributes ending in 'xls'
xls_links = soup.find_all('a', href=lambda href: href and href.endswith('.xls'))

# Download each file
base_url = "https://files.toxplanet.com/cpdb/"
for link in xls_links:
    file_url = base_url + link['href']
    file_name = file_url.split('/')[-1]
    file_path = os.path.join(download_dir, file_name)

    with requests.get(file_url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

print(f"Downloaded {len(xls_links)} files.")
