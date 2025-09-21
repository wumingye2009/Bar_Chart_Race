# src/app.py
import pathlib
import pandas as pd
import bar_chart_race as bcr
import matplotlib.pyplot as plt  # for customize()

# -------- Minimal config --------
YEAR_STEP   = 1                 # 1 = every year; 5 = every 5 years (+ latest)
COUNTRY_COL = "Name"            # your CSV: country name
YEAR_COL    = "year"            # your CSV: year
TOTAL_COL   = "co2"             # your CSV: total CO2 emissions
TITLE       = "Top 10 CO₂ Emissions by Country (Unit: MtCO₂)"
UNIT_TEXT   = "Unit: MtCO₂"     # bottom-right unit label

# -------- Paths (app.py in src/) --------
ROOT   = pathlib.Path(__file__).resolve().parent.parent
DATA   = ROOT / "data" / "co2_emissions.csv"
OUTDIR = ROOT / "images"
OUTDIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUTDIR / "CO2_Emissions_Top10.mp4"

def add_unit_label(fig, ax):
    # bottom-right corner in axes coordinates
    ax.text(1.0, -0.08, UNIT_TEXT, transform=ax.transAxes,
            ha="right", va="top", fontsize=10, color="gray")

def main():
    # 1) Load
    df = pd.read_csv(DATA)
    df.columns = [c.strip() for c in df.columns]

    # 2) Clean & types
    df = df.dropna(subset=[COUNTRY_COL, YEAR_COL, TOTAL_COL]).copy()
    df[YEAR_COL]  = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df[TOTAL_COL] = pd.to_numeric(df[TOTAL_COL], errors="coerce")
    df = df.dropna(subset=[YEAR_COL, TOTAL_COL])
    df = df[(df[YEAR_COL] > 0) & (df[TOTAL_COL] >= 0)]

    # 3) Aggregate & pivot → wide (rows=year, cols=country, values=co2)
    g = df.groupby([YEAR_COL, COUNTRY_COL], as_index=False)[TOTAL_COL].sum()
    wide = g.pivot(index=YEAR_COL, columns=COUNTRY_COL, values=TOTAL_COL).sort_index().fillna(0.0)

    # 4) Year index as int, downsample if needed
    wide.index = wide.index.round().astype(int)
    if YEAR_STEP > 1:
        y0, y1 = int(wide.index.min()), int(wide.index.max())
        years = [y for y in wide.index if (y - y0) % YEAR_STEP == 0]
        if y1 not in years:
            years.append(y1)
        wide = wide.loc[sorted(set(years))]

    # 5) Pretty label: "Year:YYYY"
    wide_pretty = wide.copy()
    wide_pretty.index = [f"Year:{y}" for y in wide.index]

    # 6) Render (no audio)
    bcr.bar_chart_race(
        df=wide_pretty,
        filename=str(OUTPUT),
        orientation="h",
        sort="desc",
        n_bars=10,
        steps_per_period=10,
        period_length=500,
        title=TITLE        
    )
    print(f"Video saved to: {OUTPUT}")

if __name__ == "__main__":
    main()
