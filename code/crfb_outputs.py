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
import ogcore
from ogcore.utils import safe_read_pickle
from ogusa.utils import read_cbo_forecast
import crfb_plots as cp

# set current directory
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
# set directory to save tables to
SAVE_DIR = os.path.join(CUR_DIR, "..", "CRFB_outputs")
# make directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)

# Constants used below
CRFB_END_YEAR = 2100
OASDI_RATIO = 12.4 / 16.2  # This is OASDI taxes to total payroll taxes

# Read in model output, put reforms in dictionary
base_params = safe_read_pickle(
    os.path.join(CUR_DIR, "OUTPUT_BASELINE_POSTOBBBA", "model_params.pkl")
)
base_tpi = safe_read_pickle(
    os.path.join(CUR_DIR, "OUTPUT_BASELINE_POSTOBBBA", "TPI", "TPI_vars.pkl")
)
simulations = {
    "2056 Trigger": {
        "params": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_50k100k_trigger2056",
                "model_params.pkl",
            )
        ),
        "tp_vars": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_50k100k_trigger2056",
                "TPI",
                "TPI_vars.pkl",
            )
        ),
        "suffix": "_trigger2056",
    },
    "2046 Trigger": {
        "params": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2046",
                "model_params.pkl",
            )
        ),
        "tp_vars": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2046",
                "TPI",
                "TPI_vars.pkl",
            )
        ),
        "suffix": "_trigger2046",
    },
    "2026 Trigger": {
        "params": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_50k100k_trigger2026",
                "model_params.pkl",
            )
        ),
        "tp_vars": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_50k100k_trigger2026",
                "TPI",
                "TPI_vars.pkl",
            )
        ),
        "suffix": "_trigger2026",
    }
}


# %%
# Read in CBO baseline LT forecast
df_cbo_fiscal = pd.read_excel(
    os.path.join(CUR_DIR, "..", "data", "CBO_projections.xlsx")
)
df_cbo_fiscal = df_cbo_fiscal.fillna(0).astype(float)
# divide all values (except year) by 100 to put in fractions
df_cbo_fiscal.iloc[:, 1:] = df_cbo_fiscal.iloc[:, 1:] / 100


# Function to put fiscal variables into dataframes
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


def create_crfb_outputs(
    base_tpi, base_params, reform_tpi, reform_params, df_cbo_fiscal, suffix
):
    """
    Creates and saves output for CRFB
    """
    # Unpack parameters
    start_year = base_params.start_year
    T = base_params.T
    S = base_params.S
    J = base_params.J

    # put macro pct changes time series into a dataframe
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
    macro_df[macro_df["Year"] <= CRFB_END_YEAR].to_csv(
        os.path.join(SAVE_DIR, f"macro_pct_changes{suffix}.csv"), index=False
    )

    # Create fiscal dataframes
    base_fiscal_df = convert_fiscal(base_tpi)
    reform_fiscal_df = convert_fiscal(reform_tpi)

    # Save to CSV for CRFB
    base_fiscal_df[base_fiscal_df["Year"] <= CRFB_END_YEAR].to_csv(
        os.path.join(SAVE_DIR, f"fiscal_vars_baseline.csv"), index=False
    )
    reform_fiscal_df[reform_fiscal_df["Year"] <= CRFB_END_YEAR].to_csv(
        os.path.join(SAVE_DIR, f"fiscal_vars{suffix}.csv"), index=False
    )

    # put cbo and baseline together in df
    df = pd.merge(
        base_fiscal_df, df_cbo_fiscal, on="Year", suffixes=("_base", "_cbo")
    )
    for cols in reform_fiscal_df.columns:
        if cols != "Year":
            reform_fiscal_df.rename(
                columns={cols: f"{cols}_reform"}, inplace=True
            )
    df = pd.merge(df, reform_fiscal_df, on="Year")
    # Keep just to end of CBO forecast
    df = df[(df["Year"] >= 2026) & (df["Year"] <= 2098)]

    # Crate dataframe with SSTF revenues and outlays
    df["SSTF_Revenues_norm"] = df["SSTF_Revenues_cbo"] - (
        df["SSTF_Revenues_base"] - df["SSTF_Revenues_reform"]
    )
    df["SSTF_Outlays_norm"] = df["SSTF_Outlays_cbo"] - (
        df["SSTF_Outlays_base"] - df["SSTF_Outlays_reform"]
    )
    # Keep only the year column and columns with the prefix "SSTF"
    df = df[
        [
            col
            for col in df.columns
            if col.startswith("Year") or col.startswith("SSTF")
        ]
    ]
    # Rename _norm columns
    df.rename(
        columns={
            "SSTF_Revenues_norm": "SSTF Revenues, Cap",
            "SSTF_Outlays_norm": "SSTF Outlays, Cap",
        },
        inplace=True,
    )
    df.rename(
        columns={
            "SSTF_Revenues_cbo": "SSTF Revenues, Current Law",
            "SSTF_Outlays_cbo": "SSTF Outlays, Current Law",
        },
        inplace=True,
    )
    # Keep just year and columns with SSTF prefix
    df = df[
        [
            col
            for col in df.columns
            if col.startswith("Year") or col.startswith("SSTF")
        ]
    ]
    # Need to add two more years to df since CBO only goes to 2098
    # Do this by growing at the average growth rate of the last 3 years
    last_year = df["Year"].max()
    for i in range(1, 3):
        new_year = last_year + i
        new_row = {"Year": new_year}
        for col in df.columns:
            if col != "Year":
                growth_rate = (
                    df.loc[df["Year"] == last_year, col].values[0]
                    - df.loc[df["Year"] == last_year - 3, col].values[0]
                ) / 3
                new_row[col] = (
                    df.loc[df["Year"] == last_year, col].values[0]
                    + growth_rate
                )
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    # Keep just to 2100
    df = df[df["Year"] <= CRFB_END_YEAR]
    # Save to CSV for CRFB
    df.to_csv(
        os.path.join(SAVE_DIR, f"SSTF_balances{suffix}.csv"), index=False
    )

    # Create distributional analysis
    # Want the following output variables: tax paid, benefits, income, consumption
    # scale by pct of benefits in the baseline
    # find array that is the pension amount in the baseline (T x S x J)
    pension_baseline = (
        base_tpi["etr"] * base_tpi["before_tax_income"]
        - base_tpi["hh_taxes"]
        - base_tpi["tr"]
    )
    # make sure no negative pensions
    pension_baseline[pension_baseline < 0] = 0
    # Make a DataFrame that is in a long panel format: year, age, J, pension, income, consumption, tax paid
    J_map = {
        0: "0-25%",
        1: "25-50%",
        2: "50-70%",
        3: "70-80%",
        4: "80-90%",
        5: "90-99%",
        6: "99-99.5%",
        7: "99.5-99.9%",
        8: "99.9-99.99%",
        9: "Top 0.01%",
    }
    # create dataframe with columns year, age, J
    # year is 2026-2100
    # ages are 20-100
    # J is 0-9
    years = np.arange(
        base_params.start_year, base_params.start_year + base_params.T
    )
    ages = np.arange(base_params.E, base_params.E + base_params.S)
    J = np.arange(base_params.J)
    year_grid, age_grid, J_grid = np.meshgrid(years, ages, J, indexing="ij")
    base_dist_df = pd.DataFrame(
        {
            "Year": year_grid.flatten(),
            "Age": age_grid.flatten(),
            "J": J_grid.flatten(),
        }
    )
    # put consumption into dataframe
    base_dist_df["Consumption"] = base_tpi["c"].flatten()
    base_dist_df["Income"] = base_tpi["before_tax_income"].flatten()
    base_dist_df["Income and Payroll Tax Paid"] = (
        base_tpi["hh_taxes"] + pension_baseline + base_tpi["tr"]
    ).flatten()
    base_dist_df["Pension"] = pension_baseline.flatten()
    # update J to be the J_map
    base_dist_df["J"] = base_dist_df["J"].map(J_map)
    # repeat for reform
    reform_dist_df = pd.DataFrame(
        {
            "Year": year_grid.flatten(),
            "Age": age_grid.flatten(),
            "J": J_grid.flatten(),
        }
    )
    reform_dist_df["Consumption"] = reform_tpi["c"].flatten()
    reform_dist_df["Income"] = reform_tpi["before_tax_income"].flatten()
    pension_reform = (
        reform_tpi["etr"] * reform_tpi["before_tax_income"]
        - reform_tpi["hh_taxes"]
        - reform_tpi["tr"]
    )
    pension_reform[pension_reform < 0] = 0
    reform_dist_df["Income and Payroll Tax Paid"] = (
        reform_tpi["hh_taxes"] + pension_reform + reform_tpi["tr"]
    ).flatten()
    reform_dist_df["Pension"] = pension_reform.flatten()
    reform_dist_df["J"] = reform_dist_df["J"].map(J_map)

    # keep just year <= 2100
    base_dist_df = base_dist_df[base_dist_df["Year"] <= CRFB_END_YEAR]
    reform_dist_df = reform_dist_df[reform_dist_df["Year"] <= CRFB_END_YEAR]
    # save to csv
    base_dist_df.to_csv(
        os.path.join(SAVE_DIR, "base_distribution.csv"), index=False
    )
    reform_dist_df.to_csv(
        os.path.join(SAVE_DIR, f"distribution{suffix}.csv"), index=False
    )

    # TODO: add some calls to create plots to inspect the output


# Loop over simulations and create outputs
for sim in simulations.keys():
    print(f"Creating CRFB outputs for {sim}")
    create_crfb_outputs(
        base_tpi,
        base_params,
        simulations[sim]["tp_vars"],
        simulations[sim]["params"],
        df_cbo_fiscal,
        simulations[sim]["suffix"],
    )
