#%%
import matplotlib.pyplot as plt

# Remove all the spines
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['bottom'].set_visible(False)
plt.gca().spines['left'].set_visible(False)

categories = [
    'Analytical thinking', 'Creative thinking', 'Resilience, Flexibility and Agility',
    'Motivation and Lifelong Learning', 'Curiosity and Lifelong Learning', 
     'Dependability and Attention to Detail',
    'Empathy and Active Listening', 'Leadership and Social Influence', 'Systems Thinking', 'Reading, Writing, Math'
]

percentages = [64, 56, 48, 45, 43, 42, 41, 39, 36, 24]

# Reduce the width of the bars to add more space between them
bar_width = 0.8  # Adjust the width as needed, less than 1.0 to add more space

plt.bar(categories, percentages, color='navy', width=bar_width)

for i, percentage in enumerate(percentages):
    plt.text(i, percentage + 1, f'{percentage}%', ha='center')

plt.title('Core Skills for Workers in 2023')
plt.ylabel('Share of Companies (%)')
plt.xticks(rotation=45, ha='right', fontsize=8)

# Remove y-axis tick labels
plt.yticks([])

# Use the 'dpi' parameter to specify the resolution. Higher values give higher resolution.
plt.figure(figsize=(50, 4), dpi=600)

plt.show()


# %%
