import os
import sqlite3
import glob

DB_PATH = '../scripts/dane_zanieczyszczenia.db'
CSV_FOLDER = '../data/csv_files'

def get_conn():
    return sqlite3.connect(DB_PATH)

def import_csv_to_db(file_path):
    conn = get_conn()
    cur = conn.cursor()

    with open(file_path, 'r', encoding='utf-8') as f:
        next(f)  # pomiń nagłówek
        for line in f:
            data = line.strip().split(',')
            # Załóżmy, że CSV ma: data, pm25, pm10, miasto
            if len(data) == 4:
                try:
                    cur.execute(
                        "INSERT INTO pomiary (data, pm25, pm10, miasto) VALUES (?, ?, ?, ?)",
                        (data[0], float(data[1]), float(data[2]), data[3])
                    )
                except Exception as e:
                    print(f"Problem z linią: {line}, błąd: {e}")
    conn.commit()
    conn.close()

def import_all_new_files():
    imported_files_path = 'imported_files.txt'
    imported_files = set()

    if os.path.exists(imported_files_path):
        with open(imported_files_path, 'r') as f:
            imported_files = set(line.strip() for line in f.readlines())

    csv_files = glob.glob(os.path.join(CSV_FOLDER, '*.csv'))
    for csv_file in csv_files:
        if csv_file not in imported_files:
            print(f"Importuję plik: {csv_file}")
            import_csv_to_db(csv_file)
            with open(imported_files_path, 'a') as f:
                f.write(csv_file + '\n')

print("Import danych zakończony pomyślnie.")


if __name__ == "__main__":
    import_all_new_files()