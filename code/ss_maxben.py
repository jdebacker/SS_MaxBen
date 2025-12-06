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
from ogusa.calibrate import Calibration
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle
import logging



def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    save_dir = os.path.dirname(os.path.realpath(__file__))  # SS_MaxBen/code
    main_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    base_dir = os.path.join(save_dir, "Baseline_2025-12-03")
    reform_dir1 = os.path.join(save_dir, "reform_trigger2026_2025-12-03")
    reform_dir2 = os.path.join(save_dir, "reform_trigger2046_2025-12-03")
    reform_dir3 = os.path.join(save_dir, "reform_trigger2056_2025-12-03")
    json_dir = os.path.join(main_dir, "json")
    # tmd_dir = (
    #     "/Users/richardevans/Docs/Economics/OSE/microsim/" +
    #     "tax-microdata-benchmarking/tmd/storage/output"
    # )
    tmd_dir = (
        "/Users/jason.debacker/repos/tax-microdata-benchmarking/"
        + "tmd/storage/output"
    )

    """
    ---------------------------------------------------------------------------
    Run baseline post-OBBBA policy from Tax-Calculator 5.2.0 default
    ---------------------------------------------------------------------------
    """
    # Set up baseline parameterization
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=base_dir,
        output_base=base_dir,
    )
    # Update parameters for baseline from default json file
    with importlib.resources.open_text(
        "ogusa", "ogusa_default_parameters.json"
    ) as file:
        defaults = json.load(file)
    # defaults["replacement_rate_adjust"] = [[1.0]]
    # defaults["J"] = 7
    # defaults["lambdas"] = [0.25, 0.25, 0.2, 0.1, 0.1, 0.09, 0.01]
    # defaults["beta_annual"] = [0.91, 0.91, 0.92, 0.93, 0.95, 0.965, 0.98]
    # defaults["labor_income_tax_noncompliance_rate"] = [[0.0]]
    # defaults["capital_income_tax_noncompliance_rate"] = [[0.0]]
    p.update_specifications(defaults)
    p.tax_func_type = "HSV"
    p.age_specific = True

    p.J = 7
    p.lambdas = np.array([0.25, 0.25, 0.2, 0.1, 0.1, 0.09, 0.01])
    p.beta = np.array([0.91, 0.91, 0.92, 0.93, 0.95, 0.965, 0.98])
    # defaults["labor_income_tax_noncompliance_rate"] = [[0.0]]
    # defaults["capital_income_tax_noncompliance_rate"] = [[0.0]]
    # p.replacement_rate_adjust = np.ones((p.T + p.S, p.S))
    # p.labor_income_tax_noncompliance_rate = np.zeros((p.T + p.S, p.J))
    # p.capital_income_tax_noncompliance_rate = np.zeros((p.T + p.S, p.J))

    c = Calibration(
        p,
        estimate_tax_functions=True,
        client=client,
        data=Path(os.path.join(tmd_dir, "tmd.csv.gz")),
        weights=Path(os.path.join(tmd_dir, "tmd_weights.csv.gz")),
        gfactors=Path(os.path.join(tmd_dir, "tmd_growfactors.csv")),
        records_start_year=2021,
    )
    d = c.get_dict()
    # Adjust estimated tax functions to have higher scale
    pct = 0.04
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
        "tG1": 40,
        "debt_ratio_ss": 2.55,
        "baseline_theta": True,
        "etr_params": etr_list,
        "mtrx_params": mtrx_list,
        "mtry_params": mtry_list,
        "mean_income_data": d["mean_income_data"],
        "frac_tax_payroll": d["frac_tax_payroll"],
        "eta": d["eta"],
        "zeta": d["zeta"],
        "replacement_rate_adjust": [[1.0]],
        "labor_income_tax_noncompliance_rate": [[0.0]],
        "capital_income_tax_noncompliance_rate": [[0.0]],
        "eta_RM": np.ones((p.T, p.S)),
        "e": d["e"]
    }
    p.update_specifications(updated_params)
    # # Run model
    # start_time = time.time()
    # runner(p, time_path=True, client=client)
    # print("run time = ", time.time() - start_time)


    """
    ---------------------------------------------------------------------------
    Run reform policy
    ---------------------------------------------------------------------------
    """
    # create new Specifications object for reform simulation
    p2 = p
    p2.baseline = False
    p2.output_base = reform_dir1
    # Use calibration class to estimate reform tax functions from
    # Tax-Calculator, specifying reform for Tax-Calculator in iit_reform

    # Read in replacement rate json
    with open(
        os.path.join(
            json_dir,
            "maxben_replacement_rate_adjust_100k50k_nonconstant_rates_trigger2026_J7.json",
        ),
        "r",
    ) as f:
        replacement_rate_adjust = json.load(f)
    p2.update_specifications(replacement_rate_adjust)
    p2.reform_use_baseline_solution = False

    # Run model
    start_time = time.time()
    # runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    Run reform policy
    ---------------------------------------------------------------------------
    """
    # create new Specifications object for reform simulation
    p2 = copy.deepcopy(p)
    p2.baseline = False
    p2.output_base = reform_dir2
    # Use calibration class to estimate reform tax functions from
    # Tax-Calculator, specifying reform for Tax-Calculator in iit_reform

    # Read in replacement rate json
    with open(
        os.path.join(
            json_dir,
            "maxben_replacement_rate_adjust_100k50k_nonconstant_rates_trigger2046_J7.json",
        ),
        "r",
    ) as f:
        replacement_rate_adjust = json.load(f)
    p2.update_specifications(replacement_rate_adjust)

    # Run model
    start_time = time.time()
    # runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    Run reform policy
    ---------------------------------------------------------------------------
    """
    # create new Specifications object for reform simulation
    p2 = copy.deepcopy(p)
    p2.baseline = False
    p2.output_base = reform_dir3
    # Use calibration class to estimate reform tax functions from
    # Tax-Calculator, specifying reform for Tax-Calculator in iit_reform

    # Read in replacement rate json
    with open(
        os.path.join(
            json_dir,
            "maxben_replacement_rate_adjust_100k50k_nonconstant_rates_trigger2056_J7.json",
        ),
        "r",
    ) as f:
        replacement_rate_adjust = json.load(f)
    p2.update_specifications(replacement_rate_adjust)

    # Run model
    start_time = time.time()
    runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ---------------------------------------------------------------------------
    Save some results of simulations
    ---------------------------------------------------------------------------
    """
    base_tpi = safe_read_pickle(
        os.path.join(base_dir, "TPI", "TPI_vars.pkl")
    )
    base_params = safe_read_pickle(
        os.path.join(base_dir, "model_params.pkl")
    )
    reform_tpi = safe_read_pickle(
        os.path.join(reform_dir1, "TPI", "TPI_vars.pkl")
    )
    reform_params = safe_read_pickle(
        os.path.join(reform_dir1, "model_params.pkl")
    )
    ans = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi,
        reform_params=reform_params,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir,
        reform_dir1,
        os.path.join(reform_dir1, "plots_tables"),
    )
    # Create CSV file with output
    ot.time_series_table(
        base_params,
        base_tpi,
        reform_params,
        reform_tpi,
        table_format="csv",
        path=os.path.join(
            reform_dir1, "plots_tables", "macro_time_series_output.csv"
        ),
    )

    print("Percentage changes in aggregates:", ans)
    # save percentage change output to csv file
    ans.to_csv(os.path.join(reform_dir1, "plots_tables", "output.csv"))


if __name__ == "__main__":
    main()
