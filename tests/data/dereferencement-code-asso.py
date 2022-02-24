import pandas as pd
import geopandas
from rich.pretty import pprint

waldec_csv = pd.read_csv('rna-nomenclature-waldec.csv', delimiter=";",
                         index_col=2).to_dict()["Libellé objet social parent"]
# pprint(waldec_csv)
waldec_csv[00000] = "AUTRES"
waldec_csv[19060] = "INTERVENTIONS SOCIALES"
waldec_csv[22010] = "REPRÉSENTATION, PROMOTION ET DÉFENSE D'INTÉRÊTS ÉCONOMIQUES"
waldec_csv[6035] = "CULTURE, PRATIQUES D'ACTIVITÉS ARTISTIQUES, PRATIQUES CULTURELLES"
waldec_csv[40510] = "ACTIVITÉS RELIGIEUSES, SPIRITUELLES OU PHILOSOPHIQUES"
waldec_csv[17035] = "SANTÉ"

gdf = geopandas.read_file("ref-france-association-repertoire-national.geojson")
gdf["social_object1"].replace(to_replace=[None], value=000000)
gdf['social_object1_libelle'] = gdf.apply(lambda row: waldec_csv[int(row["social_object1"] or 0)], axis=1)
gdf['social_object2_libelle'] = gdf.apply(lambda row: waldec_csv[int(row["social_object2"] or 0)], axis=1)
gdf.to_file("ref-france-association-repertoire-national-derefrence.geojson", driver="GeoJSON")

#pprint(gdf)
