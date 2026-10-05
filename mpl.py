# ============================================================
# Data Discovery Assignment 2 - Farmers Market SNAP/EBT Access
# Tool: pandas + matplotlib (from the Intro to Python lesson)
# Run from the root folder of the cloned dataset repo
# ============================================================
import os
import pandas as pd
import matplotlib.pyplot as plt

# folder to save the images for the assignment document
os.makedirs("figures", exist_ok=True)

# ------------------------------------------------------------
# Open the CSV
# ------------------------------------------------------------
# relative path, starting from the root folder of the repo
df = pd.read_csv("us-farmers-markets-2026.csv")
# clean up column names, just in case
df.columns = df.columns.str.strip()

# Now what? Look at the data first
print(df.head())
print(df.info())
print(df.describe())

# ------------------------------------------------------------
# Prep the SNAP/EBT columns
# ------------------------------------------------------------
# accepts_snap and accepts_ebt hold True, False, or a missing value
# A market counts as "accepts SNAP/EBT" if EITHER column is True
# (the state-level file from the data owner counts it the same way)
df['snap_any'] = (df['accepts_snap'] == True) | (df['accepts_ebt'] == True)

# A market is "unknown" if BOTH columns are missing
known = df['accepts_snap'].notna() | df['accepts_ebt'].notna()

df['snap_status'] = 'Unknown (no data)'
df.loc[known & ~df['snap_any'], 'snap_status'] = 'Does not accept'
df.loc[df['snap_any'], 'snap_status'] = 'Accepts SNAP/EBT'

# ------------------------------------------------------------
# Bar Graph 1: How many markets accept SNAP/EBT?
# ------------------------------------------------------------
# count how many markets per status
status_counts = df['snap_status'].value_counts()
status_counts = status_counts[['Accepts SNAP/EBT', 'Does not accept', 'Unknown (no data)']]
total_markets = status_counts.sum()

# create the Bar Chart
plt.figure(figsize=(8, 5))
plt.bar(
    status_counts.index.to_numpy(),
    status_counts.to_numpy(),
    color=['teal', 'coral', 'lightgray'],
    edgecolor='black', width=0.5
)

# titles and labels
plt.title('US Farmers Markets: SNAP/EBT Acceptance', fontsize=12, fontweight='bold')
plt.xlabel('SNAP/EBT Status')
plt.ylabel('Number of Markets')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.ylim(0, status_counts.max() * 1.15)  # extra room above the tallest bar for its label
for index, value in enumerate(status_counts.values):  # bar heights
    plt.text(index, value + 80, f"{value:,}\n({value / total_markets:.1%})",
             ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig("figures/01_snap_status.png", dpi=200)
plt.show()

# ------------------------------------------------------------
# Group by State
# ------------------------------------------------------------
# group by state and count the number of markets
markets_per_state = df.groupby('state')['name'].count()
# group by state and count the markets that accept SNAP/EBT (True = 1)
snap_per_state = df.groupby('state')['snap_any'].sum()
# percent of each state's markets that accept SNAP/EBT
snap_pct = snap_per_state / markets_per_state * 100

# put it together in one table
state_stats = pd.DataFrame({
    'markets': markets_per_state,
    'snap_markets': snap_per_state,
    'snap_pct': snap_pct
})

# national rate to compare each state against
national_pct = df['snap_any'].mean() * 100
print(state_stats.sort_values('snap_pct', ascending=False))
print("National SNAP/EBT rate:", round(national_pct, 1), "%")

# ------------------------------------------------------------
# Bar Graph 2: States leading the way
# ------------------------------------------------------------
# tiny states can look extreme, so only use states with 30+ markets
big_enough = state_stats[state_stats['markets'] >= 30]
top10 = big_enough.sort_values('snap_pct', ascending=False).head(10)

plt.figure(figsize=(9, 6))
plt.bar(
    top10.index.to_numpy(),
    top10['snap_pct'].to_numpy(),
    color='teal', edgecolor='black', width=0.6
)
# line for the national rate
plt.axhline(national_pct, color='black', linestyle='--',
            label=f"National rate ({national_pct:.1f}%)")

plt.title('Top 10 States by SNAP/EBT Acceptance (States with 30+ Markets)',
          fontsize=12, fontweight='bold')
plt.xlabel('State')
plt.ylabel('% of Markets Accepting SNAP/EBT')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
for index, value in enumerate(top10['snap_pct'].to_numpy()):  # bar heights
    plt.text(index, value + 0.8, f"{value:.1f}%", ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig("figures/02_top10_states.png", dpi=200)
plt.show()

# ------------------------------------------------------------
# Bar Graph 3: The biggest gaps
# ------------------------------------------------------------
# gaps matter most where there are lots of markets, so use states with 100+ markets
large_states = state_stats[state_stats['markets'] >= 100]
bottom10 = large_states.sort_values('snap_pct', ascending=True).head(10)

plt.figure(figsize=(9, 6))
plt.bar(
    bottom10.index.to_numpy(),
    bottom10['snap_pct'].to_numpy(),
    color='coral', edgecolor='black', width=0.6
)
plt.axhline(national_pct, color='black', linestyle='--',
            label=f"National rate ({national_pct:.1f}%)")

plt.title('Biggest Gaps: Lowest SNAP/EBT Acceptance (States with 100+ Markets)',
          fontsize=12, fontweight='bold')
plt.xlabel('State')
plt.ylabel('% of Markets Accepting SNAP/EBT')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.ylim(0, 14)  # room above the national-rate line for the legend
plt.legend(loc='upper right')
for index, value in enumerate(bottom10['snap_pct'].to_numpy()):  # bar heights
    plt.text(index, value + 0.2, f"{value:.1f}%", ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig("figures/03_biggest_gaps.png", dpi=200)
plt.show()

# ------------------------------------------------------------
# Scatter Plot: Does having more markets mean more SNAP/EBT access?
# ------------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(
    state_stats['markets'],
    state_stats['snap_pct'],
    color='teal',
    alpha=0.7,            # Transparency helps spot overlapping points
    edgecolors='black'
)

# label the outliers (very high rate, or lots of markets)
for state, row in state_stats.iterrows():
    if row['snap_pct'] > 25 or row['markets'] > 400:
        plt.text(row['markets'] + 6, row['snap_pct'] + 0.5, state, fontweight='bold')

# line for the national rate
plt.axhline(national_pct, color='coral', linestyle='--',
            label=f"National rate ({national_pct:.1f}%)")

# labels and layout
plt.title('Number of Markets vs. SNAP/EBT Acceptance by State', fontsize=12, fontweight='bold')
plt.xlabel('Number of Farmers Markets in State')
plt.ylabel('% of Markets Accepting SNAP/EBT')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()

plt.tight_layout()
plt.savefig("figures/04_markets_vs_snap_scatter.png", dpi=200)
plt.show()