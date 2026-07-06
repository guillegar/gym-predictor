import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
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

        # Encontrar la sección de aforo
        aforo_section = soup.find('section', {'id': 'collapseAforo'})
        if not aforo_section:
            logger.warning("No se encontró sección collapseAforo")
            return None

        # Extraer todos los h3.cliente dentro de la sección
        h3_elements = aforo_section.find_all('h3', class_='cliente')

        if len(h3_elements) < 2:
            logger.warning(f"Se encontraron solo {len(h3_elements)} h3 elementos")
            for i, elem in enumerate(h3_elements):
                logger.debug(f"h3[{i}]: {elem.get_text(strip=True)}")
            return None

        # Intenta extraer ocupación y capacidad
        occupancy = None
        capacity = None

        for elem in h3_elements:
            text = elem.get_text(strip=True)
            logger.debug(f"Analizando: {text}")

            # Buscar span con "Personas" (ocupación actual)
            if 'Personas' in text:
                occupancy = int(''.join(filter(str.isdigit, text)))

            # Buscar span con "Aforo" (capacidad total)
            if 'Aforo' in text:
                capacity = int(''.join(filter(str.isdigit, text)))

        # Si no encontramos capacidad, usamos un valor por defecto
        if occupancy is None:
            logger.error("No se pudo extraer ocupación")
            return None

        if capacity is None:
            capacity = 728  # Default para Moratalaz
            logger.info("Usando capacidad por defecto: 728")

        percentage = (occupancy / capacity * 100) if capacity > 0 else 0

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
