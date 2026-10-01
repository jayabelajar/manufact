# Dashboard Assets

This folder contains the Power BI implementation guide and reusable DAX measures.

Power BI `.pbix` files are binary artifacts created in Power BI Desktop. To build the dashboard:

1. Open Power BI Desktop.
2. Import `data/processed/manufacturing_clean.csv` or connect to the PostgreSQL `production` table.
3. Add the measures from `dax_measures.md`.
4. Build the four pages described in `powerbi_build_guide.md`.
5. Save the file as `dashboard/manufacturing_dashboard.pbix`.

Preview images for the intended dashboard pages are available in `images/`.
