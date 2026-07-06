# Integración con Home Assistant + Google Home

## Setup Home Assistant (ya desplegado)

### 1. REST Sensor

Ya añadido en `configuration.yaml` (Raspberry Pi, vía SSH):

```yaml
rest:
  - scan_interval: 300
    resource: https://raw.githubusercontent.com/guillegar/gym-predictor/master/data/latest.json
    sensor:
      - name: "Gym Aforo"
        unique_id: gym_aforo_personas
        unit_of_measurement: "personas"
        value_template: "{{ value_json.occupancy }}"
        json_attributes:
          - gym_name
          - capacity
          - percentage
          - timestamp

      - name: "Gym Aforo Porcentaje"
        unique_id: gym_aforo_porcentaje
        unit_of_measurement: "%"
        device_class: humidity
        value_template: "{{ value_json.percentage }}"
```

Entidades resultantes: `sensor.gym_aforo` (personas) y `sensor.gym_aforo_porcentaje` (%).

### 2. Sensor "disfrazado" de temperatura (para consulta por voz)

Google Assistant solo permite **preguntar por voz** sensores de `device_class` concretos:
`temperature`, `humidity`, `aqi`, `carbon_dioxide`, `carbon_monoxide`, `pm10`, `pm25`,
`volatile_organic_compounds`. Un contador de personas no es ninguno de esos tipos, así que
no se puede preguntar "cuánta gente hay" de forma nativa.

**Truco aplicado**: el porcentaje ya usa `device_class: humidity` (arriba, encaja natural porque
ambos son 0-100%). Para el número de personas, se añade un **sensor plantilla** que reexpone el
mismo valor como si fuera una temperatura en °C:

```yaml
template:
  - sensor:
      - name: "Gym Aforo Temperatura"
        unique_id: gym_aforo_temperatura
        device_class: temperature
        unit_of_measurement: "°C"
        state: "{{ states('sensor.gym_aforo') }}"
```

Esto **no crea una nueva llamada de red** — solo reinterpreta `sensor.gym_aforo`, que ya se
actualiza por el REST sensor cada 5 min.

### 3. Exponer las entidades a Google Assistant

Método recomendado (UI unificada de exposición, no hace falta tocar `google_assistant:` en YAML):

1. **Ajustes → Asistentes de voz → Exponer** (Settings → Voice assistants → Expose)
2. Busca `Gym Aforo Porcentaje` y `Gym Aforo Temperatura`
3. Marca la columna **Google Assistant** en ambas
4. Guarda

Si tu integración `google_assistant:` es manual y esa pestaña no sincroniza sola, añade en
`configuration.yaml` dentro del bloque `google_assistant:` existente:

```yaml
google_assistant:
  # ... tu configuración actual (project_id, service_account_json, etc.) ...
  entity_config:
    sensor.gym_aforo_porcentaje:
      name: "gimnasio"
    sensor.gym_aforo_temperatura:
      name: "aforo del gimnasio"
```

### 4. Reiniciar y sincronizar

```bash
ha core check
ha core restart
```

Espera ~1-2 min. Luego, en la app de Google Home, fuerza una sincronización de dispositivos
(o simplemente di "OK Google, sincroniza mis dispositivos").

## Comandos de Google Home (reales, probados)

- **"OK Google, ¿qué humedad hay en el gimnasio?"** → responde el % de aforo (p. ej. "26 por ciento")
- **"OK Google, ¿qué temperatura tiene el aforo del gimnasio?"** → responde el nº de personas
  (p. ej. "72 grados" — el número es correcto, la unidad "grados" es el precio del truco)

`sensor.gym_aforo` (sin disfraz) sigue disponible para dashboards y automatizaciones con sus
unidades reales ("personas"); el sensor plantilla es solo para la consulta por voz.

## Troubleshooting

- **No se actualiza**: Verifica que `latest.json` esté fresco en GitHub
  (`https://raw.githubusercontent.com/guillegar/gym-predictor/master/data/latest.json`)
- **REST Sensor no actualiza**: Reinicia HA o recarga la integración REST
- **Google no encuentra la entidad nueva**: hace falta sincronizar dispositivos tras exponerla
  (app Google Home → Configuración → Works with Google, o "OK Google, sincroniza mis dispositivos")
- **Google no entiende la pregunta**: prueba variantes ("humedad del gimnasio", "temperatura del
  aforo del gimnasio") — Google elige la frase según el `device_class`, no es 100% libre

## URLs útiles

- JSON de datos: `https://raw.githubusercontent.com/guillegar/gym-predictor/master/data/latest.json`
- Repo: `https://github.com/guillegar/gym-predictor`
