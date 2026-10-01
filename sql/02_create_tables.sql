DROP TABLE IF EXISTS production;

CREATE TABLE production (
    production_id BIGSERIAL PRIMARY KEY,
    work_order_id VARCHAR(32) UNIQUE NOT NULL,
    production_date DATE NOT NULL,
    year INTEGER,
    quarter VARCHAR(2),
    month INTEGER,
    month_name VARCHAR(3),
    year_month VARCHAR(7),
    plant VARCHAR(100),
    product_line VARCHAR(100),
    machine_id VARCHAR(32),
    product VARCHAR(100),
    operator VARCHAR(100),
    shift VARCHAR(32),
    order_status VARCHAR(32),
    planned_quantity NUMERIC(14, 2),
    produced_quantity NUMERIC(14, 2),
    defect_quantity NUMERIC(14, 2),
    good_production NUMERIC(14, 2),
    downtime_minutes NUMERIC(14, 2),
    production_cost NUMERIC(14, 2),
    production_achievement_pct NUMERIC(10, 4),
    defect_rate_pct NUMERIC(10, 4),
    production_gap NUMERIC(14, 2),
    cost_per_unit NUMERIC(14, 4),
    source_defect_rate_pct NUMERIC(10, 4)
);

CREATE INDEX idx_production_date ON production (production_date);
CREATE INDEX idx_production_plant ON production (plant);
CREATE INDEX idx_production_product_line ON production (product_line);
CREATE INDEX idx_production_machine ON production (machine_id);
CREATE INDEX idx_production_product ON production (product);
