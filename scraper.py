from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Définir les URLs pour chaque catégorie
Categories = {
    "Motos": {
        "url": "https://www.expat-dakar.com/motos-scooters-velos",
        "columns": ["Etat", "Marque", "Année", "Adresse", "image_link"]
    },
    "Voitures": {
        "url": "https://www.expat-dakar.com/voitures",
        "columns": ["Etat", "Marque", "Année", "Boite vitesse", "Adresse", "Prix", "image_link"]
    },
    "Équipements et pièces": {
        "url": "https://www.expat-dakar.com/equipements-pieces",
        "columns": ["Détails", "Etat", "Adresse", "Prix", "image_link"]
    }
}

class Scraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
    
    def scrape(self, category, pages):
        data = []
        base_url = Categories[category]["url"]
        columns = Categories[category]["columns"]
        
        try:
            for page in range(1, pages + 1):
                url = f"{base_url}?page={page}"
                self.driver.get(url)
                
                # Attendre le chargement dynamique
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "listing-item"))
                )
                
                # Faire défiler pour charger le contenu JS
                self._scroll_page()
                
                # Extraire les données
                items = self.driver.find_elements(By.CLASS_NAME, "listing-item")
                for item in items:
                    entry = self._parse_item(item, columns)
                    data.append(entry)
        
        finally:
            self.driver.quit()
            
        return pd.DataFrame(data)

    def _scroll_page(self):
        """Défilement pour charger tout le contenu JS"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _parse_item(self, item, columns):
        """Extraction des données avec gestion des erreurs"""
        data = {}
        for column in columns:
            try:
                if column == "image_link":
                    img_element = item.find_element(By.TAG_NAME, "img")
                    data[column] = img_element.get_attribute("src") if img_element else None
                elif column == "Etat":
                    state_element = item.find_element(By.CLASS_NAME, "listing-item-state")
                    data[column] = state_element.text.strip() if state_element else None
                elif column == "Marque":
                    title_element = item.find_element(By.CLASS_NAME, "listing-item-title")
                    data[column] = title_element.text.strip() if title_element else None
                elif column == "Année":
                    year_element = item.find_element(By.CLASS_NAME, "listing-item-year")
                    data[column] = year_element.text.strip() if year_element else None
                elif column == "Adresse":
                    location_element = item.find_element(By.CLASS_NAME, "listing-item-location")
                    data[column] = location_element.text.strip() if location_element else None
                elif column == "Prix":
                    price_element = item.find_element(By.CLASS_NAME, "listing-item-price")
                    data[column] = price_element.text.strip() if price_element else None
                elif column == "Boite vitesse":
                    transmission_element = item.find_element(By.CLASS_NAME, "listing-item-transmission")
                    data[column] = transmission_element.text.strip() if transmission_element else None
                elif column == "Détails":
                    details_element = item.find_element(By.CLASS_NAME, "listing-item-details")
                    data[column] = details_element.text.strip() if details_element else None
                else:
                    data[column] = None
            except Exception as e:
                data[column] = None
                print(f"Error parsing {column}: {e}")
        return data

    def clean_data(self, df):
        """
        Nettoyer les données scrapées
        """
        # Supprimer les doublons
        df.drop_duplicates(inplace=True)

        # Supprimer les lignes avec des valeurs manquantes
        df.dropna(inplace=True)

        # Convertir les prix en numérique
        if "Prix" in df.columns:
            df["Prix"] = df["Prix"].str.replace(" ", "").str.replace("FCFA", "").str.replace(",", "").astype(int)

        # Convertir les dates en datetime
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        return df
