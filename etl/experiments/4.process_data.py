# %% [markdown]
# ## Necessary imports

# %%
import numpy as np
import pandas as pd

# %%
def remove_space_at_the_end(x: str):
    if x is not None:
        return x.strip()

def replace_double_quote(x: str):
    if x is not None:
        return x.replace("\"\"", "'")

def normalize(data: pd.DataFrame, text_columns):
    data[text_columns] = data[text_columns].apply(
        lambda x: x.apply(remove_space_at_the_end)
    )

    data[text_columns] = data[text_columns].apply(
        lambda x: x.apply(replace_double_quote)
    )

    data["titre"] = data["titre"].apply(lambda x: x.upper())
    data["objet"] = data["objet"].apply(lambda x: x.lower())

    return data



# %% [markdown]
# ## Load and viz data

# %%
data = pd.read_csv("../ref-rna-real-mars-2022-enriched-not-qualified.csv", index_col=0)
data = data[data.columns[1:]] # ignore first column it is index not correctly saved

# %%
data.info()

# %%
text_columns = [
    "titre", "objet", "social_object1_libelle", "social_object2_libelle"
]

data = normalize(data, text_columns)
data.sample(5)

# %% [markdown]
# ## Save without index

# %%
filename = '../ref-rna-real-mars-2022-enriched-not-qualified-process'
data.to_csv(f'./{filename}.csv', index=False)

# %%



