# Gym Predictor — Arquitectura

## Decisiones

### Stack
- **Python 3.9+**: Backend, scraping, ML
- **SQLite**: Base de datos local (escalable a PostgreSQL)
- **scikit-learn**: Modelo predictivo (Random Forest)
- **APScheduler**: Tareas periódicas
- **BeautifulSoup**: Web scraping

### Arquitectura

```
Scraper (5 min)  →  SQLite  →  ML Model (1h)  →  Predicción
```

1. **scraper.py**: Extrae aforo actual de DreamFit
2. **ml_model.py**: Features temporales + Random Forest
3. **scheduler.py**: Orquesta ambas tareas

### Features del modelo

- Hora del día (`hour`) — patrón diario
- Día de la semana (`dayofweek`) — fin de semana vs. laboral
- Lags (t-1, t-2, t-3) — tendencia reciente
- Media móvil 5 — suavizado

### Entrenamiento

- Mínimo 10 observaciones (≈50 min de datos)
- Random Forest: 50 árboles, depth=10
- Predice ocupación absoluta (personas)
- Regresa trend: ↑ (+5), ↓ (-5), → (similar)

## TODO

- [ ] Validar selectores HTML reales
- [ ] Agregar logging robusto
- [ ] Dashboard web (Flask o FastAPI)
- [ ] Tests unitarios
- [ ] Exportar predicciones a CSV
- [ ] Considerar LSTM para series temporales avanzadas
