# Power BI DAX Measures

```DAX
Total Planned Production = SUM(production[planned_quantity])

Total Actual Production = SUM(production[produced_quantity])

Production Achievement % =
DIVIDE([Total Actual Production], [Total Planned Production])

Production Gap =
[Total Actual Production] - [Total Planned Production]

Total Good Production = SUM(production[good_production])

Total Defect = SUM(production[defect_quantity])

Defect Rate % =
DIVIDE([Total Defect], [Total Actual Production])

Total Downtime = SUM(production[downtime_minutes])

Total Production Cost = SUM(production[production_cost])

Cost per Unit =
DIVIDE([Total Production Cost], [Total Actual Production])

Average Achievement % =
AVERAGE(production[production_achievement_pct]) / 100

Average Defect Rate % =
AVERAGE(production[defect_rate_pct]) / 100
```

Recommended formatting:

- Percentage measures: format as Percentage with 2 decimals.
- Cost measures: format as SAR currency.
- Quantity measures: whole number with thousands separator.
