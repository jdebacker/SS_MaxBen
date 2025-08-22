""" "
This script reads in output from OG simulations (and CBO forecasts)
and creates output for CRFB as well as some plots to inspect the
OG-USA output.

CRFB wants:
* Time series (could be dollars of ratio to GDP):
    * 75 years: 2026-2100
    * trust fund revenues, trust fund outlays, solvency parameters??
    * Pct changes in GDP, K, L

* Distributional analysis
    * SS benefits, income, consumption, iit paid, payroll taxes paid
    * units: pct of benefits? pct changes
    * split by: age, year, J, decile of current income, decile of lifetime earnings

"""

# %%
# imports
import os
import pandas as pd
import numpy as np
import plotly.express as px
import ogcore
from ogcore.utils import safe_read_pickle
from ogusa.utils import read_cbo_forecast

# set current directory
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
# set directory to save tables to
SAVE_DIR = os.path.join(CUR_DIR, "..", "CRFB_outputs")
# make directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)
# set plotly theme to white
px.defaults.template = "plotly_white"

# Constants used below
CRFB_END_YEAR = 2100
OASDI_RATIO = 12.4 / 16.2  # This is OASDI taxes to total payroll taxes


# Read in data
# base_params = safe_read_pickle(
#     os.path.join(CUR_DIR, "OUTPUT_BASELINE", "model_params.pkl")
# )
base_params = ogcore.parameters.Specifications()
base_params.start_year = 2026
base_tpi = safe_read_pickle(
    os.path.join(CUR_DIR, "OUTPUT_BASELINE_POSTOBBBA", "TPI", "TPI_vars.pkl")
)
reform_tpi = safe_read_pickle(
    os.path.join(CUR_DIR, "OUTPUT_SS_MAXBEN_50_smooth", "TPI", "TPI_vars.pkl")
)

# %%
# CBO baseline LT forecast
df_cbo_fiscal = pd.read_excel(
    os.path.join(CUR_DIR, "..", "data", "CBO_projections.xlsx")
)
df_cbo_fiscal = df_cbo_fiscal.fillna(0).astype(float)
# divide all values (except year) by 100 to put in fractions
df_cbo_fiscal.iloc[:, 1:] = df_cbo_fiscal.iloc[:, 1:] / 100

# %%
# put macro time series into a dataframe
macro_dict = {
    "Year": np.arange(
        base_params.start_year, base_params.start_year + len(base_tpi["Y"])
    ),
    "GDP": (reform_tpi["Y"] - base_tpi["Y"]) / base_tpi["Y"],
    "Capital Stock": (reform_tpi["K"] - base_tpi["K"]) / base_tpi["K"],
    "Labor Supply": (reform_tpi["L"] - base_tpi["L"]) / base_tpi["L"],
    "Consumption": (reform_tpi["C"] - base_tpi["C"]) / base_tpi["C"],
}
macro_df = pd.DataFrame(macro_dict)


# Put fiscal variables into dataframes
def convert_fiscal(tpi):
    TF_revenue = tpi["payroll_tax_revenue"] * OASDI_RATIO
    TF_outlays = tpi["agg_pension_outlays"]
    total_spending = (
        tpi["G"]
        + tpi["I_g"]
        + tpi["agg_pension_outlays"]
        + tpi["debt_service"]
        + tpi["TR"]
    )
    fiscal_dict = {
        "Year": np.arange(
            base_params.start_year, base_params.start_year + len(tpi["Y"])
        ),
        "SSTF_Revenues": TF_revenue / tpi["Y"],
        "SSTF_Outlays": TF_outlays / tpi["Y"],
        "D/Y": tpi["D"] / tpi["Y"],
        "Rev/Y": tpi["total_tax_revenue"] / tpi["Y"],
        "PayrollTax/Y": tpi["payroll_tax_revenue"] / tpi["Y"],
        "IIT/Y": tpi["iit_revenue"] / tpi["Y"],
        "rD/Y": tpi["debt_service"] / tpi["Y"],
        "TotalSpend/Y": total_spending / tpi["Y"],
    }
    return pd.DataFrame(fiscal_dict)


base_fiscal_df = convert_fiscal(base_tpi)
reform_fiscal_df = convert_fiscal(reform_tpi)

# Save to CSV for CRFB
base_fiscal_df[base_fiscal_df["Year"] <= CRFB_END_YEAR].to_csv(
    os.path.join(SAVE_DIR, "base_fiscal_df.csv"), index=False
)
reform_fiscal_df[reform_fiscal_df["Year"] <= CRFB_END_YEAR].to_csv(
    os.path.join(SAVE_DIR, "reform_fiscal_df.csv"), index=False
)
macro_df[macro_df["Year"] <= CRFB_END_YEAR].to_csv(
    os.path.join(SAVE_DIR, "macro_pct_changes.csv"), index=False
)

# %%
# Create plots for our inspection
# put cbo and baseline together in df
df = pd.merge(
    base_fiscal_df, df_cbo_fiscal, on="Year", suffixes=("_base", "_cbo")
)
# Keep just to end of CBO forecast
df = df[(df["Year"] >= 2026) & (df["Year"] <= 2098)]
fig = px.line(
    df,
    x="Year",
    y=[
        "SSTF_Revenues_base",
        "SSTF_Outlays_base",
        "SSTF_Revenues_cbo",
        "SSTF_Outlays_cbo",
    ],
)
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set color based on "Revenues" or "Outlays"
    if "Revenues" in trace_name:
        color = "blue"
    elif "Outlays" in trace_name:
        color = "red"
    # Set line style based on suffix
    if trace_name.endswith("_base"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_base", " (Base)")
        .replace("_cbo", " (CBO)")
        .replace("SSTF_", "SSTF ")
    )
)
# Add title
fig.update_layout(title_text="Social Security Trust Fund Revenues and Outlays")
fig.show()

# %%
fig = px.line(
    df,
    x="Year",
    y=["PayrollTax/Y_base", "IIT/Y_base", "PayrollTax/Y_cbo", "IIT/Y_cbo"],
)
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set color based on "Revenues" or "Outlays"
    if "IIT" in trace_name:
        color = "blue"
    elif "Payroll" in trace_name:
        color = "red"
    # Set line style based on suffix
    if trace_name.endswith("_base"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_base", " (Base)")
        .replace("_cbo", " (CBO)")
        .replace("_", " ")
    )
)
# Add title
fig.update_layout(title_text="Tax Revenues: IIT and Payroll")
fig.show()

# %%
# Plot D/Y from CBO and baseline
fig = px.line(df, x="Year", y=["D/Y_base", "D/Y_cbo"])
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set color based on "Revenues" or "Outlays"
    if "D/Y" in trace_name:
        color = "blue"
    # Set line style based on suffix
    if trace_name.endswith("_base"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_base", " (Base)")
        .replace("_cbo", " (CBO)")
        .replace("_", " ")
    )
)
# Add title
fig.update_layout(title_text="Debt-to-GDP Ratio: CBO vs Baseline")
fig.show()

# %%
# Plot total Rev/Y and TotalSpend/Y
fig = px.line(
    df,
    x="Year",
    y=["Rev/Y_base", "TotalSpend/Y_base", "Rev/Y_cbo", "TotalSpend/Y_cbo"],
)
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set color based on "Revenues" or "Outlays"
    if "Rev" in trace_name:
        color = "blue"
    elif "TotalSpend" in trace_name:
        color = "red"
    # Set line style based on suffix
    if trace_name.endswith("_base"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_base", " (Base)")
        .replace("_cbo", " (CBO)")
        .replace("_", " ")
    )
)
# Add title
fig.update_layout(title_text="Total Revenue and Spending: CBO vs Baseline")
fig.show()


# %%
# Plot deficits to GDP (TotalSpend/Y - Rev/Y) for CBO and model baseline
df["Deficit/Y_base"] = df["TotalSpend/Y_base"] - df["Rev/Y_base"]
df["Deficit/Y_cbo"] = df["TotalSpend/Y_cbo"] - df["Rev/Y_cbo"]
fig = px.line(
    df,
    x="Year",
    y=["Deficit/Y_base", "Deficit/Y_cbo"],
)
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set line style based on suffix
    if trace_name.endswith("_base"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_base", " (Base)")
        .replace("_cbo", " (CBO)")
        .replace("_", " ")
    )
)
# Add title
fig.update_layout(title_text="Deficits to GDP: CBO vs Baseline")
fig.show()

# %%
# plot rD/Y
fig = px.line(
    df,
    x="Year",
    y=["rD/Y_base", "rD/Y_cbo"],
)
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set color based on "Revenues" or "Outlays"
    if "rD/Y" in trace_name:
        color = "blue"
    # Set line style based on suffix
    if trace_name.endswith("_base"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_base", " (Base)")
        .replace("_cbo", " (CBO)")
        .replace("_", " ")
    )
)
# Add title
fig.update_layout(title_text="rD/Y: CBO vs Baseline")
fig.show()
# %%
# plot pct changes in macros
fig = px.line(
    macro_df[macro_df["Year"] <= CRFB_END_YEAR],
    x="Year",
    y=["GDP", "Capital Stock", "Labor Supply", "Consumption"],
)
fig.update_layout(title_text="Percent Changes in Macroeconomic Variables")
fig.show()

# %%
for cols in reform_fiscal_df.columns:
    if cols != "Year":
        reform_fiscal_df.rename(columns={cols: f"{cols}_reform"}, inplace=True)
df = pd.merge(df, reform_fiscal_df, on="Year")
df = df[(df["Year"] >= 2026) & (df["Year"] <= 2098)]
fig = px.line(
    df,
    x="Year",
    y=[
        "SSTF_Revenues_base",
        "SSTF_Outlays_base",
        "SSTF_Revenues_cbo",
        "SSTF_Outlays_cbo",
        "SSTF_Revenues_reform",
        "SSTF_Outlays_reform",
    ],
)
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set color based on "Revenues" or "Outlays"
    if "Revenues" in trace_name:
        color = "blue"
    elif "Outlays" in trace_name:
        color = "red"
    # Set line style based on suffix
    if trace_name.endswith("_base"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    elif trace_name.endswith("_reform"):
        line_dash = "dot"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_base", " (Base)")
        .replace("_cbo", " (CBO)")
        .replace("SSTF_", "SSTF ")
    )
)
# Add title
fig.update_layout(title_text="Social Security Trust Fund Revenues and Outlays")
fig.show()

# %%
# Create fiscal_reform_df_new
# This makes sure we match the CBO forecast exactly with the baseline
# The reform series is then then the CBO forecast plus the difference
# before the model reform and baseline
df["SSTF_Revenues_norm"] = df["SSTF_Revenues_cbo"] - (
    df["SSTF_Revenues_base"] - df["SSTF_Revenues_reform"]
)

df["SSTF_Outlays_norm"] = df["SSTF_Outlays_cbo"] - (
    df["SSTF_Outlays_base"] - df["SSTF_Outlays_reform"]
)

# Keep just year and columns with SSTF prefix
df = df[
    [
        col
        for col in df.columns
        if col.startswith("Year") or col.startswith("SSTF")
    ]
]
# plot cbo and model output
fig = px.line(
    df,
    x="Year",
    y=[
        "SSTF_Revenues_norm",
        "SSTF_Outlays_norm",
        "SSTF_Revenues_cbo",
        "SSTF_Outlays_cbo",
    ],
)
# Update each trace with custom colors and line styles
for trace in fig.data:
    trace_name = trace.name
    # Set color based on "Revenues" or "Outlays"
    if "Revenues" in trace_name:
        color = "blue"
    elif "Outlays" in trace_name:
        color = "red"
    # Set line style based on suffix
    if trace_name.endswith("_norm"):
        line_dash = "dash"
    elif trace_name.endswith("_cbo"):
        line_dash = "solid"
    # Apply the styling
    trace.update(line=dict(color=color, dash=line_dash))
# Update y-axis title
fig.update_yaxes(title_text="Percent of GDP")
# update Legend labels
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace("_reform", " (Cap Benefits)")
        .replace("_cbo", " (CBO)")
        .replace("SSTF_", "SSTF ")
    )
)
# Add title
fig.update_layout(title_text="Social Security Trust Fund Revenues and Outlays")
fig.show()
# %%
