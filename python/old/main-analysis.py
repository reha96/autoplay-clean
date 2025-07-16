# %%% import packages & data
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats.mstats import winsorize
from scipy.stats import mannwhitneyu
from scipy.stats import ranksums
import statsmodels.api as sm
import statsmodels.formula.api as smf

# cleaned dataset from the last data collection
clean_data = pd.read_csv("clean-data.csv")
# %% table 1

# Calculate Age column
clean_data["Age"] = 2023 - clean_data["birthyear"]

# Calculate statistics for each treatment and overall
treatments = clean_data["treatment"].dropna().unique()

# Initialize results list
results = []

# For Mean
for treatment in treatments:
    subset = clean_data[clean_data["treatment"] == treatment]
    mean_age = subset["Age"].mean()
    std_age = subset["Age"].std()
    results.append(f"{mean_age:.2f} ({std_age:.2f})")
overall_mean_age = clean_data["Age"].mean()
overall_std_age = clean_data["Age"].std()
results.append(f"{overall_mean_age:.2f} ({overall_std_age:.2f})")

# For Median
for treatment in treatments:
    subset = clean_data[clean_data["treatment"] == treatment]
    median_age = subset["Age"].median()
    min_age = subset["Age"].min()
    max_age = subset["Age"].max()
    results.append(f"{median_age:.2f} [{min_age:.2f}, {max_age:.2f}]")
overall_median_age = clean_data["Age"].median()
overall_min_age = clean_data["Age"].min()
overall_max_age = clean_data["Age"].max()
results.append(
    f"{overall_median_age:.2f} [{overall_min_age:.2f}, {overall_max_age:.2f}]"
)

# Convert results to DataFrame
columns = list(treatments) + ["Overall"]
data = np.array(results).reshape(2, len(columns))
results_df = pd.DataFrame(data, columns=columns)
results_df["Age"] = ["Mean (SD)", "Median [Min, Max]"]
cols = results_df.columns.tolist()
cols = cols[-1:] + cols[:-1]
results_df = results_df[cols]

# Add a new row to results_df with the first value being the value of the first column and the rest being NaN
new_row = pd.Series({results_df.columns[0]: results_df.columns[0]}, name="new")
results_df_with_new_row = pd.concat([results_df, new_row.to_frame().T])

# Make the "new" row the first row and reset the index
results_df_reordered = pd.concat([new_row.to_frame().T, results_df]).reset_index(
    drop=True
)
# Change the name of the first column to "Variable"
results_df_reordered.rename(
    columns={results_df_reordered.columns[0]: "Variable"}, inplace=True
)
results_df_reordered


# Calculate rest of columns

# Helper function to calculate distribution statistics for categorical variables
def get_categorical_distribution(dataframe, column):
    results = []
    # Unique levels for the column
    levels = dataframe[column].dropna().unique()

    for level in levels:
        row_results = [level]
        for treatment in treatments:
            subset = dataframe[
                (dataframe["treatment"] == treatment) & (dataframe[column] == level)
            ]
            count = len(subset)
            total = len(dataframe[dataframe["treatment"] == treatment])
            percentage = (count / total) * 100
            row_results.append(f"{count} ({percentage:.2f}%)")

        # Overall
        overall_count = len(dataframe[dataframe[column] == level])
        overall_percentage = (overall_count / len(dataframe)) * 100
        row_results.append(f"{overall_count} ({overall_percentage:.2f}%)")
        results.append(row_results)

    # Convert results to DataFrame
    df = pd.DataFrame(
        results, columns=[column.capitalize()] + list(treatments) + ["Overall"]
    )
    return df


# Calculate distribution statistics for the given columns
columns_to_process = ["employment", "gender", "income", "marital"]
distribution_dfs = {
    col: get_categorical_distribution(clean_data, col) for col in columns_to_process
}

# Applying the specified operations to each DataFrame in distribution_dfs


def apply_operations(df):
    # Add a new row with the first value being the value of the first column and the rest being NaN
    new_row = pd.Series({df.columns[0]: df.columns[0]}, name="new")

    # Make the "new" row the first row and reset the index
    df_reordered = pd.concat([new_row.to_frame().T, df]).reset_index(drop=True)

    # Change the name of the first column to "Variable"
    df_reordered.rename(columns={df_reordered.columns[0]: "Variable"}, inplace=True)

    return df_reordered


modified_distribution_dfs_updated = {
    key: apply_operations(df.copy()) for key, df in distribution_dfs.items()
}

list(modified_distribution_dfs_updated.values())

# Merge DataFrames in modified_distribution_dfs_updated by rows
merged_by_rows_df = pd.concat(
    modified_distribution_dfs_updated.values(), ignore_index=True
)

table1 = pd.concat([results_df_reordered, merged_by_rows_df], ignore_index=True)

table1.to_csv("table1.csv", index=False)

# %% Graph 1: Distribution of End Time across treatments

# Plot with the correct adjustments for the legend
g = sns.displot(
    data=clean_data,
    x="end_time_log",
    hue="Treatment",
    kind="hist",
    fill=True,
    palette="deep",
    height=6,
    aspect=1.5,
    binwidth=30,
    legend=True,
)

# Adding a box around the plot
g.ax.spines["top"].set_visible(True)
g.ax.spines["right"].set_visible(True)
g.ax.spines["bottom"].set_visible(True)
g.ax.spines["left"].set_visible(True)

# Adjusting the legend
g._legend.set_title("Treatment")
g._legend.set_bbox_to_anchor((0.75, 0.75))
g._legend.set_frame_on(True)

# Setting x-axis and y-axis labels
g.ax.set_xlabel("End Time in seconds")
g.ax.set_ylabel("Count")

plt.show()

# %% Mann-Whitney U Test for equal population distribution for the effect of the glitch on end time

# Getting the data for the two treatments
autoplay_data = clean_data[clean_data["Treatment"] == "Autoplay"]["end_time_log"]
control_data = clean_data[clean_data["Treatment"] == "Control"]["end_time_log"]

# Applying the Mann-Whitney U Test
statistic, p_value = mannwhitneyu(autoplay_data, control_data, alternative="two-sided")

statistic, p_value

# %%  Normalizing data & graph 2a:

# Creating the new columns "typing_normalized" and "watching_normalized"
clean_data["typing_normalized"] = (
    clean_data["typing_log"] / clean_data["end_time_log"]
) * 1200
clean_data["watching_normalized"] = (
    clean_data["watching_log"] / clean_data["end_time_log"]
) * 1200

# Plot with the correct adjustments for the legend
g = sns.displot(
    data=clean_data,
    x="watching_normalized",
    hue="Treatment",
    kind="hist",
    fill=True,
    palette="deep",
    height=6,
    aspect=1.5,
    binwidth=90,
    legend=True,
)

# Adding a box around the plot
g.ax.spines["top"].set_visible(True)
g.ax.spines["right"].set_visible(True)
g.ax.spines["bottom"].set_visible(True)
g.ax.spines["left"].set_visible(True)

# Adjusting the legend
g._legend.set_title("Treatment")
g._legend.set_bbox_to_anchor((0.75, 0.75))
g._legend.set_frame_on(True)

# Setting x-axis and y-axis labels
g.ax.set_xlabel("Watching Time in seconds")
g.ax.set_ylabel("Count")

plt.show()

# %% Mann-Whitney U Test for equal population distribution for watching time on second data, then number of videos watched)

# Getting the data for the two treatments
autoplay_data = clean_data[clean_data["Treatment"] == "Autoplay"]["watching_normalized"]
control_data = clean_data[clean_data["Treatment"] == "Control"]["watching_normalized"]

# Applying the Mann-Whitney U Test
statistic, p_value = mannwhitneyu(autoplay_data, control_data, alternative="two-sided")

statistic, p_value

# %%  Graph 2b: Distribution of number of videos watched by condition

# Plot with the correct adjustments for the legend
g = sns.displot(
    data=clean_data,
    x="watchedVideo",
    hue="Treatment",
    kind="hist",
    fill=True,
    palette="deep",
    height=6,
    aspect=1.5,
    binwidth=5,
    legend=True,
)

# Adding a box around the plot
g.ax.spines["top"].set_visible(True)
g.ax.spines["right"].set_visible(True)
g.ax.spines["bottom"].set_visible(True)
g.ax.spines["left"].set_visible(True)

# Adjusting the legend
g._legend.set_title("Treatment")
g._legend.set_bbox_to_anchor((0.75, 0.75))
g._legend.set_frame_on(True)

# Setting x-axis and y-axis labels
g.ax.set_xlabel("Number of videos watched")
g.ax.set_ylabel("Count")

plt.show()

# %% Mann-Whitney U Test for equal population distribution for the number of videos watched

# Getting the data for the two treatments
autoplay_data = clean_data[clean_data["Treatment"] == "Autoplay"]["watchedVideo"]
control_data = clean_data[clean_data["Treatment"] == "Control"]["watchedVideo"]

# Applying the Mann-Whitney U Test
statistic, p_value = mannwhitneyu(autoplay_data, control_data, alternative="two-sided")

statistic, p_value

# %%  Graph 3: Distribution of initial Time Choices by condition

# Plot with the correct adjustments for the legend
g = sns.displot(
    data=clean_data,
    x="timeChoice",
    hue="Treatment",
    kind="hist",
    fill=True,
    palette="deep",
    height=6,
    aspect=1.5,
    binwidth=60,
    legend=True,
)

# Adding a box around the plot
g.ax.spines["top"].set_visible(True)
g.ax.spines["right"].set_visible(True)
g.ax.spines["bottom"].set_visible(True)
g.ax.spines["left"].set_visible(True)

# Adjusting the legend
g._legend.set_title("Treatment")
g._legend.set_bbox_to_anchor((0.75, 0.75))
g._legend.set_frame_on(True)

# Setting x-axis and y-axis labels
g.ax.set_xlabel("Time Choice in seconds")
g.ax.set_ylabel("Count")

plt.show()

# %% Mann-Whitney U Test for equal population distribution for the number of videos watched

# Getting the data for the two treatments
autoplay_data = clean_data[clean_data["Treatment"] == "Autoplay"]["watchedVideo"]
control_data = clean_data[clean_data["Treatment"] == "Control"]["watchedVideo"]

# Applying the Mann-Whitney U Test
statistic, p_value = mannwhitneyu(autoplay_data, control_data, alternative="two-sided")

statistic, p_value

# %% Mann-Whitney U Test on the "Time Choice" across treatments

# Extracting data for the two groups: Autoplay and Control
autoplay_data = clean_data[clean_data["Treatment"] == "Autoplay"]["timeChoice"]
control_data = clean_data[clean_data["Treatment"] == "Control"]["timeChoice"]

# Performing the Mann-Whitney U Test
u_statistic, p_value = mannwhitneyu(
    autoplay_data, control_data, alternative="two-sided"
)

u_statistic, p_value

# %% Hypothesis 3: Deviation from Time Choice

# Creating a new column by dividing "timeChoice" by 1200
clean_data["allocated_typing"] = clean_data["timeChoice"] / 1200 * 100

# Creating a new column by dividing "typing_normalized" by 1200
clean_data["actualized_typing"] = clean_data["typing_normalized"] / 1200 * 100

# Creating a new column by subtracting "actualized_typing" from "allocated_typing"
clean_data["diff_typing_pcent"] = (
    clean_data["allocated_typing"] - clean_data["actualized_typing"]
)

# %% Mann-Whitney U Test on the difference between initial and actualized choices across treatments

# Extracting data for the two groups: Autoplay and Control
autoplay_data = clean_data[clean_data["Treatment"] == "Autoplay"]["diff_typing_pcent"]
control_data = clean_data[clean_data["Treatment"] == "Control"]["diff_typing_pcent"]

# Performing the Mann-Whitney U Test
u_statistic, p_value = mannwhitneyu(
    autoplay_data, control_data, alternative="two-sided"
)

u_statistic, p_value

# %% Graph 4: Distribution of the deviation from initial Time Choice in percentages across treatments

# Plot with the correct adjustments for the legend
g = sns.displot(
    data=clean_data,
    x="diff_typing_pcent",
    hue="Treatment",
    kind="hist",
    fill=True,
    palette="deep",
    height=6,
    aspect=1.5,
    binwidth=25,
    legend=True,
)

# Adding a box around the plot
g.ax.spines["top"].set_visible(True)
g.ax.spines["right"].set_visible(True)
g.ax.spines["bottom"].set_visible(True)
g.ax.spines["left"].set_visible(True)

# Adjusting the legend
g._legend.set_title("Treatment")
g._legend.set_bbox_to_anchor((0.75, 0.75))
g._legend.set_frame_on(True)

# Setting x-axis and y-axis labels
g.ax.set_xlabel("Deviation from Time Choice in percentages")
g.ax.set_ylabel("Count")

plt.show()

# %% Table 2 : Sample statistics for variables of interest

# Getting the treatments from the updated clean_data
treatments_updated = clean_data["Treatment"].dropna().unique()

# Initialize results list for the updated treatments
all_results_updated_treatments = []

# variables of interest
variables_updated = ['content',
 'tabCounter',
 'typeCount',
 'watchedVideo',
 'timeChoice',
 'typing_normalized',
 'watching_normalized']

# Adjusting the code to use `concat` instead of `append`

all_results_final_format_corrected = []

for variable in variables_updated:
    results = []
    
    # For Mean
    for treatment in treatments_updated:
        subset = clean_data[clean_data["Treatment"] == treatment]
        mean_value = subset[variable].mean()
        std_value = subset[variable].std()
        results.append(f"{mean_value:.2f} ({std_value:.2f})")
    overall_mean_value = clean_data[variable].mean()
    overall_std_value = clean_data[variable].std()
    results.append(f"{overall_mean_value:.2f} ({overall_std_value:.2f})")
    
    # For Median
    for treatment in treatments_updated:
        subset = clean_data[clean_data["Treatment"] == treatment]
        median_value = subset[variable].median()
        min_value = subset[variable].min()
        max_value = subset[variable].max()
        results.append(f"{median_value:.2f} [{min_value:.2f}, {max_value:.2f}]")
    overall_median_value = clean_data[variable].median()
    overall_min_value = clean_data[variable].min()
    overall_max_value = clean_data[variable].max()
    results.append(
        f"{overall_median_value:.2f} [{overall_min_value:.2f}, {overall_max_value:.2f}]"
    )
    
    # Convert results to DataFrame
    columns = list(treatments_updated) + ["Overall"]
    data = np.array(results).reshape(2, len(columns))
    results_df = pd.DataFrame(data, columns=columns)
    
    # Add a new row to results_df with the first value being the value of the first column and the rest being NaN
    new_row = pd.Series({results_df.columns[0]: variable}, name="new")
    
    # Using concat instead of append
    results_df_with_new_row = pd.concat([results_df, new_row.to_frame().T])
    
    # Make the "new" row the first row and reset the index
    results_df_reordered = pd.concat([new_row.to_frame().T, results_df]).reset_index(drop=True)
    
    # Change the name of the first column to "Variable"
    results_df_reordered.rename(columns={results_df_reordered.columns[0]: "Variable"}, inplace=True)
    
    all_results_final_format_corrected.append(results_df_reordered)

# Concatenate all individual DataFrames to get the final results DataFrame with the corrected format
final_results_df_final_format_corrected = pd.concat(all_results_final_format_corrected).reset_index(drop=True)

# Inserting a new column "Autoplay" with the same values as "Variable"
final_results_df_final_format_corrected.insert(1, "Autoplay", final_results_df_final_format_corrected["Variable"])

# Updating the 'Variable' column
final_results_df_final_format_corrected.loc[1::3, 'Variable'] = "Mean (SD)"
final_results_df_final_format_corrected.loc[2::3, 'Variable'] = "Median [Min, Max]"

# Updating the 'Autoplay' column
final_results_df_final_format_corrected.loc[::3, 'Autoplay'] = np.nan

final_results_df_final_format_corrected


# Saving the final table to a .csv file
final_results_df_final_format_corrected.to_csv('table2.csv', index=False)

final_results_df_final_format_corrected


# %% MPL session

# load data
mpl_data = pd.read_csv("MPL.csv")

# Dropping the specified columns from mpl_data
columns_to_drop = ['ID', '__v', '_id', 'clikcedOkToSwitch.Practice', 'createdAt', 'laborTime', 'leisureTime', 
                   'lottery', 'videoPausedFor', 'transcription', 'updatedAt']

clean_mpl_data = mpl_data.drop(columns=columns_to_drop)

# Saving the cleaned data to a .csv file
clean_mpl_data.to_csv('clean-MPL-data.csv', index=False)

mpl_data = pd.read_csv("clean-MPL-data.csv")

# drop participants with connection issues
mpl_data = mpl_data[mpl_data["connection"]=="connectionGood"]

# %% Graph 5: Commitment demand

# get MPL
db_mpl = mpl_data[["MPL1", "MPL2", "MPL3", "MPL4", "MPL5", "MPL6", "MPL7", "MPL8", "MPL9"]]

# rename columns
db_mpl = db_mpl.rename(columns={
    "MPL1": "Autoplay +0.5£",
    "MPL2": "Autoplay +0.25£",
    "MPL3": "Autoplay +0.1£",
    "MPL4": "Autoplay +0.05£",
    "MPL5": "Autoplay +0£",
    "MPL6": "No Autoplay +0.05£",
    "MPL7": "No Autoplay +0.1£",
    "MPL8": "No Autoplay +0.25£",
    "MPL9": "No Autoplay +0.5£"
})

# replace values
for column in db_mpl.columns[:5]:
    db_mpl[column] = db_mpl[column].apply(lambda x: 1 if x == column else 0)

for column in db_mpl.columns[5:]:
    db_mpl[column] = db_mpl[column].apply(lambda x: 0 if x == column else 1)  

# Calculate the percentage of 1's and 0's for each column
percent_ones = (db_mpl.sum() / len(db_mpl)) * 100
percent_zeros = 100 - percent_ones

# Convert the wide DataFrame to long format for easier plotting with seaborn
long_format = pd.DataFrame({'Labels': percent_ones.index, 
                            "Autoplay": percent_ones.values, 
                            "No Autoplay": percent_zeros.values}).melt(id_vars='Labels', 
                                                                      value_vars=["Autoplay", "No Autoplay"], 
                                                                      var_name='Choice', value_name='Percentage')

# Plotting
plt.figure(figsize=(15,7))
sns.barplot(x='Labels', y='Percentage', hue='Choice', palette="deep", data=long_format)
plt.xticks(rotation=45)
plt.xlabel("Multiple Price List choices")
plt.tight_layout()
plt.show()

# %% Discussion: tests for content rating

# Plot
g = sns.displot(
    data=clean_data,
    x="content",
    hue="Treatment",
    kind="kde",
    fill=True,
    palette="deep",
    height=6,
    aspect=1.5,
    cut=0
)
    
# Adding a box around the plot
g.ax.spines["top"].set_visible(True)
g.ax.spines["right"].set_visible(True)
g.ax.spines["bottom"].set_visible(True)
g.ax.spines["left"].set_visible(True)

# Setting x-axis and y-axis labels
g.ax.set_xlabel("Content")
g.ax.set_ylabel("Density")

plt.show()

# Separate the data into two groups: Autoplay and Control
autoplay_data = clean_data[clean_data['Treatment'] == 'Autoplay']['content']
control_data = clean_data[clean_data['Treatment'] == 'Control']['content']

# Perform Shapiro-Wilk test
shapiro_test_autoplay = stats.shapiro(autoplay_data)
shapiro_test_control = stats.shapiro(control_data)

shapiro_test_autoplay, shapiro_test_control

# Performing the Mann-Whitney U Test
u_statistic, p_value = mannwhitneyu(
    autoplay_data, control_data, alternative="two-sided"
)

u_statistic, p_value

# %% Regression analysis

mod = smf.ols(formula='watchedVideo ~ allocated_typing + Treatment + speed + Age + content + gender', data=clean_data)
res = mod.fit()
print(res.summary())