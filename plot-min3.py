import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
from adjustText import adjust_text
from matplotlib.colors import ListedColormap

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
    "Ammonium magnesium sulfate": 1,
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
    "Ammonium magnesium sulfate",
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


# --- Drop rows with missing required data ---
df_clean = df.dropna(subset=["Hydration_Level", "Temperature", "Mg_Source"])

# --- Encode Mg source ---
#df_clean["Mg_Source_Cat"] = pd.Categorical(df_clean["Mg_Source"])
#df_clean["x"] = df_clean["Mg_Source_Cat"].cat.codes
#np.random.seed(42)
#df_clean["x_jittered"] = df_clean["x"] + np.random.uniform(-0.2, 0.2, size=len(df_clean))

# --- Encode Mg source ---
df_exploded["Mg_Source_Cat"] = pd.Categorical(df_exploded["Mg_Source"])
df_exploded["x"] = df_exploded["Mg_Source_Cat"].cat.codes
np.random.seed(42)
df_exploded["x_jittered"] = df_exploded["x"] + np.random.uniform(-0.3, 0.3, size=len(df_exploded)) # Increased jitter

# --- Define the custom colormap ---
colors = ["white","lightblue", "blue", "green", "orange", "yellow", "red"]
cmap_name = "custom_coolwarm"
custom_cmap = ListedColormap(colors, name=cmap_name)

# --- Plotting ---
plt.figure(figsize=(12, 6))
scatter = plt.scatter(
    df_clean["x_jittered"],
    df_clean["Hydration_Level"],
    c=df_clean["Temperature"],
    cmap=custom_cmap,
    edgecolor="black",
    s=80
)

# --- Drop Lines ---
for index, row in df_exploded.iterrows():
    plt.plot([row["x_jittered"], row["x_jittered"]], [row["Hydration_Level"], -0.5], # Extend to below y=0
             color='gray', linestyle='--', linewidth=0.5, alpha=0.7)


# --- Annotations and Handling Multiple Phases ---
texts = []
for i, row in df_clean.iterrows():
    main_phases = row["Main_Phases"].split(" + ")
    x_val = row["x_jittered"]
    for j, phase in enumerate(main_phases):
        processed_phase = phase.strip().lower()
        hydration_level = None
        for key, val in hydration_mapping.items():
            if key.lower() in processed_phase:
                hydration_level = val
                break
        if hydration_level is not None:
            # Slight horizontal offset for the second phase if present
            x_offset = 0.05 if j > 0 else 0
            plt.scatter(x_val + x_offset, hydration_level, c=row["Temperature"],
                        cmap=custom_cmap, edgecolor='gray', marker='o', s=80)
            texts.append(plt.text(x_val + x_offset, hydration_level + 0.25, phase.strip(),
                                fontsize=7, ha='center', alpha=0.7, rotation=25))

from adjustText import adjust_text
adjust_text(texts, autoalign='xy', only_move={'points':'y', 'text':'y'},
            arrowprops=dict(arrowstyle='-', color='black', lw=0.5, alpha=0.6))

# --- Annotations ---
#texts = []
#for i, row in df_clean.iterrows():
#    plt.text(row["x_jittered"], row["Hydration_Level"] + 0.2, row["Main_Phases"],
#             fontsize=7, ha='center', alpha=0.7, rotation=25)

# --- Adjust text positions ---
#adjust_text(texts, autoalign='xy', only_move={'points':'y', 'text':'y'},
#            arrowprops=dict(arrowstyle='-', color='black', lw=0.5, alpha=0.6))

# --- Colorbar ---
cbar = plt.colorbar(scatter)
cbar.set_label("Temperature (°C)")

# --- Axis formatting ---
plt.xticks(ticks=sorted(df_clean["x"].unique()), labels=df_clean["Mg_Source_Cat"].cat.categories, rotation=45)

# Corrected y-axis ticks and labels
y_ticks = list(hydration_mapping.values())
y_labels = list(hydration_mapping.keys())
plt.yticks(ticks=y_ticks, labels=y_labels)

plt.ylabel("Hydration Level (based on mapping)")
plt.xlabel("Mg Source")
plt.title("Carbonate Phases Formed vs. Mg Source (Colored by Temp)")
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()