# Canada Tech 🇨🇦

A crowd-sourced repository of tech employers across Canada. Designed for both readability (README) and interactivity (Map).

## 🗺 Interactive Map
[**View the Interactive Map here**](https://trilemmafoundation.github.io/canada-tech/)

## 🏢 Company List

| Name | Industry | Location | Remote Policy | Description |
| --- | --- | --- | --- | --- |
| [TELUS Corporation](https://www.telus.com) | Telecommunications | Vancouver, BC | Hybrid | Leading communications technology company providing 5G, fiber, and digital solutions in health and agriculture. |
| [Wealthsimple Inc.](https://www.wealthsimple.com/) | Fintech | Toronto, ON | Hybrid | The way money should be. |

### 📝 How to Contribute

1. Open `companies.csv`.
2. Add your company following the [CSV Specification](#csv-specification).
3. Submit a Pull Request.

> **Note:** The `README.md` and Interactive Map are automatically updated via GitHub Actions whenever changes are pushed to `companies.csv`.

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
