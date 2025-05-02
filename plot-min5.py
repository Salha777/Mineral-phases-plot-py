import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# --- Load and clean data ---
df = pd.read_excel("IAA-CO2-MIN-Python-copy.xlsx", engine='openpyxl')
df.columns = df.columns.str.strip()
df = df.rename(columns={"Mg Source": "Mg_Source", "T/°C": "Temperature", "Main phases": "Main_Phases"})
df["Mg_Source"] = df["Mg_Source"].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
df["Main_Phases"] = df["Main_Phases"].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
df["Mg_Source"] = df["Mg_Source"].replace({
    "SN-MgSO4 + MgOAc": "MgOAc",
    "SN-MgSO4": "MgSO4",
    "SN-MgSO4/MgOAc + MgSO4": "MgSO4",
    "SN-MgCIT": "MgCIT",
    "Nesq": "Nesquehonite"
})

# --- Hydration mapping ---
hydration_mapping = {
    "magnesium citrate hydrate": 0, "mgcit": 0, "mgcitrate": 0,
    "ammonium magnesium sulfate hydrate": 1, "epsomite": 1,
    "magnesite": 2,
    "nesquehonite": 3, "nesq": 3,
    "artinite": 4,
    "hydromagnesite": 5, "hydromagnesite (amorphous)": 5, "hydromagnesite (semi amorphous)": 5,
    "lansfordite": 6,
    "giorgiosite": 7,
    "ammonium magnesium carbonate hydrate": 8,
    "pending": np.nan, "unreacted mgso4": np.nan, "acetamido complex": np.nan,
    "mgso4": np.nan, "unknown": np.nan, "-": np.nan,
}

def extract_hydration_rank(phases):
    if pd.isna(phases):
        return np.nan
    processed_phases = [p.strip().lower() for p in phases.split(" + ")]
    hydration_levels = sorted(set([hydration_mapping.get(phase, np.nan) for phase in processed_phases if phase in hydration_mapping]))
    return hydration_levels[0] if len(hydration_levels) == 1 else hydration_levels if hydration_levels else np.nan

df["Hydration_Level"] = df["Main_Phases"].apply(extract_hydration_rank)

df_two_phases = df[df['Hydration_Level'].apply(lambda x: isinstance(x, list) and len(x) == 2)].copy()
df_single_phase = df[df['Hydration_Level'].apply(lambda x: isinstance(x, (int, float)))].copy()
df_exploded_two_phases = df_two_phases.explode('Hydration_Level').dropna(subset=['Hydration_Level', 'Temperature', 'Mg_Source'])

# --- Encode Mg source as categorical BEFORE concatenation ---
df_exploded_two_phases["Mg_Source_Cat"] = pd.Categorical(df_exploded_two_phases["Mg_Source"])
df_single_phase["Mg_Source_Cat"] = pd.Categorical(df_single_phase["Mg_Source"])

# --- Encode x values with jitter ---
np.random.seed(42)
df_exploded_two_phases["x"] = df_exploded_two_phases["Mg_Source_Cat"].cat.codes
df_exploded_two_phases["x_jittered"] = df_exploded_two_phases["x"] + np.random.uniform(-0.3, 0.3, size=len(df_exploded_two_phases))
df_single_phase["x"] = df_single_phase["Mg_Source_Cat"].cat.codes
df_single_phase["x_jittered"] = df_single_phase["x"] + np.random.uniform(-0.3, 0.3, size=len(df_single_phase))

# --- Define the custom colormap ---
colors = ["white", "blue", "green", "yellow", "orange", "red"]
custom_cmap = ListedColormap(colors, name="reversed_coolwarm")

# --- Plotting ---
plt.figure(figsize=(16, 8))

# Plot single phase data
plt.scatter(
    df_single_phase["x_jittered"],
    df_single_phase["Hydration_Level"],
    c=df_single_phase["Temperature"],
    cmap=custom_cmap,
    edgecolor="black",
    s=80
)

# Plot two-phase data
plt.scatter(
    df_exploded_two_phases["x_jittered"],
    df_exploded_two_phases["Hydration_Level"],
    c=df_exploded_two_phases["Temperature"],
    cmap=custom_cmap,
    edgecolor="black",
    s=80
)

# --- Arrows for biphasic points (no labels) ---
for index, row in df_two_phases.iterrows():
    if isinstance(row['Hydration_Level'], list) and len(row['Hydration_Level']) == 2:
        exploded_rows = df_exploded_two_phases[df_exploded_two_phases['Main_Phases'] == row['Main_Phases']]
        if len(exploded_rows) == 2:
            x_val = exploded_rows['x_jittered'].unique()[0]
            y_vals = sorted(row['Hydration_Level'])
            phases = [p.strip().lower() for p in row["Main_Phases"].split(" + ")]
            label_phase = [p for p in phases if hydration_mapping.get(p, None) != y_vals[0]]
            #if label_phase:
                # label_text = label_phase[0]  # Optional label
                #plt.annotate('', (x_val, y_vals[0]), textcoords="offset points", xytext=(0, 20), ha='center',
                             #arrowprops=dict(arrowstyle='->', color='black', lw=0.5, alpha=0.6))

# --- Connect biphasic points with lines (not necessarily vertical) ---
for index, row in df_two_phases.iterrows():
    if isinstance(row['Hydration_Level'], list) and len(row['Hydration_Level']) == 2:
        exploded_rows = df_exploded_two_phases[df_exploded_two_phases['Main_Phases'] == row['Main_Phases']]
        if len(exploded_rows) == 2:
            x_vals = exploded_rows['x_jittered'].values
            y_vals = exploded_rows['Hydration_Level'].values
            plt.plot(x_vals, y_vals, color='gray', linestyle='-', linewidth=1, alpha=0.7)

# --- Colorbar ---
cbar = plt.colorbar()
cbar.set_label("Temperature (°C)")

# --- Axis formatting ---
combined_df = pd.concat([df_exploded_two_phases, df_single_phase])
combined_df['Mg_Source_Cat'] = pd.Categorical(combined_df['Mg_Source'])
mg_sources_unique = combined_df["Mg_Source_Cat"].cat.categories
plt.xticks(ticks=range(len(mg_sources_unique)), labels=mg_sources_unique, rotation=45, ha='right')

hydration_label_map = {}
for phase, level in hydration_mapping.items():
    if pd.notna(level) and level not in hydration_label_map:
        hydration_label_map[level] = phase

y_ticks = sorted(hydration_label_map.keys())
y_labels = [hydration_label_map[level] for level in y_ticks]

plt.yticks(ticks=y_ticks, labels=y_labels)
plt.ylabel("Hydration Level (based on mapping)")
plt.xlabel("Mg Source")
plt.title("Carbonate Phases Formed vs. Mg Source (Colored by Temp)")
plt.grid(False)
plt.tight_layout(rect=[0, 0.05, 1, 0.95])
plt.show()
print(df_exploded_two_phases)