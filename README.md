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
│   ├── scraper.py       # Recoge aforo del sitio y escribe CSV + JSON
│   ├── config.py        # Lista de gyms a monitorear
│   ├── ml_model.py      # Entrena y predice (lee el CSV)
│   └── scheduler.py     # Ejecución periódica local (opcional)
├── data/
│   ├── history.csv      # Histórico completo (fuente de datos para ML)
│   ├── latest.json      # Último registro (lo lee Home Assistant)
│   ├── model.pkl        # Modelo entrenado
│   └── scaler.pkl       # Scaler del modelo
├── .github/workflows/
│   └── scrape.yml       # GitHub Actions: scraping cada 5 min
├── docs/
│   └── HOME_ASSISTANT_SETUP.md
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
                                                 └── sobrescribe latest.json → Home Assistant → Google Home
```

## Próximos pasos

- [ ] Entrenar modelo con al menos 2 semanas de datos
- [ ] Crear dashboard web para visualizar predicciones
- [ ] Agregar más centros de DreamFit (editar `src/config.py`)
