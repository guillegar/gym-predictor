# Disparo fiable cada 5 min con un cron externo

## Por qué

El `schedule:` nativo de GitHub Actions no es fiable para intervalos de 5 minutos: GitHub
retrasa o descarta ejecuciones bajo carga ("best effort", documentado y ampliamente reportado
por la comunidad). En este proyecto se confirmó con `gh run list`: en vez de cada 5 min, los
runs llegaban con huecos de 1-3 horas.

**Solución**: un cron externo llama a la API de GitHub para *disparar* el workflow
(`workflow_dispatch`) cada 5 min. GitHub solo ejecuta el job on-demand, no programa el timing —
así se evita el descarte del scheduler interno.

## 1. Crear un Personal Access Token de alcance mínimo

1. Ve a https://github.com/settings/tokens?type=beta (tokens **fine-grained**, no el clásico)
2. **Generate new token**
3. **Resource owner**: tu usuario (`guillegar`)
4. **Repository access → Only select repositories** → elige `gym-predictor` (solo este repo)
5. **Permissions → Repository permissions → Actions** → **Read and write**
   (no marques nada más: sin acceso a Contents, Issues, etc.)
6. Ponle una fecha de caducidad razonable (p. ej. 1 año) y genera el token
7. Copia el token (`github_pat_...`) — no se vuelve a mostrar

Esto limita el daño si el token se filtrara: solo puede disparar workflows de este repo, no leer
ni modificar código.

## 2. Configurar el cron en cron-job.org

1. Crea una cuenta gratuita en https://cron-job.org
2. **Create cronjob**
3. **Title**: `gym-predictor scraper`
4. **URL**:
   ```
   https://api.github.com/repos/guillegar/gym-predictor/actions/workflows/scrape.yml/dispatches
   ```
5. **Schedule**: cada 5 minutos, restringido a las horas del gym (7:00-23:00 hora de Madrid ==
   5:00-21:00 UTC en verano / 6:00-22:00 UTC en invierno — cron-job.org permite fijar la zona
   horaria del propio cronjob, usa `Europe/Madrid` directamente y pon el rango 7:00-23:00)
6. **Request method**: `POST`
7. **Headers** (Advanced → Headers):
   ```
   Accept: application/vnd.github+json
   Authorization: Bearer TU_TOKEN_AQUI
   X-GitHub-Api-Version: 2022-11-28
   Content-Type: application/json
   ```
8. **Body** (Advanced → Body):
   ```json
   {"ref":"master"}
   ```
9. Guardar y activar

## 3. Verificar

Espera a la siguiente ejecución programada y comprueba:

```bash
gh run list --workflow=scrape.yml --limit 5 --json displayTitle,event,createdAt
```

Deberías ver runs con `event: workflow_dispatch` espaciados ~5 min, en vez de `event: schedule`
con huecos de horas.

## Notas

- El `schedule:` que queda en `.github/workflows/scrape.yml` (cada 30 min) es solo un respaldo
  de baja frecuencia por si cron-job.org tiene una caída — no lo quites.
- Si el token caduca, el cron de cron-job.org empezará a fallar con 401 — cron-job.org avisa por
  email si un cronjob falla repetidamente.
