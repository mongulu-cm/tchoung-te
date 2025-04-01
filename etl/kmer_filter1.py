import pandas as pd
import glob
import os
from IPython import embed
import re
from gliner import GLiNER
import time
from datetime import datetime

# Charger la liste des villes camerounaises
try:
    # Lire le fichier avec le délimiteur tab
    df_cities = pd.read_csv("check_kmer/cm.csv", delimiter='\t', header=None)
    # Filtrer les noms de villes trop courts (moins de 4 caractères)
    cameroon_cities = df_cities.iloc[:, 1].dropna().unique().tolist()
    cameroon_cities = [city for city in cameroon_cities if len(str(city)) >= 4]
    print(f"Nombre de villes camerounaises chargées : {len(cameroon_cities)}")
except Exception as e:
    print(f"Erreur lors de la lecture du fichier des villes : {e}")
    print("Utilisation de la liste de base uniquement")
    cameroon_cities = []

# Nos mots-clés de base
base_keywords = [
    r"\bCAMEROUN\b", r"\bCAMEROUNAIS\b", r"\bCAMEROUNAISE\b", r"\bKMER\b",
    r"\bBAMILEKE\b", r"\bBETI\b", r"\bBAMOUN\b",
    r"\bSAWA\b", r"\bMBOA\b"
]

# Combiner les deux listes et ajouter les word boundaries
all_keywords = base_keywords + [r"\b" + str(city) + r"\b" for city in cameroon_cities]

def log_progress(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Démarrer le chronomètre
start_time = time.time()

log_progress("Chargement du modèle GLiNER...")
model = GLiNER.from_pretrained("gliner-large")

def filter_cameroon_with_gliner(text):
    if pd.isna(text):
        return None
    
    try:
        entities = model.predict(text)
        
        # Garder la trace de l'entité et son contexte
        for entity in entities:
            if "cameroun" in entity.lower():
                return {"entity": entity, "type": "pays"}
            if entity in cameroon_cities:
                return {"entity": entity, "type": "ville"}
        return None
    except Exception as e:
        log_progress(f"Erreur d'analyse: {str(e)[:100]}...")
        return None

log_progress("Lecture des fichiers CSV...")
file_location = f"{os.getcwd()}/rna_waldec_20220301/"
all_files = glob.glob(os.path.join(file_location, "*.csv"))

# Lecture par lots pour gérer la mémoire
chunk_size = 1000
all_results = []

for file in all_files:
    log_progress(f"Traitement du fichier: {os.path.basename(file)}")
    for chunk in pd.read_csv(file, delimiter=";", encoding="ISO-8859-1", 
                           usecols=['titre', 'objet'], chunksize=chunk_size):
        
        # Analyse du titre
        chunk['detection'] = chunk['titre'].apply(filter_cameroon_with_gliner)
        
        # Si rien trouvé dans le titre, analyser l'objet
        mask_no_detection = chunk['detection'].isna()
        chunk.loc[mask_no_detection, 'detection'] = \
            chunk.loc[mask_no_detection, 'objet'].apply(filter_cameroon_with_gliner)
        
        # Garder les résultats positifs
        positive_results = chunk[chunk['detection'].notna()]
        if len(positive_results) > 0:
            all_results.append(positive_results)
        
        log_progress(f"Traité {len(chunk)} associations...")

# Combiner tous les résultats
df_cameroon = pd.concat(all_results, ignore_index=True)

# Extraire les informations de détection
df_cameroon['mot_cle'] = df_cameroon['detection'].apply(lambda x: x['entity'] if x else None)
df_cameroon['type_detection'] = df_cameroon['detection'].apply(lambda x: x['type'] if x else None)

# Nettoyer et sauvegarder
df_cameroon = df_cameroon[['titre', 'objet', 'mot_cle', 'type_detection']]
df_cameroon.to_csv("associations_camerounaises_gliner.csv", index=False)

# Statistiques finales
end_time = time.time()
duration = end_time - start_time

log_progress(f"""
Traitement terminé !
Durée totale: {duration/60:.2f} minutes
Nombre d'associations trouvées: {len(df_cameroon)}
Répartition par type:
{df_cameroon['type_detection'].value_counts().to_dict()}
""")
