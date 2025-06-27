import pandas as pd
import sqlite3
import os
import re

CSV_DIR = "../dane"
DB_PATH = 'dane_zanieczyszczenia.db'

# Mapa miesięcy na numery (do lepszego wyświetlania)
miesiace_map = {
    'styczen': '01', 'luty': '02', 'marzec': '03', 'kwiecien': '04',
    'maj': '05', 'czerwiec': '06', 'lipiec': '07', 'sierpien': '08',
    'wrzesien': '09', 'pazdziernik': '10', 'listopad': '11', 'grudzien': '12'
}

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

total_rows_to_save = 0

for plik in os.listdir(CSV_DIR):
    if plik.endswith('.csv'):
        # Dopasowanie nazwy pliku np. plik_kwiecien_bielsko-biala.csv
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

        print(f"📄 {plik}: wczytano {len(df)} wierszy")

        if df.shape[1] != 3:
            print(f"⚠️ Pomijam plik {plik} – niepoprawna liczba kolumn.")
            continue

        df.columns = ['data', 'pm10', 'pm25']

        df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d %H:%M', errors='coerce')

        print(f"   Liczba wierszy przed filtrowaniem daty: {len(df)}")
        print(f"   Liczba błędnych dat (NaT): {df['data'].isna().sum()}")

        df.dropna(subset=['data'], inplace=True)

        print(f"   Liczba błędnych pm25: {df['pm25'].isna().sum()}")
        print(f"   Liczba błędnych pm10: {df['pm10'].isna().sum()}")

        df.dropna(subset=['pm25', 'pm10'], inplace=True)

        print(f"   Liczba wierszy po filtrowaniu: {len(df)}")

        df['miasto'] = miasto.lower()
        df['miesiac'] = miesiac_str.lower()

        df = df[['miasto', 'miesiac', 'data', 'pm25', 'pm10']]

        if not df.empty:
            df.to_sql('pomiary', conn, if_exists='append', index=False)
            total_rows_to_save += len(df)
        else:
            print(f"⚠️ Brak danych do zapisu w pliku {plik}.")

cur.execute("SELECT COUNT(*) FROM pomiary")
total_records = cur.fetchone()[0]

print(f"📈 Łączna liczba wierszy do zapisu ze wszystkich plików: {total_rows_to_save}")
print(f"📊 Łączna liczba rekordów w bazie: {total_records}")

# Wyświetlenie liczby rekordów po miastach
cur.execute("SELECT miasto, COUNT(*) FROM pomiary GROUP BY miasto")
for miasto, count in cur.fetchall():
    print(f"🏙️ Miasto {miasto}: {count} rekordów")

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
conn.close()
print("✅ Gotowe – dane wczytane.")
