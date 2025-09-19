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
from ogcore.utils import safe_read_pickle
import crfb_plots as cp

# set current directory
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
# set directory to save tables to
SAVE_DIR = os.path.join(CUR_DIR, "..", "CRFB_outputs")
plot_path = os.path.join(SAVE_DIR, "plots")
# make directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(plot_path, exist_ok=True)

# Constants used below
CRFB_END_YEAR = 2100
OASDI_RATIO = 12.4 / 16.2  # This is OASDI taxes to total payroll taxes

# Read in model output, put reforms in dictionary
base_params = safe_read_pickle(
    os.path.join(CUR_DIR, "OUTPUT_BASELINE_POSTOBBBA_tg1_40", "model_params.pkl")
)
base_tpi = safe_read_pickle(
    os.path.join(CUR_DIR, "OUTPUT_BASELINE_POSTOBBBA_tg1_40", "TPI", "TPI_vars.pkl")
)
simulations = {
    "2056 Trigger": {
        "params": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2056_tg1_40",
                "model_params.pkl",
            )
        ),
        "tp_vars": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2056_tg1_40",
                "TPI",
                "TPI_vars.pkl",
            )
        ),
        "suffix": "_2056",
    },
    "2046 Trigger": {
        "params": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2046_tg1_40",
                "model_params.pkl",
            )
        ),
        "tp_vars": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2046_tg1_40",
                "TPI",
                "TPI_vars.pkl",
            )
        ),
        "suffix": "_2046",
    },
    "2026 Trigger": {
        "params": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2026_tg1_40",
                "model_params.pkl",
            )
        ),
        "tp_vars": safe_read_pickle(
            os.path.join(
                CUR_DIR,
                "OUTPUT_SS_MAXBEN_2026_tg1_40",
                "TPI",
                "TPI_vars.pkl",
            )
        ),
        "suffix": "_2026",
    },
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


# Function to compute average annual Social Security benefits by cohort
# Create 2D array (T x S x J) of average annual SocSec benefits for s>=44 by
# cohort (t) and lifetime income group (j). The value over an individual's
# lifetime will be constant (in the diagonals)
def create_avg_ann_lftm_ssben(ss_ben_arr, p):
    lambda_arr = np.tile(
        p.lambdas.flatten().reshape(1, 1, p.J), (p.T + p.S - 1, p.S, 1)
    )
    omega_arr = np.tile(
        p.omega[:-1, :].reshape(p.T + p.S -1, p.S, 1), (1, 1, p.J)
    )
    # Extend ss_ben_arr to be T+S-1 x S x J by adding S-1 rows, repeating last row
    ss_ben_arr = np.vstack(
        (ss_ben_arr, np.tile(ss_ben_arr[-1, :, :], (p.S - 1, 1, 1)))
    )
    pop_arr = omega_arr * lambda_arr
    ss_ben_pop_arr = ss_ben_arr * pop_arr
    avg_ann_lftm_ssben = np.zeros((p.T, p.S, p.J))
    for t in range(p.T):
        for j in range(p.J):
            if t == 0:  # Fill in all the incomplete lifetimes in t=0
                for s in range(1, p.S + 1):
                    # print(f"t={t}, j={j}, s={s}")
                    if s == 1:  # Age 100 in t=0
                        bnft_age_mask = [True]
                        avg_ann_lftm_ssben[t, p.S - s, j] = (
                            ss_ben_pop_arr[t, p.S - s, j] /
                            pop_arr[t, p.S - s, j]
                        )
                    else:  # Ages 21-99 in t=0
                        bnft_age_mask = np.arange(p.S - s, p.S) >= p.retire[t]
                        avg_ann_lftm_ssben[t:t + s, p.S-s:][
                            np.eye(s, dtype=bool)
                        ] = (
                            (bnft_age_mask * np.diagonal(
                                ss_ben_pop_arr[t:t+s, -s:, j]
                            )).sum() /
                            (bnft_age_mask * np.diagonal(
                                pop_arr[t:t+s, -s:, j]
                            )).sum()
                        )
            elif t >= 1 and t <= p.T - p.S:  # Fill in complete lifetimes
                # print(f"t={t}, j={j}, s={p.S}")
                bnft_age_mask = np.arange(p.S) >= p.retire[t]
                avg_ann_lftm_ssben[t:t + p.S, :, j][
                    np.eye(p.S, dtype=bool)
                ] = (
                    (bnft_age_mask * np.diagonal(
                        ss_ben_pop_arr[t:t+p.S, :, j]
                    )).sum() /
                    (bnft_age_mask * np.diagonal(pop_arr[t:t+p.S, :, j])).sum()
                )
            else:
                # print(f"t={t}, j={j}, s={p.T - t}")
                bnft_age_mask = np.arange(p.S) >= p.retire[t]
                avg_ann_lftm_ssben[t:, :p.T - t, j][
                    np.eye(p.T - t, dtype=bool)
                ] = (
                    (bnft_age_mask * np.diagonal(
                        ss_ben_pop_arr[t:t+p.S, :, j]
                    )).sum() /
                    (bnft_age_mask * np.diagonal(pop_arr[t:t+p.S, :, j])).sum()
                )

    return avg_ann_lftm_ssben


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
    # plot macro pct changes
    filename = os.path.join(plot_path, f"macro_pct_changes{suffix}.png")
    cp.plot_macros(macro_df, CRFB_END_YEAR, filename=filename)

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
    # Create plots of fiscal variables to inspect
    filename = os.path.join(plot_path, f"rD_Y_base_v_cbo.png")
    cp.plot_rD_Y(df, filename=filename)
    filename = os.path.join(plot_path, f"deficits_base_v_cbo.png")
    cp.plot_deficit(df, filename=filename)
    filename = os.path.join(plot_path, f"rev_and_spend_base_v_cbo.png")
    cp.plot_rev_spend(df, filename=filename)
    filename = os.path.join(plot_path, f"tax_rev_base_v_cbo.png")
    cp.plot_fiscal(df, filename=filename)
    filename = os.path.join(plot_path, f"debt_base_v_cbo.png")
    cp.plot_debt(df, filename=filename)
    filename = os.path.join(plot_path, f"sstf_base_v_cbo.png")
    cp.plot_sstf_cbo(df, filename=filename)

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
    # Create plot of SSTF revenues and outlays
    filename = os.path.join(plot_path, f"SSTF_revenues_outlays{suffix}.png")
    cp.plot_sstf_revenues_outlays(df, filename=filename)

    # Create distributional analysis
    # Want the following output variables: tax paid, benefits, income, consumption
    # scale by pct of benefits in the baseline
    # find array that is the pension amount in the baseline (T x S x J)
    pension_baseline = base_tpi["pension_benefits"]
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
            "Lifetime Income Group": J_grid.flatten(),
        }
    )
    # put consumption into dataframe
    base_dist_df["Average Annual Benefits"] = create_avg_ann_lftm_ssben(
        base_tpi["pension_benefits"], base_params
    ).flatten()
    base_dist_df["Consumption"] = base_tpi["c"].flatten()
    base_dist_df["Income"] = base_tpi["before_tax_income"].flatten()
    base_dist_df["Income and Payroll Tax Paid"] = (
        base_tpi["income_payroll_taxes"]
    ).flatten()
    base_dist_df["Pension"] = pension_baseline.flatten()
    # update J to be the J_map
    base_dist_df["Lifetime Income Group"] = base_dist_df["Lifetime Income Group"].map(J_map)
    # repeat for reform
    reform_dist_df = pd.DataFrame(
        {
            "Year": year_grid.flatten(),
            "Age": age_grid.flatten(),
            "Lifetime Income Group": J_grid.flatten(),
        }
    )
    reform_dist_df["Consumption"] = reform_tpi["c"].flatten()
    reform_dist_df["Income"] = reform_tpi["before_tax_income"].flatten()
    pension_reform = reform_tpi["pension_benefits"]
    pension_reform[pension_reform < 0] = 0
    reform_dist_df["Income and Payroll Tax Paid"] = (
        reform_tpi["income_payroll_taxes"]
    ).flatten()
    reform_dist_df["Pension"] = pension_reform.flatten()
    reform_dist_df["Lifetime Income Group"] = reform_dist_df["Lifetime Income Group"].map(J_map)

    # Make plots of percentage changes in distributional variables
    plot_vars = ["Consumption", "Income", "Income and Payroll Tax Paid", "Pension"]
    for var in plot_vars:
        filename = os.path.join(plot_path, f"{var}_pct_change{suffix}.png")
        cp.plot_dist_pct_changes(
            base_dist_df,
            reform_dist_df,
            70,  # plot for 70 year olds
            var,
            CRFB_END_YEAR,
            filename=filename,
        )

    # keep just year <= 2100
    base_dist_df = base_dist_df[base_dist_df["Year"] <= CRFB_END_YEAR]
    reform_dist_df = reform_dist_df[reform_dist_df["Year"] <= CRFB_END_YEAR]
    # scale everything by pct of average annual benefits in the baseline
    for var in ["Consumption", "Income", "Income and Payroll Tax Paid", "Pension"]:
        base_dist_df[var] = base_dist_df[var] / base_dist_df[
            "Average Annual Benefits"
        ]
        reform_dist_df[var] = reform_dist_df[var] / base_dist_df[
            "Average Annual Benefits"
        ]
    # save to csv
    base_dist_df.to_csv(
        os.path.join(SAVE_DIR, "distribution_baseline.csv"), index=False
    )
    reform_dist_df.to_csv(
        os.path.join(SAVE_DIR, f"distribution{suffix}.csv"), index=False
    )


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
