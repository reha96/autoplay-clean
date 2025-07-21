#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 11:01:53 2022

@author: reha.tuncer
"""
# %% get packages
import pandas as pd
import difflib
import numpy as np
import seaborn as sns

# %% get data
db = pd.read_csv('/Users/reha.tuncer/Documents/GitHub/autoplay/python/old/MPL.csv')
db = pd.read_csv("/Users/reha.tuncer/Documents/GitHub/autoplay/python/old/autoplay.csv")

# %% get prolific data
db2 = pd.read_csv('/Users/reha.tuncer/Documents/GitHub/autoplay/python/old/prolific.csv')

# %% get CAPTCHA's
captchas = pd.read_excel("/Users/reha.tuncer/Documents/GitHub/autoplay/python/old/captchas_list.xlsx", "captchas", header=None)

# %% clean data
# db = pd.read_csv('mpl2nd.csv')
# db.columns = db.columns.str.replace('browser.', '')
# db.columns = db.columns.str.replace('platform.', '')
# db.columns = db.columns.str.replace('timespent', '')
# db = db[db.ID.str.len() > 23].reset_index(drop=True)

# db0 = pd.read_csv('mpl1st.csv')
# db0.columns = db0.columns.str.replace('browser.', '')
# db0.columns = db0.columns.str.replace('platform.', '')
# db0.columns = db0.columns.str.replace('timespent', '')
# db0 = db0[db0.ID.str.len() > 23].reset_index(drop=True)

# #### MPL extraction
# selected_columns = db0.filter(like='MPL').columns
# db[selected_columns] = db0[selected_columns]


# clean initial database
# db = db[93:]  # start of second wave in DB (1st of march)
# %% filter participants by ID

# db = db[db.ID.isin(['6017f6742d7cc9ad4f98fb4d',
#                     '6145e674f74f637530a08a39',
#                     '62cfeab06cb6c36b80b91493',
#                     '613f1d6420141eefc3e5f1b0',
#                     '55d4c46f58c35800113dc131',
#                     '60ac08be37cd5e98ab2d0037',
#                     '5bdcf08f05ed110001ab2bbf',
#                     '58a17caf6a8d3b00017ec00e',
#                     '5b7e7de287d85f0001bac19a',
#                     '5642444817bdbe00062a1129',
#                     '59b555702a78fd00010b86d4',
#                     '5cd47eac121337001afb9e96',
#                     '5c366fc38821900001b38b67',
#                     '5bf50c187ea49f0001ba734a',
#                     '608fdbc4196e5708ed3f291a',
#                     '5efde724d80f81077c0800b9'
#                     ])]
# db = db[93:] # start of second wave in DB (1st of march)
# db = db[db.ID.str.len()>20] # drop test entries shorter than prolific id's

# %% drop participants who did not finish 
# noapprove = db[db['birthyear'].isnull()]
# db = db[~db['birthyear'].isnull()]  # drop empty entries
# db = db.reset_index(drop=True)
# for i in range(len(db)):
#     if type(db['userTranscription'][i]) is float:
#         db['userTranscription'][i] = str(np.nan)
#     # if db["treatment"][i] != "MPL":  # reset MPL by treatment
#     #     db["MPLthatcounts"][i] = str(np.nan)

# #### save cleaned data
# db.to_csv('MPL.csv', index=False)


# %% drop failed attention checks
failcheck = db[(db['attention1']+db['attention2']) >= 4]
db = db[(db['attention1']+db['attention2']) < 4]  # drop more than 4 mistake
db = db.reset_index(drop=True)

"""
Get MPL bonus if treatment is MPL
"""
if "MPLthatcounts" in db.columns:
    s = '+'
    e = '£'
    MPL = []
    MPLcondition = []
    MPLid = []
    for i in range(len(db)):
        MPLid.append(db["ID"][i])
        MPLcondition.append(db["MPLthatcounts"][i].split(s)[
                            0])  # get autoplay condition but work on merge
        MPL.append(float((db["MPLthatcounts"]
                    [i].split(s))[1].split(e)[0]))


    MPL = pd.DataFrame([MPLid, MPLcondition, MPL])
    MPL = MPL.transpose()
    MPL = MPL.rename(
        columns={0: "ID"})

# %% typing analysis
text = []
for i in range(len(db)):
        a = str(db['userTranscription'][i]).replace('[', '').replace(']', '').replace('"', '')
        text.append(a.split(','))

text = pd.DataFrame(text).transpose()
allscore = pd.DataFrame(text)
accuracy = []
            
for y in range(len(text.columns)):
    for x in range(len(text[y])):
        if text[y][x] is not None:
            accuracy = [difflib.SequenceMatcher(None, text[y][x], captchas[0][i]).ratio() for i in range(len(captchas[0]))]
            allscore[y][x] = max(accuracy)            
            
t = []
v = []
for i in range(len(allscore.columns)):
    t.append(sum(filter(None, allscore[i])))
    v.append(allscore[i].count())  # completed sentences!
    t[i] = t[i]/v[i]
    t[i] = t[i].round(4)*100

#### sentences per minute spent typing
permin = (v/(db["typing"]/60)).round(2)
permin[permin>500] = 0 # for inf values when time spent typing is zero
permin = pd.DataFrame(permin).rename(
    columns={'typing': "permin"}) 
pcentacc = pd.DataFrame(t).rename(
    columns={0: "accuracy"})  # percent typing accuracy

#### visualize
sns.displot(data=permin, x="permin")
sns.displot(data=pcentacc, x="accuracy")

# %% bonus Payments

#### UNLESS YOU FIND A WAY TO EQUALIZE BOTH TREATMENTS, VIDEO PAUSED SHOULD NOT COUNT LESS

watchTime = pd.DataFrame(db["watching"] -
                          # db["videoPausedFor"]-
                         db["notWatching"]).rename(columns={0: "watchTime"})
typeTime = pd.DataFrame(db["typing"] -
                        db["notTyping"]).rename(columns={0: "typeTime"})
payment = pd.concat(
    [watchTime,
     typeTime, permin, pcentacc["accuracy"]], axis=1)


#### add 2 seconds because of db delay
payment.watchTime = payment.watchTime*0.1  # 0.1 per sec bonus
payment.typeTime = (payment.typeTime+2) * 0.15  # 0.15 per sec bonus // or 0.05 difference

#### check for accuracy and permin conditions
payment.typeTime[payment.permin<1]=0 # at least 1 submission per minute
payment.typeTime[payment.accuracy<70]=0 # at least 70 pcent acc

# get total bonuses
paysum = round(((payment.watchTime + payment.typeTime)/100),2)
# paysum = paysum-0.63 + 2.75 # after approval for the first study and participation for second
paysum = paysum + 2.75 # total bonus
if "MPLthatcounts" in db.columns:
    paysum = ((payment.typeTime/100)+MPL[2].values).astype(float)
# paysum = ((payment.typeTime/100)).astype(float)
paysum = round(paysum, 2)
paysum = paysum.rename("bonus")
paysum.to_csv('/Users/reha.tuncer/Documents/GitHub/autoplay/stata/payment.csv', index=False)

# %% payment Output Table

# for value in db['ID']:
#     #### Check if the value is not in column 'B'
#     if value not in db2['Participant id'].values:
#         print(value)
        
total = []
total = pd.DataFrame(total)
total = pd.concat([paysum, db["ID"], db["treatment"],
                  watchTime,
                  typeTime,
                  pd.DataFrame(permin).rename(
                      columns={"typing": "permin"}),
                  pcentacc,
                   ], axis=1)
total = total.reset_index(drop=True)

# #  cut people with less than 700 active seconds
# total = total[total.watchTime+total.typeTime>700]
# total = total.reset_index(drop=True)

#### print ID and bonus
print(total.ID.to_csv(index=False))
for i in range(len(total)):
    if total.bonus[i] !=0:
        print(str(total.ID[i]) + "," + str(total.bonus[i]))

# total = total.merge(MPL, on="ID")
# total['total'] = total["bonus"]+MPL[2]
# total["bonus"] = total["bonus"]+MPL[2]-2  # add MPL and remove base payment

# for i in range(len(total)):
#     if total.bonus[i] < 0:
#         total["bonus"][i] = 0
# if total["total"][i] < 2:
#     total["total"][i] = 2
# %%
