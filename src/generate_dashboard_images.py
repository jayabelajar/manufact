from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "processed" / "inventara_clean.csv"
IMAGE_DIR = ROOT_DIR / "images"


WIDTH = 1400
HEIGHT = 900
BG = "#f6f8fb"
INK = "#172033"
MUTED = "#697386"
BLUE = "#2563eb"
GREEN = "#059669"
RED = "#dc2626"
AMBER = "#d97706"
CARD = "#ffffff"
BORDER = "#d8dee9"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_card(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str, value: str, color: str) -> None:
    draw.rounded_rectangle(xy, radius=8, fill=CARD, outline=BORDER, width=1)
    x1, y1, _, _ = xy
    draw.text((x1 + 24, y1 + 20), title, fill=MUTED, font=font(24))
    draw.text((x1 + 24, y1 + 58), value, fill=color, font=font(38, bold=True))


def draw_bar_chart(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    labels: list[str],
    values: list[float],
    color: str,
) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=8, fill=CARD, outline=BORDER, width=1)
    draw.text((x1 + 24, y1 + 18), title, fill=INK, font=font(27, bold=True))

    chart_x1 = x1 + 28
    chart_y1 = y1 + 76
    chart_x2 = x2 - 28
    chart_y2 = y2 - 48
    max_value = max(values) if values else 1
    gap = 14
    bar_width = max(24, int((chart_x2 - chart_x1 - gap * (len(values) - 1)) / max(len(values), 1)))

    for i, (label, value) in enumerate(zip(labels, values)):
        bx1 = chart_x1 + i * (bar_width + gap)
        bx2 = bx1 + bar_width
        bar_height = int((chart_y2 - chart_y1) * value / max_value) if max_value else 0
        by1 = chart_y2 - bar_height
        draw.rounded_rectangle((bx1, by1, bx2, chart_y2), radius=5, fill=color)
        short_label = label[:13] + ("." if len(label) > 13 else "")
        draw.text((bx1, chart_y2 + 10), short_label, fill=MUTED, font=font(16))


def fmt_number(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def base_page(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.text((46, 34), title, fill=INK, font=font(42, bold=True))
    draw.text((48, 84), "Inventara Production Performance Dashboard", fill=MUTED, font=font(22))
    return image, draw


def save_overview(df: pd.DataFrame) -> None:
    image, draw = base_page("Production Overview")
    planned = df["planned_quantity"].sum()
    produced = df["produced_quantity"].sum()
    achievement = produced / planned * 100
    gap = produced - planned

    draw_card(draw, (48, 140, 360, 260), "Planned", fmt_number(planned), BLUE)
    draw_card(draw, (388, 140, 700, 260), "Actual", fmt_number(produced), GREEN)
    draw_card(draw, (728, 140, 1040, 260), "Achievement", f"{achievement:.2f}%", BLUE)
    draw_card(draw, (1068, 140, 1380, 260), "Gap", fmt_number(gap), RED if gap < 0 else GREEN)

    plant = df.groupby("plant")["produced_quantity"].sum().sort_values(ascending=False).head(8)
    monthly = df.groupby("year_month")["produced_quantity"].sum().tail(12)
    draw_bar_chart(draw, (48, 300, 680, 820), "Production by Plant", plant.index.tolist(), plant.tolist(), BLUE)
    draw_bar_chart(draw, (720, 300, 1380, 820), "Production Trend", monthly.index.tolist(), monthly.tolist(), GREEN)
    image.save(IMAGE_DIR / "overview.png")


def save_quality(df: pd.DataFrame) -> None:
    image, draw = base_page("Quality Analysis")
    defects = df["defect_quantity"].sum()
    produced = df["produced_quantity"].sum()
    defect_rate = defects / produced * 100

    draw_card(draw, (48, 140, 360, 260), "Total Defect", fmt_number(defects), RED)
    draw_card(draw, (388, 140, 700, 260), "Defect Rate", f"{defect_rate:.2f}%", RED)
    draw_card(draw, (728, 140, 1040, 260), "Good Production", fmt_number(df["good_production"].sum()), GREEN)
    draw_card(draw, (1068, 140, 1380, 260), "Orders", fmt_number(len(df)), BLUE)

    product = df.groupby("product")["defect_quantity"].sum().sort_values(ascending=False).head(8)
    line = df.groupby("product_line")["defect_quantity"].sum().sort_values(ascending=False)
    draw_bar_chart(draw, (48, 300, 680, 820), "Defect by Product", product.index.tolist(), product.tolist(), RED)
    draw_bar_chart(draw, (720, 300, 1380, 820), "Defect by Line", line.index.tolist(), line.tolist(), AMBER)
    image.save(IMAGE_DIR / "quality.png")


def save_downtime(df: pd.DataFrame) -> None:
    image, draw = base_page("Downtime & Performance")
    planned = df["planned_quantity"].sum()
    produced = df["produced_quantity"].sum()

    draw_card(draw, (48, 140, 360, 260), "Downtime", fmt_number(df["downtime_minutes"].sum()), AMBER)
    draw_card(draw, (388, 140, 700, 260), "Achievement", f"{produced / planned * 100:.2f}%", BLUE)
    draw_card(draw, (728, 140, 1040, 260), "Machines", fmt_number(df["machine_id"].nunique()), GREEN)
    draw_card(draw, (1068, 140, 1380, 260), "Avg Downtime", f"{df['downtime_minutes'].mean():.1f}", AMBER)

    machine = df.groupby("machine_id")["downtime_minutes"].sum().sort_values(ascending=False).head(10)
    line = df.groupby("product_line")["downtime_minutes"].sum().sort_values(ascending=False)
    draw_bar_chart(draw, (48, 300, 680, 820), "Downtime by Machine", machine.index.tolist(), machine.tolist(), AMBER)
    draw_bar_chart(draw, (720, 300, 1380, 820), "Downtime by Line", line.index.tolist(), line.tolist(), BLUE)
    image.save(IMAGE_DIR / "downtime.png")


def save_cost(df: pd.DataFrame) -> None:
    image, draw = base_page("Cost Analysis")
    total_cost = df["production_cost"].sum()
    produced = df["produced_quantity"].sum()

    draw_card(draw, (48, 140, 360, 260), "Total Cost", f"SAR {fmt_number(total_cost)}", BLUE)
    draw_card(draw, (388, 140, 700, 260), "Cost / Unit", f"SAR {total_cost / produced:.2f}", AMBER)
    draw_card(draw, (728, 140, 1040, 260), "Actual Output", fmt_number(produced), GREEN)
    draw_card(draw, (1068, 140, 1380, 260), "Plants", fmt_number(df["plant"].nunique()), BLUE)

    product = df.groupby("product")["production_cost"].sum().sort_values(ascending=False).head(8)
    plant = df.groupby("plant")["production_cost"].sum().sort_values(ascending=False)
    draw_bar_chart(draw, (48, 300, 680, 820), "Cost by Product", product.index.tolist(), product.tolist(), BLUE)
    draw_bar_chart(draw, (720, 300, 1380, 820), "Cost by Plant", plant.index.tolist(), plant.tolist(), GREEN)
    image.save(IMAGE_DIR / "cost.png")


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    save_overview(df)
    save_quality(df)
    save_downtime(df)
    save_cost(df)
    print(f"Dashboard preview images saved to {IMAGE_DIR}")


if __name__ == "__main__":
    main()
