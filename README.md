# Gym Predictor

Programa que recopila datos de ocupación del gym DreamFit Moratalaz y predice si habrá más o menos gente en la próxima hora usando Machine Learning.

## Características

- **Scraping automático**: Extrae aforo cada 5 minutos
- **Base de datos**: Almacena histórico en SQLite
- **Predicción ML**: Random Forest para predecir ocupación futura
- **Scheduler**: Ejecuta tareas periódicamente

## Requisitos

- Python 3.9+
- pip

## Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/Scripts/activate  # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Opción 1: Scheduler automático (recomendado)

Ejecuta scraping cada 5 minutos y entrenamientos cada hora:

```bash
python src/scheduler.py
```

### Opción 2: Scraping manual

```bash
python src/scraper.py
```

### Opción 3: Entrenar modelo y predecir

```bash
python src/ml_model.py
```

## Estructura

```
gym-predictor/
├── src/
│   ├── scraper.py       # Recoge aforo del sitio y escribe CSV + JSON + Sheet
│   ├── config.py        # Lista de gyms a monitorear
│   ├── sheets_sync.py   # Sincroniza el estado actual con Google Sheets
│   ├── ml_model.py      # Entrena y predice (lee el CSV)
│   └── scheduler.py     # Ejecución periódica local (opcional)
├── data/
│   ├── history.csv      # Histórico completo (fuente de datos para ML)
│   ├── latest.json      # Último registro (lo lee Home Assistant)
│   ├── estado.txt       # Resumen legible en texto plano
│   ├── service_account.json  # Credenciales Google (local, gitignored)
│   ├── model.pkl        # Modelo entrenado
│   └── scaler.pkl       # Scaler del modelo
├── .github/workflows/
│   └── scrape.yml       # GitHub Actions: scraping cada 5 min
├── docs/
│   ├── HOME_ASSISTANT_SETUP.md
│   └── GOOGLE_SHEETS_SETUP.md
├── notebooks/           # Análisis y exploración
└── requirements.txt
```

## Almacenamiento de datos

- **`data/history.csv`**: histórico append-only en texto (`timestamp,gym_name,occupancy,capacity,percentage`).
  Se eligió CSV en vez de SQLite binario porque git puede fusionarlo sin conflictos, lo que
  permite que GitHub Actions haga commit cada 5 min de forma fiable. Es la fuente de datos del ML.
- **`data/latest.json`**: solo el último registro; lo consume Home Assistant vía REST.

## Flujo automático

```
DreamFit web → GitHub Actions (cada 5 min) → scraper.py
                                                 ├── append a history.csv
                                                 ├── sobrescribe latest.json → Home Assistant → Google Home (device_class)
                                                 ├── sobrescribe estado.txt  (intento fallido de leerlo desde Gemini)
                                                 └── sobrescribe Google Sheet → Gemini (Gem, living document)
```

## Consultar el aforo con Gemini

Google Assistant no puede leer una URL/JSON externo por voz (las Conversational Actions personalizadas
se cerraron en 2023). Se probó `data/estado.txt` (texto plano en la URL raw de GitHub) como fuente para
un Gem, pero la herramienta de navegación de Gemini no pudo leer ese archivo en bruto de forma fiable.

**Solución que funciona**: `src/sheets_sync.py` sincroniza el estado actual en una **Google Sheet**.
Los Gems mantienen una conexión en vivo con archivos de Drive (Docs/Sheets/Slides) — cada actualización
se refleja automáticamente sin reprocesar el Gem. Ver [`docs/GOOGLE_SHEETS_SETUP.md`](docs/GOOGLE_SHEETS_SETUP.md)
para el setup completo (proyecto de Google Cloud, cuenta de servicio, secrets de GitHub Actions).

## Próximos pasos

- [ ] Entrenar modelo con al menos 2 semanas de datos
- [ ] Crear dashboard web para visualizar predicciones
- [ ] Agregar más centros de DreamFit (editar `src/config.py`)
