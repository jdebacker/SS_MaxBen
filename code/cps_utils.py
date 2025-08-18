import pandas as pd
import numpy as np


def weighted_percentile(values, weights, percentiles):
    """
    Calculate weighted percentiles for given values and weights.

    Parameters:
    values: array-like, values to calculate percentiles for
    weights: array-like, sampling weights
    percentiles: array-like, percentiles to calculate (0-100)

    Returns:
    array of percentile values
    """
    # Remove any NaN values
    mask = ~(np.isnan(values) | np.isnan(weights))
    values = values[mask]
    weights = weights[mask]

    # Sort values and corresponding weights
    sorted_indices = np.argsort(values)
    sorted_values = values[sorted_indices]
    sorted_weights = weights[sorted_indices]

    # Calculate cumulative weighted sum
    cumsum = np.cumsum(sorted_weights)
    total_weight = cumsum[-1]

    # Calculate cumulative percentages
    cumulative_pct = (cumsum - 0.5 * sorted_weights) / total_weight * 100

    # Interpolate to find percentile values
    percentile_values = np.interp(percentiles, cumulative_pct, sorted_values)

    return percentile_values


def add_weighted_percentile_groups(
    df, value_col="HSSVAL", weight_col="HSUP_WGT", new_col="pctile_group"
):
    """
    Add weighted percentile groups to DataFrame.

    Parameters:
    df: pandas DataFrame
    value_col: column name containing values to calculate percentiles for
    weight_col: column name containing sampling weights
    new_col: name for new percentile group column

    Returns:
    DataFrame with new percentile group column added
    """
    # Calculate weighted percentiles
    percentiles_to_calc = [25, 50, 70, 80, 90, 99]
    percentile_values = weighted_percentile(
        df[value_col].values, df[weight_col].values, percentiles_to_calc
    )

    # Create a copy to avoid modifying original
    df_copy = df.copy()

    # Define the percentile ranges and labels
    bins = [-np.inf] + list(percentile_values) + [np.inf]
    labels = ["0-25", "25-50", "50-70", "70-80", "80-90", "90-99", "99-100"]

    # Assign percentile groups
    df_copy[new_col] = pd.cut(
        df_copy[value_col],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=False,
    )

    return df_copy


# Example usage:
# df_with_groups = add_weighted_percentile_groups(df)


# If you want to see the percentile cutoff values:
def show_weighted_percentile_cutoffs(
    df, value_col="HSSVAL", weight_col="HSUP_WGT"
):
    """Display the weighted percentile cutoff values."""
    percentiles_to_calc = [25, 50, 70, 80, 90, 99]
    percentile_values = weighted_percentile(
        df[value_col].values, df[weight_col].values, percentiles_to_calc
    )

    print("Weighted Percentile Cutoffs:")
    for pct, val in zip(percentiles_to_calc, percentile_values):
        print(f"{pct}th percentile: {val:.2f}")

    return dict(zip(percentiles_to_calc, percentile_values))


def weighted_sum(values, weights):
    """Calculate weighted sum"""
    return np.sum(values * weights)
