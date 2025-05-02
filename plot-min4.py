import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import ListedColormap
import re
from adjustText import adjust_text

# --- Load and clean data ---
df = pd.read_excel("IAA-CO2-MIN-Python-copy.xlsx")
df.columns = df.columns.str.strip()

# Rename relevant columns
df = df.rename(columns={
    "Mg Source": "Mg_Source",
    "T/°C": "Temperature",
    "Main phases": "Main_Phases"
})

# Clean string columns
df["Mg_Source"] = df["Mg_Source"].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
df["Main_Phases"] = df["Main_Phases"].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)

df["Mg_Source"] = df["Mg_Source"].replace({
    "SN-MgSO4 + MgOAc": "MgOAc",
    "SN-MgSO4": "MgSO4",
    "SN-MgSO4/MgOAc + MgSO4": "MgSO4",  # Adjust based on your intended grouping
    "SN-MgCIT": "MgCIT",
    "Nesq": "Nesquehonite"
})

print(df["Mg_Source"].unique())

# --- Hydration level mapping ---
hydration_mapping = {
    "Magnesium Citrate Hydrate": 0,
    "MgCIT": 0,
    "MgCITRATE": 0,
    "Ammonium magnesium sulfate hydrate": 1, # Corrected key to match data
    "Epsomite": 1,
    "Magnesite": 2,
    "Nesquehonite": 3,
    "Artinite": 4,
    "Hydromagnesite": 5,
    "Lansfordite":6,
    "Giorgiosite":7,
    "Ammonium magnesium carbonate hydrate": 8,
    "Pending": np.nan,
}

# --- Ordered phases by CO3 content and then hydration ---
ordered_phases = [
    "Magnesium Citrate Hydrate",
    "Ammonium magnesium sulfate hydrate", # Corrected key
    "Epsomite",
    "Magnesite",
    "Nesquehonite",
    "Artinite",
    "Hydromagnesite",
    "Lansfordite",
    "Giorgiosite",
    "Ammonium magnesium carbonate hydrate",
]
phase_order_mapping = {phase.lower(): i + 1 for i, phase in enumerate(ordered_phases)}

def map_phase_order(phases):
    if pd.isna(phases):
        return np.nan
    processed_phases = [p.strip().lower() for p in phases.split(" + ")]
    for phase_map_lower in phase_order_mapping:
        if phase_map_lower in processed_phases:
            return phase_order_mapping[phase_map_lower]
    return np.nan

df["Phase_Rank"] = df["Main_Phases"].apply(map_phase_order)

def extract_hydration_rank(phases):
    if pd.isna(phases):
        return np.nan
    processed_phases = [p.strip().lower() for p in phases.split(" + ")]
    hydration_levels = []
    for phase, rank in hydration_mapping.items():
        if phase.lower() in processed_phases:
            hydration_levels.append(rank)
    if hydration_levels:
        return hydration_levels
    return np.nan

df["Hydration_Level"] = df["Main_Phases"].apply(extract_hydration_rank)
df_exploded = df.explode('Hydration_Level').dropna(subset=['Hydration_Level', 'Temperature', 'Mg_Source'])

# --- Encode Mg source ---
df_exploded["Mg_Source_Cat"] = pd.Categorical(df_exploded["Mg_Source"])
df_exploded["x"] = df_exploded["Mg_Source_Cat"].cat.codes
np.random.seed(42)
df_exploded["x_jittered"] = df_exploded["x"] + np.random.uniform(-0.3, 0.3, size=len(df_exploded)) # Increased jitter

# --- Define the custom colormap ---
colors = ["red", "yellow", "green", "blue", "white"]
cmap_name = "custom_coolwarm"
custom_cmap = ListedColormap(colors, name=cmap_name)

# --- Plotting ---
plt.figure(figsize=(16, 8)) # Increased figure size for wider x-axis
scatter = plt.scatter(
    df_exploded["x_jittered"],
    df_exploded["Hydration_Level"],
    c=df_exploded["Temperature"],
    cmap=custom_cmap,
    edgecolor="black",
    s=80
)

# --- Drop Lines ---
for index, row in df_exploded.iterrows():
    plt.plot([row["x_jittered"], row["x_jittered"]], [row["Hydration_Level"], -0.5], # Extend to below y=0
             color='gray', linestyle='--', linewidth=0.5, alpha=0.7)

# --- Annotations ---
texts = []
for index, row in df_exploded.iterrows():
    main_phase_display = row["Main_Phases"].split(" + ")[0].strip() # Just use the first phase for display
    if isinstance(row["Hydration_Level"], (int, float)):
        texts.append(plt.text(row["x_jittered"], row["Hydration_Level"] + 0.25, main_phase_display,
                             fontsize=7, ha='center', alpha=0.7, rotation=45))


adjust_text(texts, autoalign='xy', only_move={'points':'y', 'text':'y'},
            arrowprops=dict(arrowstyle='-', color='black', lw=0.5, alpha=0.6))

# --- Colorbar ---
cbar = plt.colorbar(scatter)
cbar.set_label("Temperature (°C)")

# --- Axis formatting ---
mg_sources_unique = df_exploded["Mg_Source_Cat"].cat.categories
plt.xticks(ticks=range(len(mg_sources_unique)), labels=mg_sources_unique, rotation=45, ha='right') # Use range for ticks
y_ticks = list(hydration_mapping.values())
y_labels = list(hydration_mapping.keys())
plt.yticks(ticks=y_ticks, labels=y_labels)
plt.ylabel("Hydration Level (based on mapping)")
plt.xlabel("Mg Source")
plt.title("Carbonate Phases Formed vs. Mg Source (Colored by Temp)")
plt.grid(False) # Remove horizontal grid lines
plt.tight_layout(rect=[0, 0.05, 1, 0.95]) # Adjust layout to prevent cutoff
plt.show()