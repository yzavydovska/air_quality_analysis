# Import wymaganych bibliotek
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import joblib
from datetime import datetime, timedelta
import numpy as np  
import subprocess
import os
import sys

# Dodanie ścieżki do katalogu scripts, aby możliwy był import modułów
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from init_db import init_db  # import funkcji inicjalizującej bazę danych

# Inicjalizacja bazy danych przy uruchomieniu aplikacji
init_db()

# Inicjalizacja aplikacji Flask i włączenie obsługi CORS
app = Flask(__name__)
CORS(app)

# Ścieżki do bazy danych i katalogu z modelami
DB_PATH = '../scripts/dane_zanieczyszczenia.db'
MODELS_PATH = os.path.join(os.path.dirname(__file__), '..', 'models')

# Funkcja pomocnicza do uzyskania połączenia z bazą danych
def get_conn():
    return sqlite3.connect(DB_PATH)

# Czyszczenie nazwy miasta (na potrzeby plików modeli)
def clean_city_name(city):
    return city.lower().replace('-', '_').replace(' ', '_')

# Endpoint: Zwraca listę unikalnych miast
@app.route('/api/miasta')
def miasta():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT miasto FROM pomiary")
    miasta = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify(sorted(miasta))

# Endpoint: Zwraca dane pomiarowe (dla miasta i opcjonalnie miesiąca)
@app.route('/api/dane')
def dane():
    miasto = request.args.get('miasto')
    miesiac = request.args.get('miesiac')
    all_data = request.args.get('all', 'false').lower() == 'true'

    conn = get_conn()
    cur = conn.cursor()
    query = "SELECT data, pm25, pm10, miasto FROM pomiary WHERE 1=1"
    params = []

    # Filtrowanie po mieście
    if miasto:
        query += " AND miasto = ?"
        params.append(miasto)
    # Filtrowanie po miesiącu (jeśli nie zaznaczono "pokaż wszystko")
    if miesiac and not all_data:
        query += " AND strftime('%m', data) = ?"
        params.append(miesiac)

    query += " ORDER BY data"
    cur.execute(query, tuple(params))
    wyniki = cur.fetchall()
    conn.close()

    # Zwrócenie danych w formacie JSON
    return jsonify([
        {'data': row[0], 'pm25': row[1], 'pm10': row[2], 'miasto': row[3]}
        for row in wyniki
    ])

# Endpoint: Zwraca listę dostępnych miesięcy do wyboru na froncie
@app.route('/api/miesiace')
def miesiace():
    return jsonify([
        {'value': '04', 'label': 'Kwiecień'},
        {'value': '05', 'label': 'Maj'}
    ])

# Endpoint: Zwraca statystyki (średnia, min, max) dla danego miasta
@app.route('/api/statystyki')
def statystyki():
    miasto = request.args.get('miasto')
    if not miasto:
        return jsonify({'error': 'Brak parametru miasto'}), 400

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            AVG(pm25), MIN(pm25), MAX(pm25),
            AVG(pm10), MIN(pm10), MAX(pm10)
        FROM pomiary
        WHERE miasto = ?
    """, (miasto,))
    row = cur.fetchone()
    conn.close()

    # Sprawdzenie, czy są dane
    if not row or any(val is None for val in row):
        return jsonify({'error': f'Brak danych statystycznych dla miasta {miasto}'}), 404

    # Zwrócenie statystyk jako JSON
    return jsonify({
        'PM2.5': {'srednia': round(row[0], 2), 'min': row[1], 'max': row[2]},
        'PM10': {'srednia': round(row[3], 2), 'min': row[4], 'max': row[5]}
    })

# Endpoint: Zwraca prognozę dzisiejszą lub jutrzejszą dla danego miasta
@app.route('/api/prognoza')
def prognoza():
    miasto = request.args.get('miasto')
    dzien = request.args.get('dzien', 'today')  # 'today' lub 'tomorrow'
    
    if not miasto:
        return jsonify({'error': 'Brak parametru miasto'}), 400

    # Ustalenie daty prognozy
    data = datetime.today()
    if dzien == 'tomorrow':
        data = data.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    data_str = data.strftime('%Y-%m-%d')

    try:
        # Ścieżki do modeli dla danego miasta
        city_clean = clean_city_name(miasto)
        model_pm25_path = os.path.join(MODELS_PATH, f'{city_clean}_model_pm25.joblib')
        model_pm10_path = os.path.join(MODELS_PATH, f'{city_clean}_model_pm10.joblib')

        # Wczytanie modeli regresyjnych
        model_pm25 = joblib.load(model_pm25_path)
        model_pm10 = joblib.load(model_pm10_path)
    except FileNotFoundError:
        return jsonify({'error': f'Brak modeli dla miasta {miasto}'}), 404

    # Dane wejściowe do predykcji: dzień, miesiąc, dzień tygodnia, ostatnie pomiary
    day = data.day
    month = data.month
    dayofweek = data.weekday()

    # Pobranie ostatnich dostępnych pomiarów z bazy
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT pm25, pm10 FROM pomiary
        WHERE miasto = ? AND data <= date(?)
        ORDER BY data DESC LIMIT 1
    """, (miasto, datetime.today().strftime('%Y-%m-%d')))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Brak danych pomiarowych dla miasta'}), 404

    pm25_last, pm10_last = row

    # Przygotowanie danych do predykcji
    X_pred = np.array([[day, month, dayofweek, pm25_last, pm10_last]], dtype=float)

    # Predykcja modelami
    pm25_pred = model_pm25.predict(X_pred)[0]
    pm10_pred = model_pm10.predict(X_pred)[0]

    # Zwrócenie prognozy jako JSON
    return jsonify({
        'miasto': miasto,
        'data': data_str,
        'prognoza_pm25': round(pm25_pred, 2),
        'prognoza_pm10': round(pm10_pred, 2)
    })

# Endpoint: Uruchamia import danych z plików CSV (poprzez skrypt import_csv.py)
@app.route('/api/aktualizuj-dane', methods=['POST'])
def aktualizuj_dane():
    try:
        subprocess.run(['python3', '../scripts/import_csv.py'], check=True)
        return jsonify({'status': 'Dane zostały zaktualizowane'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return 'API działa. Użyj frontendu w katalogu frontend/.'


# Uruchomienie serwera Flask w trybie debug
if __name__ == "__main__":
    app.run(debug=True)
