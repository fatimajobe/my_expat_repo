from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class Scraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self._configure_options()
        
    def _configure_options(self):
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        
    def _init_driver(self):
        service = Service(ChromeDriverManager().install())  # Gestion automatique de ChromeDriver
        self.driver = webdriver.Chrome(service=service, options=self.options)
        return self.driver
        
class ExpatDakarScraper(Scraper):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.base_urls = {
            "Voitures": "https://www.expat-dakar.com/voitures",
            "Motos": "https://www.expat-dakar.com/motos-scooters",
            "Équipements et pièces": "https://www.expat-dakar.com/equipements-pieces"
        }
        self.data = []
        
    def _get_containers(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".listings-cards__list-item"))
            )
            return self.driver.find_elements(By.CSS_SELECTOR, ".listings-cards__list-item")
        except:
            return []

    def _scroll_page(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def _scrape_page(self, page):
        self.driver.get(f"{self.base_urls[self.category]}?page={page}")
        self._scroll_page()
        containers = self._get_containers()
        
        for container in containers:
            try:
                item_data = self._extract_item_data(container)
                if item_data:
                    self.data.append(item_data)
            except Exception as e:
                print(f"Erreur sur l'item: {str(e)}")

    def _extract_item_data(self, container):
        raise NotImplementedError()

    def clean_data(self, df):
        df = df.drop_duplicates().reset_index(drop=True)
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        return df.dropna(subset=['prix'])

    def scrape(self, pages=20):
        self._init_driver()
        try:
            for page in range(1, pages + 1):
                print(f"Scraping page {page}...")
                self._scrape_page(page)
        finally:
            self.driver.quit()
        return self.clean_data(pd.DataFrame(self.data))

class VoituresScraper(ExpatDakarScraper):
    def __init__(self):
        super().__init__("Voitures")

    def _extract_item_data(self, container):
        try:
            return {
                "etat": container.find_element(By.CSS_SELECTOR, "span[class*='--condition_']").text,
                "marque": container.find_element(By.CSS_SELECTOR, "span[class*='--make_']").text,
                "annee": container.find_element(By.CSS_SELECTOR, "span[class*='--buildyear_']").text,
                "bvitesse": container.find_element(By.CSS_SELECTOR, "span[class*='--transmission_']").text,
                "adresse": container.find_element(By.CLASS_NAME, 'listing-card__header__location').text,
                "prix": container.find_element(By.CSS_SELECTOR, "span[class*='listing-card__price']").text.replace('\u202f', '').replace(' F Cfa', '').strip(),
                "image_link": container.find_element(By.TAG_NAME, 'img').get_attribute('src')
            }
        except Exception as e:
            print(f"Erreur extraction voiture: {str(e)}")
class MotosScraper(ExpatDakarScraper):
    def __init__(self):
        super().__init__("Motos")

    def _extract_item_data(self, container):
        try:
            return {
                "etat": container.find_element(By.CSS_SELECTOR, "span[class*='--condition_']").text,
                "marque": container.find_element(By.CSS_SELECTOR, "span[class*='--make_']").text,
                "annee": container.find_element(By.CSS_SELECTOR, "span[class*='--buildyear_']").text,
                "adresse": container.find_element(By.CLASS_NAME, 'listing-card__header__location').text,
                "prix": container.find_element(By.CLASS_NAME, 'listing-card__info-bar__price').text.replace('\u202f', '').replace(' F Cfa', '').strip(),
                "image_link": container.find_element(By.TAG_NAME, 'img').get_attribute('src')
            }
        except Exception as e:
            print(f"Erreur extraction moto: {str(e)}")
class EquipementsScraper(ExpatDakarScraper):
    def __init__(self):
        super().__init__("Équipements et pièces")

    def _extract_item_data(self, container):
        try:
            return {
                "details" : container.find_element(By.CLASS_NAME, 'listing-card__header__title').text,
                "etat" : container.find_element(By.CLASS_NAME, 'listing-card__header__tags').text,
                "adresse" : container.find_element(By.CLASS_NAME, 'listing-card__header__location').text,
                "prix" : container.find_element(By.CLASS_NAME, 'listing-card__info-bar__price').text.replace('\u202f', '').replace(' F Cfa', '').strip(),
                "image_link" : container.find_element(By.TAG_NAME, 'img').get_attribute('src')   
            }
        except Exception as e:
            print(f"Erreur extraction équipement: {str(e)}")
            return None
