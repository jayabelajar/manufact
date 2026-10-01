-- Run this after importing data/processed/manufacturing_clean.csv into production.

DELETE FROM production a
USING production b
WHERE a.production_id > b.production_id
  AND a.work_order_id = b.work_order_id;

UPDATE production
SET
    plant = NULLIF(BTRIM(plant), ''),
    product_line = NULLIF(BTRIM(product_line), ''),
    product = NULLIF(BTRIM(product), ''),
    machine_id = NULLIF(BTRIM(machine_id), ''),
    operator = NULLIF(BTRIM(operator), ''),
    shift = NULLIF(BTRIM(shift), ''),
    order_status = NULLIF(BTRIM(order_status), '');

UPDATE production
SET
    planned_quantity = GREATEST(COALESCE(planned_quantity, 0), 0),
    produced_quantity = GREATEST(COALESCE(produced_quantity, 0), 0),
    defect_quantity = GREATEST(COALESCE(defect_quantity, 0), 0),
    downtime_minutes = GREATEST(COALESCE(downtime_minutes, 0), 0),
    production_cost = GREATEST(COALESCE(production_cost, 0), 0);

UPDATE production
SET
    defect_quantity = LEAST(defect_quantity, produced_quantity),
    good_production = produced_quantity - LEAST(defect_quantity, produced_quantity),
    production_gap = produced_quantity - planned_quantity,
    production_achievement_pct = CASE
        WHEN planned_quantity > 0 THEN produced_quantity / planned_quantity * 100
    END,
    defect_rate_pct = CASE
        WHEN produced_quantity > 0 THEN LEAST(defect_quantity, produced_quantity) / produced_quantity * 100
    END,
    cost_per_unit = CASE
        WHEN produced_quantity > 0 THEN production_cost / produced_quantity
    END;
