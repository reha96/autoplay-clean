import pandas as pd
import numpy as np

# %%%
def debug_process_all_participants(csv_file='sess.csv'):
    """
    DEBUG VERSION: Processes participant data with detailed logging.
    Includes participant ID tracking and removes normalization.
    Shows step-by-step operations for debugging.
    """
    print("\n🔄 DEBUG: Processing all participants...")
    
    # STEP 1: Load the CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"✓ Loaded CSV: {len(df)} participants, {len(df.columns)} columns")
        print(f"✓ Column names: {list(df.columns)[:10]}...")  # Show first 10 columns
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return None, None
    
    # STEP 2: Initialize tracking variables
    all_trajectories = []
    behavior_counts = {'always_workers': 0, 'swappers': 0, 'always_watchers': 0}
    debug_info = []
    
    # STEP 3: Process each participant
    for idx in range(len(df)):
        participant_debug = {
            'participant_id': idx,  # Track original order ID
            'original_row_index': idx,
            'processing_status': 'started'
        }
        
        try:
            participant = df.iloc[idx]
            print(f"\n--- Processing Participant {idx} ---")
            
            # STEP 4: Extract session data from participant row
            logged_activities = []
            first_timestamp = None
            valid_columns = 0
            
            print("🔍 Scanning columns for timestamped data...")
            
            for col_name, value in participant.items():
                # Debug: Show what we're examining
                if pd.notna(value) and isinstance(value, str):
                    print(f"  Column '{col_name}': {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                
                # Original logic: look for timestamped activities
                if pd.notna(value) and isinstance(value, str) and ' ' in value:
                    try:
                        parts = value.split(' ')
                        timestamp = float(parts[0])
                        activity = ' '.join(parts[1:])
                        
                        if first_timestamp is None:
                            first_timestamp = timestamp
                            print(f"  ✓ Found first timestamp: {first_timestamp}")
                        
                        relative_second = int(timestamp - first_timestamp)
                        logged_activities.append({
                            'relative_second': relative_second,
                            'activity': activity,
                            'source_column': col_name
                        })
                        valid_columns += 1
                        
                        print(f"  ✓ Parsed activity: t={relative_second}s, activity='{activity[:30]}'")
                        
                    except (ValueError, IndexError) as e:
                        print(f"  ⚠ Failed to parse column '{col_name}': {e}")
                        continue
                else:
                    # Debug: Show why columns were skipped
                    if pd.isna(value):
                        reason = "null/NaN value"
                    elif not isinstance(value, str):
                        reason = f"not string (type: {type(value)})"
                    elif ' ' not in value:
                        reason = "no space character"
                    else:
                        reason = "unknown"
                    print(f"  ⏭ Skipped column '{col_name}': {reason}")
            
            participant_debug['valid_columns'] = valid_columns
            participant_debug['total_activities'] = len(logged_activities)
            
            # STEP 5: Check if we have enough data
            print(f"📊 Found {len(logged_activities)} activities from {valid_columns} columns")
            
            if len(logged_activities) < 10:
                print(f"⚠ Skipping participant {idx}: too few activities ({len(logged_activities)} < 10)")
                participant_debug['processing_status'] = 'skipped_insufficient_data'
                debug_info.append(participant_debug)
                continue
            
            # STEP 6: Sort and deduplicate activities
            print("🔧 Sorting and deduplicating activities...")
            logged_activities.sort(key=lambda x: x['relative_second'])
            print(f"  ✓ Sorted {len(logged_activities)} activities")
            
            # Prevent duplicate seconds by keeping the last activity for each second
            unique_logs = {}
            for log in logged_activities:
                unique_logs[log['relative_second']] = log
            logged_activities = sorted(list(unique_logs.values()), key=lambda x: x['relative_second'])
            print(f"  ✓ After deduplication: {len(logged_activities)} activities")
            
            participant_debug['activities_after_dedup'] = len(logged_activities)
            
            # STEP 7: Calculate session duration (NO NORMALIZATION)
            session_duration = logged_activities[-1]['relative_second'] + 1
            print(f"📏 Session duration: {session_duration} seconds")
            participant_debug['session_duration'] = session_duration
            
            # STEP 8: Generate trajectory WITHOUT normalization
            print("🏗 Building trajectory...")
            trajectory = []
            cumulative_typing = 0
            current_task = 'TYPING'  # Assume starting with typing
            task_switches = 0

            # Create activity mapping
            activity_map = {log['relative_second']: log for log in logged_activities}
            
            for second in range(session_duration):
                if second in activity_map:
                    log = activity_map[second]
                    activity = log['activity']
                    
                    # Determine task from activity
                    old_task = current_task
                    if 'current_task:watching' in activity or 'video' in activity:
                        current_task = 'WATCHING'
                    elif activity in ['typing', 'current_task:typing']:
                        current_task = 'TYPING'
                    
                    if old_task != current_task:
                        task_switches += 1
                        print(f"  🔄 Task switch at t={second}s: {old_task} → {current_task}")
                
                # Accumulate typing time
                if current_task == 'TYPING':
                    cumulative_typing += 1
                
                trajectory.append({
                    'participant_id': idx,  # Include participant ID
                    'session_time': second + 1,
                    'cumulative_typing': cumulative_typing,
                    'current_task': current_task
                })
            
            print(f"  ✓ Built trajectory with {len(trajectory)} time points")
            print(f"  ✓ Task switches: {task_switches}")
            print(f"  ✓ Final cumulative typing time: {cumulative_typing} seconds")
            
            participant_debug['task_switches'] = task_switches
            participant_debug['final_typing_time'] = cumulative_typing
            
            # STEP 9: Behavior classification (based on original session duration, not normalized)
            typing_ratio = cumulative_typing / session_duration
            print(f"📊 Typing ratio: {typing_ratio:.3f}")
            
            if typing_ratio > 0.9:
                behavior_type = 'always_workers'
            elif typing_ratio < 0.1:
                behavior_type = 'always_watchers'
            else:
                behavior_type = 'swappers'
            
            behavior_counts[behavior_type] += 1
            participant_debug['behavior_type'] = behavior_type
            participant_debug['typing_ratio'] = typing_ratio
            participant_debug['processing_status'] = 'completed'
            
            print(f"🏷 Classified as: {behavior_type}")
            
            # STEP 10: Store results
            all_trajectories.append({
                'participant_id': idx,  # Original order ID
                'behavior_type': behavior_type,
                'typing_ratio': typing_ratio,
                'final_typing_time': cumulative_typing,
                'session_duration': session_duration,  # Include original duration
                'task_switches': task_switches,
                'trajectory': trajectory
            })
            
        except Exception as e:
            print(f"❌ Error processing participant {idx}: {str(e)}")
            participant_debug['processing_status'] = f'error: {str(e)}'
            
        debug_info.append(participant_debug)
    
    # STEP 11: Summary
    print(f"\n✅ PROCESSING COMPLETE")
    print(f"📊 Successfully processed {len(all_trajectories)} participants")
    print(f"  Always Workers: {behavior_counts['always_workers']}")
    print(f"  Swappers: {behavior_counts['swappers']}")
    print(f"  Always Watchers: {behavior_counts['always_watchers']}")
    
    # Debug summary
    print(f"\n🐛 DEBUG SUMMARY:")
    status_counts = {}
    for info in debug_info:
        status = info['processing_status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"  {status}: {count} participants")
    
    return all_trajectories, behavior_counts, debug_info

def compare_with_cleandata(trajectories, cleandata_file='cleandata.xlsx'):
    """
    Compare the processed trajectories with the existing clean dataset.
    """
    print(f"\n🔍 COMPARING WITH CLEAN DATASET...")
    
    try:
        # Load the clean data
        clean_df = pd.read_excel(cleandata_file)
        print(f"✓ Loaded clean dataset: {len(clean_df)} participants")
        
        # Check if we have the same number of participants
        print(f"📊 Comparison:")
        print(f"  Processed trajectories: {len(trajectories)} participants")
        print(f"  Clean dataset: {len(clean_df)} participants")
        
        if len(trajectories) != len(clean_df):
            print("⚠ WARNING: Different number of participants!")
        
        # Compare key metrics for first few participants
        print(f"\n📋 DETAILED COMPARISON (first 5 participants):")
        
        for i in range(min(5, len(trajectories), len(clean_df))):
            traj = trajectories[i]
            clean_row = clean_df.iloc[i]
            
            print(f"\n--- Participant {i} ---")
            print(f"  Processed typing time: {traj['final_typing_time']}s")
            
            # Look for corresponding columns in clean data
            if 'typing_log' in clean_df.columns:
                clean_typing = clean_row['typing_log']
                print(f"  Clean typing_log: {clean_typing}")
                
            if 'watching_log' in clean_df.columns:
                clean_watching = clean_row['watching_log']
                print(f"  Clean watching_log: {clean_watching}")
                
            if 'end_time_log' in clean_df.columns:
                clean_total = clean_row['end_time_log']
                print(f"  Clean end_time_log: {clean_total}")
                print(f"  Processed session duration: {traj['session_duration']}s")
        
        return clean_df
        
    except Exception as e:
        print(f"❌ Error loading clean dataset: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    # Process the data with debugging
    trajectories, behavior_counts, debug_info = debug_process_all_participants('sess.csv')
    
    # Compare with clean dataset
    clean_data = compare_with_cleandata(trajectories, 'clean-data.xlsx')
# %%
