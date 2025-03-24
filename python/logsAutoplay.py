#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 11:05:19 2023

@author: reha.tuncer
"""
# %%%
# packages & data
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats.mstats import winsorize
from scipy.stats import mannwhitneyu
from scipy.stats import ranksums

# %%%
# CHOOSE DATA
# cleaned dataset from the final data collection
df = pd.read_csv("autoplay.csv")

# combined dataset with the last pretest
# df = pd.read_csv("autoplay_final.csv")

# %%%
# LOGGED MEASUREMENTS (USE FOR ANALYSIS)
# store session data & clean json notation
x = 0
i = 0
sess = []
pattern = r"(?=(?!\:)\,(?!\s[r]))"
for i in range(len(df)):
    sess.append(re.split(r"(?=(?!\:)\,(?!\s[rd]))", df.session.iloc[i]))
for i in range(len(sess)):
    for x in range(len(sess[i])):
        sess[i][x] = sess[i][x].replace("\\", "")
        sess[i][x] = sess[i][x].replace(",", "")
        sess[i][x] = sess[i][x].replace('"', "")
        sess[i][x] = sess[i][x].replace("[", "")
        sess[i][x] = sess[i][x].replace("]", "")

# separate time & activity
time = []
activity = []
id = []
z = []
for i in range(len(sess)):
    for x in range(len(sess[i])):
        if sess[i][x][0] != " ":
            time.append(float(sess[i][x].split(maxsplit=1)[0]))
            activity.append(sess[i][x].split(maxsplit=1)[1])
            id.append(i)
            z = [time, activity, id]

# calculate time for each activity
for w in range(len(z[0])):
    if z[1][w] == "start":
        save = w
    if z[1][w] != "start":
        if z[2][w] == z[2][w - 1]:
            z[0][w] = round(float(z[0][w] - z[0][save]), 1)

# find task switches & mouseout
s = []
s2 = []
out = []
vid = []
for w in range(len(z[0])):
    if "start" in z[1][w]:
        s.append([0, z[1][w], z[2][w]])
        s2.append([0, z[1][w], z[2][w]])
    if "end" in z[1][w]:
        if "ended" not in z[1][w]:
            s.append([z[0][w], z[1][w], z[2][w]])
            s2.append([z[0][w], z[1][w], z[2][w]])
    if "current_task:" in z[1][w]:
        s.append([z[0][w], z[1][w], z[2][w]])
        s2.append([z[0][w], z[1][w], z[2][w]])
    if "mouseout:true" in z[1][w]:
        s.append([z[0][w], z[1][w], z[2][w]])
        out.append([z[0][w], z[1][w], z[2][w]])
    if "video" in z[1][w]:
        vid.append([z[0][w], z[1][w], z[2][w]])

s = pd.DataFrame(s)
s2 = pd.DataFrame(s2)
out = pd.DataFrame(out)
vid = pd.DataFrame(vid)
# find mouseout:true inactive seconds
conditions = [
    (s[1] == "mouseout:true") & (s[1].shift(1) == "start"),
    (s[1] == "mouseout:true") & (s[1].shift(1) == "current_task:watching"),
    (s[1] == "mouseout:true") & (s[1].shift(1) == "current_task:typing"),
    (s[1] == "mouseout:true") & (s[1].shift(1) == "mouseout:true"),
]

choices = ["not_typing", "not_watching", "not_typing", "check_again"]
s["task"] = np.select(conditions, choices, default=np.nan)

last_value = None
for i, row in s.iterrows():
    if row[1] == "mouseout:true":
        if last_value is not None:
            s.at[i, "task"] = last_value
        else:
            last_value = row["task"]
    else:
        last_value = None

melt = s.groupby(2)["task"].agg(list).reset_index()
melt["not_watching"] = melt["task"].apply(lambda x: x.count("not_watching"))
melt["not_typing"] = melt["task"].apply(lambda x: x.count("not_typing"))

# calculate end time per participant
end_time = s.groupby(2)[[0, 1]].agg(list).reset_index()
end_time["end_time"] = end_time[0].apply(lambda x: max(x))

# calculate time spent on the typing and watching tasks
ty = []
for w in range(len(s2)):
    if w > 0:
        if s2[2][w] == s2[2][w - 1]:
            if s2[1][w] == "current_task:watching":
                if s2[1][w - 1] == "current_task:typing" or s2[1][w - 1] == "start":
                    ty.append([s2[0][w] - s2[0][w - 1], s2[2][w]])
    if s2[1][w] == "end":
        if s2[1][w - 1] == "current_task:typing":
            ty.append([s2[0][w] - s2[0][w - 1], s2[2][w]])
        if s2[1][w - 1] == "start":
            ty.append([s2[0][w], s2[2][w]])

watch = []
for w in range(len(s2)):
    if w > 0:
        if s2[2][w] == s2[2][w - 1]:
            if s2[1][w] == "current_task:typing":
                if s2[1][w - 1] == "current_task:watching":
                    watch.append([s2[0][w] - s2[0][w - 1], s2[2][w]])
    if s2[1][w] == "end":
        if s2[1][w - 1] == "current_task:watching":
            watch.append([s2[0][w] - s2[0][w - 1], s2[2][w]])

# convert typing to df and merge
typing = {}
for value in ty:
    if value[1] not in typing:
        typing[value[1]] = value[0]
    else:
        typing[value[1]] += value[0]
typing = pd.DataFrame(list(typing.values()))
typing = round(typing, 1)
df["typing_log"] = typing[0]

# convert watching to df and merge
result = []
current_sum = watch[0][0]
current_index = watch[0][1]
for row in watch[1:]:
    if row[1] == current_index:
        current_sum += row[0]
    else:
        result.append([current_sum, current_index])
        for i in range(current_index + 1, row[1]):
            result.append([0, i])
        current_sum = row[0]
        current_index = row[1]
result.append([current_sum, current_index])

df["watching_log"] = pd.DataFrame(list(result))[0]

# other variables merged
df["end_time_log"] = end_time["end_time"]
df["notWatching_log"] = melt["not_watching"]
df["notTyping_log"] = melt["not_typing"]

df["end_time_log_increase"] = df["end_time_log"]-1200
# %%% compare 
# with the original measures planned for the study
df["typing"] = df["typing"] + df["notTyping"]
df["end_time"] = df["typing"] + df["notWatching"] + df["watching"]

# %%%
#  difference between 2 measures
variables = [
    "notTyping",
    "typing",
    "watching",
    "notWatching",
    "end_time"
]

for variable in variables:
    sns.relplot(df, x=f"{variable}", y=f"{variable}_log")
    print((df[[f"{variable}", f"{variable}_log"]].corr()))
    
# %%%
#  relation with end_time
variables = [
    "notTyping_log",
    "typing_log",
    "watching_log",
    "notWatching_log",
    "videoPausedFor"
]

for variable in variables:
    sns.relplot(df, x=f"{variable}", y="end_time_log_increase")
    print(round(df[f"{variable}"].corr(df['end_time_log_increase']),3))

# sns.relplot(df[df["treatment"]=="autoplayOff"], x="watching_log", y="end_time_log_increase")
# sns.relplot(df[df["treatment"]=="autoplayOn"], x="watching_log", y="end_time_log_increase")
# sns.relplot(df[df["treatment"]=="autoplayOff"], x="typing_log", y="end_time_log_increase")
# sns.relplot(df[df["treatment"]=="autoplayOn"], x="typing_log", y="end_time_log_increase")

# print(round(df[df["treatment"]=="autoplayOff"]["watching_log"].corr(df['end_time_log_increase']),3))
# print(round(df[df["treatment"]=="autoplayOn"]["watching_log"].corr(df['end_time_log_increase']),3))
# print(round(df[df["treatment"]=="autoplayOff"]["typing_log"].corr(df['end_time_log_increase']),3))
# print(round(df[df["treatment"]=="autoplayOn"]["typing_log"].corr(df['end_time_log_increase']),3))

# %%
# t-test on base variables and descriptive stats

# df_1300 = df[df["end_time2"] < 1300]
# df_1250 = df[df["end_time2"] < 1250]

# new datasets
# df["diff_watching"] = abs(df["watching"] - df["watching_log"])
# df["diff_typing"] = abs(df["typing"] - df["typing_log"])
# df["diff_not_watching"] = abs(df["notWatching"] - df["notWatching_log"])
# df["diff_not_typing"] = abs(df["notTyping"] - df["notTyping_log"])

# # df_t1 = df[df["measurement_err"] < 60]
# df_t2 = df[df["end_time"] < 1250]
# cut_end_time = df[df["end_time"] >= 1250]

# df_t3 = df[df["notWatching_log"]+df["notTyping_log"] < 60]
# cut_inactive = df[df["notWatching_log"]+df["notTyping_log"] >= 60]


# cut_end = df[df["end_time_log"] >= 1300]
# cut_mes = df[df["measurement_err"] >= 60]

bootstrapped_1 = df.sample(n=500, replace=True)
bootstrapped_2 = df.sample(n=600, replace=True)
bootstrapped_3 = df.sample(n=700, replace=True)
bootstrapped_4 = df.sample(n=800, replace=True)

variables = [
    "notTyping_log",
    "typing_log",
    "watching_log",
    "notWatching_log",
    # "diff_watching",
    # "diff_typing",
    # "diff_not_watching",
    # "diff_not_typing",
    # "watching",
    # "notWatching",
    "end_time_log",
    # "end_time",
    "timeChoice",
    "tabCounter",
    "typeCount",
    "watchedVideo",
    "videoPausedFor"
    # "measurement_err"
]
results_dfs = []

dataframes = [df]

for dataframe in dataframes:
    results = []
    for var in variables:
        t_stat, p_value = stats.ttest_ind(
            dataframe[var][dataframe["treatment"] == "autoplayOff"],
            dataframe[var][dataframe["treatment"] == "autoplayOn"],
            equal_var=False,
        )
        u1, p = mannwhitneyu(dataframe[var][dataframe["treatment"] == "autoplayOff"],
                             dataframe[var][dataframe["treatment"] == "autoplayOn"],
                             method="auto")
        u1 = round(u1,3)
        p = round(p,3)        
        p_value = round(p_value,3)    
        t_stat = round(t_stat,3)
        stat, pval = ranksums(dataframe[var][dataframe["treatment"] == "autoplayOff"],
                              dataframe[var][dataframe["treatment"] == "autoplayOn"],)
        stat = round(stat, 3)
        pval = round(pval,3)
        mean_off = round(dataframe[var][dataframe["treatment"] == "autoplayOff"].mean(),1)
        mean_on = round(dataframe[var][dataframe["treatment"] == "autoplayOn"].mean(),1)
        median_off = round(dataframe[var][dataframe["treatment"] == "autoplayOff"].median(),1)
        median_on = round(dataframe[var][dataframe["treatment"] == "autoplayOn"].median(),1)
        mad_on = round(stats.median_abs_deviation(dataframe[var][dataframe["treatment"] == "autoplayOn"]),1)
        mad_off = round(stats.median_abs_deviation(dataframe[var][dataframe["treatment"] == "autoplayOff"]),1)
        std_off = round(dataframe[var][dataframe["treatment"] == "autoplayOff"].std(),1)
        std_on = round(dataframe[var][dataframe["treatment"] == "autoplayOn"].std(),1)
        results.append(
            [
                var,
                p_value,
                p,
                pval,
                mean_off,
                mean_on,
                std_off,
                std_on,
                median_off,
                median_on,
                mad_off,
                mad_on,

            ]
        )

    results_df = pd.DataFrame(
        results,
        columns=[
            "Variable",
            "p (t-test)",
            "p (Mann-Whitney-U)",
            "p (Wilcoxon)",
            "Mean (Off)",
            "Mean (On)",
            "Std (Off)",
            "Std (On)",
            "Median (Off)",
            "Median (On)",
            "MAD (Off)",
            "MAD (On)",

        ],
    )
    results_dfs.append(results_df)

for i, results_df in enumerate(results_dfs):
    print(
        f"Results with n={len(dataframes[i])} obs with {dataframes[i].treatment.describe()[3]} in {dataframes[i].treatment.describe()[2]}"
    )
    print(results_df.to_string(index=False))

# %%% inspect 

variables = [
    "notTyping_log",
    "typing_log",
    "watching_log",
    "notWatching_log",
    "end_time_log",
    "timeChoice",
    "tabCounter",
    "typeCount",
    "watchedVideo",
]
results = []

for var in variables:
    t_stat, p_value = stats.ttest_ind(
        cut_end[var],
        df[var],
        equal_var=False,
    )
    p_value = round(p_value,3)    
    t_stat = round(t_stat,3)
    mean_cut_end = round(cut_end[var].mean(),1)
    mean_df = round(df[var].mean(),1)
    median_cut_end = round(cut_end[var].median(),1)
    median_df = round(df[var].median(),1)
    std_cut_end = round(cut_end[var].std(),1)
    std_df = round(df[var].std(),1)
    results.append(
        [
            var,
            p_value,
            mean_cut_end,
            mean_df,
            std_cut_end,
            std_df,
            median_cut_end,
            median_df,
            t_stat,
        ]
    )

results_df = pd.DataFrame(
    results,
    columns=[
        "Variable",
        "p-value",
        "Mean (cut_end)",
        "Mean (df)",
        "Std (cut_end)",
        "Std (df)",
        "Median (cut_end)",
        "Median (df)",
        "t-statistic",
    ],
)

print(results_df.to_string(index=False))

