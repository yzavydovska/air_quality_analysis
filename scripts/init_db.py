
import pandas as pd
import sqlite3
import os
import re
#Skrypt scripts/init_db.py tworzy strukturę bazy danych.


CSV_DIR = os.path.join(os.path.dirname(__file__), '../dane')
DB_PATH = os.path.join(os.path.dirname(__file__), 'dane_zanieczyszczenia.db')

miesiace_map = {
    'styczen': '01', 'luty': '02', 'marzec': '03', 'kwiecien': '04',
    'maj': '05', 'czerwiec': '06', 'lipiec': '07', 'sierpien': '08',
    'wrzesien': '09', 'pazdziernik': '10', 'listopad': '11', 'grudzien': '12'
}

def load_data(conn):
    cur = conn.cursor()
    total_rows_to_save = 0
    
    for plik in os.listdir(CSV_DIR):
        if plik.endswith('.csv'):
            match = re.match(r"plik_([\w\-]+)_([\w\-]+)\.csv", plik)
            if not match:
                print(f"⚠️ Niepoprawna nazwa pliku: {plik}")
                continue
            miesiac_str, miasto = match.groups()
            miesiac_num = miesiace_map.get(miesiac_str.lower(), '00')

            print(f"✅ Przetwarzam plik: {plik}, miesiac: {miesiac_str} (num: {miesiac_num}), miasto: {miasto}")

            sciezka = os.path.join(CSV_DIR, plik)
            try:
                df = pd.read_csv(sciezka, sep=',', skiprows=1, header=None, usecols=[0,1,2], engine='python')
            except Exception as e:
                print(f"❌ Błąd przy wczytywaniu {plik}: {e}")
                continue

            if df.shape[1] != 3:
                print(f"⚠️ Pomijam plik {plik} – niepoprawna liczba kolumn.")
                continue

            df.columns = ['data', 'pm10', 'pm25']
            df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d %H:%M', errors='coerce')
            df.dropna(subset=['data', 'pm25', 'pm10'], inplace=True)

            df['miasto'] = miasto.lower()
            df['miesiac'] = miesiac_str.lower()
            df = df[['miasto', 'miesiac', 'data', 'pm25', 'pm10']]

            if not df.empty:
                df.to_sql('pomiary', conn, if_exists='append', index=False)
                total_rows_to_save += len(df)

    print(f"📈 Łączna liczba wierszy do zapisu ze wszystkich plików: {total_rows_to_save}")

    # Tworzenie tabeli statystyki dzienne
    cur.execute('DROP TABLE IF EXISTS statystyki_dzienne')
    cur.execute('''
    CREATE TABLE statystyki_dzienne AS
    SELECT 
        miasto, miesiac,
        DATE(data) as dzien,
        AVG(pm25) as avg_pm25,
        AVG(pm10) as avg_pm10
    FROM pomiary
    GROUP BY miasto, miesiac, dzien
    ''')

    conn.commit()
    print("✅ Dane zostały załadowane do bazy.")

def init_db():
    baza_istnieje = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS pomiary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        miasto TEXT,
        miesiac TEXT,
        data TIMESTAMP,
        pm25 REAL,
        pm10 REAL
    )
    ''')
    conn.commit()

    # Sprawdzenie czy tabela jest pusta
    cur.execute("SELECT COUNT(*) FROM pomiary")
    count = cur.fetchone()[0]

    if count == 0:
        print("Tabela pomiary jest pusta, ładuję dane z CSV...")
        load_data(conn)
    else:
        print(f"Baza i tabela już zawierają {count} rekordów, pomijam ładowanie danych.")
    conn.close()

if __name__ == '__main__':
    init_db()
