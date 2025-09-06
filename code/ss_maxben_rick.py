"""
This Python script must be run in the ss-maxben-dev Conda environment, which
can be created using the provided environment.yml file.
"""

import numpy as np
import multiprocessing
from distributed import Client
import os
import json
import time
import importlib.resources
import copy
import argparse
from pathlib import Path
from taxcalc import Calculator
import matplotlib.pyplot as plt
from ogusa.calibrate import Calibration
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle

# Use a custom matplotlib style file for plots
style_file_url = (
    "https://raw.githubusercontent.com/PSLmodels/OG-Core/"
    + "master/ogcore/OGcorePlots.mplstyle"
)
plt.style.use(style_file_url)


def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    save_dir = os.path.dirname(os.path.realpath(__file__))  # SS_MaxBen/code
    main_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    base_dir_postOBBBA = os.path.join(save_dir, "OUTPUT_BASELINE_POSTOBBBA")
    reform_dir_2046 = os.path.join(save_dir, "OUTPUT_SS_MAXBEN_2046")
    reform_dir_2056 = os.path.join(save_dir, "OUTPUT_SS_MAXBEN_2056")
    json_dir = os.path.join(main_dir, "json")
    tmd_dir = (
        "/Users/richardevans/Docs/Economics/OSE/microsim/" +
        "tax-microdata-benchmarking/tmd/storage/output"
    )
    # tmd_dir = (
    #     "/Users/jason.debacker/repos/tax-microdata-benchmarking/"
    #     + "tmd/storage/output"
    # )

    """
    ---------------------------------------------------------------------------
    Run baseline post-OBBBA policy from Tax-Calculator 5.2.0 default
    ---------------------------------------------------------------------------
    """
    # Set up baseline parameterization
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=base_dir_postOBBBA,
        output_base=base_dir_postOBBBA,
    )
    # Update parameters for baseline from default json file
    with importlib.resources.open_text(
        "ogusa", "ogusa_default_parameters.json"
    ) as file:
        defaults = json.load(file)
    defaults["replacement_rate_adjust"] = [[1.0]]
    p.update_specifications(defaults)
    p.tax_func_type = "HSV"
    p.age_specific = True

    c = Calibration(
        p,
        estimate_tax_functions=True,
        client=client,
        data=Path(os.path.join(tmd_dir, "tmd.csv.gz")),
        weights=Path(os.path.join(tmd_dir, "tmd_weights.csv.gz")),
        gfactors=Path(os.path.join(tmd_dir, "tmd_growfactors.csv")),
        records_start_year=2021,
    )
    client.close()
    d = c.get_dict()
    # Adjust estimated tax functions to have higher scale
    pct = 0.02
    etr_arr = np.array(d["etr_params"], dtype=np.float64)
    mtrx_arr = np.array(d["mtrx_params"], dtype=np.float64)
    mtry_arr = np.array(d["mtry_params"], dtype=np.float64)
    etr_arr[:, :, 0] *= 1.0 - pct
    mtrx_arr[:, :, 0] *= 1.0 - pct
    mtry_arr[:, :, 0] *= 1.0 - pct
    etr_list = etr_arr.tolist()
    mtrx_list = mtrx_arr.tolist()
    mtry_list = mtry_arr.tolist()

    # Additional parameters to change. Set alpha_T to 30 years of CBO
    # forecasts. Set alpha_G to 21 years of CBO forecasts.
    updated_params = {
        "start_year": 2026,
        "RC_TPI": 100 * 1e-4,
        "initial_debt_ratio": 1.01727,
        "alpha_T": np.array(
            [
                8.685,
                8.713,
                8.519,
                8.82,
                8.804,
                8.839,
                8.915,
                8.974,
                9.022,
                9.109,
                9.184,
                9.256,
                9.332,
                9.405,
                9.47,
                9.537,
                9.597,
                9.652,
                9.700,
                9.744,
                9.787,
                9.823,
                9.858,
                9.889,
                9.917,
                9.944,
                9.967,
                9.986,
                10.001,
                10.017,
            ]
        )
        / 100,
        "alpha_G": np.array(
            [
                6.053,
                5.996,
                5.914,
                5.816,
                5.731,
                5.637,
                5.54,
                5.453,
                5.365,
                5.284,
                5.212,
                5.16,
                5.126,
                5.11,
                5.11,
                5.11,
                5.11,
                5.11,
                5.11,
                5.11,
                5.11,
            ]
        )
        * 0.975
        / 100,
        "cit_rate": [
            [0.260],
            [0.255],
            [0.250],
            [0.245],
            [0.240],
            [0.235],
            [0.230],
        ],
        "debt_ratio_ss": 1.90,
        "etr_params": etr_list,
        "mtrx_params": mtrx_list,
        "mtry_params": mtry_list,
        "mean_income_data": d["mean_income_data"],
        "frac_tax_payroll": d["frac_tax_payroll"],
    }
    p.update_specifications(updated_params)
    # Run model
    start_time = time.time()
    client = Client(n_workers=num_workers, threads_per_worker=1)
    runner(p, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ---------------------------------------------------------------------------
    Run reform policy, 2046 trigger
    ---------------------------------------------------------------------------
    """
    # create new Specifications object for reform simulation
    p2 = copy.deepcopy(p)
    p2.baseline = False
    p2.output_base = reform_dir_2046
    # Use calibration class to estimate reform tax functions from
    # Tax-Calculator, specifying reform for Tax-Calculator in iit_reform

    # Update parameters
    updated_params_2046 = {
        "RC_TPI": 100 * 1e-4,
        "debt_ratio_ss": 1.90 - 0.01911958  # This is the difference at 2046
    }
    p2.update_specifications(updated_params_2046)
    # Read in replacement rate json
    with open(
        os.path.join(
            json_dir,
            "maxben_replacement_rate_adjust_100k50k_trigger2046.json",
        ),
        "r",
    ) as f:
        replacement_rate_adjust = json.load(f)
    p2.update_specifications(replacement_rate_adjust)
    # Run model
    start_time = time.time()
    client = Client(n_workers=num_workers, threads_per_worker=1)
    runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ---------------------------------------------------------------------------
    Save some results of simulations, 2046 trigger
    ---------------------------------------------------------------------------
    """
    base_tpi_postOBBBA = safe_read_pickle(
        os.path.join(base_dir_postOBBBA, "TPI", "TPI_vars.pkl")
    )
    base_params_postOBBBA = safe_read_pickle(
        os.path.join(base_dir_postOBBBA, "model_params.pkl")
    )
    reform_tpi_2046 = safe_read_pickle(
        os.path.join(reform_dir_2046, "TPI", "TPI_vars.pkl")
    )
    reform_params_2046 = safe_read_pickle(
        os.path.join(reform_dir_2046, "model_params.pkl")
    )
    ans_2046 = ot.macro_table(
        base_tpi_postOBBBA,
        base_params_postOBBBA,
        reform_tpi=reform_tpi_2046,
        reform_params=reform_params_2046,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params_postOBBBA.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir_postOBBBA,
        reform_dir_2046,
        os.path.join(reform_dir_2046, "plots_tables"),
    )
    # Create CSV file with output
    ot.time_series_table(
        base_params_postOBBBA,
        base_tpi_postOBBBA,
        reform_params_2046,
        reform_tpi_2046,
        table_format="csv",
        path=os.path.join(
            reform_dir_2046, "plots_tables", "macro_time_series_output.csv"
        ),
    )

    print("Percentage changes in aggregates:", ans_2046)
    # save percentage change output to csv file
    ans_2046.to_csv(
        os.path.join(reform_dir_2046, "plots_tables", "output.csv")
    )

    """
    ---------------------------------------------------------------------------
    Run reform policy, 2056 trigger
    ---------------------------------------------------------------------------
    """
    # create new Specifications object for reform simulation
    p3 = copy.deepcopy(p)
    p3.baseline = False
    p3.output_base = reform_dir_2056
    # Use calibration class to estimate reform tax functions from
    # Tax-Calculator, specifying reform for Tax-Calculator in iit_reform

    # Update parameters
    updated_params_2056 = {
        "RC_TPI": 100 * 1e-4,
        "debt_ratio_ss": 1.90 - 0.039  # This is the difference at 2056
    }
    p3.update_specifications(updated_params_2056)
    # Read in replacement rate json
    with open(
        os.path.join(
            json_dir,
            "maxben_replacement_rate_adjust_100k50k_trigger2056.json",
        ),
        "r",
    ) as f:
        replacement_rate_adjust = json.load(f)
    p3.update_specifications(replacement_rate_adjust)
    # Run model
    start_time = time.time()
    client = Client(n_workers=num_workers, threads_per_worker=1)
    runner(p3, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ---------------------------------------------------------------------------
    Save some results of simulations, 2056 trigger
    ---------------------------------------------------------------------------
    """
    base_tpi_postOBBBA = safe_read_pickle(
        os.path.join(base_dir_postOBBBA, "TPI", "TPI_vars.pkl")
    )
    base_params_postOBBBA = safe_read_pickle(
        os.path.join(base_dir_postOBBBA, "model_params.pkl")
    )
    reform_tpi_2056 = safe_read_pickle(
        os.path.join(reform_dir_2056, "TPI", "TPI_vars.pkl")
    )
    reform_params_2056 = safe_read_pickle(
        os.path.join(reform_dir_2056, "model_params.pkl")
    )
    ans_2056 = ot.macro_table(
        base_tpi_postOBBBA,
        base_params_postOBBBA,
        reform_tpi=reform_tpi_2056,
        reform_params=reform_params_2056,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params_postOBBBA.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir_postOBBBA,
        reform_dir_2056,
        os.path.join(reform_dir_2056, "plots_tables"),
    )
    # Create CSV file with output
    ot.time_series_table(
        base_params_postOBBBA,
        base_tpi_postOBBBA,
        reform_params_2056,
        reform_tpi_2056,
        table_format="csv",
        path=os.path.join(
            reform_dir_2056, "plots_tables", "macro_time_series_output.csv"
        ),
    )

    print("Percentage changes in aggregates:", ans_2056)
    # save percentage change output to csv file
    ans_2056.to_csv(
        os.path.join(reform_dir_2056, "plots_tables", "output.csv")
    )


if __name__ == "__main__":
    main()
