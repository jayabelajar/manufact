-- Overall KPI
SELECT
    SUM(planned_quantity) AS total_planned_production,
    SUM(produced_quantity) AS total_actual_production,
    SUM(produced_quantity) / NULLIF(SUM(planned_quantity), 0) * 100 AS production_achievement_pct,
    SUM(produced_quantity - planned_quantity) AS production_gap,
    SUM(good_production) AS total_good_production,
    SUM(defect_quantity) AS total_defect,
    SUM(defect_quantity) / NULLIF(SUM(produced_quantity), 0) * 100 AS defect_rate_pct,
    SUM(downtime_minutes) AS total_downtime,
    SUM(production_cost) AS total_production_cost,
    SUM(production_cost) / NULLIF(SUM(produced_quantity), 0) AS cost_per_unit
FROM production;

-- Total production per month
SELECT
    year_month,
    SUM(planned_quantity) AS planned_quantity,
    SUM(produced_quantity) AS produced_quantity,
    SUM(produced_quantity) / NULLIF(SUM(planned_quantity), 0) * 100 AS achievement_pct
FROM production
GROUP BY year_month
ORDER BY year_month;

-- Production by plant
SELECT
    plant,
    SUM(produced_quantity) AS produced_quantity,
    SUM(produced_quantity) / NULLIF(SUM(planned_quantity), 0) * 100 AS achievement_pct
FROM production
GROUP BY plant
ORDER BY produced_quantity DESC;

-- Production by product
SELECT
    product,
    SUM(produced_quantity) AS produced_quantity,
    SUM(good_production) AS good_production,
    SUM(defect_quantity) AS defect_quantity
FROM production
GROUP BY product
ORDER BY produced_quantity DESC;

-- Production by production line
SELECT
    product_line,
    SUM(planned_quantity) AS planned_quantity,
    SUM(produced_quantity) AS produced_quantity,
    SUM(produced_quantity) / NULLIF(SUM(planned_quantity), 0) * 100 AS achievement_pct
FROM production
GROUP BY product_line
ORDER BY achievement_pct DESC;

-- Defect rate by product line
SELECT
    product_line,
    SUM(defect_quantity) AS defect_quantity,
    SUM(defect_quantity) / NULLIF(SUM(produced_quantity), 0) * 100 AS defect_rate_pct
FROM production
GROUP BY product_line
ORDER BY defect_rate_pct DESC;

-- Machine downtime and performance
SELECT
    machine_id,
    SUM(downtime_minutes) AS downtime_minutes,
    SUM(produced_quantity) / NULLIF(SUM(planned_quantity), 0) * 100 AS achievement_pct,
    SUM(defect_quantity) / NULLIF(SUM(produced_quantity), 0) * 100 AS defect_rate_pct
FROM production
GROUP BY machine_id
ORDER BY downtime_minutes DESC;

-- Production cost analysis
SELECT
    product,
    plant,
    SUM(production_cost) AS production_cost,
    SUM(production_cost) / NULLIF(SUM(produced_quantity), 0) AS cost_per_unit,
    SUM(produced_quantity) AS produced_quantity
FROM production
GROUP BY product, plant
ORDER BY production_cost DESC;
