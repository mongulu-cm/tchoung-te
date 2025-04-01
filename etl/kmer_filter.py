import pandas as pd
import glob
import os
import time
import re
from datetime import datetime
import spacy

def log_progress(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Démarrer le chronomètre
start_time = time.time()

# Charger le modèle spaCy français
log_progress("Chargement du modèle spaCy...")
try:
    nlp = spacy.load("fr_core_news_md")
    log_progress("Modèle chargé avec succès")
except:
    log_progress("Installation du modèle français...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "fr_core_news_md"])
    nlp = spacy.load("fr_core_news_md")

# Mots-clés camerounais de base
base_keywords = [
    "cameroun", "camerounais", "camerounaise", "kmer",
    "douala", "yaoundé", "bamenda", "garoua", "maroua", 
    "bafoussam", "bamileke", "beti", "bamoun", "sawa"
]

# Charger les villes du Cameroun depuis cm.csv
log_progress("Chargement des villes camerounaises...")
try:
    df_cities = pd.read_csv("check_kmer/cm.csv", delimiter='\t', header=None)
    # Filtrer les noms de villes trop courts (moins de 4 caractères)
    cameroon_cities = df_cities.iloc[:, 1].dropna().unique().tolist()
    cameroon_cities = [str(city).lower() for city in cameroon_cities if len(str(city)) >= 4]
    log_progress(f"Chargé {len(cameroon_cities)} villes camerounaises")
except Exception as e:
    log_progress(f"Erreur lors du chargement des villes : {e}")
    cameroon_cities = []

# Combiner les deux listes
all_keywords = base_keywords + cameroon_cities

def filter_cameroon_with_spacy(text):
    if pd.isna(text):
        return None
    
    try:
        # Traiter le texte avec spaCy
        text = text.lower()
        doc = nlp(text)
        
        # Vérifier les entités géographiques
        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE"]:  # Lieu ou entité géopolitique
                ent_text = ent.text.lower()
                if ent_text in all_keywords:
                    return ent.text
        
        # Si aucune entité n'est trouvée, vérifier les mots-clés avec des expressions régulières
        for keyword in all_keywords:
            # Utiliser une regex pour trouver des mots entiers uniquement
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                return keyword
                
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
    try:
        for chunk in pd.read_csv(file, delimiter=";", encoding="ISO-8859-1", 
                               usecols=['titre', 'objet'], chunksize=chunk_size):
            
            # Analyse du titre
            chunk['mot_cle'] = chunk['titre'].apply(filter_cameroon_with_spacy)
            
            # Si rien trouvé dans le titre, analyser l'objet
            mask_no_detection = chunk['mot_cle'].isna()
            chunk.loc[mask_no_detection, 'mot_cle'] = \
                chunk.loc[mask_no_detection, 'objet'].apply(filter_cameroon_with_spacy)
            
            # Garder les résultats positifs
            positive_results = chunk[chunk['mot_cle'].notna()]
            if len(positive_results) > 0:
                all_results.append(positive_results)
            
            log_progress(f"Traité {len(chunk)} associations...")
    except Exception as e:
        log_progress(f"Erreur lors du traitement du fichier {os.path.basename(file)}: {str(e)}")
        continue

# Combiner tous les résultats
if all_results:
    df_cameroon = pd.concat(all_results, ignore_index=True)
    
    # Sauvegarder les résultats
    df_cameroon.to_csv("associations_camerounaises_spacy.csv", index=False)
    
    # Statistiques finales
    end_time = time.time()
    duration = end_time - start_time
    
    log_progress(f"""
    Traitement terminé !
    Durée totale: {duration/60:.2f} minutes
    Nombre d'associations trouvées: {len(df_cameroon)}
    """)
else:
    log_progress("Aucune association camerounaise trouvée.")
