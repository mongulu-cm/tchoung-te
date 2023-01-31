# %%
# create a pandas   dataframe from a csv file
import pandas as pd

df = pd.read_csv('diff.csv', usecols=['id'])
df2 = pd.read_csv('../../ref-rna-real-mars-2022-enriched-not-qualified.csv', )

# %%
# join df and df2 on the id column
df3 = df.join(df2.set_index('id'), on='id')
# drop columns that are not needed
df4 = df3.drop(columns=['Unnamed: 0.1', 'Unnamed: 0','adrs_numvoie','adrs_typevoie','adrs_libvoie',
                  'adrs_codepostal','adrs_libcommune','siteweb','latitude','longitude'])
df4.to_csv("ref-rna-real-mars-2022-enriched-not-qualified-new-only.csv")

# %%
df5 = pd.read_csv('ref-rna-real-mars-2022-enriched-qualified-new-only.csv')
df5 = df5.join(df3.drop(columns=['objet','Unnamed: 0.1', 'Unnamed: 0','adrs', 'dept', 'region',
                                 'social_object1_libelle', 'titre','facebook_url', 'helloasso_url'])
               .set_index('id'), on='id')

df6 = pd.read_csv('../../ref-rna-real-mars-2022-enriched-qualified.csv')
if df5['id'].isin(df6['id']).any():
    print("Dataframes have at least one common value on column 'id'")
else:
    df7 = pd.concat([df5, df6], ignore_index=True)
    df7.set_index('id', inplace=True)
    """
        replace "not found" values with '' so that when not present they are not displayed on Gogocarto
    """
    df7['helloasso_url'].replace('not found', '', inplace=True)
    df7['facebook_url'].replace('not found', '', inplace=True)
    df7.to_csv("../../ref-rna-real-mars-2022-enriched-qualified.csv")
