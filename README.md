# Canada Tech 🇨🇦

A crowd-sourced repository of tech employers across Canada. Designed for both readability (README) and interactivity (Map).

## 🗺 Interactive Map
[**View the Interactive Map here**](https://trilemmafoundation.github.io/canada-tech/)

## 🏢 Company List

| Name | Industry | Location | Remote Policy | Description |
| --- | --- | --- | --- | --- |
| [TELUS Corporation](https://www.telus.com) | Telecommunications | Vancouver, BC | Hybrid | Leading communications technology company providing 5G, fiber, and digital solutions in health and agriculture. |
| [Wealthsimple Inc.](https://www.wealthsimple.com/) | Fintech | Toronto, ON | Hybrid | The way money should be. |

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
