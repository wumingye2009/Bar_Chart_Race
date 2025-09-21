# src/app.py
import pathlib
from typing import List, Optional
import pandas as pd
import bar_chart_race as bcr
import matplotlib.pyplot as plt  # used by the customize() callback

# =========================
# Config
# =========================
# interval between frames in years:
#   5 -> one frame every 5 years (+ latest year)
#   1 -> one frame every single year
INTERVAL_YEARS = 1

TITLE = "Top 10 CO₂ Emissions by Country "  # title of the chart
UNIT_TEXT = "Unit: MtCO₂"     # what to display at bottom-right
# YEAR_LABEL_MODE = "YearNoSpace"  # "YearNoSpace" -> "Year:2023"

# =========================
# Paths (app.py lives in src/)
# =========================
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = PROJECT_ROOT / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "co2_emissions.csv"
OUTPUT = IMAGES_DIR / "CO2_Emissions_Top10_NoBGM.mp4"

# =========================
# Column detection helpers
# =========================
COLUMN_GUESSES = {
    "description": ["Description", "description", "Type", "type", "Category", "category"],
    "country":     ["country","Country","entity","Entity","name","Name"],
    "year":        ["year","Year","YEAR"],
    "total_co2":   ["co2","CO2","total_co2","total_emissions","emissions","Total_CO2","Total Emissions"],
    "region":      ["region","Region","continent","Continent","country_group","group"],
}

def pick_first_col(df_: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df_.columns:
            return c
    return None


# =========================
# Main
# =========================
def main():
    # 1) Load
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]

    # 2) Detect key columns
    desc_col    = pick_first_col(df, COLUMN_GUESSES["description"])
    country_col = pick_first_col(df, COLUMN_GUESSES["country"])
    year_col    = pick_first_col(df, COLUMN_GUESSES["year"])
    tcandidates = [c for c in COLUMN_GUESSES["total_co2"] if c in df.columns]
    total_col   = tcandidates[0] if tcandidates else None

    if not (country_col and year_col and total_col):
        raise ValueError(
            f"Missing key columns. Detected -> country:{country_col}, year:{year_col}, total:{total_col}. "
            f"Please align COLUMN_GUESSES with your CSV headers."
        )

    # 3) Basic cleaning
    if desc_col is not None:
        df[desc_col] = (
            df[desc_col].astype(str)
                         .str.strip()
                         .str.replace(r"\s+", " ", regex=True)
        )

    df = df.drop_duplicates()
    df[year_col]  = pd.to_numeric(df[year_col], errors="coerce")
    df[total_col] = pd.to_numeric(df[total_col], errors="coerce")
    df = df.dropna(subset=[year_col, country_col, total_col])
    df = df[df[year_col] > 0]
    df = df[df[total_col] >= 0]

    # Keep only country-level rows if the dataset mixes levels
    if desc_col is not None:
        df = df[df[desc_col].str.lower().eq("country")]

    # 4) Aggregate and pivot: rows=year, cols=country, values=total CO2
    df_agg = df.groupby([year_col, country_col], as_index=False)[total_col].sum()
    wide = df_agg.pivot(index=year_col, columns=country_col, values=total_col).sort_index().fillna(0.0)

    # Ensure the index is integer years (avoid "2023.0")
    wide.index = pd.to_numeric(wide.index, errors="coerce").round().astype(int)

    # 5) Downsample years (every N years) + always include the latest year
    if INTERVAL_YEARS > 1:
        years = wide.index.to_series()
        min_y, max_y = int(years.min()), int(years.max())
        keep = [y for y in years if (y - min_y) % INTERVAL_YEARS == 0]
        if max_y not in keep:
            keep.append(max_y)
        keep = sorted(set(keep))
        wide = wide.loc[keep]

    # ---- 6) Render (force title to show on PyPI 0.1.0) ----
    # import matplotlib.pyplot as plt

    FIGSIZE = (9, 5)
    DPI = 150

    # 1) Figure + Axes
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("white")

    # 2) 先写“轴标题”（很多情况下这个最稳）
    # ax.set_title(
    #     TITLE,
    #     fontsize=12, fontweight='bold', color='black',
    #     pad=10, loc='center'  # pad=与图之间的距离
    # )

    # 3) 预留上边距，避免标题被挤掉；同时调左右边距让画面更居中
    fig.subplots_adjust(left=0.20, right=0.94, top=0.88, bottom=0.12)

    # 4) （可选兜底）再写一层“总标题”，万一轴标题被覆盖还有 suptitle
    #    你也可以把这一段注释掉，只保留 ax.set_title()
    fig.suptitle(TITLE, y=0.985, fontsize=14, fontweight='bold')

    # 5) 右下角单位（整张画布坐标）
    fig.text(0.985, 0.02, "Unit: MtCO₂",
            ha="right", va="bottom", fontsize=10, color="gray")

    # 6) 生成动画 —— 不再依赖函数的 title 参数
    bcr.bar_chart_race(
        df=wide,                      # 或 wide_5
        filename=str(OUTPUT),
        orientation="h",
        sort="desc",
        n_bars=10,
        steps_per_period=10,
        period_length=500,
        fig=fig,                      # 关键：用你这个带标题的 Figure
        period_label=True,            # 旧版只支持 True/False
        period_fmt="Year:{x:.0f}",
        tick_label_size=9,
        bar_size=0.92
    )

    print(f"Video saved to: {OUTPUT}")




if __name__ == "__main__":
    main()
