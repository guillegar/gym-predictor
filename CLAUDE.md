# Gym Predictor — Arquitectura

## Decisiones

### Stack
- **Python 3.9+**: Backend, scraping, ML
- **CSV (data/history.csv)**: histórico append-only en texto (ver decisión abajo)
- **scikit-learn**: Modelo predictivo (Random Forest)
- **GitHub Actions**: ejecuta el scraper cada 5 min (gym abierto 7:00-23:00)
- **BeautifulSoup**: Web scraping
- **Home Assistant**: lee `data/latest.json` vía REST → Google Home
- **Gemini**: lee `data/estado.txt` (texto plano) vía un Gem con la URL raw en sus instrucciones

### Arquitectura

```
DreamFit → GitHub Actions (5 min) → scraper.py ─┬─ append history.csv → ML Model → Predicción
                                                ├─ latest.json → Home Assistant → Google Home
                                                └─ estado.txt  → Gemini (Gem)
```

1. **scraper.py**: Extrae aforo de DreamFit (multi-gym vía `config.py`), escribe CSV + JSON + estado.txt
2. **ml_model.py**: Lee `history.csv`, features temporales + Random Forest
3. **scheduler.py**: Orquestación local opcional (en producción se usa GitHub Actions)

### Decisión: consulta por voz vía Gemini, no Google Assistant (2026-07-06)

Objetivo original: preguntar el aforo a "OK Google". Investigado y descartado por limitación de
plataforma (no de este proyecto): las Conversational Actions personalizadas de Google Assistant se
cerraron el 13/06/2023, y `google_assistant_sdk` solo manda comandos a Google (no permite que un
altavoz consulte una URL/JSON externo por voz). La integración `google_assistant` manual solo deja
"preguntar" sensores de `device_class` concretos (temperature, humidity, etc.), no un contador de
personas — el aforo se expone en HA disfrazado de esos tipos si se quiere usar por voz en Google Home.
Para consulta en lenguaje natural sin ese truco, la vía elegida es un **Gem de Gemini** con la URL de
`estado.txt` (repo público) en sus instrucciones; Gemini navega y lee el resumen en texto plano.

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
