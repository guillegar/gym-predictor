import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import logging
import sys
import json
from config import GYMS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

DB_PATH = "data/gym_data.db"

def init_db():
    """Inicializa la base de datos si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS gym_occupancy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            gym_name TEXT NOT NULL,
            occupancy INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            percentage REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def scrape_gym_occupancy(gym_url):
    """Extrae el aforo actual de una URL de DreamFit."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(gym_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Encontrar la sección de aforo
        aforo_section = soup.find('section', {'id': 'collapseAforo'})
        if not aforo_section:
            logger.warning(f"No se encontró sección collapseAforo en {gym_url}")
            return None

        # Extraer todos los h3.cliente dentro de la sección
        h3_elements = aforo_section.find_all('h3', class_='cliente')

        if len(h3_elements) < 2:
            logger.warning(f"Se encontraron solo {len(h3_elements)} h3 elementos en {gym_url}")
            return None

        # Intenta extraer ocupación y capacidad
        occupancy = None
        capacity = None

        for elem in h3_elements:
            text = elem.get_text(strip=True)

            # Buscar span con "Personas" (ocupación actual)
            if 'Personas' in text:
                occupancy = int(''.join(filter(str.isdigit, text)))

            # Buscar span con "Aforo" (capacidad total)
            if 'Aforo' in text:
                capacity = int(''.join(filter(str.isdigit, text)))

        # Si no encontramos capacidad, usamos un valor por defecto
        if occupancy is None:
            logger.error(f"No se pudo extraer ocupación de {gym_url}")
            return None

        if capacity is None:
            logger.warning(f"Capacidad no encontrada, usando default")
            capacity = 728

        percentage = (occupancy / capacity * 100) if capacity > 0 else 0

        return {
            'occupancy': occupancy,
            'capacity': capacity,
            'percentage': percentage
        }

    except Exception as e:
        logger.error(f"Error scraping {gym_url}: {e}")
        return None

def save_occupancy(occupancy_data, gym_name):
    """Guarda los datos de aforo en la BD y en JSON."""
    if not occupancy_data:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO gym_occupancy (gym_name, occupancy, capacity, percentage)
        VALUES (?, ?, ?, ?)
    """, (gym_name, occupancy_data['occupancy'], occupancy_data['capacity'], occupancy_data['percentage']))
    conn.commit()
    conn.close()

    save_latest_json(gym_name, occupancy_data)

def save_latest_json(gym_name, occupancy_data):
    """Guarda el ultimo registro en un archivo JSON para Home Assistant."""
    latest_data = {
        "gym_name": gym_name,
        "occupancy": occupancy_data['occupancy'],
        "capacity": occupancy_data['capacity'],
        "percentage": round(occupancy_data['percentage'], 1),
        "timestamp": datetime.now().isoformat()
    }

    json_path = "data/latest.json"
    with open(json_path, 'w') as f:
        json.dump(latest_data, f, indent=2)
    logger.info(f"JSON actualizado: {json_path}")

def scrape_all_gyms():
    """Scrapeacomunale todos los gyms configurados."""
    init_db()

    logger.info(f"Iniciando scraping de {len(GYMS)} gym(s)")

    for gym in GYMS:
        gym_name = gym['name']
        gym_url = gym['url']
        logger.info(f"Scrapeando {gym_name}...")

        data = scrape_gym_occupancy(gym_url)
        if data:
            save_occupancy(data, gym_name)
            logger.info(f"OK - {gym_name}: {data['occupancy']}/{data['capacity']} ({data['percentage']:.1f}%)")
        else:
            logger.warning(f"ERROR - {gym_name}: No se pudo obtener datos")

if __name__ == "__main__":
    scrape_all_gyms()
