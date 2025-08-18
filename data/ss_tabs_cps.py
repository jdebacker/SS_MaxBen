# %%
import pandas as pd
import os
from statsmodels.stats.weightstats import DescrStatsW

cur_dir = os.path.dirname(os.path.abspath(__file__))
# puf_path = os.path.join(cur_dir, "..", "PSLFoundation", "DataAssets", "PUF_contract_files" 'puf_2015.csv')


# %%
# Read CPS data for 2023
# Download from: https://www.nber.org/research/data/current-population-survey-cps-supplements-annual-demographic-file
# Codebook: https://data.nber.org/cps_supp_1/raw/2023/march/asec2023_ddl_pub_full.pdf
cps_path = os.path.join(cur_dir, "asecpub23csv", "hhpub23.csv")

df = pd.read_csv(cps_path, dtype=str)

# cast HSSVAL as float
df["HSSVAL"] = df["HSSVAL"].astype(float)
# cast HSUP_WGT as float
df["HSUP_WGT"] = df["HSUP_WGT"].astype(float)

# HSS_YN -- SS income, yes or no
# HSSVAL -- SS amount
# A_AGE

"""
RESNSS1
588
1 (0:8)
What were the reasons (you/name) (was/were) getting Social
Security Income last year?
Values: 0 = niu
1 = retired
2 = disabled (adult or child)
3 = widowed
4 = spouse
5 = surviving child
6 = dependent child
7 = on behalf of surviving, dependent, or disabled
child(ren)
8 = other (adult or child)
"""

"""
FKIND
31
1 (1:3)
Kind of family
Values: 1=Married couple family
2=Male reference person
3=Female reference person
"""

"""
HRHTYPE
72
2 (00:10)
Household type
Values: 00 = Non-interview household
01 = Married couple primary family (neither spouse in
Armed Forces)
02 = Married couple primary family (one spouse in Armed
Forces)
03 = Unmarried civilian male primary family householder
04 = Unmarried civilian female primary family householder
05 = Primary family household - reference person in
Armed Forces and unmarried
06 = Civilian male nonfamily householder
07 = Civilian female nonfamily householder
08 = Nonfamily householder household - reference person
in Armed Forces
09 = Group quarters with actual families (This is new in
1994)
10 = Group quarters with secondary individuals only
"""

weighted_stats = DescrStatsW(df[["HSSVAL"]], weights=df["HSUP_WGT"])

# Find fraction of SS benefits that accrue to households with > 100k in benefits
df_high_benefit = df[df["HSSVAL"].astype(float) > 100000]
high_income_fraction = (
    df_high_benefit.HSSVAL * df_high_benefit.HSUP_WGT
).sum() / (df.HSSVAL * df.HSUP_WGT).sum()
print(
    "Fraction of SS benefits to high-benefit households:", high_income_fraction
)
