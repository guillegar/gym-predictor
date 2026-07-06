# Integración con Google Sheets (para Gemini Gems)

## Por qué

Los Gems de Gemini no pueden navegar de forma fiable a URLs de texto en bruto
(`raw.githubusercontent.com`), pero sí mantienen una **conexión en vivo** con
archivos de Google Drive (Docs/Sheets/Slides) adjuntados como fuente de
conocimiento: cada edición del archivo se refleja automáticamente sin
reprocesar el Gem. Por eso el scraper también escribe el estado actual en una
Google Sheet, que el Gem lee como "living document".

## Pasos (los tiene que hacer el propietario de la cuenta de Google)

### 1. Crear proyecto en Google Cloud y habilitar la API

1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo (o usa uno existente), p. ej. `gym-predictor`
3. Ve a **APIs y servicios → Biblioteca**
4. Busca **"Google Sheets API"** → **Habilitar**

### 2. Crear una cuenta de servicio (service account)

1. **APIs y servicios → Credenciales → Crear credenciales → Cuenta de servicio**
2. Nombre: `gym-predictor-bot` (o el que quieras)
3. No necesita roles de proyecto (déjalo vacío) → Continuar → Listo
4. Entra en la cuenta de servicio creada → pestaña **Claves** → **Agregar clave → Crear clave nueva → JSON**
5. Se descarga un fichero `.json` — **guárdalo bien, no lo subas nunca a GitHub**

### 3. Crear la Google Sheet y compartirla con la cuenta de servicio

1. Crea una Google Sheet nueva en tu Drive (p. ej. "Gym Aforo")
2. Copia el **ID de la hoja** de la URL: `https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit`
3. Comparte la Sheet con el email de la cuenta de servicio (está dentro del JSON descargado,
   campo `client_email`, algo como `gym-predictor-bot@tu-proyecto.iam.gserviceaccount.com`)
   con permiso de **Editor**

### 4. Configurar el proyecto

**Para GitHub Actions** (producción, cada 5 min):

En el repo → **Settings → Secrets and variables → Actions → New repository secret**:

- `GOOGLE_SHEET_ID`: el ID copiado en el paso 3
- `GOOGLE_SHEETS_CREDENTIALS_JSON`: el **contenido completo** del fichero `.json` descargado
  (pégalo entero, es un JSON válido)

**Para pruebas locales** (opcional):

- Guarda el `.json` descargado como `data/service_account.json` (ya está en `.gitignore`, nunca se sube)
- Define la variable de entorno `GOOGLE_SHEET_ID` con el ID de la hoja

### 5. Adjuntar la Sheet al Gem en Gemini

1. Edita tu Gem → **Añadir fuentes de conocimiento → Google Drive**
2. Selecciona la Sheet "Gym Aforo"
3. Actualiza las instrucciones del Gem para que consulte esa hoja en vez de (o además de) la URL de `estado.txt`

## Qué escribe el scraper

Una pestaña llamada **"Aforo"** con una fila por gym configurado en `src/config.py`:

| gym_name | occupancy | capacity | percentage | actualizado |
|---|---|---|---|---|
| DreamFit Moratalaz | 68 | 728 | 9.3 | 2026-07-06 22:47 |

Se sobrescribe en cada ejecución (siempre refleja el último dato).
