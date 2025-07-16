#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 14:59:16 2023

@author: reha.tuncer
"""
# %% packages
import pandas as pd
# import difflib
import numpy as np
# import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# %% clean data
df = pd.read_csv('first_experiment.csv')
# clean initial database
df = df[93:]  # start of second wave in DB (1st of march)
# drop test entries shorter than prolific id's
df = df[df.ID.str.len() > 20]
# %% drop participants who did not finish 

df = df[~df['browser.birthyear'].isnull()]  # drop empty entries
df = df.reset_index(drop=True)
for i in range(len(df)):
    if type(df['browser.userTranscription'][i]) is float:
        df['browser.userTranscription'][i] = str(np.nan)
        
# %%  

# df2.columns = df2.columns.str.replace('browser.', '')
# df2.columns = df2.columns.str.replace('platform.', '')
# df2.columns = df2.columns.str.replace('timespent', '')
# df2 = df2.drop(columns=['laborTime', 'leisureTime', 'transcription'])

# %% drop failed attention checks

failcheck = db[(db['attention1']+db['attention2']) >= 4]
db = db[(db['attention1']+db['attention2']) < 4]  # drop more than 4 mistake
db = db.reset_index(drop=True)


"""
Drop time choice binding
"""

db = db[~db['lottery'].str.contains(
    "lotteryWin")]  # drop lotteryWin entries

# db0 = db0[~db0['lottery'].str.contains(
#     "lotteryWin")]

"""
Correct for actual time spent on task
"""

# db["browser.videoPausedFor"][db.treatment =='autoplayOff'] = db["browser.watchedVideo"][db.treatment == 'autoplayOff']*2


db["watchTime"] = pd.DataFrame(db["browser.timespentWatching"] -
                               db["browser.videoPausedFor"] -
                               db["browser.timespentNotWatching"]).rename(columns={0: "watchTime"})


"""
KS test for heterogeneity
"""
stats.kstest(db["watchTime"][db["treatment"] == 'autoplayOn'],
             db["watchTime"][db["treatment"] == 'autoplayOff'])

stats.kstest(db["browser.watchedVideo"][db["treatment"] == 'autoplayOn'],
             db["browser.watchedVideo"][db["treatment"] == 'autoplayOff'])


stats.kstest(db["increaseType"][db["treatment"] == 'autoplayOn'],
             db["increaseType"][db["treatment"] == 'autoplayOff'])

stats.kstest(db["timeChoice"][db["treatment"] == 'autoplayOn'],
             db["timeChoice"][db["treatment"] == 'autoplayOff'])

"""
t test for difference in means
"""
stats.ttest_ind(db["watchTime"][db.treatment == "autoplayOff"],
                db["watchTime"][db.treatment == "autoplayOn"])


"""
Time choice vs realized typing
"""

db['actualType'] = ((720-db.watchTime)/720)*100
db['increaseType'] = ((720-db['watchTime'] - db.timeChoice)/720)*100

db['increaseType'][db['treatment'] == 'autoplayOn'].describe()
db['increaseType'][db['treatment'] == 'autoplayOff'].describe()


"""
Graphs
"""
sns.catplot(db, x="watchTime",
            y="treatment", kind="boxen")
sns.displot(db, x="watchTime", hue="treatment", kind="ecdf")

sns.displot(db[db["watchTime"] >= 120], x="watchTime",
            hue="treatment", kind='kde')


sns.catplot(db, x="increaseType", y="treatment", kind="boxen")
sns.displot(db, x="increaseType", hue="treatment", kind='kde')

sns.catplot(db, x="timeChoice", y="treatment", kind="boxen")

sns.displot(db, x="browser.videoPausedFor", hue="treatment", kind='ecdf')
sns.catplot(db, x="browser.watchedVideo", y="treatment", kind="box")
