#!/usr/bin/env python3
"""
CORRECTED SESSION PROCESSOR - Handles mouseout deductions and proper task assignment
"""

import pandas as pd
import numpy as np
from datetime import datetime

# %%%
# CORRECTED SESSION RECONSTRUCTION WITH MOUSEOUT HANDLING

def process_participant_corrected(csv_file='sess.csv', participant_idx=0):
    """Corrected processing with mouseout deductions and proper task assignment"""
    print("="*80)
    print(f"CORRECTED SESSION PROCESSING - PARTICIPANT {participant_idx}")
    print("="*80)
    
    # Load data
    df = pd.read_csv(csv_file)
    participant = df.iloc[participant_idx]
    
    # Step 1: Extract all logged activities
    print("STEP 1: Extracting and analyzing logged activities...")
    logged_activities = []
    
    for col_name, value in participant.items():
        if pd.notna(value) and value != '':
            try:
                timestamp = float(value.split(' ')[0])
                activity = ' '.join(value.split(' ')[1:])
                relative_second = int(timestamp - float(df.iloc[participant_idx, 0].split(' ')[0]))
                
                logged_activities.append({
                    'timestamp': timestamp,
                    'relative_second': relative_second,
                    'activity': activity
                })
            except:
                continue
    
    logged_activities.sort(key=lambda x: x['relative_second'])
    session_duration = logged_activities[-1]['relative_second'] + 1
    
    print(f"  Session duration: {session_duration} seconds")
    print(f"  Logged activities: {len(logged_activities)}")
    
    # Step 2: Identify task contexts and mouseout periods
    print("STEP 2: Analyzing task contexts and mouseout periods...")
    
    def classify_activity(activity):
        if activity in ['typing', 'current_task:typing']:
            return 'TYPING'
        elif activity in ['current_task:watching'] or 'video' in activity:
            return 'WATCHING'
        elif activity == 'mouseout:true':
            return 'MOUSEOUT'
        elif activity in ['start', 'end', 'submit']:
            return 'SYSTEM'
        else:
            return 'OTHER'
    
    # Track current task context for mouseout classification
    current_task_context = 'TYPING'  # START WITH TYPING as you specified
    mouseout_periods = {'TYPING': [], 'WATCHING': []}
    activity_timeline = {}
    
    for activity_log in logged_activities:
        second = activity_log['relative_second']
        activity = activity_log['activity']
        activity_type = classify_activity(activity)
        
        # Update task context
        if activity_type in ['TYPING', 'WATCHING']:
            current_task_context = activity_type
        
        # Track mouseout in context
        if activity_type == 'MOUSEOUT':
            mouseout_periods[current_task_context].append(second)
        
        activity_timeline[second] = {
            'activity': activity,
            'activity_type': activity_type,
            'task_context': current_task_context
        }
    
    total_mouseout_typing = len(mouseout_periods['TYPING'])
    total_mouseout_watching = len(mouseout_periods['WATCHING'])
    
    print(f"  Mouseout during typing: {total_mouseout_typing} seconds")
    print(f"  Mouseout during watching: {total_mouseout_watching} seconds")
    print(f"  Total mouseout time: {total_mouseout_typing + total_mouseout_watching} seconds")
    
    # Step 3: Identify corrected task sessions with mouseout deductions
    print("STEP 3: Identifying task sessions with mouseout deductions...")
    
    task_sessions = []
    current_session = None
    
    # Fill in the complete timeline with proper task assignment
    complete_timeline = []
    current_task = 'TYPING'  # START WITH TYPING
    
    for second in range(session_duration):
        if second in activity_timeline:
            logged_activity = activity_timeline[second]
            
            # Switch task context if explicit task change
            if logged_activity['activity_type'] in ['TYPING', 'WATCHING']:
                if current_task != logged_activity['activity_type']:
                    # End previous session
                    if current_session:
                        current_session['end_second'] = second - 1
                        current_session['raw_duration'] = current_session['end_second'] - current_session['start_second'] + 1
                        # Deduct mouseout time for this session
                        session_mouseout = len([s for s in mouseout_periods[current_session['task']] 
                                              if current_session['start_second'] <= s <= current_session['end_second']])
                        current_session['effective_duration'] = current_session['raw_duration'] - session_mouseout
                        current_session['mouseout_deducted'] = session_mouseout
                        task_sessions.append(current_session)
                    
                    # Start new session
                    current_task = logged_activity['activity_type']
                    current_session = {
                        'task': current_task,
                        'start_second': second
                    }
        
        complete_timeline.append({
            'second': second + 1,  # 1-indexed for CDF
            'task': current_task,
            'logged_activity': activity_timeline.get(second, {}).get('activity', 'no_activity_logged'),
            'is_mouseout': second in mouseout_periods.get(current_task, [])
        })
    
    # Close final session
    if current_session:
        current_session['end_second'] = session_duration - 1
        current_session['raw_duration'] = current_session['end_second'] - current_session['start_second'] + 1
        session_mouseout = len([s for s in mouseout_periods[current_session['task']] 
                              if current_session['start_second'] <= s <= current_session['end_second']])
        current_session['effective_duration'] = current_session['raw_duration'] - session_mouseout
        current_session['mouseout_deducted'] = session_mouseout
        task_sessions.append(current_session)
    
    print(f"  Identified {len(task_sessions)} task sessions:")
    for i, session in enumerate(task_sessions):
        print(f"    Session {i+1}: {session['task']} seconds {session['start_second']}-{session['end_second']} "
              f"(raw: {session['raw_duration']}s, effective: {session['effective_duration']}s, "
              f"mouseout: -{session['mouseout_deducted']}s)")
    
    return {
        'session_duration': session_duration,
        'task_sessions': task_sessions,
        'complete_timeline': complete_timeline,
        'mouseout_analysis': {
            'typing': total_mouseout_typing,
            'watching': total_mouseout_watching,
            'total': total_mouseout_typing + total_mouseout_watching
        },
        'logged_activities': logged_activities
    }

# %%%
# BUILD CORRECTED CDF TRAJECTORY

def build_corrected_cdf(session_data):
    """Build CDF trajectory with mouseout handling"""
    print("STEP 4: Building corrected CDF trajectory...")
    
    timeline = session_data['complete_timeline']
    
    # Build CDF trajectory
    cdf_trajectory = []
    cumulative_typing = 0
    cumulative_effective_typing = 0  # Typing time minus mouseout
    
    for point in timeline:
        # Regular cumulative typing (includes mouseout periods)
        if point['task'] == 'TYPING':
            cumulative_typing += 1
        
        # Effective cumulative typing (excludes mouseout periods)
        if point['task'] == 'TYPING' and not point['is_mouseout']:
            cumulative_effective_typing += 1
        
        cdf_trajectory.append({
            'session_time': point['second'],
            'cumulative_typing_raw': cumulative_typing,
            'cumulative_typing_effective': cumulative_effective_typing,
            'task': point['task'],
            'is_mouseout': point['is_mouseout'],
            'logged_activity': point['logged_activity']
        })
    
    final_raw_typing = cdf_trajectory[-1]['cumulative_typing_raw']
    final_effective_typing = cdf_trajectory[-1]['cumulative_typing_effective']
    mouseout_total = final_raw_typing - final_effective_typing
    
    print(f"  CDF trajectory: {len(cdf_trajectory)} points")
    print(f"  Raw cumulative typing: {final_raw_typing} seconds")
    print(f"  Effective cumulative typing: {final_effective_typing} seconds")
    print(f"  Total mouseout deducted: {mouseout_total} seconds")
    print(f"  Effective typing ratio: {final_effective_typing / len(cdf_trajectory):.3f}")
    
    return cdf_trajectory

# %%%
# VISUALIZATION DATA EXPORT

def export_corrected_data(session_data, cdf_trajectory):
    """Export corrected data for visualization"""
    print("STEP 5: Preparing data for visualization...")
    
    # Calculate summary statistics
    total_typing_sessions = len([s for s in session_data['task_sessions'] if s['task'] == 'TYPING'])
    total_watching_sessions = len([s for s in session_data['task_sessions'] if s['task'] == 'WATCHING'])
    
    avg_typing_session = np.mean([s['effective_duration'] for s in session_data['task_sessions'] if s['task'] == 'TYPING'])
    avg_watching_session = np.mean([s['effective_duration'] for s in session_data['task_sessions'] if s['task'] == 'WATCHING'])
    
    longest_typing = max([s['effective_duration'] for s in session_data['task_sessions'] if s['task'] == 'TYPING'])
    longest_watching = max([s['effective_duration'] for s in session_data['task_sessions'] if s['task'] == 'WATCHING'])
    
    export_data = {
        'summary': {
            'session_duration': session_data['session_duration'],
            'final_effective_typing': cdf_trajectory[-1]['cumulative_typing_effective'],
            'final_raw_typing': cdf_trajectory[-1]['cumulative_typing_raw'],
            'total_mouseout': session_data['mouseout_analysis']['total'],
            'effective_typing_ratio': cdf_trajectory[-1]['cumulative_typing_effective'] / session_data['session_duration'],
            'typing_sessions': total_typing_sessions,
            'watching_sessions': total_watching_sessions,
            'avg_typing_session_duration': avg_typing_session,
            'avg_watching_session_duration': avg_watching_session,
            'longest_typing_session': longest_typing,
            'longest_watching_session': longest_watching
        },
        'task_sessions': session_data['task_sessions'],
        'cdf_trajectory': cdf_trajectory,
        'mouseout_analysis': session_data['mouseout_analysis']
    }
    
    print(f"  Session analysis:")
    print(f"    Total sessions: {len(session_data['task_sessions'])}")
    print(f"    Typing sessions: {total_typing_sessions} (avg: {avg_typing_session:.1f}s, max: {longest_typing}s)")
    print(f"    Watching sessions: {total_watching_sessions} (avg: {avg_watching_session:.1f}s, max: {longest_watching}s)")
    print(f"    Effective typing ratio: {export_data['summary']['effective_typing_ratio']:.3f}")
    
    return export_data

# %%%
# MAIN EXECUTION

def main_corrected_processing():
    """Main function for corrected session processing"""
    print("CORRECTED SESSION PROCESSING WITH MOUSEOUT HANDLING")
    print("="*80)
    
    # Process participant with corrections
    session_data = process_participant_corrected('sess.csv', 0)
    
    # Build corrected CDF
    cdf_trajectory = build_corrected_cdf(session_data)
    
    # Export data
    export_data = export_corrected_data(session_data, cdf_trajectory)
    
    print(f"\n{'='*80}")
    print("CORRECTED ANALYSIS SUMMARY:")
    print("="*80)
    print("✓ Sessions start with TYPING (as specified)")
    print("✓ Mouseout time properly deducted from session durations")
    print("✓ Two CDF trajectories: raw and effective (minus mouseout)")
    print("✓ Task switching properly identified")
    print("✓ Ready for corrected CDF visualization")
    
    # Show comparison
    print(f"\nComparison with original analysis:")
    print(f"  Original cumulative typing: 587 seconds")
    print(f"  Corrected effective typing: {export_data['summary']['final_effective_typing']} seconds")
    print(f"  Mouseout time deducted: {export_data['summary']['total_mouseout']} seconds")
    print(f"  Difference: {587 - export_data['summary']['final_effective_typing']} seconds")
    
    return export_data

if __name__ == "__main__":
    corrected_data = main_corrected_processing()
# %%
