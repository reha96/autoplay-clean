# %% table 6
import pandas as pd

# Load the specific sheet "Core_8_9" into a DataFrame
df = pd.read_excel("AllExercices.xlsx", sheet_name="Core_8_9")

df.head()

# Create a new column 'time_budgets' with unique combinations of 'p3', 'p4', 'time_given'
df['time_budgets'] = df.groupby(['p3', 'p4', 'time_given']).ngroup() + 1

# Create a new column 'money_budgets' with unique combinations of 'p', 'p2', 'b1'
df['money_budgets'] = df.groupby(['p', 'p2', 'b2']).ngroup() + 1

# Define a function to calculate the number of unique 'time_budgets' and 'money_budgets' for each unique value in a given column
def unique_budgets_per_category(column_name):
    unique_values = df[column_name].unique()
    unique_time_budgets_per_category = {value: df[df[column_name] == value]['time_budgets'].nunique() for value in unique_values}
    unique_money_budgets_per_category = {value: df[df[column_name] == value]['money_budgets'].nunique() for value in unique_values}
    return unique_time_budgets_per_category, unique_money_budgets_per_category

# List of columns to check
columns_to_check = ['Gender', 'Age', 'Education', 'Marital Status', 'Employment']

# Create a dictionary to store the results
results = {}

# For each column, calculate the number of unique 'time_budgets' and 'money_budgets' for each unique value in that column
for column in columns_to_check:
    results[column] = unique_budgets_per_category(column)

results
    