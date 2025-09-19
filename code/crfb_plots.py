import plotly.express as px

# set plotly theme to white
px.defaults.template = "plotly_white"


def SSTF_plot(df, filename=None):
    plot_vars = [
            "SSTF_Revenues_base",
            "SSTF_Outlays_base",
            "SSTF_Revenues_cbo",
            "SSTF_Outlays_cbo",
        ]
    # put in pct by multiply by 100
    for var in plot_vars:
        df[var] = 100 * df[var]
    fig = px.line(
        df,
        x="Year",
        y=plot_vars,
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
    fig.update_layout(
        title_text="Social Security Trust Fund Revenues and Outlays"
    )
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_fiscal(df, end_year=2054, filename=None):
    plot_vars = [
            "PayrollTax/Y_base", "IIT/Y_base", "PayrollTax/Y_cbo", "IIT/Y_cbo"
        ]
    # put in pct by multiply by 100
    for var in plot_vars:
        df[var] = 100 * df[var]
    fig = px.line(
        df[df["Year"] <= end_year],
        x="Year",
        y=plot_vars,
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
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_debt(df, end_year=2054, filename=None):
    plot_vars = ["D/Y_base", "D/Y_cbo"]
    for var in plot_vars:
        df[var] = 100 * df[var]
    # Plot D/Y from CBO and baseline
    fig = px.line(
        df[df["Year"] <= end_year], x="Year", y=plot_vars
    )
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
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_rev_spend(df, end_year=2054, filename=None):
    plot_vars = [
        "Rev/Y_base", "TotalSpend/Y_base", "Rev/Y_cbo", "TotalSpend/Y_cbo"
    ]
    for var in plot_vars:
        df[var] = 100 * df[var]
    # Plot total Rev/Y and TotalSpend/Y
    fig = px.line(
        df[df["Year"] <= end_year],
        x="Year",
        y=plot_vars,
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
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_deficit(df, end_year=2054, filename=None):
    # Plot deficits to GDP (TotalSpend/Y - Rev/Y) for CBO and model baseline
    df["Deficit/Y_base"] = (df["TotalSpend/Y_base"] - df["Rev/Y_base"]) * 100
    df["Deficit/Y_cbo"] = (df["TotalSpend/Y_cbo"] - df["Rev/Y_cbo"]) * 100
    fig = px.line(
        df[df["Year"] <= end_year],
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
        trace.update(line=dict(color="black", dash=line_dash))
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
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_rD_Y(df, end_year=2054, filename=None):
    df["rD/Y_base"] = 100 * df["rD/Y_base"]
    df["rD/Y_cbo"] = 100 * df["rD/Y_cbo"]
    # Plot rD/Y from CBO and baseline
    fig = px.line(
        df[df["Year"] <= end_year],
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
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_macros(macro_df, end_year=2100, filename=None):
    # plot pct changes in macros
    for vars in ["GDP", "Capital Stock", "Labor Supply", "Consumption"]:
        macro_df[vars] = 100 * macro_df[vars]
    fig = px.line(
        macro_df[macro_df["Year"] <= end_year],
        x="Year",
        # multiply by 100 to get percent changes
        y=["GDP", "Capital Stock", "Labor Supply", "Consumption"],
    )
    fig.update_layout(title_text="Percent Changes in Macroeconomic Variables")
    # Update y-axis title
    fig.update_yaxes(title_text="Percent Change from Baseline")
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_sstf_cbo(df, filename=None):
    plot_vars = [
        "SSTF_Revenues_base",
            "SSTF_Outlays_base",
            "SSTF_Revenues_cbo",
            "SSTF_Outlays_cbo",
            "SSTF_Revenues_reform",
            "SSTF_Outlays_reform",
    ]
    for var in plot_vars:
        df[var] = 100 * df[var]
     # Plot D/Y from CBO and baseline
    fig = px.line(
        df,
        x="Year",
        y=plot_vars,
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
    fig.update_layout(
        title_text="Social Security Trust Fund Revenues and Outlays"
    )
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_sstf_revenues_outlays(df, filename=None):
    plot_vars = [
            "SSTF Revenues, Cap",
            "SSTF Outlays, Cap",
            "SSTF Revenues, Current Law",
            "SSTF Outlays, Current Law",
        ]
    # plot cbo and model output
    fig = px.line(
        df,
        x="Year",
        y=plot_vars,
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
        if trace_name.endswith(" Cap"):
            line_dash = "dash"
        elif trace_name.endswith("Current Law"):
            line_dash = "solid"
        # Apply the styling
        trace.update(line=dict(color=color, dash=line_dash))
    # Update y-axis title
    fig.update_yaxes(title_text="Percent of GDP")
    # Change the aspect ratio of the figure
    fig.update_layout(
        autosize=False,
        width=1000,
        height=500,
    )
    # Add title
    fig.update_layout(
        title_text="Social Security Trust Fund Revenues and Outlays"
    )
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_dist_pct_changes(base_dist_df, reform_dist_df, age=70, var="Consumption", endyear=2100, filename=None):
    """
    Plots the time series of percentage changes between baseline and
    reform for `var` in a plot with lines for each lifetime income
    group.

    Args:
        base_dist_df (pd.DataFrame): DataFrame with baseline distribution data.
        reform_dist_df (pd.DataFrame): DataFrame with reform distribution data.
        age (int): Age to filter the data on.
        var (str): Variable to plot percentage changes for.
        endyear (int): Last year to include in the plot.
        filename (str, optional): If provided, saves the plot to this file.

    Returns:
        None
    """
    # filter to age
    base_dist_df = base_dist_df[base_dist_df["Age"] == age]
    reform_dist_df = reform_dist_df[reform_dist_df["Age"] == age]
    # create pct change columns for each lifetime income group
    reform_dist_df["pct_diff"] = ((reform_dist_df[var] - base_dist_df[var]) / base_dist_df[var]) * 100
    fig = px.line(
        reform_dist_df[reform_dist_df["Year"] <= endyear],
        x="Year",
        y="pct_diff",
        color="Lifetime Income Group",
        title=f"Percentage Changes in {var} by Lifetime Income Group, for Age {age}"
    )
    fig.update_yaxes(title_text="Percent Change")
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()