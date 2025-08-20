"""
This Python script must be run in the ss-maxben-preOBBBA Conda environment,
which can be created using the provided environment_preOBBBA.yml file.
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
    cur_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    base_mar2025_dir = os.path.join(save_dir, "OUTPUT_BASELINE_MAR2025")
    reform_dir = os.path.join(save_dir, "OUTPUT_SS_MAXBEN")
    tmd_dir = (
        "/Users/richardevans/Docs/Economics/OSE/microsim/" +
        "tax-microdata-benchmarking/tmd/storage/output"
    )
    # tmd_dir = (
    #     "/Users/jason.debacker/repos/tax-microdata-benchmarking/" +
    #     "tmd/storage/output"
    # )

    """
    ---------------------------------------------------------------------------
    Run baseline pre-OBBBA policy from Tax-Calculator 5.1.0 default
    ---------------------------------------------------------------------------
    """
    # Set up baseline parameterization
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=base_mar2025_dir,
        output_base=base_mar2025_dir,
    )
    # Update parameters for baseline from default json file
    with importlib.resources.open_text(
        "ogusa", "ogusa_default_parameters.json"
    ) as file:
        defaults = json.load(file)
    p.update_specifications(defaults)
    p.tax_func_type = "HSV"
    p.age_specific = True

    c = Calibration(
        p,
        estimate_tax_functions=True,
        client=client,
        data=Path(os.path.join(tmd_dir, "tmd_jason2.csv.gz")),
        weights=Path(os.path.join(tmd_dir, "tmd_weights_jason2.csv.gz")),
        gfactors=Path(os.path.join(tmd_dir, "tmd_growfactors_jason2.csv")),
        records_start_year=2021,
    )
    client.close()
    d = c.get_dict()
    # Adjust estimated tax functions to have higher scale
    pct = 0.02
    etr_arr = np.array(d["etr_params"], dtype=np.float64)
    mtrx_arr = np.array(d["mtrx_params"], dtype=np.float64)
    mtry_arr = np.array(d["mtry_params"], dtype=np.float64)
    etr_arr[:, :, 0] *= (1.0 - pct)
    mtrx_arr[:, :, 0] *= (1.0 - pct)
    mtry_arr[:, :, 0] *= (1.0 - pct)
    etr_list = etr_arr.tolist()
    mtrx_list = mtrx_arr.tolist()
    mtry_list = mtry_arr.tolist()

    # Additional parameters to change. Set alpha_T to 30 years of CBO
    # forecasts. Set alpha_G to 21 years of CBO forecasts.
    updated_params = {
        "start_year": 2026,
        "RC_TPI": 100 * 1e-4,
        "initial_debt_ratio": 1.01727,
        "alpha_T": np.array([
            8.685, 8.713, 8.519, 8.82, 8.804, 8.839, 8.915, 8.974, 9.022,
            9.109, 9.184, 9.256, 9.332, 9.405, 9.47, 9.537, 9.597, 9.652,
            9.700, 9.744, 9.787, 9.823, 9.858, 9.889, 9.917, 9.944, 9.967,
            9.986, 10.001, 10.017
        ]) / 100,
        "alpha_G": np.array([
            6.053, 5.996, 5.914, 5.816, 5.731, 5.637, 5.54, 5.453, 5.365,
            5.284, 5.212, 5.16, 5.126, 5.11, 5.11, 5.11, 5.11, 5.11, 5.11,
            5.11, 5.11
        ]) / 100,
        "cit_rate": [
            [0.260], [0.255], [0.250], [0.245], [0.240], [0.235], [0.230]
        ],
        "debt_ratio_ss": 1.65,
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


if __name__ == "__main__":
    main()
