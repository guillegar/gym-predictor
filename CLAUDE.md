# Gym Predictor — Arquitectura

## Decisiones

### Stack
- **Python 3.9+**: Backend, scraping, ML
- **CSV (data/history.csv)**: histórico append-only en texto (ver decisión abajo)
- **scikit-learn**: Modelo predictivo (Random Forest)
- **GitHub Actions**: ejecuta el scraper (gym abierto 7:00-23:00); disparo real cada 5 min vía
  cron externo, ver decisión de scheduling abajo
- **BeautifulSoup**: Web scraping
- **Home Assistant**: lee `data/latest.json` vía REST → Google Home
- **Gemini**: lee `data/estado.txt` (texto plano) vía un Gem con la URL raw en sus instrucciones

### Arquitectura

```
cron-job.org (5 min) → GitHub API workflow_dispatch → GitHub Actions → scraper.py
                                                                          ├─ append history.csv → ML Model → Predicción
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

Para consulta en lenguaje natural se probó un **Gem de Gemini**. Primer intento: URL de
`estado.txt` (raw de GitHub) en las instrucciones del Gem — **falló**, la herramienta de navegación
del Gem no puede leer archivos de texto en bruto de forma fiable. Segunda vía preparada (código listo,
**pendiente de credenciales de Google Cloud, aparcada de momento**): `src/sheets_sync.py` escribe el
estado en una Google Sheet, que los Gems sí leen en vivo ("living document"); ver
`docs/GOOGLE_SHEETS_SETUP.md`.

**Vía activa ahora (2026-07-06)**: truco de `device_class` en Home Assistant para consulta directa
por "OK Google", sin pasar por Gemini. `sensor.gym_aforo_porcentaje` ya usa `device_class: humidity`
(match natural, ambos 0-100%). Se añade un sensor plantilla `sensor.gym_aforo_temperatura` que
reexpone `sensor.gym_aforo` (personas) como `device_class: temperature` / unit `°C` — Google solo
permite preguntar por voz sensores de estos tipos concretos. Frases resultantes ("qué humedad hay
en el gimnasio", "qué temperatura tiene el aforo") son forzadas por la limitación de Google, no
elegibles libremente. Detalle completo y YAML en `docs/HOME_ASSISTANT_SETUP.md`.

### Decisión: cron externo en vez de `schedule` de GitHub Actions (2026-07-08)

El cron `*/5 7-22 * * *` de GitHub Actions dejó de disparar cada 5 min: verificado con
`gh run list` que los runs `event: schedule` llegaban con huecos de 1-3 horas en vez de 5 min.
Es una limitación conocida y documentada de la plataforma (no arreglable desde el YAML): GitHub
retrasa/descarta ejecuciones de `schedule` bajo carga alta, y cuanto más frecuente el cron, más
se descarta — ampliamente reportado por la comunidad para intervalos de 5 min en repos gratuitos.

Solución: un cron externo (cron-job.org) llama cada 5 min a la API de GitHub
(`POST /repos/.../actions/workflows/scrape.yml/dispatches`) con un Personal Access Token de
alcance mínimo (fine-grained, solo este repo, permiso Actions: read/write). GitHub solo *ejecuta*
el job on-demand (`workflow_dispatch`), no *programa* el timing — así que no sufre el descarte del
scheduler interno. El `schedule: cron: '0,30 7-22 * * *'` que queda en el workflow es solo un
respaldo de baja frecuencia (menos disputado en su infra) por si el cron externo falla algún día.

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
