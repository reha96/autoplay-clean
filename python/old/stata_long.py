#!/usr/bin/env python3
"""
STATA LONG-FORMAT DATASET GENERATOR
Creates second-by-second dataset for econometric analysis
Merges with autoplay.csv for treatment, timeChoice, typeCount, and watchedVideo variables
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("STATA LONG-FORMAT DATASET GENERATOR")
print("Second-by-Second Work/Watch Dataset for Econometric Analysis")
print("="*80)

# %%%
# STEP 1: LOAD AND MERGE TREATMENT DATA

def load_treatment_data(autoplay_file='autoplay.csv'):
    """Load treatment, timeChoice, typeCount, and watchedVideo data from autoplay.csv"""
    print("\n📊 STEP 1: Loading treatment data...")
    
    try:
        autoplay_df = pd.read_csv(autoplay_file)
        print(f"Loaded autoplay.csv: {len(autoplay_df)} participants")
        
        # Check required columns
        required_cols = ['treatment', 'timeChoice', 'typeCount', 'watchedVideo']
        missing_cols = [col for col in required_cols if col not in autoplay_df.columns]
        
        if missing_cols:
            print(f"❌ Missing columns in autoplay.csv: {missing_cols}")
            print(f"Available columns: {list(autoplay_df.columns)}")
            return None
        
        # Create participant mapping (assuming row index matches participant_id from sess.csv)
        treatment_data = autoplay_df[['treatment', 'timeChoice', 'typeCount', 'watchedVideo']].copy()
        treatment_data['participant_id'] = range(len(treatment_data))
        
        print(f"✓ Treatment mapping created for {len(treatment_data)} participants")
        print(f"Treatment distribution:")
        print(treatment_data['treatment'].value_counts())
        print(f"\nTimeChoice statistics:")
        print(treatment_data['timeChoice'].describe())
        print(f"\nTypeCount statistics:")
        print(treatment_data['typeCount'].describe())
        print(f"\nWatchedVideo statistics:")
        print(treatment_data['watchedVideo'].describe())
        
        return treatment_data
        
    except FileNotFoundError:
        print(f"❌ Error: {autoplay_file} not found!")
        return None
    except Exception as e:
        print(f"❌ Error loading treatment data: {str(e)}")
        return None

# %%%
# STEP 2: PROCESS SESSION DATA WITH MOUSEOUT DETECTION

def process_participant_with_mouseout(participant_row, participant_id, treatment_info):
    """Process single participant with mouseout detection for >20s consecutive periods"""
    
    # Extract logged activities
    logged_activities = []
    first_timestamp = None
    
    for col_name, value in participant_row.items():
        if pd.notna(value) and isinstance(value, str) and ' ' in value:
            try:
                parts = value.split(' ')
                timestamp = float(parts[0])
                activity = ' '.join(parts[1:])
                
                if first_timestamp is None:
                    first_timestamp = timestamp
                
                relative_second = int(timestamp - first_timestamp)
                logged_activities.append({
                    'relative_second': relative_second,
                    'activity': activity
                })
            except (ValueError, IndexError):
                continue
    
    if len(logged_activities) < 10:
        return None
        
    logged_activities.sort(key=lambda x: x['relative_second'])
    
    # Remove duplicates (keep last activity for each second)
    unique_logs = {log['relative_second']: log for log in logged_activities}
    logged_activities = sorted(list(unique_logs.values()), key=lambda x: x['relative_second'])
    
    session_duration = logged_activities[-1]['relative_second'] + 1
    
    # Create activity map
    activity_map = {log['relative_second']: log['activity'] for log in logged_activities}
    
    # Build original trajectory with task assignments
    original_trajectory = []
    cumulative_typing = 0
    current_task = 'TYPING'  # Start with typing
    
    for second in range(session_duration):
        if second in activity_map:
            activity = activity_map[second]
            if 'current_task:watching' in activity or 'video' in activity:
                current_task = 'WATCHING'
            elif activity in ['typing', 'current_task:typing']:
                current_task = 'TYPING'
        
        # Count typing
        work_this_second = 1 if current_task == 'TYPING' else 0
        if work_this_second:
            cumulative_typing += 1
        
        original_trajectory.append({
            'second': second,
            'work': work_this_second,
            'cumulative_work': cumulative_typing,
            'logged_activity': activity_map.get(second, 'no_activity_logged'),
            'task': current_task
        })
    
    # --- MOUSEOUT DETECTION ---
    # Identify consecutive mouseout periods >20 seconds
    mouseout_flags = [0] * len(original_trajectory)
    
    # Find all mouseout seconds
    mouseout_seconds = []
    for second in range(session_duration):
        if second in activity_map and activity_map[second] == 'mouseout:true':
            mouseout_seconds.append(second)
    
    # Group consecutive mouseout periods
    if mouseout_seconds:
        consecutive_groups = []
        current_group = [mouseout_seconds[0]]
        
        for i in range(1, len(mouseout_seconds)):
            if mouseout_seconds[i] == mouseout_seconds[i-1] + 1:
                current_group.append(mouseout_seconds[i])
            else:
                consecutive_groups.append(current_group)
                current_group = [mouseout_seconds[i]]
        consecutive_groups.append(current_group)
        
        # Flag periods >20 seconds
        for group in consecutive_groups:
            if len(group) > 20:  # More than 20 consecutive seconds
                for second in group:
                    mouseout_flags[second] = 1
    
    # Add mouseout flags to trajectory
    for i, point in enumerate(original_trajectory):
        point['mouseout'] = mouseout_flags[i]
    
    # --- NORMALIZATION TO 1200 SECONDS ---
    if session_duration > 1:
        # Original data for interpolation
        original_seconds = [p['second'] for p in original_trajectory]
        original_work = [p['work'] for p in original_trajectory]
        original_cumulative = [p['cumulative_work'] for p in original_trajectory]
        original_mouseout = [p['mouseout'] for p in original_trajectory]
        
        # Target timeline: 1200 seconds (0-1199)
        target_seconds = np.arange(0, 1200)
        
        # Interpolate (using nearest neighbor for binary variables)
        interpolated_work = np.interp(target_seconds, original_seconds, original_work)
        interpolated_work = np.round(interpolated_work).astype(int)  # Round to 0/1
        
        interpolated_cumulative = np.interp(target_seconds, original_seconds, original_cumulative)
        interpolated_cumulative = np.round(interpolated_cumulative).astype(int)
        
        interpolated_mouseout = np.interp(target_seconds, original_seconds, original_mouseout)
        interpolated_mouseout = np.round(interpolated_mouseout).astype(int)  # Round to 0/1
        
        # Create normalized trajectory
        normalized_trajectory = []
        for i in range(1200):
            normalized_trajectory.append({
                'participant_id': participant_id,
                'second': i,  # 0-indexed seconds
                'work': interpolated_work[i],
                'cumulative_work': interpolated_cumulative[i],
                'mouseout': interpolated_mouseout[i],
                'treatment': treatment_info['treatment'],
                'timeChoice': treatment_info['timeChoice'],
                'typeCount': treatment_info['typeCount'],
                'watchedVideo': treatment_info['watchedVideo']
            })
        
        # Calculate behavior classification
        final_work_time = interpolated_cumulative[-1]
        work_ratio = final_work_time / 1200
        
        if work_ratio > 0.9:
            behavior_type = 'always_workers'
        elif work_ratio < 0.1:
            behavior_type = 'always_watchers'
        else:
            behavior_type = 'swappers'
        
        # Add behavior type to all observations
        for point in normalized_trajectory:
            point['behavior_type'] = behavior_type
            point['work_ratio'] = work_ratio
        
        return normalized_trajectory
    
    return None

# %%%
# STEP 3: CREATE LONG-FORMAT DATASET

def create_long_format_dataset(sess_file='sess.csv', autoplay_file='autoplay.csv'):
    """Create the complete long-format dataset for Stata analysis"""
    print("\n🔄 STEP 2: Creating long-format dataset...")
    
    # Load treatment data
    treatment_data = load_treatment_data(autoplay_file)
    if treatment_data is None:
        return None
    
    # Load session data
    try:
        sess_df = pd.read_csv(sess_file)
        print(f"Loaded sess.csv: {len(sess_df)} participants, {len(sess_df.columns)} columns")
    except FileNotFoundError:
        print(f"❌ Error: {sess_file} not found!")
        return None
    
    # Process all participants
    all_observations = []
    successful_participants = 0
    failed_participants = []
    
    for idx in range(len(sess_df)):
        # Get treatment info for this participant
        if idx < len(treatment_data):
            treatment_info = {
                'treatment': treatment_data.iloc[idx]['treatment'],
                'timeChoice': treatment_data.iloc[idx]['timeChoice'],
                'typeCount': treatment_data.iloc[idx]['typeCount'],
                'watchedVideo': treatment_data.iloc[idx]['watchedVideo']
            }
        else:
            print(f"⚠️ Warning: No treatment data for participant {idx}")
            treatment_info = {
                'treatment': 'unknown',
                'timeChoice': np.nan,
                'typeCount': np.nan,
                'watchedVideo': np.nan
            }
        
        try:
            participant_observations = process_participant_with_mouseout(
                sess_df.iloc[idx], idx, treatment_info
            )
            
            if participant_observations:
                all_observations.extend(participant_observations)
                successful_participants += 1
                
                if successful_participants % 50 == 0:
                    print(f"  Processed {successful_participants} participants...")
            else:
                failed_participants.append(idx)
                
        except Exception as e:
            print(f"Error processing participant {idx}: {str(e)}")
            failed_participants.append(idx)
            continue
    
    print(f"✓ Successfully processed {successful_participants} participants")
    print(f"✗ Failed to process {len(failed_participants)} participants")
    
    if failed_participants:
        print(f"Failed participant IDs: {failed_participants[:10]}{'...' if len(failed_participants) > 10 else ''}")
    
    # Convert to DataFrame
    if all_observations:
        long_df = pd.DataFrame(all_observations)
        print(f"\n📋 Dataset created:")
        print(f"  Total observations: {len(long_df):,}")
        print(f"  Participants: {long_df['participant_id'].nunique()}")
        print(f"  Seconds per participant: {len(long_df) // long_df['participant_id'].nunique()}")
        
        return long_df
    else:
        print("❌ No observations created")
        return None

# %%%
# STEP 4: DATA VALIDATION AND EXPORT

def validate_and_export_dataset(long_df, output_file='stata_dataset.csv'):
    """Validate the dataset and export for Stata"""
    print(f"\n🔍 STEP 3: Validating and exporting dataset...")
    
    if long_df is None:
        print("❌ No dataset to validate")
        return None
    
    # Basic validation
    print("Basic validation:")
    print(f"  Shape: {long_df.shape}")
    print(f"  Participants: {long_df['participant_id'].nunique()}")
    print(f"  Seconds range: {long_df['second'].min()} to {long_df['second'].max()}")
    print(f"  Work variable: {long_df['work'].min()} to {long_df['work'].max()}")
    
    # Check for missing values
    missing_summary = long_df.isnull().sum()
    if missing_summary.any():
        print(f"\nMissing values:")
        for col, missing in missing_summary.items():
            if missing > 0:
                print(f"  {col}: {missing}")
    else:
        print("  ✓ No missing values")
    
    # Treatment distribution
    print(f"\nTreatment distribution:")
    treatment_counts = long_df.groupby('participant_id')['treatment'].first().value_counts()
    for treatment, count in treatment_counts.items():
        print(f"  {treatment}: {count} participants")
    
    # Behavior type distribution
    print(f"\nBehavior type distribution:")
    behavior_counts = long_df.groupby('participant_id')['behavior_type'].first().value_counts()
    for behavior, count in behavior_counts.items():
        print(f"  {behavior}: {count} participants")
    
    # Work and mouseout statistics
    print(f"\nWork statistics:")
    print(f"  Mean work probability: {long_df['work'].mean():.3f}")
    print(f"  Total work observations: {long_df['work'].sum():,}")
    print(f"  Total watch observations: {(long_df['work']==0).sum():,}")
    
    print(f"\nMouseout statistics:")
    print(f"  Mouseout probability: {long_df['mouseout'].mean():.3f}")
    print(f"  Total mouseout observations: {long_df['mouseout'].sum():,}")
    
    # TimeChoice statistics
    print(f"\nTimeChoice statistics:")
    timechoice_stats = long_df.groupby('participant_id')['timeChoice'].first()
    print(f"  Mean: {timechoice_stats.mean():.2f}")
    print(f"  Std: {timechoice_stats.std():.2f}")
    print(f"  Range: {timechoice_stats.min():.0f} to {timechoice_stats.max():.0f}")
    
    # TypeCount statistics
    print(f"\nTypeCount statistics:")
    typecount_stats = long_df.groupby('participant_id')['typeCount'].first()
    print(f"  Mean: {typecount_stats.mean():.2f}")
    print(f"  Std: {typecount_stats.std():.2f}")
    print(f"  Range: {typecount_stats.min():.0f} to {typecount_stats.max():.0f}")
    
    # WatchedVideo statistics
    print(f"\nWatchedVideo statistics:")
    watchedvideo_stats = long_df.groupby('participant_id')['watchedVideo'].first()
    print(f"  Mean: {watchedvideo_stats.mean():.2f}")
    print(f"  Std: {watchedvideo_stats.std():.2f}")
    print(f"  Range: {watchedvideo_stats.min():.0f} to {watchedvideo_stats.max():.0f}")
    
    # Export to CSV
    try:
        # Reorder columns for Stata convenience
        column_order = [
            'participant_id', 'second', 'work', 'cumulative_work', 'mouseout',
            'treatment', 'timeChoice', 'typeCount', 'watchedVideo', 
            'behavior_type', 'work_ratio'
        ]
        
        export_df = long_df[column_order].copy()
        
        # Ensure proper data types
        export_df['participant_id'] = export_df['participant_id'].astype(int)
        export_df['second'] = export_df['second'].astype(int)
        export_df['work'] = export_df['work'].astype(int)
        export_df['cumulative_work'] = export_df['cumulative_work'].astype(int)
        export_df['mouseout'] = export_df['mouseout'].astype(int)
        
        export_df.to_csv(output_file, index=False)
        print(f"\n💾 Dataset exported to: {output_file}")
        print(f"   Ready for import into Stata!")
        
        # Generate Stata import code
        stata_code = f"""
* Stata import code:
import delimited "{output_file}", clear

* Set panel structure
xtset participant_id second

* Label variables
label variable participant_id "Participant ID"
label variable second "Second (0-1199)"
label variable work "Work indicator (1=typing, 0=watching)"
label variable cumulative_work "Cumulative work time"
label variable mouseout "Mouseout >20s indicator"
label variable treatment "Treatment assignment"
label variable timeChoice "Initial time choice preference"
label variable typeCount "Number of typing actions"
label variable watchedVideo "Amount of video watched"
label variable behavior_type "Behavioral classification"
label variable work_ratio "Overall work ratio"

* Create treatment dummy
encode treatment, generate(treatment_num)
generate autoplay = (treatment_num == 1) if !missing(treatment_num)
label variable autoplay "Autoplay treatment (1=on, 0=off)"

* Summary statistics
summarize
xtsum work

* Correlation matrix for key variables
correlate timeChoice typeCount watchedVideo work_ratio
"""
        
        with open('stata_import_code.do', 'w') as f:
            f.write(stata_code)
        
        print(f"   Stata import code saved to: stata_import_code.do")
        
        return export_df
        
    except Exception as e:
        print(f"❌ Error exporting dataset: {str(e)}")
        return None

# %%%
# STEP 5: CREATE SUMMARY STATISTICS

def create_summary_report(long_df):
    """Create a summary report of the dataset"""
    print(f"\n📊 STEP 4: Creating summary report...")
    
    if long_df is None:
        return
    
    # Participant-level summary
    participant_summary = long_df.groupby('participant_id').agg({
        'work': ['sum', 'mean'],
        'cumulative_work': 'max',
        'mouseout': 'sum',
        'treatment': 'first',
        'timeChoice': 'first',
        'typeCount': 'first',
        'watchedVideo': 'first',
        'behavior_type': 'first',
        'work_ratio': 'first'
    }).reset_index()
    
    # Flatten column names
    participant_summary.columns = [
        'participant_id', 'total_work', 'avg_work_prob', 'final_cumulative',
        'total_mouseout', 'treatment', 'timeChoice', 'typeCount', 'watchedVideo',
        'behavior_type', 'work_ratio'
    ]
    
    print("Participant-level summary statistics:")
    print(participant_summary[['total_work', 'avg_work_prob', 'total_mouseout', 
                              'timeChoice', 'typeCount', 'watchedVideo', 'work_ratio']].describe())
    
    # Treatment group comparison
    print(f"\nTreatment group comparison:")
    treatment_comparison = participant_summary.groupby('treatment').agg({
        'total_work': ['mean', 'std'],
        'avg_work_prob': ['mean', 'std'],
        'total_mouseout': ['mean', 'std'],
        'timeChoice': ['mean', 'std'],
        'typeCount': ['mean', 'std'],
        'watchedVideo': ['mean', 'std']
    })
    print(treatment_comparison)
    
    # Behavior type comparison
    print(f"\nBehavior type comparison:")
    behavior_comparison = participant_summary.groupby('behavior_type').agg({
        'total_work': ['mean', 'std', 'count'],
        'timeChoice': ['mean', 'std'],
        'typeCount': ['mean', 'std'],
        'watchedVideo': ['mean', 'std']
    })
    print(behavior_comparison)
    
    # Correlation analysis
    print(f"\nCorrelation analysis:")
    corr_vars = ['timeChoice', 'typeCount', 'watchedVideo', 'total_work', 'work_ratio']
    correlation_matrix = participant_summary[corr_vars].corr()
    print(correlation_matrix)
    
    return participant_summary

# %%%
# MAIN EXECUTION

def main():
    """Main execution function"""
    print("Starting Stata long-format dataset generation...")
    
    try:
        # Create the long-format dataset
        long_df = create_long_format_dataset('sess.csv', 'autoplay.csv')
        
        if long_df is not None:
            # Validate and export
            export_df = validate_and_export_dataset(long_df, 'stata_dataset.csv')
            
            if export_df is not None:
                # Create summary report
                participant_summary = create_summary_report(long_df)
                
                print(f"\n{'='*80}")
                print("🎉 DATASET GENERATION COMPLETE!")
                print("="*80)
                print(f"✓ Long-format dataset created: {len(long_df):,} observations")
                print(f"✓ {long_df['participant_id'].nunique()} participants × 1200 seconds each")
                print(f"✓ Treatment, timeChoice, typeCount, and watchedVideo variables merged")
                print(f"✓ Mouseout periods >20s identified")
                print(f"✓ Ready for Stata econometric analysis")
                
                print(f"\n📋 Files created:")
                print(f"   - stata_dataset.csv (main dataset)")
                print(f"   - stata_import_code.do (Stata import script)")
                
                print(f"\n🔧 Suggested Stata analyses:")
                print(f"   - Conditional logistic regression: clogit work time treatment")
                print(f"   - Panel data models: xtlogit work time treatment")
                print(f"   - Treatment effect heterogeneity: interactions with behavior_type")
                print(f"   - Dynamic models: including lagged work variable")
                print(f"   - Pre-treatment controls: typeCount and watchedVideo as controls")
                print(f"   - Mechanism analysis: treatment effects on typeCount/watchedVideo")
                print(f"   - CDF reconstruction: line cumulative_work second, by(participant_id)")
                
                return long_df, participant_summary
            
        return None
        
    except Exception as e:
        print(f"❌ Error in main execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()
# %%