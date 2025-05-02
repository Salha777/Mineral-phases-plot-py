import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# ---- Load the Excel file ----
# Adjust the path as needed
file_path = "IAA-CO2-MIN-Python-copy.xlsx"
df = pd.read_excel(file_path)

# Clean up column names (remove leading/trailing whitespace)
df.columns = df.columns.str.strip()

# Rename for consistent usage in code
df = df.rename(columns={
    "Mg Source": "Mg_Source",
    "T /°C": "Temperature",
    "Main phases": "Main_Phases"
})

# ---- Select only relevant columns ----
# Ensure your sheet uses these exact column names or update as necessary
df = df[["Mg_Source", "T/°C", "Main_phases"]].copy()
df.columns = ["Mg_Source", "Temperature", "Main_Phases"]

# ---- Define hydration levels (based on your custom hydration ranking) ----
hydration_dict = {
    "Magnesite": 1,
    "Nesquehonite": 2,
    "Nesq": 2,  # Shorthand
    "Artinite": 3,
    "Hydromagnesite": 4,
    "Ammonium magnesium carbonate hydrate": 5,
    "Ammonium magnesium sulfate hydrate": 6,
    "Lansfordite": 7,
    "MgCIT": 8,   # Magnesium citrate hydrate (tentatively hydrated)
    "MgCITRATE": 8
}

# ---- Function to map phase string to hydration level ----
def get_hydration_level(phase):
    if pd.isna(phase):
        return None
    matched = []
    for k, v in hydration_dict.items():
        if re.search(rf"\b{k}\b", phase, re.IGNORECASE):
            matched.append(v)
    return max(matched) if matched else None

df["Hydration_Level"] = df["Main_Phases"].apply(get_hydration_level)

# ---- Drop rows where hydration level couldn't be assigned ----
df_clean = df.dropna(subset=["Hydration_Level", "Mg_Source", "Temperature"])

# ---- Plot ----
plt.figure(figsize=(14, 7))
sns.scatterplot(
    x="Mg_Source",
    y="Hydration_Level",
    hue="Temperature",
    data=df_clean,
    palette="viridis",
    s=120
)

# Add annotations (phase labels)
for i, row in df_clean.iterrows():
    plt.text(row["Mg_Source"], row["Hydration_Level"] + 0.1, row["Main_Phases"], 
             fontsize=7, ha='center', alpha=0.7, rotation=25)

# ---- Plot settings ----
plt.title("Hydration Levels of Main Carbonate Phases vs. Mg Source and Temperature", fontsize=14)
plt.xlabel("Mg Source")
plt.ylabel("Hydration Level (increasing water content)")
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.legend(title="Temperature (°C)")
plt.show()
print(df.columns.tolist())

