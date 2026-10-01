# Power BI Build Guide

Use `data/processed/manufacturing_clean.csv` or the PostgreSQL `production` table as the model source.

## Page 1: Production Overview

- KPI cards: Total Planned Production, Total Actual Production, Production Achievement %, Production Gap, Total Good Production.
- Line chart: Actual production by `year_month`.
- Clustered column chart: Planned vs Actual by `year_month`.
- Bar charts: Production by `plant`, `product_line`, and `product`.
- Slicers: `production_date`, `plant`, `product_line`, `product`.

## Page 2: Quality Analysis

- KPI cards: Total Defect, Defect Rate %, Total Good Production.
- Donut chart: Good vs Defect Production.
- Line chart: Defect Rate % by `year_month`.
- Bar charts: Defect by `product`, `product_line`, and `machine_id`.

## Page 3: Downtime & Performance

- KPI cards: Total Downtime, Production Achievement %, Production Gap.
- Line chart: Downtime by `year_month`.
- Bar charts: Downtime by `machine_id` and `product_line`.
- Scatter chart: Downtime Minutes vs Production Achievement % by `machine_id`.

## Page 4: Cost Analysis

- KPI cards: Total Production Cost, Cost per Unit, Total Actual Production.
- Line chart: Production Cost by `year_month`.
- Bar charts: Cost by `product` and `plant`.
- Scatter chart: Production Cost vs Produced Quantity by `product`.
