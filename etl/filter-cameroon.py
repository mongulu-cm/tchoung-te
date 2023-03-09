# %%
# CSV Files downloaded from https://www.data.gouv.fr/fr/datasets/repertoire-national-des-associations/  Fichier RNA Waldec du 01 Mars 2022
import glob
import os
import openai
import boto3

import geocoder
import pandas as pd
import requests_cache
from geopy.geocoders import Nominatim
from pandarallel import pandarallel
from lambdaprompt import prompt, GPT3Prompt

# %%
file_location = os.getcwd() + "/rna_waldec_20220301/"
all_files = glob.glob(os.path.join(file_location, "*.csv"))

df = pd.concat((pd.read_csv(f, delimiter=";", header=0, encoding="ISO-8859-1")
               for f in all_files), ignore_index=True)

ssm = boto3.client('ssm', region_name='eu-central-1')
openai.api_key = ssm.get_parameter(Name="/tchoung-te/openai_api_key", WithDecryption=False)['Parameter']['Value']
os.environ["OPENAI_API_KEY"] = openai.api_key # setter la variable d'environnement

# %%
df.columns

# %%


def filter_cameroon(df):
    return df[df['titre'].str.contains("CAMEROUN", case=False, na=False) | df['objet'].str.contains("CAMEROUN", case=False, na=False)]


def remove_closed(df):
    return df[df["position"].str.contains("D|S") == False]


def normalize(df):
    df['titre'].str.upper()
    df['objet'].str.lower()
    df['adrs_codepostal'] = df["adrs_codepostal"].astype(int)
    df['objet_social1'] = df["objet_social1"].astype(int)
    df['objet_social2'] = df["objet_social2"].astype(int)
    # this will avoid nan in adrs which concatenate multiple values
    df = df.fillna('')

    return df


def select_relevant_columns(df):
    return df[["id", "titre", "objet", "objet_social1", "objet_social2", "adrs_numvoie", "adrs_typevoie", "adrs_libvoie", "adrs_codepostal", "adrs_libcommune", "siteweb"]]


def add_column_adrs(df):
    df["adrs"] = df['adrs_numvoie'].map(str) + " " + df['adrs_typevoie'].map(str) + " " + df['adrs_libvoie'].map(str)+" " + \
        df['adrs_codepostal'].map(str)+" "+df['adrs_libcommune'].map(str)

    # Complete the right way to write the type of way in the address
    prompt_function = GPT3Prompt("Replace the abbreviation by the correct word in address in french: {{ prmt }} ")
    tmp = df['adrs_typevoie'].map(prompt_function).apply(lambda x: x.replace("\n", ""))
    df['adrs_typevoie'] = tmp

    from postal.expand import expand_address
    df["adrs"] = df.apply(lambda row: expand_address(row["adrs"])[0], axis=1)
    return df


df2 = df.pipe(filter_cameroon) \
        .pipe(remove_closed) \
        .pipe(normalize) \
        .pipe(select_relevant_columns) \
        .pipe(add_column_adrs)

df2.sample(5)

# %%
# Downloaded from https://download.geonames.org/export/zip/
region_by_postal_codes = pd.read_csv('code-postal-geonames.tsv', delimiter="\t",
                                     index_col=1).to_dict()["REGION"]

dept_by_postal_codes = pd.read_csv('code-postal-geonames.tsv', delimiter="\t",
                                   index_col=1).to_dict()["DEPT"]

region_by_postal_codes["97300"] = "Guyane"
dept_by_postal_codes["97300"] = "Guyane"
region_by_postal_codes["97419"] = "Réunion"
dept_by_postal_codes["97419"] = "Réunion"
region_by_postal_codes["97438"] = "Réunion"
dept_by_postal_codes["97438"] = "Réunion"
region_by_postal_codes["97600"] = "Mayotte"
dept_by_postal_codes["97600"] = "Mayotte"


waldec_csv = pd.read_csv('rna-nomenclature-waldec.csv', delimiter=";",
                         index_col=2).to_dict()["Libellé objet social parent"]
# pprint(waldec_csv)
waldec_csv[00000] = "AUTRES"
waldec_csv[19060] = "INTERVENTIONS SOCIALES"
waldec_csv[22010] = "REPRÉSENTATION, PROMOTION ET DÉFENSE D'INTÉRÊTS ÉCONOMIQUES"
waldec_csv[6035] = "CULTURE, PRATIQUES D'ACTIVITÉS ARTISTIQUES, PRATIQUES CULTURELLES"
waldec_csv[40510] = "ACTIVITÉS RELIGIEUSES, SPIRITUELLES OU PHILOSOPHIQUES"
waldec_csv[17035] = "SANTÉ"

# %%


def add_dept_and_region(df):

    def get_dept_region(code_postal):
        try:
            dept = dept_by_postal_codes[str(code_postal)]
        except KeyError:
            dept = dept_by_postal_codes[[
                x for x in dept_by_postal_codes.keys() if str(code_postal) in x][0]]

        try:
            region = region_by_postal_codes[str(code_postal)]
        except KeyError:
            region = region_by_postal_codes[[
                x for x in region_by_postal_codes.keys() if str(code_postal) in x][0]]

        return {"dept": dept, "region": region}

    df["dept"] = df.apply(lambda row: get_dept_region(
        row["adrs_codepostal"])["dept"], axis=1)
    df["region"] = df.apply(lambda row: get_dept_region(
        row["adrs_codepostal"])["region"], axis=1)

    return df


def add_social_object_libelle(df):
    df['social_object1_libelle'] = df.apply(
        lambda row: waldec_csv[int(row["objet_social1"] or 0)], axis=1)
    df['social_object2_libelle'] = df.apply(
        lambda row: waldec_csv[int(row["objet_social2"] or 0)], axis=1)

    return df


df2 = df2.pipe(add_dept_and_region) \
         .pipe(add_social_object_libelle)

#df2["dept"] = df2.apply(lambda row: get_dept_region(row["adrs_codepostal"])["dept"],axis=1)
#df2["region"] = df2.apply(lambda row: get_dept_region(row["adrs_codepostal"])["region"],axis=1)

# get_info("W212001727")
# get_dept_region(30913)
df2.sample(5)

# %%
pandarallel.initialize(progress_bar=True)
requests_cache.install_cache('geocode_cache')

geolocator = Nominatim(user_agent="tchoung-te.mongulu.cm")


def add_lat_lon(df):
    def geocode(adrs):
        return geolocator.geocode(adrs, country_codes="fr", timeout=None)

    df['geocode'] = df.parallel_apply(lambda row: geocode(row["adrs"]), axis=1)

    # df2[df2.geocode.isnull()] 417 rows n'ont pas de géocodage
    # df2[df2.adrs_libcommune.isnull()] # mais aucune n'a le nom de la commune vide donc ce sera ça qui sera utilisé
    df.loc[df.geocode.isnull(), "geocode"] = df[df.geocode.isnull()].parallel_apply(
        lambda row: geocode(row["adrs_libcommune"]), axis=1)
    # 4 associations restent sans geocode, on les force
    df.loc[df.id == "W251002897", "geocode"] = df[df.geocode.isnull()].apply(
        lambda row: geocode("Besançon"), axis=1)
    df.loc[df.id == "W302012059", "geocode"] = df[df.geocode.isnull()].apply(
        lambda row: geocode("Nimes"), axis=1)
    df.loc[df.id == "W313015063", "geocode"] = df[df.geocode.isnull()].apply(
        lambda row: geocode("Toulouse"), axis=1)
    df.loc[df.id == "W382000558", "geocode"] = df[df.geocode.isnull()].apply(
        lambda row: geocode("Satolas-et-Bonce"), axis=1)

    df['longitude'] = df['geocode'].apply(lambda x: x.longitude)
    df['latitude'] = df['geocode'].apply(lambda x: x.latitude)
    df = df.drop(columns=["objet_social1", "objet_social2", "geocode"], axis=1)

    return df


def format_libelle_for_gogocarto(df):
    # Gogocarto lit une liste de catégories sur un champ défini et considère la virgule comme le caractère de séparation
    # On a donc opté pour remplacer la virgule(",") par le slash("/")
    df["social_object1_libelle"] = df["social_object1_libelle"].apply(
        lambda x: x.replace(",", "/"))
    df["social_object2_libelle"] = df["social_object2_libelle"].apply(
        lambda x: x.replace(",", "/"))

    return df


df2 = df2.pipe(add_lat_lon) \
         .pipe(format_libelle_for_gogocarto)
df2.sample(5)

# %%


def remove_space_at_the_end(x: str):
    if x is not None:
        return x.strip()


def replace_double_quote(x: str):
    if x is not None:
        return x.replace("\"\"", "'")


def normalize(data: pd.DataFrame):
    text_columns = [
        "titre", "objet", "social_object1_libelle", "social_object2_libelle"
    ]
    data[text_columns] = data[text_columns].apply(
        lambda x: x.apply(remove_space_at_the_end)
    )
    data[text_columns] = data[text_columns].apply(
        lambda x: x.apply(replace_double_quote)
    )
    data["titre"] = data["titre"].apply(lambda x: x.upper())
    data["objet"] = data["objet"].apply(lambda x: x.lower())

    return data


df2 = df2.pipe(normalize)

df2.sample(5)

# %%
df2.to_csv("rna-real-mars-2022-new.csv")
