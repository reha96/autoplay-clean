# %%%
#!/usr/bin/env python3
"""
COMPLETE CDF ANALYSIS - End-to-End Pipeline
Combines data processing and visualization in one script
Uses linear interpolation for robust session normalization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("="*80)
print("COMPLETE CDF ANALYSIS PIPELINE")
print("Participant Journey Reconstruction with Task Switching")
print("="*80)

# %%%
# STEP 1: PROCESS ALL PARTICIPANTS (with corrected interpolation)
def process_all_participants_simple(csv_file='sess.csv'):
    """
    Processes participant data, reconstructing session trajectories.
    Normalizes all sessions to 1200 seconds using linear interpolation
    to avoid artifacts from manual scaling.
    """
    print("\n🔄 STEP 1: Processing all participants with interpolation...")
    
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} participants, {len(df.columns)} columns")
    
    all_trajectories = []
    behavior_counts = {'always_workers': 0, 'swappers': 0, 'always_watchers': 0}
    
    for idx in range(len(df)):
        try:
            participant = df.iloc[idx]
            
            # Extract session data from participant row
            logged_activities = []
            first_timestamp = None
            
            for col_name, value in participant.items():
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
                        # Ignore columns that don't fit the timestamped activity format
                        continue
            
            if len(logged_activities) < 10:  # Skip participants with too little data
                continue
                
            logged_activities.sort(key=lambda x: x['relative_second'])
            
            # Prevent duplicate seconds by keeping the last activity for a given second
            unique_logs = {log['relative_second']: log for log in logged_activities}
            logged_activities = sorted(list(unique_logs.values()), key=lambda x: x['relative_second'])
            
            session_duration = logged_activities[-1]['relative_second'] + 1
            
            # Generate original, un-normalized CDF trajectory
            trajectory = []
            cumulative_typing = 0
            current_task = 'TYPING'  # Assume starting with typing

            activity_map = {log['relative_second']: log['activity'] for log in logged_activities}
            
            for second in range(session_duration):
                if second in activity_map:
                    activity = activity_map[second]
                    if 'current_task:watching' in activity or 'video' in activity:
                        current_task = 'WATCHING'
                    elif activity in ['typing', 'current_task:typing']:
                        current_task = 'TYPING'
                
                if current_task == 'TYPING':
                    cumulative_typing += 1
                
                trajectory.append({
                    'session_time': second + 1,
                    'cumulative_typing': cumulative_typing,
                })

            # --- NORMALIZATION USING LINEAR INTERPOLATION ---
            # This is the corrected section to prevent artificial peaks
            if len(trajectory) > 1:
                # Original data points for interpolation
                original_x = [p['session_time'] for p in trajectory]
                original_y = [p['cumulative_typing'] for p in trajectory]
                
                # Target timeline: 1200 seconds
                target_x = np.arange(1, 1201)
                
                # Interpolate the cumulative typing values onto the new timeline
                interpolated_y = np.interp(target_x, original_x, original_y)
                
                # Create the final, normalized trajectory
                normalized_trajectory = []
                for i in range(len(target_x)):
                    normalized_trajectory.append({
                        'session_time': int(target_x[i]),
                        'cumulative_typing': int(interpolated_y[i]),
                        'task': 'N/A' # Task is not interpolated, only cumulative time
                    })

            else: # Skip if not enough data to interpolate
                continue

            # Behavior classification based on the final normalized typing time
            final_typing = normalized_trajectory[-1]['cumulative_typing']
            typing_ratio = final_typing / 1200.0
            
            if typing_ratio > 0.9:
                behavior_type = 'always_workers'
            elif typing_ratio < 0.1:
                behavior_type = 'always_watchers'
            else:
                behavior_type = 'swappers'
            
            behavior_counts[behavior_type] += 1
            
            all_trajectories.append({
                'participant_id': idx,
                'behavior_type': behavior_type,
                'typing_ratio': typing_ratio,
                'final_typing_time': final_typing,
                'trajectory': normalized_trajectory
            })
                
        except Exception as e:
            print(f"Error processing participant {idx}: {str(e)}")
            continue
    
    print(f"✓ Successfully processed {len(all_trajectories)} participants")
    print(f"  Always Workers: {behavior_counts['always_workers']}")
    print(f"  Swappers: {behavior_counts['swappers']}")
    print(f"  Always Watchers: {behavior_counts['always_watchers']}")
    
    return all_trajectories, behavior_counts

# %%%
# STEP 2: CREATE VISUALIZATIONS (No changes needed here)

def create_cdf_visualizations(all_trajectories, behavior_counts):
    """Create comprehensive CDF visualizations"""
    print("\n📊 STEP 2: Creating visualizations...")
    
    behavior_colors = {
        'always_workers': '#27ae60',
        'swappers': '#f39c12', 
        'always_watchers': '#e74c3c'
    }
    
    # Prepare data
    df_trajectories = []
    for participant in all_trajectories:
        for point in participant['trajectory']:
            df_trajectories.append({
                'participant_id': participant['participant_id'],
                'session_time': point['session_time'],
                'cumulative_typing': point['cumulative_typing'],
                'task': point['task'],
                'behavior_type': participant['behavior_type'],
                'typing_ratio': participant['typing_ratio']
            })
    
    if not df_trajectories:
        print("No data to visualize. Exiting visualization step.")
        return None, None
        
    df_trajectories = pd.DataFrame(df_trajectories)
    
    # Calculate average trajectories
    avg_trajectories = {}
    for behavior in behavior_colors.keys():
        if behavior in df_trajectories['behavior_type'].unique():
            behavior_data = df_trajectories[df_trajectories['behavior_type'] == behavior]
            avg_traj = behavior_data.groupby('session_time')['cumulative_typing'].agg(['mean', 'std']).reset_index()
            avg_trajectories[behavior] = avg_traj
    
    # Create the main visualization
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('Complete CDF Analysis: Participant Work Journey Reconstruction\n' + 
                 '1200s Interpolated Normalization | Task Switching Patterns', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Individual trajectories sample
    ax1 = axes[0, 0]
    unique_pids = df_trajectories['participant_id'].unique()
    sample_participants = unique_pids[:min(30, len(unique_pids))]
    
    for pid in sample_participants:
        participant_data = df_trajectories[df_trajectories['participant_id'] == pid]
        behavior = participant_data['behavior_type'].iloc[0]
        
        ax1.plot(participant_data['session_time'], 
                participant_data['cumulative_typing'],
                color=behavior_colors[behavior], 
                alpha=0.4, 
                linewidth=1.5)
    
    ax1.set_xlabel('Session Time (seconds)')
    ax1.set_ylabel('Cumulative Typing Time (seconds)')
    ax1.set_title('Individual Trajectories (Sample of 30)')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Behavior type averages
    ax2 = axes[0, 1]
    
    for behavior, trajectory in avg_trajectories.items():
        color = behavior_colors[behavior]
        label = behavior.replace('_', ' ').title()
        count = behavior_counts.get(behavior, 0)
        
        ax2.plot(trajectory['session_time'], trajectory['mean'], 
                color=color, linewidth=4, label=f'{label} (n={count})')
        
        # Add confidence band
        ax2.fill_between(trajectory['session_time'], 
                        trajectory['mean'] - trajectory['std'],
                        trajectory['mean'] + trajectory['std'],
                        color=color, alpha=0.2)
    
    ax2.set_xlabel('Session Time (seconds)')
    ax2.set_ylabel('Cumulative Typing Time (seconds)')
    ax2.set_title('Average Trajectories by Behavior Type')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Comprehensive view
    ax3 = axes[0, 2]
    
    # Faded individual lines
    for pid in sample_participants[:min(20, len(sample_participants))]:
        participant_data = df_trajectories[df_trajectories['participant_id'] == pid]
        behavior = participant_data['behavior_type'].iloc[0]
        
        ax3.plot(participant_data['session_time'], 
                participant_data['cumulative_typing'],
                color=behavior_colors[behavior], 
                alpha=0.15, 
                linewidth=1)
    
    # Bold averages
    for behavior, trajectory in avg_trajectories.items():
        color = behavior_colors[behavior]
        label = behavior.replace('_', ' ').title()
        
        ax3.plot(trajectory['session_time'], trajectory['mean'], 
                color=color, linewidth=4, label=label, zorder=10)
    
    ax3.set_xlabel('Session Time (seconds)')
    ax3.set_ylabel('Cumulative Typing Time (seconds)')
    ax3.set_title('Individual + Average Combined')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Behavior distribution
    ax4 = axes[1, 0]
    
    labels = [k.replace('_', ' ').title() for k in behavior_counts.keys()]
    sizes = list(behavior_counts.values())
    colors = [behavior_colors[k] for k in behavior_counts.keys()]
    
    if sum(sizes) > 0:
        ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax4.set_title('Behavior Type Distribution')
    
    # Plot 5: Final typing time distribution
    ax5 = axes[1, 1]
    
    for behavior in behavior_colors.keys():
        if behavior in df_trajectories['behavior_type'].unique():
            behavior_data = df_trajectories[df_trajectories['behavior_type'] == behavior]
            final_times = behavior_data.groupby('participant_id')['cumulative_typing'].max()
            
            ax5.hist(final_times, bins=20, alpha=0.6, 
                    color=behavior_colors[behavior], 
                    label=behavior.replace('_', ' ').title())
    
    ax5.set_xlabel('Final Typing Time (seconds)')
    ax5.set_ylabel('Number of Participants')
    ax5.set_title('Distribution of Final Typing Times')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Task switching patterns
    ax6 = axes[1, 2]
    
    # Calculate typing rates over time windows
    window_size = 120  # 2-minute windows
    time_windows = range(0, 1200, window_size)
    
    for behavior, trajectory in avg_trajectories.items():
        color = behavior_colors[behavior]
        label = behavior.replace('_', ' ').title()
        
        typing_rates = []
        window_centers = []
        
        for start_time in time_windows:
            end_time = start_time + window_size
            # Ensure we select data correctly from the trajectory DataFrame
            start_val_row = trajectory[trajectory['session_time'] == start_time]
            end_val_row = trajectory[trajectory['session_time'] == end_time -1]

            if not start_val_row.empty and not end_val_row.empty:
                typing_gained = end_val_row['mean'].iloc[0] - start_val_row['mean'].iloc[0]
                rate = typing_gained / window_size
                typing_rates.append(rate)
                window_centers.append(start_time + window_size / 2)
        
        if window_centers:
            ax6.plot(window_centers, typing_rates, 
                    color=color, linewidth=3, marker='o', label=label)
    
    ax6.set_xlabel('Session Time (seconds)')
    ax6.set_ylabel('Typing Rate (seconds/second)')
    ax6.set_title('Typing Rate Over Time (2-min windows)')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    ax6.set_ylim(0, 1.1) # Set y-limit to handle potential small overshoots
    
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout to make room for suptitle
    plt.savefig('complete_cdf_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ Main visualization completed")
    
    # Create detailed analysis plot
    create_detailed_analysis_plot(df_trajectories, avg_trajectories, behavior_counts)
    
    return df_trajectories, avg_trajectories

def create_detailed_analysis_plot(df_trajectories, avg_trajectories, behavior_counts):
    """Create detailed analysis with focus on patterns"""
    if df_trajectories is None or avg_trajectories is None:
        print("Skipping detailed analysis due to no data.")
        return

    print("📈 Creating detailed pattern analysis...")
    
    behavior_colors = {
        'always_workers': '#27ae60',
        'swappers': '#f39c12', 
        'always_watchers': '#e74c3c'
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Detailed CDF Pattern Analysis\nTask Switching & Work Allocation Strategies', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: CDF trajectories with key points highlighted
    ax1 = axes[0, 0]
    
    for behavior, trajectory in avg_trajectories.items():
        color = behavior_colors[behavior]
        label = behavior.replace('_', ' ').title()
        
        ax1.plot(trajectory['session_time'], trajectory['mean'], 
                color=color, linewidth=4, label=label)
        
        # Highlight key time points
        key_times = [300, 600, 900, 1199]  # 5, 10, 15, 20 minutes
        for time_point in key_times:
            val_row = trajectory[trajectory['session_time'] == time_point]
            if not val_row.empty:
                typing_at_time = val_row['mean'].iloc[0]
                ax1.scatter(time_point, typing_at_time, color=color, s=100, zorder=10)
    
    ax1.set_xlabel('Session Time (seconds)')
    ax1.set_ylabel('Cumulative Typing Time (seconds)')
    ax1.set_title('CDF Trajectories with Key Time Points')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add diagonal reference line (perfect typing efficiency)
    ax1.plot([0, 1200], [0, 1200], 'k--', alpha=0.3, label='Perfect Efficiency')
    ax1.legend()

    # Plot 2: Typing efficiency over time
    ax2 = axes[0, 1]
    
    for behavior, trajectory in avg_trajectories.items():
        color = behavior_colors[behavior]
        label = behavior.replace('_', ' ').title()
        
        # Calculate efficiency (cumulative typing / time elapsed), avoid division by zero
        efficiency = trajectory['mean'] / trajectory['session_time'].replace(0, 1)
        
        ax2.plot(trajectory['session_time'], efficiency, 
                color=color, linewidth=3, label=label)
    
    ax2.set_xlabel('Session Time (seconds)')
    ax2.set_ylabel('Typing Efficiency (cumulative/elapsed)')
    ax2.set_title('Typing Efficiency Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1.1)
    
    # Plot 3: Work allocation strategy comparison
    ax3 = axes[1, 0]
    
    quartile_times = [0, 300, 600, 900, 1200]
    quartile_labels = ['Q1 (0-5min)', 'Q2 (5-10min)', 'Q3 (10-15min)', 'Q4 (15-20min)']
    
    behavior_quartiles = {b.replace('_', ' ').title(): [] for b in behavior_colors.keys()}
    
    for behavior, trajectory in avg_trajectories.items():
        prev_typing = 0
        for i in range(len(quartile_times) - 1):
            start_time, end_time = quartile_times[i], quartile_times[i+1]
            end_row = trajectory[trajectory['session_time'] == end_time - 1]
            if not end_row.empty:
                current_typing = end_row['mean'].iloc[0]
                behavior_quartiles[behavior.replace('_', ' ').title()].append(current_typing - prev_typing)
                prev_typing = current_typing
            else:
                behavior_quartiles[behavior.replace('_', ' ').title()].append(0)

    # Create stacked bar chart
    width = 0.5
    bottom = np.zeros(len(behavior_quartiles))
    
    for i, label in enumerate(quartile_labels):
        values = [q[i] for q in behavior_quartiles.values() if q]
        if not values: continue
        ax3.bar(behavior_quartiles.keys(), values, width, label=label, bottom=bottom)
        bottom += values

    ax3.set_ylabel('Typing Time (seconds)')
    ax3.set_title('Work Allocation by Time Quartiles')
    ax3.legend()
    plt.setp(ax3.get_xticklabels(), rotation=15, ha="right")
    
    # Plot 4: Summary statistics table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    stats_data = []
    col_colors = []
    
    for behavior in behavior_colors.keys():
        if behavior in df_trajectories['behavior_type'].unique():
            behavior_data = df_trajectories[df_trajectories['behavior_type'] == behavior]
            final_times = behavior_data.groupby('participant_id')['cumulative_typing'].max()
            
            stats_data.append([
                behavior.replace('_', ' ').title(),
                len(final_times),
                f"{final_times.mean():.0f}",
                f"{final_times.std():.0f}",
                f"{final_times.mean()/1200:.2f}"
            ])
            col_colors.append(behavior_colors[behavior])
    
    all_final_times = df_trajectories.groupby('participant_id')['cumulative_typing'].max()
    stats_data.append([
        'OVERALL',
        len(all_final_times),
        f"{all_final_times.mean():.0f}",
        f"{all_final_times.std():.0f}",
        f"{all_final_times.mean()/1200:.2f}"
    ])
    col_colors.append('#7f8c8d') # Grey for overall

    table = ax4.table(cellText=stats_data, 
                      colLabels=['Behavior Type', 'N', 'Mean\nTyping', 'Std\nDev', 'Efficiency\nRatio'],
                      cellLoc='center', loc='center',
                      colColours=['#ecf0f1']*5)

    for i in range(len(stats_data)):
        table[(i+1, 0)].set_facecolor(col_colors[i])
        table[(i+1, 0)].set_alpha(0.4)

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.1, 1.8)
    ax4.set_title('Summary Statistics\n(1200s Interpolated Sessions)', fontweight='bold', y=0.8)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('detailed_cdf_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ Detailed analysis completed")

# %%%
# MAIN EXECUTION

def main():
    """Main execution function"""
    print("Starting complete CDF analysis pipeline...")
    
    try:
        # Step 1: Process all participants
        all_trajectories, behavior_counts = process_all_participants_simple('sess.csv')
        
        if not all_trajectories:
            print("❌ No participants were successfully processed. Halting analysis.")
            return None

        # Step 2: Create visualizations
        df_trajectories, avg_trajectories = create_cdf_visualizations(all_trajectories, behavior_counts)
        
        # Step 3: Print summary
        print(f"\n{'='*80}")
        print("🎉 ANALYSIS COMPLETE!")
        print("="*80)
        total_participants = len(all_trajectories)
        print(f"✓ Processed {total_participants} participants")
        print(f"✓ Generated comprehensive CDF visualizations with interpolation")
        print(f"✓ Identified {len(behavior_counts)} behavior types:")
        
        for behavior, count in behavior_counts.items():
            percentage = (count / total_participants * 100) if total_participants > 0 else 0
            print(f"    - {behavior.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Calculate overall statistics
        all_final_times = [p['final_typing_time'] for p in all_trajectories]
        if all_final_times:
            print(f"\n📊 Overall Statistics:")
            print(f"    - Mean typing time: {np.mean(all_final_times):.0f}s ({np.mean(all_final_times)/1200:.1%})")
            print(f"    - Median typing time: {np.median(all_final_times):.0f}s")
            print(f"    - Standard deviation: {np.std(all_final_times):.0f}s")
        
        print(f"\n📁 Files saved:")
        print(f"    - complete_cdf_analysis.png")
        print(f"    - detailed_cdf_analysis.png")
        
        return all_trajectories, df_trajectories, avg_trajectories, behavior_counts
        
    except FileNotFoundError:
        print("❌ Error: 'sess.csv' file not found!")
        print("Please ensure the session data file is in the current directory.")
        return None
        
    except Exception as e:
        print(f"❌ An unexpected error occurred during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()
# %%