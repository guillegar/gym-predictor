import json
import os
import logging
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_ENV = "GOOGLE_SHEETS_CREDENTIALS_JSON"
CREDENTIALS_FILE = "data/service_account.json"
SHEET_ID_ENV = "GOOGLE_SHEET_ID"
WORKSHEET_NAME = "Aforo"

def _load_credentials():
    """Carga las credenciales desde la variable de entorno (Actions) o un fichero local."""
    raw_json = os.environ.get(CREDENTIALS_ENV)
    if raw_json:
        info = json.loads(raw_json)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    if os.path.exists(CREDENTIALS_FILE):
        return Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)

    return None

def update_sheet(results):
    """Escribe el estado actual (una fila legible por gym) en Google Sheets.

    Si no hay credenciales configuradas, no hace nada (permite seguir
    desarrollando/local sin tener que montar Google Sheets).
    """
    sheet_id = os.environ.get(SHEET_ID_ENV)
    if not sheet_id:
        logger.info("GOOGLE_SHEET_ID no configurado, saltando sync a Sheets")
        return

    creds = _load_credentials()
    if not creds:
        logger.info("Credenciales de Google Sheets no configuradas, saltando sync")
        return

    try:
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)

        try:
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=20, cols=6)

        header = ["gym_name", "occupancy", "capacity", "percentage", "actualizado"]
        rows = [header]
        for gym_name, occupancy_data, updated_at in results:
            rows.append([
                gym_name,
                occupancy_data['occupancy'],
                occupancy_data['capacity'],
                round(occupancy_data['percentage'], 1),
                updated_at,
            ])

        worksheet.clear()
        worksheet.update(values=rows, range_name="A1")
        logger.info(f"Google Sheet actualizado: {len(results)} gym(s)")

    except Exception as e:
        logger.error(f"Error actualizando Google Sheet: {e}")
