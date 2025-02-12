import pandas as pd    
import random
from fastapi import FastAPI, BackgroundTasks
import requests
from bs4 import BeautifulSoup
import time
import random
app = FastAPI()

# Variabili globali per memorizzare i risultati dello scraping
scraping_results = []
scraping_done = False

def controlled(link):
    """
    Se l'URL non contiene 'http', lo aggiunge per creare un URL completo
    """
    if link[:4] != 'http':
        link = 'https://www.immobiliare.it' + link
    return link

def scraping():
    """
    Funzione di scraping principale che estrae le informazioni delle proprietà da Immobiliare.it
    e salva i dati in una variabile globale per poterli restituire via API.
    """
    global scraping_results, scraping_done
    links = []  # Lista per memorizzare i link alle proprietà
    idx = 1  # Contatore per le pagine

    # Raccoglie i link dalle pagine
    while len(links) < 1:
        url = 'https://www.immobiliare.it/affitto-case/milano/?criterio=rilevanza&prezzoMassimo=800&pag=' + str(idx)
        idx += 1
        try:
            start_time = time.time()
            content = requests.get(url, timeout=10)
            print(f"Richiesta a {url} durata: {time.time() - start_time:.2f} secondi")
            soup = BeautifulSoup(content.text, "lxml")
        except requests.exceptions.Timeout:
            print(f"Timeout durante l'accesso a {url}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Errore durante l'accesso a {url}: {e}")
            continue

        time.sleep(random.uniform(1, 3))

        print(f"Parsing pagina {idx-1}...")

        divTag = soup.find_all("div", {'class': "nd-mediaObject__content in-listingCardPropertyContent"})
        if not divTag:
            print(f"Nessun div trovato nella pagina {idx-1}, potresti voler verificare la struttura del sito.")
            break
        else:
            print(f"Trovati {len(divTag)} div con class='nd-mediaObject__content in-listingCardPropertyContent'")

        for tag in divTag:
            tdTags = tag.find_all("a")
            for tag in tdTags:
                if 'href' in tag.attrs:
                    link = controlled(tag['href'])
                    if link not in links:
                        links.append(link)
        
        print(f"Raccolti {len(links)} link finora...")

    # Lista per memorizzare i dati delle proprietà
    data = []
    count = 1

    # Raccoglie i dati da ogni URL trovato
    for url in links:
        try:
            start_time = time.time()
            content = requests.get(url, timeout=10)
            print(f"Richiesta a {url} durata: {time.time() - start_time:.2f} secondi")
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
            divTag = soup.find_all("div", {"class": "re-mainFeatures"})  # Estrai tutti i div con le caratteristiche
            features = []  # Lista per memorizzare le caratteristiche

            for tag in divTag:
                feature_items = tag.find_all("div", {'class': 're-mainFeatures__item'})  # Trova ogni elemento con le caratteristiche
                for feature in feature_items:
                    feature_text = feature.text.replace('\xa0', ' ').replace('\n', ' ').replace('+', ' ').strip()  # Pulizia del testo
                    features.append(feature_text)  # Aggiungi la caratteristica alla lista

            # Aggiungi i numeri (se ci sono) e le caratteristiche al row
            for feature in features:
                row.append(feature)

            # Aggiungi la riga finale dei dati alla lista dei dati
            data.append(row)
            count += 1
            print(f"Proprietà {count}: {url} raccolta con successo.")

            # Ritardo casuale tra le richieste per evitare di sovraccaricare il server
            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"Errore durante l'elaborazione di {url}: {e}")
            continue

    # Memorizza i risultati come variabili globali
    scraping_results = data
    scraping_done = True
    print(f"Raccolti {len(data)} annunci.")

@app.post("/start-scraping")
async def start_scraping(background_tasks: BackgroundTasks):
    """
    Avvia il processo di scraping in background.
    """
    background_tasks.add_task(scraping)
    return {"message": "Scraping avviato in background."}

@app.get("/get-results")
async def get_results():
    """
    Restituisce i risultati dello scraping una volta completato.
    """
    if scraping_done:
        return {"results": scraping_results}
    else:
        return {"message": "Lo scraping non è ancora completato. Riprova tra qualche secondo."}