#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Add this code after the existing code in your script, or run it after the main processing

# %%%
# PART 3: VIDEO TRANSITION ANALYSIS
print("\n" + "="*60)
print("PART 3: VIDEO TRANSITION ANALYSIS")
print("="*60)

# Check if required variables exist, if not recreate them
try:
    print(f"Using existing events_df with {len(events_df)} rows")
    print(f"Using existing df_clean with {len(df_clean)} rows")
except NameError:
    print("Required variables not found. Please run the main data processing code first.")
    print("Loading data from CSV files...")
    
    # Try to load from saved files
    try:
        df = pd.read_csv("autoplay.csv")
        df = df.reset_index(drop=True)
        df['participant_id'] = df.index
        
        # Recreate df_clean
        keep_cols = [col for col in df.columns if col not in ['notTyping', 'notWatching', 'os', 'platform', 'session', 'tabCounter', 'feedback', 'strategy', 'typeCount', 'typing', 'userTranscription', 'videoPaused', 'watchedVideo', 'watching', 'updatedAt']]
        df_clean = df[keep_cols].copy()
        
        # Recreate events processing
        sess = []
        pattern = r"(?=(?!\:)\,(?!\s[rd]))"
        for i in range(len(df)):
            sess.append(re.split(pattern, df.session.iloc[i]))

        for i in range(len(sess)):
            for x in range(len(sess[i])):
                sess[i][x] = sess[i][x].replace("\\", "").replace(",", "").replace('"', "").replace("[", "").replace("]", "")

        # Extract events
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

        # Convert to relative time
        events_with_mouseout = []
        for pid in raw_events['participant_id'].unique():
            p_events = raw_events[raw_events['participant_id'] == pid].copy()
            p_events = p_events.sort_values('timestamp')
            
            start_time = p_events[p_events['activity'] == 'start']['timestamp'].iloc[0] if len(p_events[p_events['activity'] == 'start']) > 0 else p_events['timestamp'].iloc[0]
            p_events['relative_time'] = (p_events['timestamp'] - start_time).round(0).astype(int)
            
            events_with_mouseout.append(p_events)

        events_df = pd.concat(events_with_mouseout, ignore_index=True)
        print(f"Successfully recreated events_df with {len(events_df)} rows")
        
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Please ensure 'autoplay.csv' exists or run the main processing code first.")
        raise

def extract_video_events(events_df):
    """Extract video playing and ended events"""
    video_events = []
    
    print("Scanning for video events...")
    for pid in events_df['participant_id'].unique():
        p_events = events_df[events_df['participant_id'] == pid].copy()
        p_events = p_events.sort_values('relative_time')
        
        for _, row in p_events.iterrows():
            activity = row['activity']
            
            # Match video playing events - handle both formats:
            # autoplayOn: "videoX: playing: duration: ..."
            # autoplayOff: "video X: playing" (with space)
            if 'playing' in activity and 'video' in activity:
                # Try autoplayOn format first: "videoX: playing:"
                match = re.search(r'video(\d+): playing:', activity)
                if match:
                    video_events.append({
                        'participant_id': pid,
                        'relative_time': row['relative_time'],
                        'event_type': 'playing',
                        'video_number': int(match.group(1)),
                        'raw_activity': activity
                    })
                else:
                    # Try autoplayOff format: "video X: playing"
                    match = re.search(r'video (\d+): playing', activity)
                    if match:
                        video_events.append({
                            'participant_id': pid,
                            'relative_time': row['relative_time'],
                            'event_type': 'playing',
                            'video_number': int(match.group(1)),
                            'raw_activity': activity
                        })
            
            # Match video ended events: "videoX: ended" (same for both treatments)
            elif ': ended' in activity and 'video' in activity:
                match = re.search(r'video(\d+): ended', activity)
                if match:
                    video_events.append({
                        'participant_id': pid,
                        'relative_time': row['relative_time'],
                        'event_type': 'ended',
                        'video_number': int(match.group(1)),
                        'raw_activity': activity
                    })
    
    return pd.DataFrame(video_events)

def calculate_video_transitions(video_events_df):
    """Calculate transition times between video end and next video start"""
    transitions = []
    edge_cases = []
    
    print("Calculating video transitions...")
    for pid in video_events_df['participant_id'].unique():
        p_events = video_events_df[video_events_df['participant_id'] == pid].copy()
        p_events = p_events.sort_values(['relative_time', 'video_number'])
        
        # Find transitions: ended followed by playing
        for i in range(len(p_events) - 1):
            current_event = p_events.iloc[i]
            next_event = p_events.iloc[i + 1]
            
            # Check for edge cases
            if current_event['event_type'] == next_event['event_type']:
                edge_cases.append({
                    'participant_id': pid,
                    'issue': f"Consecutive {current_event['event_type']} events",
                    'video1': current_event['video_number'],
                    'video2': next_event['video_number'],
                    'time1': current_event['relative_time'],
                    'time2': next_event['relative_time']
                })
                continue
            
            # Valid transition: ended → playing
            if (current_event['event_type'] == 'ended' and 
                next_event['event_type'] == 'playing'):
                
                transition_time = next_event['relative_time'] - current_event['relative_time']
                
                transitions.append({
                    'participant_id': pid,
                    'from_video': current_event['video_number'],
                    'to_video': next_event['video_number'],
                    'end_time': current_event['relative_time'],
                    'start_time': next_event['relative_time'],
                    'transition_time': transition_time,
                    'is_outlier': transition_time > 30,
                    'is_consecutive': next_event['video_number'] == current_event['video_number'] + 1
                })
    
    return pd.DataFrame(transitions), pd.DataFrame(edge_cases)

def calculate_video_durations(video_events_df):
    """Calculate duration of each video"""
    durations = []
    
    print("Calculating video durations...")
    for pid in video_events_df['participant_id'].unique():
        p_events = video_events_df[video_events_df['participant_id'] == pid].copy()
        p_events = p_events.sort_values(['video_number', 'relative_time'])
        
        # Group by video number to find playing→ended pairs
        for video_num in p_events['video_number'].unique():
            video_events = p_events[p_events['video_number'] == video_num].copy()
            
            playing_events = video_events[video_events['event_type'] == 'playing']
            ended_events = video_events[video_events['event_type'] == 'ended']
            
            if len(playing_events) > 0 and len(ended_events) > 0:
                # Take first playing and last ended event for this video
                start_time = playing_events['relative_time'].iloc[0]
                end_time = ended_events['relative_time'].iloc[-1]
                duration = end_time - start_time
                
                durations.append({
                    'participant_id': pid,
                    'vid_id': video_num,
                    'duration': duration,
                    'start_time': start_time,
                    'end_time': end_time
                })
    
    return pd.DataFrame(durations)

# Execute the analysis
print("Extracting video events...")
video_events_df = extract_video_events(events_df)
print(f"Found {len(video_events_df)} video events")

# Show sample of events for debugging
print("\nSample video events:")
print(video_events_df.head(10))

print("\nVideo events summary:")
event_summary = video_events_df.groupby(['event_type']).size()
print(event_summary)

if len(video_events_df) == 0:
    print("WARNING: No video events found! Checking raw activities...")
    print("\nSample activities containing 'video':")
    video_activities = events_df[events_df['activity'].str.contains('video', na=False)]['activity'].unique()
    print(video_activities[:10])  # Show first 10 video activities
    
    print("\nSample activities containing 'playing':")
    playing_activities = events_df[events_df['activity'].str.contains('playing', na=False)]['activity'].unique()
    print(playing_activities[:10])
    
    print("\nSample activities containing 'ended':")
    ended_activities = events_df[events_df['activity'].str.contains('ended', na=False)]['activity'].unique()
    print(ended_activities[:10])
    
    print("\nPlease check the activity patterns and regex matching.")
else:
    print("\nCalculating transitions...")
    transitions_df, edge_cases_df = calculate_video_transitions(video_events_df)
    print(f"Found {len(transitions_df)} transitions")

    if len(edge_cases_df) > 0:
        print(f"\nWARNING: Found {len(edge_cases_df)} edge cases:")
        print(edge_cases_df)

    print("\nCalculating video durations...")
    durations_df = calculate_video_durations(video_events_df)
    print(f"Found {len(durations_df)} video duration records")

    # %%%
    # Analyze transitions by participant and treatment
    print("\n" + "="*60)
    print("TRANSITION ANALYSIS RESULTS")
    print("="*60)

    # Create base dataframe with ALL participants (184 total)
    all_participants = df_clean[['participant_id', 'treatment']].copy()
    print(f"Total participants in original dataset: {len(all_participants)}")

    if len(transitions_df) > 0:
        # Add treatment information to transitions
        transitions_with_treatment = transitions_df.merge(all_participants, on='participant_id', how='left')

        # Calculate average transition times per participant (only for those with transitions)
        participant_transitions_calculated = transitions_with_treatment.groupby(['participant_id', 'treatment']).agg({
            'transition_time': ['mean', 'count', 'std'],
            'is_outlier': 'sum'
        }).round(2)

        participant_transitions_calculated.columns = ['avg_transition_time', 'num_transitions', 'std_transition_time', 'num_outliers']
        participant_transitions_calculated = participant_transitions_calculated.reset_index()

        print(f"Participants with video transitions: {len(participant_transitions_calculated)}")

        # Merge with ALL participants to ensure complete dataset
        participant_transitions = all_participants.merge(participant_transitions_calculated, on=['participant_id', 'treatment'], how='left')

        # Fill missing values for participants without transitions
        participant_transitions['avg_transition_time'] = participant_transitions['avg_transition_time'].fillna(0)
        participant_transitions['num_transitions'] = participant_transitions['num_transitions'].fillna(0).astype(int)
        participant_transitions['std_transition_time'] = participant_transitions['std_transition_time'].fillna(0)
        participant_transitions['num_outliers'] = participant_transitions['num_outliers'].fillna(0).astype(int)

        print(f"Final dataset: {len(participant_transitions)} participants (should be 184)")
        print("Participant-level transition statistics:")
        print(participant_transitions.head(10))

        # Summary by treatment (only for participants with transitions)
        print("\nTransition times by treatment:")
        participants_with_transitions = participant_transitions[participant_transitions['num_transitions'] > 0]
        treatment_summary = participants_with_transitions.groupby('treatment').agg({
            'avg_transition_time': ['mean', 'std', 'count'],
            'num_transitions': 'mean',
            'num_outliers': 'mean'
        }).round(3)
        print(treatment_summary)

        # Show breakdown of participants with/without transitions
        print("\nParticipant breakdown:")
        transition_breakdown = participant_transitions.groupby('treatment').agg({
            'participant_id': 'count',  # Total participants
            'num_transitions': lambda x: (x > 0).sum()  # Participants with transitions
        })
        transition_breakdown.columns = ['total_participants', 'participants_with_transitions']
        transition_breakdown['participants_without_transitions'] = transition_breakdown['total_participants'] - transition_breakdown['participants_with_transitions']
        print(transition_breakdown)

        # Outlier analysis
        if len(transitions_with_treatment) > 0:
            outlier_transitions = transitions_with_treatment[transitions_with_treatment['is_outlier']]
            print(f"\nOutlier transitions (>30 seconds): {len(outlier_transitions)}")
            if len(outlier_transitions) > 0:
                print("Outlier summary by treatment:")
                print(outlier_transitions.groupby('treatment')['transition_time'].describe())

        # %%%
        # Find participant with maximum videos watched
        print("\n" + "="*60)
        print("VIDEO DURATION ANALYSIS")
        print("="*60)

        # Find max videos watched per participant
        max_videos_per_participant = video_events_df.groupby('participant_id')['video_number'].max().reset_index()
        max_videos_per_participant.columns = ['participant_id', 'max_video_watched']

        print("Top 10 participants by videos watched:")
        top_participants = max_videos_per_participant.sort_values('max_video_watched', ascending=False).head(10)
        print(top_participants)

        # Find participant who watched the most videos
        max_video_participant = max_videos_per_participant.loc[max_videos_per_participant['max_video_watched'].idxmax()]
        print(f"\nParticipant {max_video_participant['participant_id']} watched the most videos: {max_video_participant['max_video_watched']}")

        # Extract video durations from this participant
        selected_participant = max_video_participant['participant_id']
        selected_durations = durations_df[durations_df['participant_id'] == selected_participant].copy()
        selected_durations = selected_durations.sort_values('vid_id')

        print(f"\nVideo durations for participant {selected_participant}:")
        print(f"Videos 1-20:")
        print(selected_durations[selected_durations['vid_id'] <= 20][['vid_id', 'duration']])

        print(f"\nSummary statistics for video durations:")
        print(selected_durations['duration'].describe())

        # Create final output for video duration analysis
        video_duration_stats = selected_durations[['vid_id', 'duration']].copy()
        print(f"\nFinal video duration dataset: {len(video_duration_stats)} videos")
        print("Sample:")
        print(video_duration_stats.head())

        # %%%
        # Save results
        print("\n" + "="*60)
        print("SAVING RESULTS")
        print("="*60)

        # Save transition analysis - READY FOR APPENDING TO CLEAN-DATA.XLSX
        participant_transitions.to_csv('participant_transition_times.csv', index=False)
        if len(transitions_with_treatment) > 0:
            transitions_with_treatment.to_csv('all_transitions.csv', index=False)

        # Save video duration analysis
        video_duration_stats.to_csv('video_duration_stats.csv', index=False)

        # Save summary statistics
        with open('transition_analysis_summary.txt', 'w') as f:
            f.write("VIDEO TRANSITION ANALYSIS SUMMARY\n")
            f.write("="*50 + "\n\n")
            
            f.write("DATASET OVERVIEW:\n")
            f.write(f"Total participants: {len(participant_transitions)}\n")
            f.write(f"Participants with video transitions: {len(participants_with_transitions)}\n")
            f.write(f"Participants without video transitions: {len(participant_transitions) - len(participants_with_transitions)}\n\n")
            
            f.write("TREATMENT COMPARISON (participants with transitions only):\n")
            f.write(str(treatment_summary) + "\n\n")
            
            f.write("PARTICIPANT BREAKDOWN BY TREATMENT:\n")
            f.write(str(transition_breakdown) + "\n\n")
            
            f.write("PARTICIPANT WITH MOST VIDEOS:\n")
            f.write(f"Participant ID: {selected_participant}\n")
            f.write(f"Max video watched: {max_video_participant['max_video_watched']}\n")
            f.write(f"Number of video durations calculated: {len(video_duration_stats)}\n\n")
            
            f.write("VIDEO DURATION STATISTICS:\n")
            f.write(str(video_duration_stats['duration'].describe()) + "\n\n")
            
            if len(edge_cases_df) > 0:
                f.write("EDGE CASES FOUND:\n")
                f.write(str(edge_cases_df) + "\n")

        print("Saved files:")
        print("- participant_transition_times.csv (READY FOR MERGING WITH CLEAN-DATA.XLSX)")
        print("- all_transitions.csv") 
        print("- video_duration_stats.csv")
        print("- transition_analysis_summary.txt")

        print(f"\nFINAL RESULTS:")
        print(f"- {len(participant_transitions)} total participants (all from original dataset)")
        print(f"- {len(participants_with_transitions)} participants with video transitions")
        print(f"- {len(transitions_df)} total transitions found")
        if len(transitions_with_treatment) > 0:
            outlier_transitions = transitions_with_treatment[transitions_with_treatment['is_outlier']]
            print(f"- {len(outlier_transitions)} outlier transitions (>30 sec)")
        print(f"- Participant {selected_participant} watched {max_video_participant['max_video_watched']} videos")
        print(f"- {len(video_duration_stats)} video durations calculated")
        
        print(f"\nREADY FOR EXCEL MERGE:")
        print(f"participant_transition_times.csv has {len(participant_transitions)} rows")
        print("Columns: participant_id, treatment, avg_transition_time, num_transitions, std_transition_time, num_outliers")
        print("This matches your clean-data.xlsx structure for direct merging/appending")
# %%