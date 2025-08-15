"""
This script uses the 2023 CPS to compute the fraction of total
SS benefits that exceed a nominal cap.

Data are aged forward under and assumed benefit growth rate and
the fraction of benefits exceeding the cap is computed for each year
given the constant benefits growth rate assumption.
"""

# %%
import pandas as pd
import numpy as np
import os
import cps_utils as cpsu


cur_dir = os.path.dirname(os.path.abspath(__file__))
# Read CPS data for 2023
# Download from: https://www.nber.org/research/data/current-population-survey-cps-supplements-annual-demographic-file
# Codebook: https://data.nber.org/cps_supp_1/raw/2023/march/asec2023_ddl_pub_full.pdf
cps_path = os.path.join(cur_dir, "..", "data", "asecpub23csv", "hhpub23.csv")
df = pd.read_csv(cps_path, dtype=str)
# keep just variables of interest
df = df[["HSSVAL", "HSUP_WGT", "HRHTYPE"]]

# cast HSSVAL as float
df["HSSVAL"] = df["HSSVAL"].astype(float)
# cast HSUP_WGT as float
df["HSUP_WGT"] = df["HSUP_WGT"].astype(float)

# %%
# Limit sample to just those receiving benefits
df = df[df["HSSVAL"] > 0]
# create indicator for married or single
df["married"] = df["HRHTYPE"].isin(["1", "2"])

cutoffs = cpsu.show_weighted_percentile_cutoffs(df)
df = cpsu.add_weighted_percentile_groups(df)


# %%
# Find fraction of SS benefits that accrue to households above a benefit cap
# CONSTANTS
BENEFIT_CAP_COUPLES = 100_000  # Nominal cap on benefits
BENEFIT_CAP_SINGLES = 67_000  # Nominal cap on benefits
BENEFIT_GROWTH_RATE = 0.04  # Assumed annual growth rate in nominal benefits
END_YEAR = 2100  # final year to grow out to

out_dict = {
    "year": [],
    "0-25": [],
    "25-50": [],
    "50-70": [],
    "70-80": [],
    "80-90": [],
    "90-99": [],
    "99-100": [],
}
for y in range(2023, END_YEAR + 1):
    # inflation HSSVAL
    df.loc[:, "HSSVAL"] *= (1 + BENEFIT_GROWTH_RATE) ** (y - 2023)

    df["capped"] = np.where(
        df["married"],
        np.maximum(df["HSSVAL"] - BENEFIT_CAP_COUPLES, 0),
        np.maximum(df["HSSVAL"] - BENEFIT_CAP_SINGLES, 0),
    )
    total_benefits = (df.HSSVAL * df.HSUP_WGT).sum()

    # group by percentile group and sum total HSSVAL and capped
    df_grouped = (
        df.groupby("pctile_group")[
            ["pctile_group", "HSSVAL", "HSUP_WGT", "capped"]
        ]
        .apply(
            lambda x: pd.Series(
                {
                    "total_SS": cpsu.weighted_sum(x["HSSVAL"], x["HSUP_WGT"]),
                    "capped_SS": cpsu.weighted_sum(x["capped"], x["HSUP_WGT"]),
                }
            )
        )
        .reset_index()
    )

    df_grouped["fraction_capped"] = (
        df_grouped["capped_SS"] / df_grouped["total_SS"]
    )

    out_dict["year"].append(y)
    for pct in df_grouped.pctile_group.unique():
        out_dict[pct].append(
            df_grouped[df_grouped.pctile_group == pct][
                "fraction_capped"
            ].values[0]
        )

# %%
# turn to df
out_df = pd.DataFrame.from_dict(out_dict)

# %%
# plot by year and percentile
import plotly.express as px

fig = px.line(
    out_df,
    x="year",
    y=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
    title="Fraction of SS Benefits Exceeding Cap by Percentile",
)
fig.show()

# %%
