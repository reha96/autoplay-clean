#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 17:26:35 2023

"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy import stats
from matplotlib import pyplot as plt
# from patsy.contrasts import ContrastMatrix
import statsmodels.api as sm
from openpyxl import Workbook
import statsmodels.stats.multicomp as mc
import pingouin as pg

np.random.seed(0)
df = pd.read_excel("new_data_timers.xlsx", "1")


"""
CLEAN DATA (no need to run since new_data_timers.xlsx is being used)
"""

# df.filter(like='NASASUM')  # FILTER by name and get COLUMN
# df.filter(like='AGE').astype(str).describe()  # CONVERT to STR and DESCRIBE
# df.filter(like='GEN').astype(str).describe()
# df.filter(like='EDU').astype(str).describe()
# df.filter(like='RAND').astype(str).describe()

# df.filter(like='AGE').value_counts()  # counts of each value
# df.filter(like='GEN').value_counts()
# df.filter(like='EDU').value_counts()

# y1 = str(df.filter(like='NASASUM').columns[0])
# y2 = str(df.filter(like='NASAFRUST').columns[0])
# y3 = str(df.filter(like='BENSUM').columns[0])
# y4 = str(df.filter(like='UXPRAG').columns[0])
# y5 = str(df.filter(like='UXHED').columns[0])
# x1 = str(df.filter(like='AGE').columns[0])
# x2 = str(df.filter(like='GEN').columns[0])
# x3 = str(df.filter(like='EDU').columns[0])
# t = str(df.filter(like='RAND').columns[0])

# df.rename(columns={y1: 'NASASUM'}, inplace=True)
# df.rename(columns={y2: 'NASAFRUST'}, inplace=True)
# df.rename(columns={y3: 'BENSUM'}, inplace=True)
# df.rename(columns={y4: 'UXPRAG'}, inplace=True)
# df.rename(columns={y5: 'UXHED'}, inplace=True)
# df.rename(columns={x1: 'AGE'}, inplace=True)
# df.rename(columns={x2: 'GEN'}, inplace=True)
# df.rename(columns={x3: 'EDU'}, inplace=True)
# df.rename(columns={t: 'RAND'}, inplace=True)

# for i in range(len(df)):  # Distrubute GENDER category Other to Female and Male
#     if df.GEN[i] == 3:
#         test = np.random.randint(1, 2)
#         df.GEN[i] = test

# # df['GEN'] = df['GEN'].map({1: 'Female', 2: 'Male' })

# for i in range(len(df)):  # Distrubute AGE category 4 and 5 to 3
#     if df.AGE[i] == 4 or df.AGE[i] == 5:
#         df.AGE[i] = 3

# # df['AGE'] = df['AGE'].map({1: '18-24', 2: '25-34', 3: '35+' })

# # Distrubute EDU category 1 (< highschool) to 2 (highschool), 4 (Associate Degree) to 5 (Bachelor)
# for i in range(len(df)):
#     if df.EDU[i] == 1:
#         df.EDU[i] = 2
#     if df.EDU[i] == 4:
#         df.EDU[i] = 5
# df.EDU = df.EDU.map({2: 1, 3: 2, 5: 3, 6: 4})

# # RAND 1 = control, 2 = stock, 3 = timer
# df.RAND = df.RAND.map({1: 3, 3: 1})

"""
Analysis
"""


# welch anova's

for x in ('NASASUM', 'NASAFRUST', 'BENSUM', 'UXPRAG', 'UXHED'):
    for y in ('AGE', 'GEN', 'EDU'):
        print(x+' ' + y)
        print(pg.welch_anova(dv=x, between=y, data=df))


# regressions (not reported)

model = smf.ols(
    formula='NASASUM ~ C(RAND) + C(AGE) + C(GEN) + C(EDU)', data=df).fit(cov_type='HC3')
results = model.summary()
print(results)

model = smf.ols(
    formula='NASAFRUST ~ C(RAND) + C(AGE) + C(GEN) + C(EDU)', data=df).fit(cov_type='HC3')
results = model.summary()
print(results)

model = smf.ols(
    formula='BENSUM ~ C(RAND) + NASAFRUST + C(AGE) + C(GEN) + C(EDU)', data=df).fit(cov_type='HC3')
results = model.summary()
print(results)

model = smf.ols(
    formula='UXPRAG ~ C(RAND) + C(AGE) + C(GEN) + C(EDU)', data=df).fit(cov_type='HC3')
results = model.summary()
print(results)

model = smf.ols(
    formula='UXHED ~ C(RAND) + C(AGE) + C(GEN) + C(EDU)', data=df).fit(cov_type='HC3')
results = model.summary()
print(results)


# multiple comparisons

# BENSUM x AGE
comp = mc.MultiComparison(df.BENSUM, df.AGE)
post_hoc_res = comp.tukeyhsd()
print(post_hoc_res.summary())
plt.figure(4)
post_hoc_res.plot_simultaneous(ylabel="AGE", xlabel="BENSUM")

# UXHED x GENDER
comp = mc.MultiComparison(df.UXHED, df.GEN)
post_hoc_res = comp.tukeyhsd()
print(post_hoc_res.summary())
plt.figure(5)
post_hoc_res.plot_simultaneous(ylabel="GEN", xlabel="UXHED")


# chi2 tests for independence

# AGE
crosstab = pd.crosstab(df.AGE, df.RAND)
chi2, p, dof, expected = stats.chi2_contingency(crosstab)
p

# GEN
crosstab = pd.crosstab(df.GEN, df.RAND)
chi2, p, dof, expected = stats.chi2_contingency(crosstab)
p

# EDU
crosstab = pd.crosstab(df.EDU, df.RAND)
chi2, p, dof, expected = stats.chi2_contingency(crosstab)
p


# Histograms of demographic variables

# UXHED x GEN

plt.figure(0)
kwargs = dict(alpha=0.5, bins=5, density=True, cumulative=True)
plt.hist(df.loc[df.GEN == 1, 'UXHED'], **kwargs, color='g', label='female')
plt.hist(df.loc[df.GEN == 2, 'UXHED'], **kwargs, color='b', label='male')
plt.gca().set(xlabel='UXHED')
plt.legend()

plt.figure(1)
kwargs = dict(alpha=0.5, bins=5)
plt.hist(df.loc[df.GEN == 1, 'UXHED'], **kwargs, color='g', label='female')
plt.hist(df.loc[df.GEN == 2, 'UXHED'], **kwargs, color='b', label='male')
plt.gca().set(xlabel='UXHED')
plt.legend()

# BENSUM x AGE

plt.figure(2)
kwargs = dict(alpha=0.5, bins=5, density=True, cumulative=True)
plt.hist(df.loc[df.AGE == 1, 'BENSUM'], **kwargs, color='g', label='age 18-24')
plt.hist(df.loc[df.AGE == 2, 'BENSUM'], **kwargs, color='b', label='age 25-34')
plt.hist(df.loc[df.AGE == 3, 'BENSUM'], **kwargs, color='r', label='age 35-44')
plt.gca().set(xlabel='BENSUM')
plt.legend()

plt.figure(3)
kwargs = dict(alpha=0.5, bins=5, density=True)
plt.hist(df.loc[df.AGE == 1, 'BENSUM'], **kwargs, color='g', label='age 18-24')
plt.hist(df.loc[df.AGE == 2, 'BENSUM'], **kwargs, color='b', label='age 25-34')
plt.hist(df.loc[df.AGE == 3, 'BENSUM'], **kwargs, color='r', label='age 35-44')
plt.gca().set(xlabel='BENSUM')
plt.legend()

# code to create EXCEL sheet: new_data_timers.xlsx

# d = Workbook()
# d.save(filename='new_data_timers.xlsx')

# with pd.ExcelWriter('new_data_timers.xlsx', engine="openpyxl", mode='a') as writer:
#     df.to_excel(writer, header=True, index=True, sheet_name='1')
