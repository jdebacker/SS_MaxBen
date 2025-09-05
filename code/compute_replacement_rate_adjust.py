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
import json
import os
import cps_utils as cpsu


cur_dir = os.path.dirname(os.path.abspath(__file__))
# Read CPS data for 2023  #NOTE: Consider using HRS data in the future
# Download from: https://www.nber.org/research/data/current-population-survey-cps-supplements-annual-demographic-file
# Codebook: https://data.nber.org/cps_supp_1/raw/2023/march/asec2023_ddl_pub_full.pdf
cps_path = os.path.join(cur_dir, "..", "data", "asecpub23csv", "hhpub23.csv")
df = pd.read_csv(cps_path, dtype=str)
# Also read in person file to get age
p_cps_path = os.path.join(cur_dir, "..", "data", "asecpub23csv", "pppub23.csv")
p_df = pd.read_csv(p_cps_path, dtype=str)
# keep just variables of interest
df = df[["HSSVAL", "HSUP_WGT", "HRHTYPE", "H_SEQ"]]
p_df = p_df[["A_AGE", "PH_SEQ"]]
# in p_df, just keep oldest person in each household
p_df = p_df.loc[p_df.groupby("PH_SEQ")["A_AGE"].idxmax()]
# Merge person data with household data
df = df.merge(p_df, left_on="H_SEQ", right_on="PH_SEQ", how="left")

# cast HSSVAL as float
df["HSSVAL"] = df["HSSVAL"].astype(float)
# cast HSUP_WGT as float
df["HSUP_WGT"] = df["HSUP_WGT"].astype(float)

# %%
# Limit sample to just those receiving benefits
df = df[df["HSSVAL"] > 0]
# create indicator for married or single
df["married"] = df["HRHTYPE"].isin(["1", "2"])
# drop if missing age
df = df[df["A_AGE"].notna()]
# cast A_AGE as int
df["A_AGE"] = df["A_AGE"].astype(int)


cutoffs = cpsu.show_weighted_percentile_cutoffs(df)
df = cpsu.add_weighted_percentile_groups(df)

# %%
# Find fraction of SS benefits that accrue to households above a benefit cap
# CONSTANTS
BENEFIT_CAP_COUPLES = 100_000  # Nominal cap on benefits
BENEFIT_CAP_SINGLES = 50_000  # Nominal cap on benefits
INFLATION_RATE = 0.02  # Assumed inflation rate, affects benefit growth
WAGE_GROWTH_RATE = 0.04  # Assumed annual growth rate wages, applies to AIME and the benefit cap (after trigger)
# this growth rate should be come combination of inflation for COLA adjustments
# and real wage growth for new beneficiaries
END_YEAR = 2100  # final year to grow out to
PHASE_OUT_RATE = (
    0.02  # number of years to phase out replacement rate adjustment
)
PHASE_OUT_YEARS = 150
BENEFIT_TRIGGER_PCT = 0.25
MAX_AGE = 85  # in simulated panel, this is age at which SS benefits end
TRIGGER_YEAR = 2023

out_dict = {
    "year": [],
    "0-25": [],
    "25-50": [],
    "50-70": [],
    "70-80": [],
    "80-90": [],
    "90-99": [],
    "99-100": [],
    "total_capped_fraction": [],
}

# while loop to see when new benefits hit trigger
fraction_capped = 0.0
y = 2023
# Create df of new beneficiaries: proxy by aged 70 and under
df_new = df[df["A_AGE"].astype(int) <= 70].copy()
while fraction_capped < BENEFIT_TRIGGER_PCT:
    # HSSVAL for new beneficiaries grows at the wage rate
    df_new.loc[:, "HSSVAL"] *= 1 + WAGE_GROWTH_RATE
    df_new["capped"] = np.where(
        df_new["married"],
        np.maximum(df_new["HSSVAL"] - BENEFIT_CAP_COUPLES, 0),
        np.maximum(df_new["HSSVAL"] - BENEFIT_CAP_SINGLES, 0),
    )
    total_benefits = (df_new.HSSVAL * df_new.HSUP_WGT).sum()
    total_capped = (df_new["capped"] * df_new["HSUP_WGT"]).sum()
    fraction_capped = total_capped / total_benefits
    y += 1

trigger_year = TRIGGER_YEAR
print(f"{BENEFIT_TRIGGER_PCT * 100:.0f} pct trigger happens in {trigger_year}")

# Now loop back over all years, noting trigger year where cap will be indexed
# caps set to nominal values to start
cap_singles = BENEFIT_CAP_SINGLES
cap_couples = BENEFIT_CAP_COUPLES
# will be creating a panel from the CPS: aging folks through each year
# until they hit MAX_AGE
# Will keep track of this in 2 dataframes:
# 1) df_new: new cohort entering SS system each year
# 2) df_existing: existing cohort in SS system (derived from aging new cohort)
df_existing = df.copy()
# Create a new DF of new beneficiaries
df_new = df[df["A_AGE"].astype(int) <= 70].copy()
for y in range(2023, END_YEAR + 1):
    # Compute benefits and capped amount
    df_existing["capped"] = np.where(
        df_existing["married"],
        np.maximum(df_existing["HSSVAL"] - cap_couples, 0),
        np.maximum(df_existing["HSSVAL"] - cap_singles, 0),
    )
    total_uncapped_benefits = (df_existing.HSSVAL * df_existing.HSUP_WGT).sum()
    total_capped = (df_existing["capped"] * df_existing["HSUP_WGT"]).sum()

    # group by percentile group and sum total HSSVAL and capped
    df_grouped = (
        df_existing.groupby("pctile_group", observed=False)[
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
    out_dict["total_capped_fraction"].append(
        total_capped / total_uncapped_benefits
    )

    # Age existing beneficiaries
    df_existing["A_AGE"] += 1
    # drop if age > MAX_AGE
    df_existing = df_existing[df_existing["A_AGE"] <= MAX_AGE]

    # Assume new claimants' benefits grow at the wage rate
    df_new["HSSVAL"] *= 1 + WAGE_GROWTH_RATE
    # existing beneficiaries grow at the inflation rate
    df_existing["HSSVAL"] *= 1 + INFLATION_RATE
    # append the new claimants onto the existing dataframe
    df_existing = pd.concat([df_existing, df_new], ignore_index=True).copy()

    # after trigger year, grow cap at wage index
    if y > trigger_year:
        # cap_singles *= 1 + WAGE_GROWTH_RATE
        # cap_couples *= 1 + WAGE_GROWTH_RATE
        cap_singles *= 1 + INFLATION_RATE
        cap_couples *= 1 + INFLATION_RATE


# %%
# turn to df
out_df = pd.DataFrame.from_dict(out_dict)

# save to JSON for use in OG-USA calibration of replacement_rate_adjust
a = out_df[
    ["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"]
].values
# add to a: have values linearly go back down to zero over next PHASE_OUT years
# for i in range(1, PHASE_OUT + 1):
#     a = np.append(a, (a[-1, :] * (1 - i / PHASE_OUT)).reshape(1, 7), axis=0)
# Smooth phase out (not linear)
# for i in range(1, PHASE_OUT_YEARS + 1):
#     a = np.append(a, (a[-1, :] / (1 + PHASE_OUT_RATE)).reshape(1, 7), axis=0)

# append 3 columns with same values as last column
# this is because we are using OG-Core with J=10
a = np.append(a, np.tile(a[:, -1].reshape(a.shape[0], 1), (1, 3)), axis=1)
# appends one row of all 0 to make sure back to SS value
# a = np.append(a, np.zeros((1, 10)), axis=0)
a = 1 - a
a_dict = {"replacement_rate_adjust": a.tolist()}
# do one minus the fraction capped to get the replacement_rate_adjust parameter
# save to json
with open(
    f"maxben_replacement_rate_adjust_100k50k_trigger{TRIGGER_YEAR}.json",
    "w",
) as f:
    json.dump(a_dict, f)

# plot by year and percentile
import plotly.express as px

fig = px.line(
    out_df,
    x="year",
    y=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
    title="Fraction of SS Benefits Exceeding Cap by Percentile",
)
fig.show()

a_df = pd.DataFrame(
    np.array(a_dict["replacement_rate_adjust"])[:, :7],
    columns=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
)
# make index a year variable
a_df["year"] = np.arange(2023, a_df.shape[0] + 2023)
fig = px.line(
    a_df,
    x="year",
    y=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
    title="Ratio of Capped System Benefits to CL Benefits by Percentile",
)
fig.show()

# %%
# put a_dict in a dataframe with columns "percentile" and "replacement_rate_adjust"

# read in and plot replacement rates
# with open(
#     os.path.join(
#         cur_dir,
#         "maxben_replacement_rate_adjust_100k50k_25pct_100yrs.json",
#     ),
#     "r",
# ) as f:
#     a_dict = json.load(f)
# a_df = pd.DataFrame(
#     np.array(a_dict["replacement_rate_adjust"])[:, :7],
#     columns=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
# )
# # make index a year variable
# a_df["year"] = np.arange(2023, a_df.shape[0] + 2023)
# fig = px.line(
#     a_df,
#     x="year",
#     y=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
#     title="Fraction of SS Benefits Exceeding Cap by Percentile",
# )
# fig.show()

# %%
# import ogcore

# # Check that get the same from the replacement rates in the parameters object in the reform
# p = ogcore.utils.safe_read_pickle(
#     "/Users/jason.debacker/repos/SS_MaxBen/code/OUTPUT_SS_MAXBEN_50_smooth/p_with_maxben_replacement_rate_adjust_100k50k_25pct_100yrs.pkl"
# )
# a_df = pd.DataFrame(
#     np.array(p.replacement_rate_adjust[:, :7]),
#     columns=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
# )
# # make index a year variable
# a_df["year"] = np.arange(2023, a_df.shape[0] + 2023)
# fig = px.line(
#     a_df,
#     x="year",
#     y=["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"],
#     title="Fraction of SS Benefits Exceeding Cap by Percentile",
# )
# fig.show()


# %%
