import os
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import re

DB_PATH = '../scripts/dane_zanieczyszczenia.db'
MODELS_PATH = '../models'

os.makedirs(MODELS_PATH, exist_ok=True)

def clean_city_name(name):
    name = name.lower()
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l',
        'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        ' ': '_', '-': '_'
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

def get_data_for_city(city):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT data, pm25, pm10 FROM pomiary WHERE miasto = ? ORDER BY data"
    df = pd.read_sql_query(query, conn, params=(city,))
    conn.close()
    return df

def train_and_save_model(city):
    df = get_data_for_city(city)
    if df.empty:
        print(f"Brak danych dla miasta {city}")
        return

    # Zamień puste lub niepoprawne ciągi na NaN i usuń je
    df['pm25'] = pd.to_numeric(df['pm25'], errors='coerce')
    df['pm10'] = pd.to_numeric(df['pm10'], errors='coerce')
    df = df.dropna(subset=['pm25', 'pm10'])

    if df.empty:
        print(f"Brak danych do trenowania po czyszczeniu dla miasta {city}")
        return

    # Dodaj cechy czasowe
    df['data'] = pd.to_datetime(df['data'])
    df['day'] = df['data'].dt.day
    df['month'] = df['data'].dt.month
    df['dayofweek'] = df['data'].dt.dayofweek

    # Dodaj cechy opóźnione
    df['pm25_lag'] = df['pm25'].shift(1)
    df['pm10_lag'] = df['pm10'].shift(1)
    df = df.dropna()

    X = df[['day', 'month', 'dayofweek', 'pm25_lag', 'pm10_lag']]
    y_pm25 = df['pm25']
    y_pm10 = df['pm10']

    model_pm25 = LinearRegression()
    model_pm10 = LinearRegression()

    model_pm25.fit(X, y_pm25)
    model_pm10.fit(X, y_pm10)

    city_clean = clean_city_name(city)

    joblib.dump(model_pm25, os.path.join(MODELS_PATH, f'{city_clean}_model_pm25.joblib'))
    joblib.dump(model_pm10, os.path.join(MODELS_PATH, f'{city_clean}_model_pm10.joblib'))

    print(f"Modele dla miasta {city} zapisane.")

if __name__ == '__main__':
    miasta = ['bielsko-biala', 'bydgoszcz', 'krakow', 'lublin', 'poznan', 'warszawa']
    for city in miasta:
        try:
            train_and_save_model(city)
        except Exception as e:
            print(f"Błąd podczas trenowania modelu dla miasta {city}: {e}")
