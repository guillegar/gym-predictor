import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "data/gym_data.db"
DREAMFIT_URL = "https://www.dreamfit.es/centros/moratalaz"

def init_db():
    """Inicializa la base de datos si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS gym_occupancy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            occupancy INTEGER,
            capacity INTEGER,
            percentage REAL
        )
    """)
    conn.commit()
    conn.close()

def scrape_gym_occupancy():
    """Extrae el aforo actual del sitio de DreamFit."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(DREAMFIT_URL, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # TODO: Inspeccionar la página y ajustar selectores
        # Buscar elemento con aforo (puede ser span, div, etc.)
        aforo_element = soup.find(class_="aforo")

        if not aforo_element:
            logger.warning("No se encontró elemento de aforo en la página")
            return None

        occupancy = int(aforo_element.text.strip())
        capacity = 100  # TODO: Extraer capacidad si está disponible
        percentage = (occupancy / capacity) * 100 if capacity > 0 else 0

        logger.info(f"Aforo: {occupancy}/{capacity} ({percentage:.1f}%)")
        return {
            'occupancy': occupancy,
            'capacity': capacity,
            'percentage': percentage
        }

    except Exception as e:
        logger.error(f"Error scraping: {e}")
        return None

def save_occupancy(occupancy_data):
    """Guarda los datos de aforo en la BD."""
    if not occupancy_data:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO gym_occupancy (occupancy, capacity, percentage)
        VALUES (?, ?, ?)
    """, (occupancy_data['occupancy'], occupancy_data['capacity'], occupancy_data['percentage']))
    conn.commit()
    conn.close()
    logger.info("Datos guardados en BD")

if __name__ == "__main__":
    init_db()
    data = scrape_gym_occupancy()
    if data:
        save_occupancy(data)
