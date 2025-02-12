
# coding: utf-8

# In[1]:
import pandas as pd    
import numpy as np
import nltk
import csv
import io
import sklearn
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
import json
import math
import sklearn.cluster as sk
from collections import Counter
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
import wordcloud
from PIL import Image
import math
import random

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
    prezzi = []
    idx = 1  # Contatore per le pagine
    count = 0  # Contatore per il numero di richieste
    max_links = 2  # Limita il numero di link da raccogliere per il test

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

           

            # Funzione per verificare se una stringa contiene numeri
            def contains_number(s):
                return any(char.isdigit() for char in s)

            # Processa le caratteristiche estratte
            for feature in features:
                print(f"Feature: {feature}")  # Per vedere la feature estratta

                # Verifica se la caratteristica contiene numeri (per locali, superficie, bagni)
                if contains_number(feature):
                    # Se la caratteristica contiene numeri, estrai solo i numeri (per esempio per locali o superficie)
                    numbers = ''.join([c for c in feature if c.isdigit()])
                    row.append(numbers)  # Aggiungi il numero estratto
                else:
                    # Se la caratteristica non contiene numeri, metti "si" o "no"
                    # Ad esempio, se trovi "ascensore", "arredato", ecc.
                    if 'ascensore' in feature.lower():
                        row.append('si' if 'ascensore' in feature.lower() else 'no')
                    elif 'arredato' in feature.lower():
                        row.append('si' if 'arredato' in feature.lower() else 'no')
                    elif 'cantina' in feature.lower():
                        row.append('si' if 'cantina' in feature.lower() else 'no')
                    elif 'balcone' in feature.lower():
                        row.append('si' if 'balcone' in feature.lower() else 'no')
                    else:
                        row.append('si' if len(feature.strip()) > 0 else 'no')
    
            # Aggiungi la riga finale dei dati alla lista dei dati
            data.append(row)
            count += 1
            print(f"Proprietà {count}: {url} raccolta con successo.")

            # Ritardo casuale tra le richieste per evitare di sovraccaricare il server
            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"Errore durante l'elaborazione di {url}: {e}")
            continue

    # Creazione del DataFrame finale
    df = pd.DataFrame(data, columns=['title', 'description', 'price', 'locali', 'superficie', 'bagni', 'piano', 'Ascensore', 'Balcone', 'Arredato', 'Cantina'])

    # Salva su CSV
    df.to_csv('data.csv', sep=",", header=True, index=False)

    print(f"Raccolti {len(data)} annunci.")



# Avvia la funzione di scraping
scraping()

