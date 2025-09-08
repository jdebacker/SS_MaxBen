import plotly.express as px
import pandas as pd
import numpy as np
import os

# set plotly theme to white
px.defaults.template = "plotly_white"


def SSTF_plot(df):
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
    fig.update_layout(
        title_text="Social Security Trust Fund Revenues and Outlays"
    )
    fig.show()


def plot_fiscal(df):
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


def plot_debt(df):
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


def plot_fiscal(df):
    # Plot PayrollTax/Y and IIT/Y
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


def plot_rev_spend(df):
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


def plot_deficit(df):
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


def plot_rD_Y(df):
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


def plot_macros(macro_df, filename=None):
    # plot pct changes in macros
    fig = px.line(
        macro_df[macro_df["Year"] <= CRFB_END_YEAR],
        x="Year",
        y=["GDP", "Capital Stock", "Labor Supply", "Consumption"],
    )
    fig.update_layout(title_text="Percent Changes in Macroeconomic Variables")
    if filename is not None:
        fig.write_image(filename, scale=3)
    else:
        fig.show()


def plot_rev_outlays_cbo(df):
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
    fig.update_layout(
        title_text="Social Security Trust Fund Revenues and Outlays"
    )
    fig.show()


def plot_sstf_revenues_outlays(df):
    # plot cbo and model output
    fig = px.line(
        df,
        x="Year",
        y=[
            "SSTF Revenues, Cap",
            "SSTF Outlays, Cap",
            "SSTF Revenues, Current Law",
            "SSTF Outlays, Current Law",
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
    # update Legend labels
    # fig.for_each_trace(
    #     lambda t: t.update(
    #         name=t.name.replace("_reform", " (Cap Benefits)")
    #         .replace("_cbo", " (CBO)")
    #         .replace("SSTF_", "SSTF ")
    #     )
    # )
    # Add title
    fig.update_layout(
        title_text="Social Security Trust Fund Revenues and Outlays"
    )
    fig.show()
