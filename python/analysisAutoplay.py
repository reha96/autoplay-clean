#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 11:05:19 2023

@author: reha.tuncer
"""
# %%
# packages & data
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats.mstats import winsorize

#  %% CHOOSE DATA
# cleaned dataset from the last data collection
df = pd.read_csv("autoplay.csv")

# combined dataset with the previous pretest
# df = pd.read_csv("autoplay_final.csv")

# %% MPL preparation

# df2 = pd.read_csv('mpl2nd.csv')
# df2.columns = df2.columns.str.replace('browser.', '')
# df2.columns = df2.columns.str.replace('platform.', '')
# df2.columns = df2.columns.str.replace('timespent', '')
# df2 = df2.drop(columns=['laborTime', 'leisureTime', 'transcription'])

# df1 = pd.read_csv('mpl1st.csv')
# df1.columns = df1.columns.str.replace('platform.', '')
# df1 = df1[df1.ID.str.len() > 23]
# selected_columns = df1.filter(like='MPL').columns
# df_with_selected_columns = df1[selected_columns].join(df1['ID'])
# df_with_selected_columns = df_with_selected_columns[df_with_selected_columns.ID.str.len(
# ) > 23].reset_index(drop=True)

# df2[selected_columns] = df_with_selected_columns[selected_columns]

#### clean MPL data
db = pd.read_csv("MPL.csv")

# %% get data
#### the last pretest data with the same setup
df0 = pd.read_csv("participants_04.csv")
df0 = df0[df0.ID.str.len() > 23]
df0 = df0.reset_index(drop=True)
df0.columns = df0.columns.str.replace("browser.", "")
df0.columns = df0.columns.str.replace("platform.", "")
df0.columns = df0.columns.str.replace("timespent", "")
df0 = df0.drop(columns=["__v", "_id", "laborTime", "leisureTime", "transcription"])

#### final dataset
df = pd.read_csv("final_2ses.csv")
df.columns = df.columns.str.replace("browser.", "")
df.columns = df.columns.str.replace("platform.", "")
df.columns = df.columns.str.replace("timespent", "")
df = df.drop(columns=["laborTime", "clikcedOkToSwitch", "leisureTime", "transcription"])

# drop participants who stopped at the 2nd page
tried = df[df.ID.str.len() == 17]
df = df[df.ID.str.len() > 23]
df = df.reset_index(drop=True)


# %% OPTIONAL browser // network speed // platform // OS
# check speed > 30
fast = tried[tried.speed > 30]

# check browser Chrome or Edge
chrome = fast[fast.browser == "Chrome"]
edge = fast[fast.browser == "Microsoft Edge"]
m = [chrome, edge]
m = pd.concat(m)

# check browser OS
m = m[m.os != "Android"]

# check platform
m = m[m.platform == "desktop"]


# %% drop participants who did not finish end survey
noapprove = df[df["birthyear"].isnull()]
df = df[~df["birthyear"].isnull()]  # drop empty entries
df = df.reset_index(drop=True)
for i in range(len(df)):
    if type(df["userTranscription"][i]) is float:
        df["userTranscription"][i] = str(np.nan)

# same for the last pretest data
try:
    noapprove0 = df0[df0["birthyear"].isnull()]
    df0 = df0[~df0["birthyear"].isnull()]  # drop empty entries
    df0 = df0.reset_index(drop=True)
    for i in range(len(df0)):
        if type(df0["userTranscription"][i]) is float:
            df0["userTranscription"][i] = str(np.nan)
    # merge both sets
    df = pd.concat([df, df0], axis=0, ignore_index=True)
except:
    print("df0 does not exist")
# %% drop failed attention checks
failcheck = df[(df["attention1"] + df["attention2"]) >= 4]
df = df[(df["attention1"] + df["attention2"]) < 4]  # drop more than 4 mistake
df = df.reset_index(drop=True)

# df0 = df0[(df0['attention1']+df0['attention2'])
#           < 4]  # drop more than 4 mistake
# df0 = df0.reset_index(drop=True)


# %% drop self-reported network issues
badconnection = df[df["connection"].str.contains("Bad")]  # drop bad connection entries
df = df[~df["connection"].str.contains("Bad")]
df = df.reset_index(drop=True)

# %% drop self-reported other activities
otheractivity = df[
    df["trueWatch"].str.contains("False")
]  # drop people doing other activities
df = df[~df["trueWatch"].str.contains("False")]
df = df.reset_index(drop=True)


# %% drop time choice binding

lotwin = df[df["lottery"].str.contains("lotteryWin")]
df = df[~df["lottery"].str.contains("lotteryWin")]  # drop lotteryWin entries

# df0 = df0[~df0['lottery'].str.contains(
#     "lotteryWin")]


# %% sample from old db videoPausedFor


# list = pd.DataFrame(db["browser.videoPausedFor"]
#                     [db["treatment"] == 'autoplayOff'].reset_index(drop=True))

# a = df["platform.videoPausedFor"][df.treatment == 'autoplayOff'].reset_index(
#     drop=True)
# # list.sample(n=1)['browser.videoPausedFor']
# for i in range(len(df["platform.videoPausedFor"][df.treatment == 'autoplayOff'])):
#     a[i] = list.sample(n=1)['browser.videoPausedFor']

# df["platform.videoPausedFor"][df.treatment == 'autoplayOff'] = a


# """
# Manually correct for videoPausedFor by 2 sec per watched video
# """


# df["platform.videoPausedFor"][df.treatment =='autoplayOff'] = df["platform.watchedVideo"][df.treatment == 'autoplayOff']*2


# %%
# correction for tasks
df["pure_watch"] = pd.DataFrame(df["watching"] - df["videoPausedFor"]).rename(
    columns={0: "pure_watch"}
)
df["typing"] = pd.DataFrame(df["typing"] + 2).rename(columns={0: "typing"})

# %%
# total time spent at each task
df["watch_total"] = pd.DataFrame(
    df["watching"] + df["notWatching"] + df["videoPausedFor"]
).rename(columns={0: "watch_total"})
df["type_total"] = pd.DataFrame(df["typing"] + df["notTyping"]).rename(
    columns={0: "type_total"}
)

# %%
# get variables to compare 2 measures (see below)
# total time away from tasks
df["out_sum"] = df["notTyping"] + df["notWatching"]

# end time
df["end_time"] = df["watch_total"] + df["type_total"]

# %%
# time choice vs realized watching
df["watch_choice"] = 1200 - df["timeChoice"]
df["increase_watching"] = df["watch_total"] - df["watch_choice"]

# %%
# winsorize
df["notWatching_w"] = winsorize(df["notWatching"], limits=[0, 0.1])

# # correction for not being at the task
df["pure_watch_w"] = pd.DataFrame(
    df["watching"] - df["videoPausedFor"] - df["notWatching_w"]
).rename(columns={0: "pure_watch_w"})

df["increase_watching_w"] = df["pure_watch_w"] - df["watch_choice"]


# %%
# look at smaller subsamples bc
sns.relplot(df, x="watch_total", y="type_total", hue="treatment")
# sns.relplot(df, x="notWatching", y='notTyping',hue="treatment")

df_1300 = df[df["end_time"] < 1300]
df_1250 = df[df["end_time"] < 1250]
df_1225 = df[df["end_time"] < 1225]
df_1210 = df[df["end_time"] < 1210]


# %%
# t-test on base variables and descriptive stats
variables = [
    "content",
    "watch_choice",
    "increase_watching",
    "watchedVideo",
    "watching",
    "pure_watch",
    "watch_total",
    "type_total",
    "typing",
    "videoPausedFor",
    "end_time",
    "notWatching",
    "notTyping",
]
results_dfs = []

dataframes = [df, df_1250, df_1225]

for dataframe in dataframes:
    results = []
    for var in variables:
        t_stat, p_value = stats.ttest_ind(
            dataframe[var][dataframe["treatment"] == "autoplayOff"],
            dataframe[var][dataframe["treatment"] == "autoplayOn"],
            equal_var=False,
        )
        if p_value < 0.0001:
            p_value = 0.000
        mean_off = dataframe[var][dataframe["treatment"] == "autoplayOff"].mean()
        mean_on = dataframe[var][dataframe["treatment"] == "autoplayOn"].mean()
        median_off = dataframe[var][dataframe["treatment"] == "autoplayOff"].median()
        median_on = dataframe[var][dataframe["treatment"] == "autoplayOn"].median()
        mad_on = stats.median_absolute_deviation(dataframe[var][dataframe["treatment"] == "autoplayOn"], scale=1)
        mad_off = stats.median_absolute_deviation(dataframe[var][dataframe["treatment"] == "autoplayOff"], scale=1)
        std_off = dataframe[var][dataframe["treatment"] == "autoplayOff"].std()
        std_on = dataframe[var][dataframe["treatment"] == "autoplayOn"].std()
        results.append(
            [
                var,
                p_value,
                mean_off,
                mean_on,
                std_off,
                std_on,
                median_off,
                median_on,
                t_stat,
            ]
        )

    results_df = pd.DataFrame(
        results,
        columns=[
            "Variable",
            "p-value",
            "Mean (autoplayOff)",
            "Mean (autoplayOn)",
            "Std (autoplayOff)",
            "Std (autoplayOn)",
            "Median (autoplayOff)",
            "Median (autoplayOn)",
            "t-statistic",
        ],
    )
    results_dfs.append(results_df)

for i, results_df in enumerate(results_dfs):
    print(
        f"Results with n={len(dataframes[i])} obs with {dataframes[i].treatment.describe()[3]} in {dataframes[i].treatment.describe()[2]}"
    )
    print(results_df.to_string(index=False))

# %% Latex table output

latex_table = results_df.style.to_latex()
print(latex_table)

# %% MPL

first_occurrences = []
for index, row in db.iterrows():
    prev_value = row["MPL1"][0]
    for i in range(2, 10):
        column_name = f"MPL{i}"
        if row[column_name][0] != prev_value:
            first_occurrences.append(row[column_name])
            break

db_mpl = db[["MPL1", "MPL2", "MPL3", "MPL4", "MPL5", "MPL6", "MPL7", "MPL8", "MPL9"]]

# Count the number of occurrences of unique values for each column
counts = db_mpl.apply(lambda x: x.value_counts())

# Plot the histograms
counts.plot(kind="bar", subplots=True)
plt.show()

# %% histograms
sns.displot(df, x="end_time", hue="treatment", kde=True)
sns.displot(df, x="content", hue="treatment", kde=True)
sns.displot(df, x="timeChoice", hue="treatment", kde=True)
sns.displot(df, x="increaseType", hue="treatment", kde=True)
sns.displot(df, x="watchedVideo", hue="treatment", kde=True)
sns.displot(df, x="watchTime", hue="treatment", kde=True)
sns.displot(df, x="normalizedinc", hue="treatment", kde=True)
sns.displot(df, x="actualType", hue="treatment", kde=True)
sns.displot(df[df.notWatching > 50], x="notWatching", hue="treatment", kde=True)


# other
sns.lmplot(data=df, x="timeChoice", y="typeTime", hue="treatment")
sns.displot(df, x="notWatching", hue="treatment")

# mpl first switch
df_sorted = pd.DataFrame(first_occurrences).sort_values(by=0)
ax = sns.displot(df_sorted, x=0, kde=True)
ax.set_xticklabels(rotation=90)
plt.show()

# sns.catplot(df0, x="browser.watchedVideo", y="treatment", kind="boxen")
# sns.catplot(df0, x="typeTime", y="treatment", kind="boxen")
# sns.catplot(df0, x="watchTime", y="treatment", kind="boxen")


# %%% # 2ND MEASUREMENT PART
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

# %%%
# separate time & activity
t = []
a = []
m = []
z = []
for i in range(len(sess)):
    for x in range(len(sess[i])):
        if sess[i][x][0] != " ":
            t.append(float(sess[i][x].split(maxsplit=1)[0]))
            a.append(sess[i][x].split(maxsplit=1)[1])
            m.append(i)
            z = [t, a, m]

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

s = pd.DataFrame(s)
s2 = pd.DataFrame(s2)
out = pd.DataFrame(out)

# %%% find backup measure inactive seconds

conditions = [
    (s[1] == "mouseout:true") & (s[1].shift(1) == "start"),
    (s[1] == "mouseout:true") & (s[1].shift(1) == "current_task:watching"),
    (s[1] == "mouseout:true") & (s[1].shift(1) == "current_task:typing"),
]

choices = ["start", "not_watching", "not_typing"]

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

# %%%
# calculate end time per participant
end_time = s.groupby(2)[[0, 1]].agg(list).reset_index()
end_time["end_time"] = end_time[0].apply(lambda x: max(x))

# calculate total mouseout duration per participant
n_out = out.groupby(2)[[0, 1]].agg(list).reset_index()
n_out.columns = ["Column 2", "Column 0", "Column 1"]
n_out["out_sum"] = n_out["Column 0"].apply(len)
n_out = n_out.set_index("Column 2")

# find the missing indices
missing_indices = set(range(n_out.index.min(), n_out.index.max() + 1)).difference(
    n_out.index
)

# create a new dataframe with the missing indices and fill with 0's
missing_df = pd.DataFrame(
    0, index=pd.Index(missing_indices, name="Column 2"), columns=n_out.columns
)

# concatenate the two dataframes and sort by index
n_out = pd.concat([n_out, missing_df]).sort_index()

# %%%
# calculate time spent on the typing and watching tasks
ty = []
watch = []
for w in range(len(s2)):
    if w > 0:
        if s2[2][w] == s2[2][w - 1]:
            if s2[1][w] == "current_task:watching":
                if s2[1][w - 1] == "current_task:typing" or s2[1][w - 1] == "start":
                    ty.append([s2[0][w] - s2[0][w - 1], s2[2][w]])
            if s2[1][w] == "current_task:typing":
                if s2[1][w - 1] == "current_task:watching" or s2[1][w - 1] == "start":
                    watch.append([s2[0][w] - s2[0][w - 1], s2[2][w]])
    if s2[1][w] == "end":
        if s2[1][w - 1] == "current_task:typing":
            ty.append([s2[0][w] - s2[0][w - 1], s2[2][w]])
        if s2[1][w - 1] == "current_task:watching":
            watch.append([s2[0][w] - s2[0][w - 1], s2[2][w]])
        if s2[1][w - 1] == "start":
            ty.append([s2[0][w], s2[2][w]])


# %%%
# convert to df and merge
backup = {}
for value in ty:
    if value[1] not in backup:
        backup[value[1]] = value[0]
    else:
        backup[value[1]] += value[0]
backup = pd.DataFrame(list(backup.values()))
backup = backup.rename(columns={0: "typing"})
backup = round(backup, 1)

# %%%
backup_2 = {}
for value in watch:
    if value[1] not in backup_2:
        backup_2[value[1]] = value[0]
    else:
        backup_2[value[1]] += value[0]

backup_2 = pd.DataFrame(list(backup_2.values()))
backup_2 = backup_2.rename(columns={0: "watching"})
backup_2 = round(backup_2, 1)

# %%%
df["watching2"] = backup_2["watching"]
df["watching2"] = df["watching2"].fillna(0)
df["typing2"] = backup["typing"]
df["out_sum2"] = n_out["out_sum"]
df["end_time2"] = end_time["end_time"]
df["notWatching2"] = melt["not_watching"]
df["notTyping2"] = melt["not_typing"]
df["watch_total2"] = df["watching2"] + df["notWatching2"]
df["type_total2"] = df["typing2"] + df["notTyping2"]

# %%%
#  difference between 2 measures
variables = [
    "type_total",
    "notTyping",
    "typing",
    "watching",
    "watch_total",
    "notWatching", 
    "end_time",
]
diff = pd.DataFrame()

for variable in variables:
    sns.relplot(df, x=f"{variable}", y=f"{variable}2")

# diff['out_sum_log'] = n_out["out_sum"]
# diff['out_sum_timer'] = df["out_sum"]
# diff['end_time_log'] = backup["end_time"]
# diff['end_time_timer'] = df["end_time"]

# %%% plot

# diff_1250 = diff[diff['end_time_log']<1250]

df["end_time_log"] = diff["end_time_log"]

sns.relplot(data=diff, x="end_time_timer", y="end_time_log")
sns.relplot(data=diff, x="out_sum_timer", y="out_sum_log")
df_1250_b = df[df["end_time_log"] < 1250]

df["type_total_log"] = backup["type_total"]
sns.relplot(data=df, x="type_total_log", y="type_total")
# sns.lmplot(data=df, x="end_time", y="out_sum")
# %%
# %%
# t-test on base variables and descriptive stats

df_1300 = df[df["end_time2"] < 1300]
df_1250 = df[df["end_time2"] < 1250]
df_nw = df[df["notWatching2"] < 60]

variables = [
    "watchedVideo",
    "watching2",
    "watch_total2",
    "notWatching2",
    "type_total2",
    "typing2",
    "notTyping2",
    "end_time2",
]
results_dfs = []

dataframes = [df, df_1300, df_1250, df_1230]

for dataframe in dataframes:
    results = []
    for var in variables:
        t_stat, p_value = stats.ttest_ind(
            dataframe[var][dataframe["treatment"] == "autoplayOff"],
            dataframe[var][dataframe["treatment"] == "autoplayOn"],
            equal_var=False,
        )
        if p_value < 0.0001:
            p_value = 0.000
        mean_off = dataframe[var][dataframe["treatment"] == "autoplayOff"].mean()
        mean_on = dataframe[var][dataframe["treatment"] == "autoplayOn"].mean()
        median_off = dataframe[var][dataframe["treatment"] == "autoplayOff"].median()
        median_on = dataframe[var][dataframe["treatment"] == "autoplayOn"].median()
        std_off = dataframe[var][dataframe["treatment"] == "autoplayOff"].std()
        std_on = dataframe[var][dataframe["treatment"] == "autoplayOn"].std()
        results.append(
            [
                var,
                p_value,
                mean_off,
                mean_on,
                std_off,
                std_on,
                median_off,
                median_on,
                t_stat,
            ]
        )

    results_df = pd.DataFrame(
        results,
        columns=[
            "Variable",
            "p-value",
            "Mean (autoplayOff)",
            "Mean (autoplayOn)",
            "Std (autoplayOff)",
            "Std (autoplayOn)",
            "Median (autoplayOff)",
            "Median (autoplayOn)",
            "t-statistic",
        ],
    )
    results_dfs.append(results_df)

for i, results_df in enumerate(results_dfs):
    print(
        f"Results with n={len(dataframes[i])} obs with {dataframes[i].treatment.describe()[3]} in {dataframes[i].treatment.describe()[2]}"
    )
    print(results_df.to_string(index=False))

# %%
