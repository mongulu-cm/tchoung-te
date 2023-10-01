# %%
import os

import ftfy
import pandas as pd
import requests
import requests_cache
from abbreviations import schwartz_hearst
from pandarallel import pandarallel
from rich.traceback import install
from tqdm import tqdm

tqdm.pandas()
pandarallel.initialize(progress_bar=True)
requests_cache.install_cache("enrich_cache", backend="sqlite")
install(show_locals=True)


subscription_key = os.environ["BING_SUBSCRIPTION_KEY"]
search_url = "https://api.bing.microsoft.com/v7.0/search"

# %%
df = pd.read_csv("ref-rna-real-mars-2022.csv")

# %%
# Plusieurs titres contiennent le nom de l'association et abbreviation entre parenthèses ou pas
df[df.titre.str.contains("\(")].head(2)

# %%


def enrich(site, name):
    # time.sleep(1)

    name = ftfy.fix_text(name)  # enlever les \
    if "(" in name:
        # L'algorithme de schwartz_hearst sépare le texte en 2 parties {"abbreviation" : "texte sans abbreviation"}
        # Cependant il ne fonctionne que si abbreviation est entre parenthèses et après le nom non abrégé.
        # Il ne fonctionne donc pas si abbreviation est avant celui-ci et dans le cas ou il n'y a pas de parenthèses.
        pairs = schwartz_hearst.extract_abbreviation_definition_pairs(doc_text=name)
        # print(pairs)
        if len(pairs) == 1:
            name = list(pairs.values())[0]

    # inspired from https://github.com/Azure-Samples/cognitive-services-REST-api-samples/blob/master/python/Search/BingWebSearchv7.py
    search_term = f"{name} site:{site}"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {
        "q": search_term,
        "textDecorations": True,
        "textFormat": "HTML",
        "mkt": "fr-FR",
    }
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    return (
        search_results["webPages"]["value"][0]["url"]
        if "webPages" in search_results
        else "not found"
    )


# %%
df["facebook_url"] = df.parallel_apply(
    lambda row: enrich("facebook.com", row["titre"]), axis=1
)

# %%
df["facebook_url"].describe()

# %%
df["facebook_url"].head(100)

# %%
df["helloasso_url"] = df.parallel_apply(
    lambda row: enrich("helloasso.com", row["titre"]), axis=1
)

# %%
df["helloasso_url"].describe()

# %%
df["helloasso_url"].head(10)

# %%
df.head(2)

# %%
df.to_csv("ref-rna-real-mars-2022-enriched-not-qualified.csv")
