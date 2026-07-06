import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "data/gym_data.db"
MODEL_PATH = "data/model.pkl"
SCALER_PATH = "data/scaler.pkl"

def load_data():
    """Carga datos de la BD."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT timestamp, occupancy, percentage FROM gym_occupancy ORDER BY timestamp",
        conn
    )
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def engineer_features(df):
    """Genera features para el modelo."""
    df_copy = df.copy()

    # Features temporales
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    df_copy['dayofweek'] = df_copy['timestamp'].dt.dayofweek
    df_copy['minute'] = df_copy['timestamp'].dt.minute

    # Features de tendencia (últimas 3 observaciones)
    df_copy['occupancy_lag1'] = df_copy['occupancy'].shift(1)
    df_copy['occupancy_lag2'] = df_copy['occupancy'].shift(2)
    df_copy['occupancy_lag3'] = df_copy['occupancy'].shift(3)

    # Media móvil
    df_copy['occupancy_ma5'] = df_copy['occupancy'].rolling(window=5, min_periods=1).mean()

    return df_copy.dropna()

def train_model(df):
    """Entrena modelo de predicción."""
    if len(df) < 10:
        logger.warning("Datos insuficientes para entrenar (mín 10 observaciones)")
        return None, None

    df_features = engineer_features(df)

    feature_cols = ['hour', 'dayofweek', 'minute', 'occupancy_lag1',
                    'occupancy_lag2', 'occupancy_lag3', 'occupancy_ma5']

    X = df_features[feature_cols]
    y = df_features['occupancy']

    # Scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Modelo
    model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
    model.fit(X_scaled, y)

    logger.info(f"Modelo entrenado con {len(df_features)} observaciones")

    # Guardar
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    return model, scaler

def predict_next_hour(model, scaler, last_data):
    """Predice aforo para la próxima hora."""
    if not model or not scaler:
        return None

    try:
        now = datetime.now()
        next_hour = now + timedelta(hours=1)

        # Crear features para próxima hora
        features = {
            'hour': next_hour.hour,
            'dayofweek': next_hour.dayofweek,
            'minute': next_hour.minute,
            'occupancy_lag1': last_data.iloc[-1]['occupancy'] if len(last_data) > 0 else 0,
            'occupancy_lag2': last_data.iloc[-2]['occupancy'] if len(last_data) > 1 else 0,
            'occupancy_lag3': last_data.iloc[-3]['occupancy'] if len(last_data) > 2 else 0,
            'occupancy_ma5': last_data.iloc[-5:]['occupancy'].mean() if len(last_data) > 4 else 0
        }

        X = np.array([list(features.values())])
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)[0]

        current_occupancy = last_data.iloc[-1]['occupancy']
        difference = prediction - current_occupancy
        trend = "↑ MÁS gente" if difference > 5 else "↓ MENOS gente" if difference < -5 else "→ SIMILAR"

        logger.info(f"Predicción para próxima hora: {prediction:.0f} ({trend})")

        return {
            'predicted_occupancy': prediction,
            'current_occupancy': current_occupancy,
            'difference': difference,
            'trend': trend
        }

    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return None

if __name__ == "__main__":
    df = load_data()
    if len(df) > 0:
        model, scaler = train_model(df)
        if model:
            pred = predict_next_hour(model, scaler, df)
