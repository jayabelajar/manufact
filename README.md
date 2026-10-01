# Manufacturing Production Performance Dashboard

End-to-end data analytics project for monitoring production achievement, product quality, machine downtime, and production cost from Saudi manufacturing production orders for 2024-2026.

## Project Structure

```text
data/raw/manufacturing.csv
data/processed/manufacturing_clean.csv
notebooks/01_data_cleaning.ipynb
notebooks/02_eda.ipynb
sql/
dashboard/
images/
src/preprocess.py
```

## Dataset

Source file: `docs/manufacturing-production-ksa-2024-2026.csv`

The cleaned dataset standardizes column names, parses production dates, validates production values, removes duplicates, and adds derived metrics:

- `good_production`
- `production_achievement_pct`
- `defect_rate_pct`
- `production_gap`
- `cost_per_unit`
- calendar columns such as `year`, `quarter`, and `year_month`

## How to Run

```bash
pip install -r requirements.txt
python src/preprocess.py
```

Output:

- `data/processed/manufacturing_clean.csv`
- `data/processed/manufacturing_insights.md`

## PostgreSQL Workflow

Automatic import:

```bash
python src/import_to_postgres.py --host localhost --port 5432 --user postgres --password postgres
```

The importer creates the `manufacturing_production` database when possible, recreates the `production` table, imports `data/processed/manufacturing_clean.csv`, and runs SQL cleaning checks.

Manual import:

1. Run `sql/01_create_database.sql`.
2. Connect to `manufacturing_production`.
3. Run `sql/02_create_tables.sql`.
4. Run the `\copy` helper in `sql/05_import_clean_csv.sql`.
5. Run `sql/03_data_cleaning.sql`.
6. Use `sql/04_kpi_analysis.sql` for KPI and dashboard analysis queries.

## Power BI Workflow

Use `dashboard/dax_measures.md` for measures and `dashboard/powerbi_build_guide.md` for page layout.
Preview images are available in `images/`.

Recommended pages:

- Production Overview
- Quality Analysis
- Downtime & Performance
- Cost Analysis

## Key Deliverables

- Clean dataset
- Python data cleaning pipeline
- EDA notebooks
- PostgreSQL schema and SQL analysis
- Power BI DAX measures and build guide
- Dashboard preview screenshots
- Data-driven business insights
