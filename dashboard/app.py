from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_PATH = ROOT_DIR / "data" / "processed" / "inventara_clean.csv"
RAW_PATH = ROOT_DIR / "data" / "raw" / "manufacturing.csv"
SRC_DIR = ROOT_DIR / "src"
REQUIRED_COLUMNS = {
    "work_order_id",
    "production_date",
    "year",
    "year_month",
    "plant",
    "product_line",
    "machine_id",
    "product",
    "planned_quantity",
    "produced_quantity",
    "defect_quantity",
    "good_production",
    "downtime_minutes",
    "production_cost",
    "production_achievement_pct",
    "defect_rate_pct",
}


st.set_page_config(
    page_title="Inventara Dashboard",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    if PROCESSED_PATH.exists():
        df = pd.read_csv(PROCESSED_PATH)
    else:
        sys.path.append(str(SRC_DIR))
        from preprocess import clean_data, load_raw

        df = clean_data(load_raw(RAW_PATH))

    df["production_date"] = pd.to_datetime(df["production_date"], errors="coerce")
    df["year_month"] = df["production_date"].dt.to_period("M").astype(str)
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing required columns: {missing}")
    return df.dropna(subset=["production_date"])


def format_number(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.0f}"


def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    planned = df["planned_quantity"].sum()
    produced = df["produced_quantity"].sum()
    defects = df["defect_quantity"].sum()
    cost = df["production_cost"].sum()

    return {
        "orders": len(df),
        "planned": planned,
        "produced": produced,
        "achievement": produced / planned * 100 if planned else 0,
        "gap": produced - planned,
        "good": df["good_production"].sum(),
        "defects": defects,
        "defect_rate": defects / produced * 100 if produced else 0,
        "downtime": df["downtime_minutes"].sum(),
        "cost": cost,
        "cost_per_unit": cost / produced if produced else 0,
    }


def filter_multiselect(label: str, values: pd.Series) -> list[str]:
    options = sorted(values.dropna().unique().tolist())
    return st.sidebar.multiselect(label, options=options, default=options)


def metric_row(kpis: dict[str, float]) -> None:
    first_row = st.columns(5)
    first_row[0].metric("Orders", format_number(kpis["orders"]))
    first_row[1].metric("Planned Production", format_number(kpis["planned"]))
    first_row[2].metric("Actual Production", format_number(kpis["produced"]))
    first_row[3].metric("Achievement", f"{kpis['achievement']:.2f}%")
    first_row[4].metric("Production Gap", format_number(kpis["gap"]))

    second_row = st.columns(5)
    second_row[0].metric("Good Production", format_number(kpis["good"]))
    second_row[1].metric("Defect Quantity", format_number(kpis["defects"]))
    second_row[2].metric("Defect Rate", f"{kpis['defect_rate']:.2f}%")
    second_row[3].metric("Downtime", f"{format_number(kpis['downtime'])} min")
    second_row[4].metric("Cost / Unit", f"SAR {kpis['cost_per_unit']:.2f}")


def bar_data(df: pd.DataFrame, group: str, value: str, top_n: int = 10) -> pd.DataFrame:
    return (
        df.groupby(group, dropna=False)[value]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .rename(value)
        .to_frame()
    )


def rate_by_group(
    df: pd.DataFrame,
    group: str,
    numerator: str,
    denominator: str,
    rate_name: str,
    top_n: int = 10,
) -> pd.DataFrame:
    grouped = df.groupby(group, dropna=False).agg(
        numerator=(numerator, "sum"),
        denominator=(denominator, "sum"),
    )
    grouped[rate_name] = grouped["numerator"].div(grouped["denominator"]).fillna(0) * 100
    return grouped[[rate_name]].sort_values(rate_name, ascending=False).head(top_n)


df = load_data()

st.title("Inventara Production Dashboard")
st.caption(
    "Interactive monitoring for production achievement, product quality, machine downtime, and production cost."
)

min_date = df["production_date"].min().date()
max_date = df["production_date"].max().date()

st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Production Date",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

years = st.sidebar.multiselect(
    "Year",
    options=sorted(df["year"].dropna().unique().tolist()),
    default=sorted(df["year"].dropna().unique().tolist()),
)
plants = filter_multiselect("Plant", df["plant"])
lines = filter_multiselect("Product Line", df["product_line"])
products = filter_multiselect("Product", df["product"])

filtered = df.copy()
if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[
        (filtered["production_date"] >= start_date)
        & (filtered["production_date"] <= end_date)
    ]

filtered = filtered[
    filtered["year"].isin(years)
    & filtered["plant"].isin(plants)
    & filtered["product_line"].isin(lines)
    & filtered["product"].isin(products)
]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

kpis = calculate_kpis(filtered)
metric_row(kpis)

overview_tab, quality_tab, downtime_tab, cost_tab, detail_tab = st.tabs(
    ["Overview", "Quality", "Downtime", "Cost", "Detail"]
)

with overview_tab:
    left, right = st.columns(2)
    monthly = (
        filtered.groupby("year_month")[["planned_quantity", "produced_quantity"]]
        .sum()
        .sort_index()
    )
    left.subheader("Planned vs Actual Production")
    left.line_chart(monthly)

    right.subheader("Production by Plant")
    right.bar_chart(bar_data(filtered, "plant", "produced_quantity"))

    st.subheader("Production by Product Line")
    st.bar_chart(bar_data(filtered, "product_line", "produced_quantity"))

    st.subheader("Top Products by Actual Production")
    st.dataframe(
        bar_data(filtered, "product", "produced_quantity")
        .rename(columns={"produced_quantity": "actual_production"})
        .reset_index(),
        use_container_width=True,
        hide_index=True,
    )

with quality_tab:
    left, right = st.columns(2)
    left.subheader("Defect Rate by Product Line")
    left.bar_chart(
        rate_by_group(
            filtered,
            "product_line",
            "defect_quantity",
            "produced_quantity",
            "defect_rate_pct",
        )
    )

    right.subheader("Defect Quantity by Product")
    right.bar_chart(bar_data(filtered, "product", "defect_quantity"))

    st.subheader("Good vs Defect Production")
    st.bar_chart(
        pd.DataFrame(
            {
                "quantity": {
                    "Good Production": kpis["good"],
                    "Defect Quantity": kpis["defects"],
                }
            }
        )
    )

with downtime_tab:
    left, right = st.columns(2)
    left.subheader("Downtime by Machine")
    left.bar_chart(bar_data(filtered, "machine_id", "downtime_minutes", top_n=12))

    right.subheader("Downtime by Product Line")
    right.bar_chart(bar_data(filtered, "product_line", "downtime_minutes"))

    st.subheader("Monthly Downtime")
    st.line_chart(
        filtered.groupby("year_month")["downtime_minutes"].sum().sort_index().to_frame()
    )

with cost_tab:
    left, right = st.columns(2)
    left.subheader("Production Cost by Product")
    left.bar_chart(bar_data(filtered, "product", "production_cost"))

    right.subheader("Cost per Unit by Product")
    cost_per_product = (
        filtered.groupby("product")
        .agg(production_cost=("production_cost", "sum"), produced_quantity=("produced_quantity", "sum"))
        .assign(cost_per_unit=lambda x: x["production_cost"].div(x["produced_quantity"]).fillna(0))
        [["cost_per_unit"]]
        .sort_values("cost_per_unit", ascending=False)
        .head(10)
    )
    right.bar_chart(cost_per_product)

    st.subheader("Monthly Production Cost")
    st.line_chart(
        filtered.groupby("year_month")["production_cost"].sum().sort_index().to_frame()
    )

with detail_tab:
    st.subheader("Filtered Records")
    display_columns = [
        "work_order_id",
        "production_date",
        "plant",
        "product_line",
        "machine_id",
        "product",
        "planned_quantity",
        "produced_quantity",
        "defect_quantity",
        "downtime_minutes",
        "production_cost",
        "production_achievement_pct",
        "defect_rate_pct",
    ]
    st.dataframe(
        filtered[display_columns].sort_values("production_date", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "production_date": st.column_config.DateColumn("production_date"),
            "production_cost": st.column_config.NumberColumn("production_cost", format="SAR %.2f"),
            "production_achievement_pct": st.column_config.NumberColumn(
                "production_achievement_pct", format="%.2f%%"
            ),
            "defect_rate_pct": st.column_config.NumberColumn("defect_rate_pct", format="%.2f%%"),
        },
    )
