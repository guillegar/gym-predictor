# Gym Predictor — Arquitectura

## Decisiones

### Stack
- **Python 3.9+**: Backend, scraping, ML
- **CSV (data/history.csv)**: histórico append-only en texto (ver decisión abajo)
- **scikit-learn**: Modelo predictivo (Random Forest)
- **GitHub Actions**: ejecuta el scraper cada 5 min (gym abierto 7:00-23:00)
- **BeautifulSoup**: Web scraping
- **Home Assistant**: lee `data/latest.json` vía REST → Google Home

### Arquitectura

```
DreamFit → GitHub Actions (5 min) → scraper.py ─┬─ append history.csv → ML Model → Predicción
                                                └─ latest.json → Home Assistant → Google Home
```

1. **scraper.py**: Extrae aforo de DreamFit (multi-gym vía `config.py`), escribe CSV + JSON
2. **ml_model.py**: Lee `history.csv`, features temporales + Random Forest
3. **scheduler.py**: Orquestación local opcional (en producción se usa GitHub Actions)

### Decisión: CSV en vez de SQLite (2026-07-06)

El histórico se guardaba en `gym_data.db` (SQLite binario) commiteado por GitHub Actions cada 5 min.
git **no puede fusionar binarios**, así que `git pull --rebase` daba conflicto y el push del workflow
fallaba constantemente ("Cannot merge binary files"). Se cambió a **CSV de texto** (`data/history.csv`),
que git fusiona sin problema. El `.db` dejó de trackearse (`git rm --cached`, sigue en `.gitignore`).
El workflow además serializa runs con `concurrency` y reintenta el push con `pull --rebase --autostash`.

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

- [ ] Dashboard web (Flask o FastAPI)
- [ ] Tests unitarios
- [ ] Considerar LSTM para series temporales avanzadas
- [ ] Reactivar entrenamiento automático cuando haya ~2 semanas de datos
