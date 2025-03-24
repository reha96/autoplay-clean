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

# %%%Step 1: Visualize the relationship
plt.figure(figsize=(10, 6))
sns.scatterplot(x='timeChoice', y='typing_log', hue='treatment', data=clean_data)
plt.plot([0, clean_data['timeChoice'].max()], [0, clean_data['timeChoice'].max()], 'k--', alpha=0.5)
plt.title('Typing vs Time Choice by Treatment')
plt.xlabel('Time Choice (seconds)')
plt.ylabel('Typing (seconds)')
plt.legend(title='Treatment')
plt.show()
plt.savefig('typing_vs_timechoice.png')
plt.close()

# %%%Step 4: Negative binomial regression - watchedVideo predicted by timeChoice and treatment
def categorize_time_choice(time):
    if time == 0:
        return "Low"
    elif time == 1200:
        return "High"
    elif time == 600:
        return "Medium"
    else:
        # For other values, use nearest category
        if time < 300:
            return "Low"
        elif time > 900:
            return "High"
        else:
            return "Medium"

# Create the categorical variable
clean_data['timeChoice_cat'] = clean_data['timeChoice'].apply(categorize_time_choice)

# Dummy-encode the categorical variable (creates dummy variables for Low and Medium, with High as reference)
df = pd.get_dummies(clean_data, columns=['timeChoice_cat'], drop_first=False)

# Create interaction terms between treatment and timeChoice categories
df['treatment_Low'] = (df['treatment'] == 'autoplayOn').astype(int) * df['timeChoice_cat_Low']
df['treatment_Medium'] = (df['treatment'] == 'autoplayOn').astype(int) * df['timeChoice_cat_Medium']
df['treatment_High'] = (df['treatment'] == 'autoplayOn').astype(int) * df['timeChoice_cat_High']
# %%%Step 3: Multiple regression - typing_log predicted by timeChoice and treatment
model4 = smf.ols('watchedVideo ~ timeChoice_cat_Low + timeChoice_cat_Medium + timeChoice_cat_High + treatment', data=df).fit()
print(model4.summary())
# %%%
model5 = smf.ols('watchedVideo ~ treatment_Low +  treatment_Medium + treatment_High', data=df).fit()
print(model5.summary())
# %%%
model5 = smf.glm('watchedVideo ~ treatment_Low +  treatment_Medium + treatment_High', data=df ,family=sm.families.NegativeBinomial()).fit()
print(model5.summary())

# %%%
model6 = smf.ols('typing_log ~ treatment_Low +  treatment_Medium + treatment_High', data=df).fit()
print(model6.summary())

# %%%
model = smf.ols('watchedVideo ~ timeChoice_cat_Low + timeChoice_cat_High + treatment + treatment:timeChoice_cat_Low + treatment:timeChoice_cat_High', data=df).fit()
print(model.summary())
# %%%
clean_data['deviation'] = clean_data['typing_log'] - clean_data['timeChoice']
model = smf.ols('deviation ~ timeChoice_cat_Low + timeChoice_cat_Medium + timeChoice_cat_High + treatment', data=df).fit()
print(model.summary())
# %%%
clean_data['deviation'] = clean_data['typing_log'] - clean_data['timeChoice']
model = smf.ols('deviation ~ timeChoice_cat_High:treatment + timeChoice_cat_High + treatment', data=df).fit()
print(model.summary())

# %%%Step 2: Simple regression - typing_log predicted by timeChoice
model1 = smf.ols('typing_log ~ timeChoice', data=clean_data).fit()
print("\nReg 1: Simple Linear Regression - typing_log predicted by timeChoice")
print(model1.summary())
# %%%
model2 = smf.ols('watchedVideo ~ timeChoice', data=clean_data).fit()
print("\nReg 2: Simple Linear Regression - watchedVideo predicted by timeChoice")
print(model2.summary())
# %%%
model3 = smf.ols('typeCount ~ timeChoice', data=clean_data).fit()
print("\nReg 3: Simple Linear Regression - typeCount predicted by Treatment")
print(model3.summary())
# %%%
model = smf.ols('end_time_log ~ deviation + treatment', data=df).fit()
print(model.summary())