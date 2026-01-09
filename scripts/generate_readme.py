import csv
import os

def generate_readme():
    csv_path = 'companies.csv'
    readme_path = 'README.md'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    companies = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)

    # Sort companies by province then name
    companies.sort(key=lambda x: (x['province'], x['name']))

    markdown_content = """# Canada Tech 🇨🇦

A crowd-sourced repository of tech employers across Canada. Designed for both readability (README) and interactivity (Map).

## 🗺 Interactive Map
[**View the Interactive Map here**](https://trilemmafoundation.github.io/canada-tech/)

## 🏢 Company List

| Name | Industry | Location | Remote Policy | Description |
| --- | --- | --- | --- | --- |
"""

    for c in companies:
        location = f"{c['city']}, {c['province']}"
        markdown_content += f"| [{c['name']}]({c['url']}) | {c['industry']} | {location} | {c['remote_policy']} | {c['description']} |\n"

    markdown_content += """
## 📝 How to Contribute

### Prerequisites

1. Fork and clone this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Contribution Steps

1. **Add your company to `data/incoming.csv`** following the [CSV Specification](#csv-specification) below.
   - Do NOT edit `companies.csv` directly
   - The script will automatically generate `id`, `lat`, and `lng` fields for you

2. **Validate your entry** (optional but recommended):
   ```bash
   python scripts/add_companies.py --check
   ```
   This will validate your entry without making changes.

3. **Process your addition**:
   ```bash
   python scripts/add_companies.py
   ```
   This script automatically:
   - Generates a unique `id` slug from company name + city
   - Looks up geocoordinates (`lat`/`lng`) for the city
   - Normalizes URLs (adds `https://`, strips trailing slashes)
   - Validates all enum fields (industry, remote_policy, province)
   - Checks for duplicate entries

4. **Update the README**:
   ```bash
   python scripts/generate_readme.py
   ```

5. **Submit a Pull Request**

### CSV Specification

When adding companies to `data/incoming.csv`, use the following format:

| Column Header | Data Type | Required? | Validation / Format Rule |
| --- | --- | --- | --- |
| **name** | `string` | **Yes** | The official company name. |
| **url** | `url` | **Yes** | Company website URL (will be normalized to `https://` automatically). |
| **industry** | `enum` | **Yes** | One of: SaaS, Fintech, Healthtech, Ecommerce, Agency, Gaming, AI, Cleantech, Telecommunications. |
| **remote_policy** | `enum` | **Yes** | One of: Remote, Hybrid, Onsite. |
| **city** | `string` | **Yes** | The physical city name. |
| **province** | `enum` | **Yes** | 2-letter ISO code: AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, QC, SK, YT. |
| **description** | `string` | No | Brief company description (optional). |
| **tags** | `string` | No | Comma-separated tags (optional). |
| **hq_address** | `string` | No | Full headquarters address for more precise geocoding (optional). |

**Auto-generated fields** (do not include these in `incoming.csv`):
- **id**: Automatically generated as `slug(name)-slug(city)`
- **lat**: Automatically geocoded from city/province
- **lng**: Automatically geocoded from city/province
"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    # Sync CSV to docs folder for Github Pages map
    docs_csv_path = os.path.join('docs', 'companies.csv')
    try:
        import shutil
        shutil.copy2(csv_path, docs_csv_path)
        print(f"Synced {csv_path} to {docs_csv_path}")
        
        # Sync favicons from public to docs
        public_dir = 'public'
        docs_dir = 'docs'
        if os.path.exists(public_dir):
            for filename in os.listdir(public_dir):
                if filename.endswith(('.png', '.ico', '.svg', '.webmanifest', '.xml')):
                    src = os.path.join(public_dir, filename)
                    dst = os.path.join(docs_dir, filename)
                    shutil.copy2(src, dst)
                    print(f"Synced {filename} to {docs_dir}")
    except Exception as e:
        print(f"Error syncing files: {e}")

    print("README.md updated successfully!")

if __name__ == "__main__":
    generate_readme()
