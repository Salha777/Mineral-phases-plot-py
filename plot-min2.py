import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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
    "Hydromagnesite",
    "Nesquehonite",
    "Artinite",
    "Lansfordite",
    "Giorgiosite",
    "Ammonium magnesium carbonate hydrate",
    
]
phase_order_mapping = {phase.lower(): i + 1 for i, phase in enumerate(ordered_phases)}

def map_phase_order(phases):
    if pd.isna(phases):
        return np.nan
    for phase in phase_order_mapping:
        if phase == phases.lower():
            return phase_order_mapping[phase]
    return np.nan

df["Phase_Rank"] = df["Main_Phases"].apply(map_phase_order)

def extract_hydration_rank(phases):
    if pd.isna(phases):
        return np.nan
    for phase, rank in hydration_mapping.items():
        if phase.lower() in phases.lower():
            return rank
    return np.nan

df["Hydration_Level"] = df["Main_Phases"].apply(extract_hydration_rank)

# --- Drop rows with missing required data ---
df_clean = df.dropna(subset=["Hydration_Level", "Temperature", "Mg_Source"])

# --- Encode Mg source ---
df_clean["Mg_Source_Cat"] = pd.Categorical(df_clean["Mg_Source"])
df_clean["x"] = df_clean["Mg_Source_Cat"].cat.codes
np.random.seed(42)
df_clean["x_jittered"] = df_clean["x"] + np.random.uniform(-0.2, 0.2, size=len(df_clean))

# --- Plotting ---
plt.figure(figsize=(12, 6))
scatter = plt.scatter(
    df_clean["x_jittered"],
    df_clean["Hydration_Level"],
    c=df_clean["Temperature"],
    cmap="coolwarm",
    edgecolor="black",
    s=80
)

# --- Annotations ---
for i, row in df_clean.iterrows():
    plt.text(row["x_jittered"], row["Hydration_Level"] + 0.2, row["Main_Phases"],
             fontsize=7, ha='center', alpha=0.7, rotation=25)

# --- Colorbar ---
cbar = plt.colorbar(scatter)
cbar.set_label("Temperature (°C)")

# --- Axis formatting ---
plt.xticks(ticks=sorted(df_clean["x"].unique()), labels=df_clean["Mg_Source_Cat"].cat.categories, rotation=45)
plt.yticks(
    ticks=range(1, len(ordered_phases)+1),
    labels=ordered_phases
)
#plt.ylabel("Phases (Carbonation → Hydration Ordered)")
plt.ylabel("Hydration Level (ranked)")
plt.xlabel("Mg Source")
plt.title("Carbonate Phases Formed vs. Mg Source (Colored by Temp)")
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()
