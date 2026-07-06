# Integración con Home Assistant + Google Home

## Setup Home Assistant

### 1. Agregar REST Sensor

En `configuration.yaml` o en un archivo separado (`packages/gym.yaml`):

```yaml
rest:
  - scan_interval: 300  # Cada 5 minutos
    resource: https://raw.githubusercontent.com/guillegar/gym-predictor/master/data/latest.json
    name: "Gym Occupancy"
    sensor:
      - name: "Gym Occupancy"
        unique_id: gym_occupancy_people
        unit_of_measurement: "personas"
        state_class: "measurement"
        json_attributes:
          - gym_name
          - capacity
          - percentage
          - timestamp
        value_template: "{{ value_json.occupancy }}"

      - name: "Gym Occupancy Percentage"
        unique_id: gym_occupancy_percentage
        unit_of_measurement: "%"
        state_class: "measurement"
        value_template: "{{ value_json.percentage }}"
```

### 2. Exponer a Google Home

En `configuration.yaml`:

```yaml
google_home:
  # Ya debe estar configurada

google_assistant:
  project_id: your_project_id
  service_account_json: SERVICE_ACCOUNT_JSON_PATH
  report_state: true
  exposed_domains:
    - sensor
  entity_config:
    sensor.gym_occupancy:
      name: "Aforo del Gym"
      aliases:
        - "gente en el gym"
        - "ocupacion del gym"
    sensor.gym_occupancy_percentage:
      name: "Porcentaje del Gym"
      aliases:
        - "porcentaje de ocupacion"
```

### 3. Crear una Automation (opcional)

Para recibir notificaciones cuando el gym esté vacío o lleno:

```yaml
automation:
  - alias: "Notify when gym is empty"
    trigger:
      platform: numeric_state
      entity_id: sensor.gym_occupancy
      below: 50
    action:
      service: notify.mobile_app_phone
      data:
        title: "Gym casi vacío"
        message: "Hay {{ states('sensor.gym_occupancy') }} personas"
```

## Comandos de Google Home

Una vez configurado, podrás decir:

- "OK Google, ¿cuánta gente hay en el gym?"
- "OK Google, ¿cuál es la ocupación del gym?"
- "OK Google, ¿cuál es el porcentaje de ocupación del gym?"

## Troubleshooting

- **No se actualiza**: Verifica que el JSON esté en GitHub
- **REST Sensor no actualiza**: Reinicia HA o recarga REST config
- **Google Home no entiende**: Asegúrate de que la entidad está expuesta en `exposed_domains`

## URLs útiles

- JSON de datos: `https://raw.githubusercontent.com/guillegar/gym-predictor/master/data/latest.json`
- Repo: `https://github.com/guillegar/gym-predictor`
