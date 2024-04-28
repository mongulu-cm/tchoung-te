import os
import requests
from bs4 import BeautifulSoup

DATA_GOUV_PATH = "https://www.data.gouv.fr/fr/datasets/repertoire-national-des-associations/"

def read_data_gouv_page():
    headers = {'User-Agent': None}
    response = requests.get(DATA_GOUV_PATH, headers=headers)
    if 200 <= response.status_code <= 300:
        return response.content
    raise Exception(response.content)

def download_link(url: str, headers=None):
    if url.endswith("download") or url.endswith((".pdf", ".docx", ".zip", ".exe", ".jpg", ".png")):
        response = requests.get(url, headers=headers)
        if  (200 <= response.status_code <= 300):
            name = os.path.basename(url)
            with open(name, "wb") as file:
                file.write(response.content)
            return name

def search_and_download_data():
    page = read_data_gouv_page()
    soup = BeautifulSoup(page, 'html.parser')
    links = soup.find_all('a', href=True)
    links: list[str] = [
        i["href"] for i in links if ("media.interieur.gouv" in i["href"])
    ]
    rna_import = [i for i in links if "rna_import" in i]
    rna_waldec = [i for i in links if "rna_waldec" in i]

    rna_import = sorted(rna_import, reverse=True)[0]
    rna_waldec = sorted(rna_waldec, reverse=True)[0]

    rna_import = download_link(rna_import)
    rna_waldec = download_link(rna_waldec)
    return rna_import, rna_waldec

if __name__ == "__main__":
    search_and_download_data()