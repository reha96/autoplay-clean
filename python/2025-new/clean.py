#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import pandas as pd
import numpy as np

# %%%
# load and assign participant IDs
df = pd.read_csv("autoplay.csv")
df = df.reset_index(drop=True)
df['participant_id'] = df.index

# keep only needed columns from original data
keep_cols = [col for col in df.columns if col not in ['notTyping', 'notWatching', 'os', 'platform', 'session', 'tabCounter', 'feedback', 'strategy', 'typeCount', 'typing', 'userTranscription', 'videoPaused', 'watchedVideo', 'watching', 'updatedAt']]
df_clean = df[keep_cols].copy()

print(f"Loaded {len(df)} participants, kept {len(keep_cols)} columns")

# %%%
# clean session data
sess = []
pattern = r"(?=(?!\:)\,(?!\s[rd]))"
for i in range(len(df)):
    sess.append(re.split(pattern, df.session.iloc[i]))

for i in range(len(sess)):
    for x in range(len(sess[i])):
        sess[i][x] = sess[i][x].replace("\\", "").replace(",", "").replace('"', "").replace("[", "").replace("]", "")

# %%%
# extract events
time = []
activity = []
participant_id = []

for i in range(len(sess)):
    for x in range(len(sess[i])):
        if sess[i][x] and sess[i][x][0] != " ":
            try:
                parts = sess[i][x].split(maxsplit=1)
                if len(parts) == 2:
                    time.append(float(parts[0]))
                    activity.append(parts[1])
                    participant_id.append(i)
            except:
                continue

raw_events = pd.DataFrame({
    'timestamp': time,
    'activity': activity, 
    'participant_id': participant_id
})

# %%%
# convert to relative time and detect mouseout periods
events_with_mouseout = []

for pid in raw_events['participant_id'].unique():
    p_events = raw_events[raw_events['participant_id'] == pid].copy()
    p_events = p_events.sort_values('timestamp')
    
    start_time = p_events[p_events['activity'] == 'start']['timestamp'].iloc[0] if len(p_events[p_events['activity'] == 'start']) > 0 else p_events['timestamp'].iloc[0]
    p_events['relative_time'] = (p_events['timestamp'] - start_time).round(0).astype(int)
    
    # detect mouseout periods (21+ consecutive seconds)
    mouseout_events = p_events[p_events['activity'] == 'mouseout:true']['relative_time'].tolist()
    mouseout_periods = []
    
    if mouseout_events:
        current_start = mouseout_events[0]
        current_end = mouseout_events[0]
        
        for t in mouseout_events[1:]:
            if t == current_end + 1:
                current_end = t
            else:
                if current_end - current_start + 1 >= 21:
                    mouseout_periods.extend(range(current_start, current_end + 1))
                current_start = t
                current_end = t
        
        if current_end - current_start + 1 >= 21:
            mouseout_periods.extend(range(current_start, current_end + 1))
    
    p_events['long_mouseout'] = p_events['relative_time'].isin(mouseout_periods)
    events_with_mouseout.append(p_events)

events_df = pd.concat(events_with_mouseout, ignore_index=True)
print(f"Processed {len(events_df['participant_id'].unique())} participants, detected mouseout periods")

# %%%
# identify sessions
sessions = []

for pid in events_df['participant_id'].unique():
    p_events = events_df[events_df['participant_id'] == pid].copy()
    p_events = p_events.sort_values('relative_time')
    
    state_events = p_events[p_events['activity'].isin(['start', 'current_task:watching', 'current_task:typing', 'end'])].copy()
    
    if len(state_events) == 0:
        continue
        
    current_task = 'typing'
    session_start = 0
    session_count = 0
    
    for idx, row in state_events.iterrows():
        if row['activity'] == 'current_task:watching' and current_task == 'typing':
            sessions.append({
                'participant_id': pid,
                'session_id': session_count,
                'task': 'typing',
                'start_time': session_start,
                'end_time': row['relative_time']
            })
            session_start = row['relative_time']
            current_task = 'watching'
            session_count += 1
            
        elif row['activity'] == 'current_task:typing' and current_task == 'watching':
            sessions.append({
                'participant_id': pid,
                'session_id': session_count,
                'task': 'watching',
                'start_time': session_start,
                'end_time': row['relative_time']
            })
            session_start = row['relative_time']
            current_task = 'typing'
            session_count += 1
            
        elif row['activity'] == 'end':
            sessions.append({
                'participant_id': pid,
                'session_id': session_count,
                'task': current_task,
                'start_time': session_start,
                'end_time': row['relative_time']
            })

sessions_df = pd.DataFrame(sessions)

# %%%
# count events per session
for idx, session in sessions_df.iterrows():
    pid = session['participant_id']
    start_t = session['start_time'] 
    end_t = session['end_time']
    
    p_events = events_df[events_df['participant_id'] == pid]
    session_events = p_events[(p_events['relative_time'] >= start_t) & (p_events['relative_time'] < end_t)]
    
    sessions_df.loc[idx, 'videos_watched'] = len(session_events[session_events['activity'].str.contains('ended', na=False)])
    sessions_df.loc[idx, 'captchas_submitted'] = len(session_events[session_events['activity'] == 'submit'])

# %%%
# create long format dataset - vectorized approach
long_data_list = []

for pid in events_df['participant_id'].unique():
    p_events = events_df[events_df['participant_id'] == pid].copy()
    p_sessions = sessions_df[sessions_df['participant_id'] == pid].copy()
    
    if len(p_sessions) == 0:
        continue
        
    max_time = int(p_sessions['end_time'].max())
    p_chars = df_clean[df_clean['participant_id'] == pid].iloc[0]
    treatment = 1 if p_chars['treatment'] == 'autoplayOn' else 0
    
    # create timeline
    timeline = pd.DataFrame({
        'participant_id': pid,
        'second': range(max_time + 1)
    })
    
    # assign sessions to timeline
    session_assignment = []
    for _, session in p_sessions.iterrows():
        mask = (timeline['second'] >= session['start_time']) & (timeline['second'] < session['end_time'])
        timeline.loc[mask, 'task'] = 1 if session['task'] == 'typing' else 0
        timeline.loc[mask, 'session_id'] = session['session_id']
        timeline.loc[mask, 'videos_in_session'] = session['videos_watched']
        timeline.loc[mask, 'captchas_in_session'] = session['captchas_submitted']
    
    timeline = timeline.fillna({'task': 0, 'session_id': -1, 'videos_in_session': 0, 'captchas_in_session': 0})
    
    # add mouseout - vectorized
    mouseout_times = set(p_events[p_events['long_mouseout']]['relative_time'])
    timeline['mouseout'] = timeline['second'].isin(mouseout_times).astype(int)
    
    # add event counts - vectorized
    video_times = p_events[p_events['activity'].str.contains('ended', na=False)]['relative_time'].value_counts()
    captcha_times = p_events[p_events['activity'] == 'submit']['relative_time'].value_counts()
    
    timeline['videos_this_second'] = timeline['second'].map(video_times).fillna(0)
    timeline['captchas_this_second'] = timeline['second'].map(captcha_times).fillna(0)
    
    # cumulative calculations
    timeline['cumulative_work'] = (timeline['task'] == 1).cumsum()
    timeline['total_videos_watched'] = timeline['videos_this_second'].cumsum()
    timeline['total_captchas_submitted'] = timeline['captchas_this_second'].cumsum()
    
    # add participant characteristics
    timeline['treatment'] = treatment
    timeline['timeChoice'] = p_chars['timeChoice']
    
    # select final columns
    timeline = timeline[['participant_id', 'second', 'task', 'cumulative_work', 'mouseout', 
                        'treatment', 'timeChoice', 'session_id', 'videos_in_session', 
                        'captchas_in_session', 'total_videos_watched', 'total_captchas_submitted']]
    
    long_data_list.append(timeline)

long_df = pd.concat(long_data_list, ignore_index=True)
print(f"Created long format dataset: {len(long_df)} rows for {len(long_df['participant_id'].unique())} participants")
# %%%
# save datasets
sessions_df.to_csv('sessions_data.csv', index=False)
long_df.to_csv('long_format_data.csv', index=False)

print("Saved: sessions_data.csv, long_format_data.csv")
print(f"\nLong format preview:")
print(long_df.head(10))
print(f"\nSummary stats:")
print(f"Total mouseout seconds: {long_df['mouseout'].sum()}")
print(f"Total typing seconds: {long_df['task'].sum()}")
print(f"Participants with mouseout: {len(long_df[long_df['mouseout']==1]['participant_id'].unique())}")



# %%% PART 2
# create wide format dataset for stata
# calculate mouseout by task separately (only long mouseout periods)
mouseout_by_task = long_df[long_df['mouseout'] == 1].groupby(['participant_id', 'task']).size().reset_index(name='mouseout_seconds')
mouseout_typing = mouseout_by_task[mouseout_by_task['task'] == 1].set_index('participant_id')['mouseout_seconds']
mouseout_watching = mouseout_by_task[mouseout_by_task['task'] == 0].set_index('participant_id')['mouseout_seconds']

# aggregate long data to participant level
participant_agg = long_df.groupby('participant_id').agg({
    'second': 'max',  # session duration
    'cumulative_work': 'max',  # total typing seconds
    'total_videos_watched': 'max',
    'total_captchas_submitted': 'max',
    'session_id': 'max'  # number of sessions - 1
}).reset_index()

participant_agg['total_sessions'] = participant_agg['session_id'] + 1
participant_agg['session_duration'] = participant_agg['second'] + 1

# add mouseout by task
participant_agg['mouseout_typing'] = participant_agg['participant_id'].map(mouseout_typing).fillna(0)
participant_agg['mouseout_watching'] = participant_agg['participant_id'].map(mouseout_watching).fillna(0)
participant_agg['mouseout_total'] = participant_agg['mouseout_typing'] + participant_agg['mouseout_watching']

# calculate average session length
session_lengths = sessions_df.groupby('participant_id').agg({
    'end_time': lambda x: (x - sessions_df.loc[x.index, 'start_time']).mean(),
    'start_time': 'count'  # number of sessions
}).reset_index()
session_lengths.columns = ['participant_id', 'avg_session_length', 'num_sessions']

participant_agg = participant_agg.merge(session_lengths, on='participant_id', how='left')

print(f"Aggregated long data for {len(participant_agg)} participants")

# %%%
# merge with original autoplay data
# keep variables needed for stata
keep_original = ['participant_id', 'birthyear', 'content', 'education', 'employment', 
                'gender', 'income', 'marital', 'timeChoice', 'treatment']

df_for_wide = df_clean[keep_original].copy()

# merge aggregated data
wide_df = df_for_wide.merge(participant_agg[['participant_id', 'session_duration', 'cumulative_work', 
                                           'mouseout_typing', 'mouseout_watching',
                                           'total_videos_watched', 'total_captchas_submitted',
                                           'total_sessions', 'avg_session_length']], 
                           on='participant_id', how='left')

# create stata-compatible variables
wide_df['id'] = wide_df['participant_id']
wide_df['typing_log'] = wide_df['cumulative_work']  # seconds spent typing (excluding mouseout)
wide_df['Treatment'] = wide_df['treatment'].map({'autoplayOff': 'Control', 'autoplayOn': 'Autoplay'})

# additional summary variables
wide_df['videos_watched_total'] = wide_df['total_videos_watched'] 
wide_df['captchas_submitted_total'] = wide_df['total_captchas_submitted']
wide_df['number_of_sessions'] = wide_df['total_sessions']
wide_df['average_session_length'] = wide_df['avg_session_length']

print(f"Created wide dataset with {len(wide_df)} participants and {len(wide_df.columns)} variables")

# %%%
# final wide dataset for stata
stata_columns = ['id', 'birthyear', 'content', 'education', 'employment', 
                'gender', 'income', 'marital', 'timeChoice', 
                'treatment', 'Treatment', 'typing_log', 'mouseout_typing', 'mouseout_watching',
                'videos_watched_total', 'captchas_submitted_total', 'number_of_sessions', 
                'average_session_length', 'session_duration']

wide_final = wide_df[stata_columns].copy()

# %%%
# save datasets
wide_final.to_excel('/Users/reha.tuncer/Documents/GitHub/autoplay/stata/clean-data.xlsx', index=False)
long_df.to_csv('/Users/reha.tuncer/Documents/GitHub/autoplay/stata/long_format_data.csv', index=False)

print("Saved: clean-data.xlsx, clean-data.csv, long_format_data.csv")
print(f"\nWide dataset preview:")
print(wide_final[['id', 'Treatment', 'typing_log', 'videos_watched_total', 'captchas_submitted_total', 'number_of_sessions']].head())
print(f"\nSummary:")
print(f"Participants: {len(wide_final)}")
print(f"Mean typing seconds: {wide_final['typing_log'].mean():.1f}")
print(f"Mean videos watched: {wide_final['videos_watched_total'].mean():.1f}")
print(f"Mean captchas submitted: {wide_final['captchas_submitted_total'].mean():.1f}")
print(f"Mean sessions per participant: {wide_final['number_of_sessions'].mean():.1f}")
# %%
