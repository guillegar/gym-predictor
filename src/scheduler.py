from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
from scraper import init_db, scrape_gym_occupancy, save_occupancy
from ml_model import load_data, train_model, predict_next_hour, MODEL_PATH, SCALER_PATH
import pickle
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

GYM_OPEN = 7      # 7:00
GYM_CLOSE = 23    # 23:00

def is_gym_open():
    """Verifica si el gym está abierto."""
    now = datetime.now()
    return GYM_OPEN <= now.hour < GYM_CLOSE

def scheduled_scrape():
    """Ejecuta el scraping cada 5 minutos (solo si el gym está abierto)."""
    if not is_gym_open():
        logger.debug("Gym cerrado, skipping scraping")
        return

    logger.info("Iniciando scraping...")
    data = scrape_gym_occupancy()
    if data:
        save_occupancy(data)
        logger.info(f"Aforo registrado: {data['occupancy']}/{data['capacity']}")

def scheduled_train_and_predict():
    """Entrena el modelo y genera predicción cada hora (solo si gym abierto)."""
    if not is_gym_open():
        logger.debug("Gym cerrado, skipping entrenamiento")
        return

    logger.info("Entrenando modelo...")
    try:
        df = load_data()
        if len(df) >= 10:
            model, scaler = train_model(df)
            if model:
                pred = predict_next_hour(model, scaler, df)
                if pred:
                    logger.info(f"Predicción: {pred['predicted_occupancy']:.0f} personas - {pred['trend']}")
        else:
            logger.info(f"Datos insuficientes: {len(df)}/10 observaciones")
    except Exception as e:
        logger.error(f"Error en entrenamiento: {e}")

def start_scheduler():
    """Inicia el scheduler con tareas periódicas."""
    init_db()

    # Scraping cada 5 minutos
    scheduler.add_job(
        scheduled_scrape,
        trigger=IntervalTrigger(minutes=5),
        id='scrape_job',
        name='Scraping cada 5 min',
        replace_existing=True
    )

    # Entrenar y predecir cada hora
    scheduler.add_job(
        scheduled_train_and_predict,
        trigger=IntervalTrigger(hours=1),
        id='train_job',
        name='Entrenar modelo cada hora',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler iniciado")

    try:
        # Mantener el scheduler corriendo
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Deteniendo scheduler...")
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler()
