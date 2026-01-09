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

1. Open `companies.csv`.
2. Add your company following the [CSV Specification](#csv-specification).
3. Run `python scripts/generate_readme.py` to update this list.
4. Submit a Pull Request.

### CSV Specification

| Column Header | Data Type | Required? | Validation / Format Rule |
| --- | --- | --- | --- |
| **id** | `string` | **Yes** | A unique slug. Format: `company-city`. |
| **name** | `string` | **Yes** | The official company name. |
| **url** | `url` | **Yes** | Must include `https://`. |
| **industry** | `enum` | **Yes** | SaaS, Fintech, Healthtech, Ecommerce, Agency, Gaming, AI, Cleantech. |
| **remote_policy** | `enum` | **Yes** | Remote, Hybrid, Onsite. |
| **city** | `string` | **Yes** | The physical city name. |
| **province** | `enum` | **Yes** | 2-letter ISO code (e.g., BC, ON, QC, AB). |
| **lat/lng** | `decimal` | **Yes** | Coordinates for map rendering. |
"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print("README.md updated successfully!")

if __name__ == "__main__":
    generate_readme()
