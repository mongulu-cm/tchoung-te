import pandas as pd
import geopandas
from rich.pretty import pprint
from tqdm import tqdm

tqdm.pandas()
waldec_csv = pd.read_csv('rna-nomenclature-waldec.csv', delimiter=";",
                         index_col=2).to_dict()["Libellé objet social parent"]
# pprint(waldec_csv)
waldec_csv[00000] = "AUTRES"
waldec_csv[19060] = "INTERVENTIONS SOCIALES"
waldec_csv[22010] = "REPRÉSENTATION, PROMOTION ET DÉFENSE D'INTÉRÊTS ÉCONOMIQUES"
waldec_csv[6035] = "CULTURE, PRATIQUES D'ACTIVITÉS ARTISTIQUES, PRATIQUES CULTURELLES"
waldec_csv[40510] = "ACTIVITÉS RELIGIEUSES, SPIRITUELLES OU PHILOSOPHIQUES"
waldec_csv[17035] = "SANTÉ"

gdf = geopandas.read_file("ref-rna.geojson")
gdf["social_object1"].replace(to_replace=[None], value=000000)
gdf['social_object1_libelle'] = gdf.apply(lambda row: waldec_csv[int(row["social_object1"] or 0)], axis=1)
gdf['social_object2_libelle'] = gdf.apply(lambda row: waldec_csv[int(row["social_object2"] or 0)], axis=1)

# gdf.to_file("ref-rnal-derefrence.geojson", driver="GeoJSON")
# pprint(gdf)

gdf = gdf.drop(columns=['dissolution_date', 'reg_name', 'creation_date', 'publication_date', 'pc_address_asso',
                         'social_object1', 'id', 'social_object2', 'update_date', 'dep_name', 'group',
                         'com_arm_area_code', 'siret', 'website', 'nature', 'namedplace_address_asso',
                         'declaration_date', 'management', 'id_ex', 'civility_manager', 'observation', 'ispublic',
                         'short_title', 'position', 'epci_name'])
gdf.to_file("ref-rna-derefrence-clean.geojson", driver="GeoJSON")
gdf.to_csv("ref-rna-derefrence-clean.csv") # ajouter id au début
pprint(gdf.columns)
