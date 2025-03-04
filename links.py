import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pymongo

# Conectar a MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["procore_scraper"]

# Lista de URLs con su respectiva colección en MongoDB
state_collections = {
    "https://www.procore.com/network/us/mn": "minnesota",
    "https://www.procore.com/network/us/ms": "mississippi",
    "https://www.procore.com/network/us/mo": "missouri",
    "https://www.procore.com/network/us/mt": "montana",
    "https://www.procore.com/network/us/ne": "nebraska",
    "https://www.procore.com/network/us/nv": "nevada",
    "https://www.procore.com/network/us/nh": "new_hampshire",
    "https://www.procore.com/network/us/nj": "new_jersey",
    "https://www.procore.com/network/us/ny": "new_york",
    "https://www.procore.com/network/us/nc": "north_carolina",
    "https://www.procore.com/network/us/nd": "north_dakota",
    "https://www.procore.com/network/us/oh": "ohio",
    "https://www.procore.com/network/us/ok": "oklahoma",
    "https://www.procore.com/network/us/or": "oregon",
    "https://www.procore.com/network/us/pa": "pennsylvania",
    "https://www.procore.com/network/us/ri": "rhode island",
    "https://www.procore.com/network/us/sc": "south_carolina",
    "https://www.procore.com/network/us/sd": "south_dakota",
    "https://www.procore.com/network/us/tn": "tennessee",
    "https://www.procore.com/network/us/ut": "utah",
    "https://www.procore.com/network/us/vt": "vermont",
    "https://www.procore.com/network/us/va": "virginia",
    "https://www.procore.com/network/us/wa": "washington",
    "https://www.procore.com/network/us/wv": "west_virginia",
    "https://www.procore.com/network/us/wi": "wisconsin",
    "https://www.procore.com/network/us/wy": "wyoming",
}

def setup_driver():
    """
    Configura y devuelve una nueva instancia de Selenium WebDriver.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def click_checkbox(driver, wait, xpath):
    """
    Intenta hacer clic en un checkbox y verifica si se activó correctamente.
    """
    try:
        checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView();", checkbox)
        time.sleep(1)

        is_checked_before = "checked" in checkbox.get_attribute("outerHTML").lower()

        if not is_checked_before:
            driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(2)  # Dar tiempo para que la página actualice

            is_checked_after = "checked" in checkbox.get_attribute("outerHTML").lower()
            if is_checked_after:
                print(f"✔ Checkbox activado correctamente: {xpath}")
            else:
                print(f"⚠ No se pudo activar con `click()`, intentando con `send_keys(' ')`...")
                checkbox.send_keys(" ")  # Alternativa si el `click()` no funciona
                time.sleep(2)
        else:
            print(f"✔ Checkbox ya estaba activado: {xpath}")
    except Exception as e:
        print(f"❌ Error al hacer clic en el checkbox {xpath}: {e}")

def scrape_state(url, collection_name):
    """
    Realiza el scraping en un estado específico y guarda los enlaces en MongoDB.
    """
    print(f"🟢 Iniciando scraping en {collection_name}...")

    driver = setup_driver()
    wait = WebDriverWait(driver, 10)
    
    start_time = time.time()
    driver.get(url)

    # Esperar a que la página cargue
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)

    # Intentar activar los filtros
    checkboxes = {
        "Specialty Contractors": "//span[@data-track-click='Company Type Options, Update Checkbox, specialty_contractor']",
        "General Contractors": "//span[@data-track-click='Company Type Options, Update Checkbox, general_contractor']"
    }

    for name, xpath in checkboxes.items():
        click_checkbox(driver, wait, xpath)

    time.sleep(3)  # Esperar actualización de resultados

    # Conectar a la colección correspondiente en MongoDB
    collection = db[collection_name]
    stored_links = set(doc["url"] for doc in collection.find({}, {"url": 1}))

    page_count = 0
    total_links = 0

    while True:
        print(f"🔍 Extrayendo enlaces de la página {page_count + 1} en {collection_name}...")

        # Esperar a que se carguen las tarjetas
        try:
            cards = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//a[contains(@data-track-click, 'Search Results, Navigation')]")
            ))
        except:
            print(f"⚠ No se encontraron más tarjetas en {collection_name}.")
            break

        new_links = [card.get_attribute("href") for card in cards if card.get_attribute("href")]

        # Filtrar nuevos links que aún no están en MongoDB
        unique_links = [link for link in new_links if link not in stored_links]

        # Guardar los nuevos enlaces en MongoDB
        if unique_links:
            collection.insert_many([{"url": link, "status": 0} for link in unique_links])
            stored_links.update(unique_links)
            total_links += len(unique_links)

        print(f"✅ Se obtuvieron {len(unique_links)} enlaces nuevos en {collection_name}, página {page_count + 1}")

        # Intentar ir a la siguiente página
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']")))
            driver.execute_script("arguments[0].click();", next_button)
            page_count += 1
            print(f"➡ Pasando a la página {page_count + 1} en {collection_name}...")
            time.sleep(3)
        except:
            print(f"🚫 No hay más páginas en {collection_name}.")
            break

    driver.quit()

    elapsed_time = time.time() - start_time
    elapsed_minutes = round(elapsed_time / 60, 2)

    print(f"🎯 Scraping en {collection_name} completado. Se extrajeron {total_links} enlaces en {elapsed_minutes} minutos.")

# Ejecutar el scraper en todos los estados definidos manualmente
for url, collection_name in state_collections.items():
    scrape_state(url, collection_name)
