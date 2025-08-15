"""
This script uses the 2023 CPS to compute the fraction of total
SS benefits that exceed a nominal cap.

Data are aged forward under and assumed benefit growth rate and
the fraction of benefits exceeding the cap is computed for each year
given the constant benefits growth rate assumption.
"""

# %%
import pandas as pd
import os

cur_dir = os.path.dirname(os.path.abspath(__file__))
# Read CPS data for 2023
# Download from: https://www.nber.org/research/data/current-population-survey-cps-supplements-annual-demographic-file
# Codebook: https://data.nber.org/cps_supp_1/raw/2023/march/asec2023_ddl_pub_full.pdf
cps_path = os.path.join(cur_dir, "..", "data", "asecpub23csv", "hhpub23.csv")
df = pd.read_csv(cps_path, dtype=str)

# cast HSSVAL as float
df["HSSVAL"] = df["HSSVAL"].astype(float)
# cast HSUP_WGT as float
df["HSUP_WGT"] = df["HSUP_WGT"].astype(float)

#%%
# Limit sample to just those receiving benefits
df = df[df["HSSVAL"] > 0]
df["married"] = df["HRHTYPE"].isin(["1", "2"])
married_df = df[df["married"] == True]
singles_df = df[df["married"] == False]

#%%
# Find fraction of SS benefits that accrue to households above a benefit cap
# CONSTANTS
BENEFIT_CAP_COUPLES = 100_000  # Nominal cap on benefits
BENEFIT_CAP_SINGLES = 67_000  # Nominal cap on benefits
BENEFIT_GROWTH_RATE = 0.04  # Assumed annual growth rate in nominal benefits
END_YEAR = 2100  # final year to grow out to

out_dict = {}
for y in range(2023, END_YEAR + 1):
    # inflation HSSVAL
    df.loc[:, "HSSVAL"] *= (1 + BENEFIT_GROWTH_RATE) ** (y - 2023)
    married_df.loc[:, "HSSVAL"] *= (1 + BENEFIT_GROWTH_RATE) ** (y - 2023)
    singles_df.loc[:, "HSSVAL"] *= (1 + BENEFIT_GROWTH_RATE) ** (y - 2023)

    total_benefits = (df.HSSVAL * df.HSUP_WGT).sum()
    total_couple_capped = (
        married_df[married_df["HSSVAL"] > BENEFIT_CAP_COUPLES].HSSVAL * married_df[married_df["HSSVAL"] > BENEFIT_CAP_COUPLES].HSUP_WGT).sum()

    total_singles_capped = (
        singles_df[singles_df["HSSVAL"] > BENEFIT_CAP_SINGLES].HSSVAL * singles_df[singles_df["HSSVAL"] > BENEFIT_CAP_SINGLES].HSUP_WGT).sum()

    fraction_capped = (total_couple_capped + total_singles_capped) / total_benefits

    out_dict[y] = fraction_capped

#%%
# turn to df
out_df = pd.DataFrame.from_dict(out_dict, orient="index", columns=["fraction_capped"])
out_df.index.name = "year"
out_df = out_df.reset_index()

# plot by year
import plotly.express as px

fig = px.line(out_df, x="year", y="fraction_capped", title="Fraction of SS Benefits Exceeding Cap")
fig.show()
