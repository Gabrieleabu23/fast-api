import pandas as pd    
import random
from fastapi import FastAPI

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
# Funzione per controllare e completare l'URL se necessario
def controlled(link):
    """
    Se l'URL non contiene 'http', lo aggiunge per creare un URL completo
    """
    if link[:4] != 'http':
        link = 'https://www.immobiliare.it' + link
    return link

# Funzione di scraping principale
def scraping():
    """
    Estrae le informazioni delle proprietà da Immobiliare.it e salva i dati in un CSV
    """
    links = []  # Lista per memorizzare i link alle proprietà
    idx = 1  # Contatore per le pagine

    # Raccoglie i link dalle pagine
    while len(links) < 1:
        url = f'https://www.immobiliare.it/affitto-case/milano/?criterio=rilevanza&prezzoMassimo=800&pag={idx}'
        idx += 1
        try:
            content = requests.get(url, timeout=10)
            soup = BeautifulSoup(content.text, "lxml")
        except requests.exceptions.Timeout:
            print(f"Timeout durante l'accesso a {url}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Errore durante l'accesso a {url}: {e}")
            continue

        time.sleep(random.uniform(1, 3))

        divTag = soup.find_all("div", {'class': "nd-mediaObject__content in-listingCardPropertyContent"})
        for tag in divTag:
            tdTags = tag.find_all("a")
            for tag in tdTags:
                if 'href' in tag.attrs:
                    link = controlled(tag['href'])
                    if link not in links:
                        links.append(link)

    # Lista per memorizzare i dati delle proprietà
    data = []
    for url in links:
        try:
            content = requests.get(url, timeout=10)
            soup = BeautifulSoup(content.text, "lxml")
            row = []

            # Estrai il titolo della proprietà
            divTag = soup.find_all("h1", {'class': "re-title__title"})
            row.append(divTag[0].text.strip() if divTag else "")

            # Estrai la descrizione della proprietà
            divTag = soup.find_all("div", {"data-tracking-key": "description"})
            description_text = ""
            for desc in divTag:
                description_content = desc.find("div", {'class': "in-readAll in-readAll--lessContent"})
                if description_content:
                    description_text = description_content.text.strip().replace('\n', ' ')
            row.append(description_text)

            # Estrai il prezzo e altre informazioni della proprietà
            divTag = soup.find_all("div", {"class": "re-overview__price"})
            price = ""
            for tag in divTag:
                price_tag = tag.find("span")
                if price_tag:
                    price = price_tag.text.strip().replace("€", "").split("/")[0].strip()
            row.append(price)

            # Estrai tutte le caratteristiche dalla sezione 're-mainFeatures'
            divTag = soup.find_all("div", {"class": "re-mainFeatures"})
            features = []  # Lista per memorizzare le caratteristiche
            for tag in divTag:
                feature_items = tag.find_all("div", {'class': 're-mainFeatures__item'})
                for feature in feature_items:
                    feature_text = feature.text.replace('\xa0', ' ').replace('\n', ' ').replace('+', ' ').strip()
                    features.append(feature_text)

            # Aggiungi le caratteristiche
            row.extend(features)

            # Aggiungi la riga finale dei dati alla lista dei dati
            data.append(row)

            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"Errore durante l'elaborazione di {url}: {e}")
            continue

    # Creazione del DataFrame finale
    df = pd.DataFrame(data, columns=['title', 'description', 'price', 'features'])

    # Salva su CSV
    df.to_csv('data.csv', sep=",", header=True, index=False)
    print(f"Raccolti {len(data)} annunci.")
    return len(data)


# Crea l'app FastAPI
app = FastAPI()

@app.get("/scraping")
async def start_scraping(background_tasks: BackgroundTasks):
    """
    Avvia il processo di scraping in background.
    """
    background_tasks.add_task(scraping)
    return {"message": "Scraping avviato in background."}


# Avvia il server FastAPI con il comando:
# uvicorn nome_file:app --reload