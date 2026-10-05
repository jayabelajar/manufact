from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT_DIR / "data" / "raw" / "manufacturing.csv"
PROCESSED_PATH = ROOT_DIR / "data" / "processed" / "inventara_clean.csv"
INSIGHTS_PATH = ROOT_DIR / "data" / "processed" / "inventara_insights.md"


COLUMN_MAP = {
    "work_order_id": "work_order_id",
    "plant_name": "plant",
    "product_line": "product_line",
    "product_name": "product",
    "machine_id": "machine_id",
    "shift": "shift",
    "planned_quantity": "planned_quantity",
    "produced_quantity": "produced_quantity",
    "defect_quantity": "defect_quantity",
    "defect_rate_pct": "source_defect_rate_pct",
    "downtime_minutes": "downtime_minutes",
    "production_cost_sar": "production_cost",
    "production_date": "production_date",
    "operator_name": "operator",
    "order_status": "order_status",
}


def clean_category(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .replace({"": pd.NA})
    )


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {path}")
    return pd.read_csv(path)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = sorted(set(COLUMN_MAP) - set(df.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    df = df.rename(columns=COLUMN_MAP)
    df = df[list(COLUMN_MAP.values())].copy()
    df = df.drop_duplicates()

    df["production_date"] = pd.to_datetime(
        df["production_date"], format="%d-%m-%Y", errors="coerce"
    )

    category_columns = [
        "work_order_id",
        "plant",
        "product_line",
        "product",
        "machine_id",
        "shift",
        "operator",
        "order_status",
    ]
    for column in category_columns:
        df[column] = clean_category(df[column])

    numeric_columns = [
        "planned_quantity",
        "produced_quantity",
        "defect_quantity",
        "source_defect_rate_pct",
        "downtime_minutes",
        "production_cost",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["production_date", "work_order_id"])

    for column in [
        "planned_quantity",
        "produced_quantity",
        "defect_quantity",
        "downtime_minutes",
        "production_cost",
    ]:
        df[column] = df[column].fillna(0).clip(lower=0)

    df["defect_quantity"] = np.minimum(df["defect_quantity"], df["produced_quantity"])
    df["good_production"] = df["produced_quantity"] - df["defect_quantity"]
    df["production_gap"] = df["produced_quantity"] - df["planned_quantity"]
    df["production_achievement_pct"] = np.where(
        df["planned_quantity"] > 0,
        df["produced_quantity"] / df["planned_quantity"] * 100,
        np.nan,
    )
    df["defect_rate_pct"] = np.where(
        df["produced_quantity"] > 0,
        df["defect_quantity"] / df["produced_quantity"] * 100,
        np.nan,
    )
    df["cost_per_unit"] = np.where(
        df["produced_quantity"] > 0,
        df["production_cost"] / df["produced_quantity"],
        np.nan,
    )

    df["year"] = df["production_date"].dt.year
    df["month"] = df["production_date"].dt.month
    df["month_name"] = df["production_date"].dt.strftime("%b")
    df["year_month"] = df["production_date"].dt.to_period("M").astype(str)
    df["quarter"] = "Q" + df["production_date"].dt.quarter.astype(str)

    ordered_columns = [
        "work_order_id",
        "production_date",
        "year",
        "quarter",
        "month",
        "month_name",
        "year_month",
        "plant",
        "product_line",
        "machine_id",
        "product",
        "operator",
        "shift",
        "order_status",
        "planned_quantity",
        "produced_quantity",
        "defect_quantity",
        "good_production",
        "downtime_minutes",
        "production_cost",
        "production_achievement_pct",
        "defect_rate_pct",
        "production_gap",
        "cost_per_unit",
        "source_defect_rate_pct",
    ]
    return df[ordered_columns].sort_values(["production_date", "work_order_id"])


def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    planned = df["planned_quantity"].sum()
    produced = df["produced_quantity"].sum()
    defects = df["defect_quantity"].sum()
    cost = df["production_cost"].sum()

    return {
        "total_orders": len(df),
        "total_planned_production": planned,
        "total_actual_production": produced,
        "production_achievement_pct": produced / planned * 100 if planned else np.nan,
        "production_gap": produced - planned,
        "total_good_production": df["good_production"].sum(),
        "total_defect": defects,
        "defect_rate_pct": defects / produced * 100 if produced else np.nan,
        "total_downtime_minutes": df["downtime_minutes"].sum(),
        "total_production_cost": cost,
        "cost_per_unit": cost / produced if produced else np.nan,
    }


def build_insights(df: pd.DataFrame) -> str:
    kpis = calculate_kpis(df)
    line_defect = (
        df.groupby("product_line", dropna=False)
        .agg(defect_quantity=("defect_quantity", "sum"), produced_quantity=("produced_quantity", "sum"))
        .assign(defect_rate_pct=lambda x: x["defect_quantity"] / x["produced_quantity"] * 100)
        .sort_values("defect_rate_pct", ascending=False)
    )
    machine_perf = (
        df.groupby("machine_id", dropna=False)
        .agg(
            downtime_minutes=("downtime_minutes", "sum"),
            planned_quantity=("planned_quantity", "sum"),
            produced_quantity=("produced_quantity", "sum"),
        )
        .assign(
            production_achievement_pct=lambda x: x["produced_quantity"]
            / x["planned_quantity"]
            * 100
        )
        .sort_values(["downtime_minutes", "production_achievement_pct"], ascending=[False, True])
    )
    cost_product = (
        df.groupby("product", dropna=False)
        .agg(production_cost=("production_cost", "sum"), produced_quantity=("produced_quantity", "sum"))
        .assign(cost_per_unit=lambda x: x["production_cost"] / x["produced_quantity"])
        .sort_values("cost_per_unit", ascending=False)
    )

    top_line = line_defect.iloc[0]
    top_machine = machine_perf.iloc[0]
    top_cost_product = cost_product.iloc[0]

    return f"""# Inventara Production Insights

## Executive KPI

- Total orders: {kpis["total_orders"]:,.0f}
- Planned production: {kpis["total_planned_production"]:,.0f}
- Actual production: {kpis["total_actual_production"]:,.0f}
- Production achievement: {kpis["production_achievement_pct"]:,.2f}%
- Production gap: {kpis["production_gap"]:,.0f}
- Good production: {kpis["total_good_production"]:,.0f}
- Defect rate: {kpis["defect_rate_pct"]:,.2f}%
- Downtime: {kpis["total_downtime_minutes"]:,.0f} minutes
- Production cost: SAR {kpis["total_production_cost"]:,.2f}
- Cost per unit: SAR {kpis["cost_per_unit"]:,.2f}

## Data-Driven Insights

- {line_defect.index[0]} has the highest defect rate at {top_line["defect_rate_pct"]:,.2f}%.
- {machine_perf.index[0]} records the highest downtime at {top_machine["downtime_minutes"]:,.0f} minutes with production achievement of {top_machine["production_achievement_pct"]:,.2f}%.
- {cost_product.index[0]} has the highest cost per unit at SAR {top_cost_product["cost_per_unit"]:,.2f}.
- Operational review should prioritize high-defect production lines, high-downtime machines, and products with above-average unit cost.
"""


def main() -> None:
    raw = load_raw()
    clean = clean_data(raw)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(PROCESSED_PATH, index=False)
    INSIGHTS_PATH.write_text(build_insights(clean), encoding="utf-8")

    print(f"Rows cleaned: {len(clean):,}")
    print(f"Clean dataset: {PROCESSED_PATH}")
    print(f"Insights: {INSIGHTS_PATH}")


if __name__ == "__main__":
    main()
