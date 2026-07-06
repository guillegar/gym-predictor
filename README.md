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
│   ├── scraper.py       # Recoge aforo del sitio
│   ├── ml_model.py      # Entrena y predice
│   └── scheduler.py     # Ejecuta tareas periódicamente
├── data/
│   ├── gym_data.db      # Base de datos (se crea automáticamente)
│   ├── model.pkl        # Modelo entrenado
│   └── scaler.pkl       # Scaler del modelo
├── notebooks/           # Análisis y exploración
└── requirements.txt
```

## Próximos pasos

- [ ] Inspeccionar HTML del sitio para ajustar selectores
- [ ] Entrenar modelo con al menos 2 semanas de datos
- [ ] Crear dashboard web para visualizar predicciones
- [ ] Agregar más centros de DreamFit

## Notas

El scraper necesita validación con la estructura HTML real del sitio. Ajustaré los selectores una vez verifiquemos cómo está organizado el elemento de aforo.
