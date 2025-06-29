import pandas as pd
import glob
import os

def wczytaj_i_przetworz_plik(filepath, separator):
    try:
        df = pd.read_csv(filepath, sep=separator, engine='python', encoding='utf-8', on_bad_lines='skip')
    except Exception as e:
        print(f"Błąd podczas wczytywania pliku {filepath}: {e}")
        return None

    if df.shape[1] == 1:
        col = df.columns[0]
        nowy_df = df[col].str.strip().str.split(',', expand=True)
        nowy_df.columns = ['czas', 'pm25', 'pm10'] + [f'col{i}' for i in range(3, nowy_df.shape[1])]
        nowy_df['pm25'] = pd.to_numeric(nowy_df['pm25'], errors='coerce')
        nowy_df['pm10'] = pd.to_numeric(nowy_df['pm10'], errors='coerce')
        return nowy_df[['czas', 'pm25', 'pm10']]
    else:
        return df

def oblicz_statystyki(df):
    if 'pm25' not in df.columns or 'pm10' not in df.columns:
        print("Brak kolumn pm25 lub pm10 w danych.")
        return None

    return {
        'pm25_mean': df['pm25'].mean(),
        'pm25_max': df['pm25'].max(),
        'pm25_min': df['pm25'].min(),
        'pm10_mean': df['pm10'].mean(),
        'pm10_max': df['pm10'].max(),
        'pm10_min': df['pm10'].min(),
    }

def main():
    print("START programu generuj_statystyki.py")

    folder_dane = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dane'))
    pliki = glob.glob(os.path.join(folder_dane, '*.csv'))
    print("Znalezione pliki:", pliki)

    wyniki = []

    for plik in pliki:
        print(f"\nWczytuję: {plik}")

        df = None
        for sep in [',', ';', '\t', ' ']:
            try:
                df = wczytaj_i_przetworz_plik(plik, sep)
                if df is not None:
                    break
            except Exception as e:
                print(f"Błąd z separatorem '{sep}': {e}")
                continue

        if df is None:
            print(f"❌ Nie udało się wczytać pliku: {plik}")
            continue

        print(f"✅ Wczytano {len(df)} rekordów z pliku")

        stat = oblicz_statystyki(df)
        if stat is None:
            print(f"⚠️ Brak wymaganych danych w pliku: {plik}")
            continue

        nazwa = os.path.basename(plik).replace('.csv', '')
        miasto = nazwa.split('_')[-1]
        stat['miasto'] = miasto
        wyniki.append(stat)

    if not wyniki:
        print("❌ Brak danych do zapisania.")
        return

    df_wyniki = pd.DataFrame(wyniki)
    kolumny = ['miasto', 'pm25_mean', 'pm25_max', 'pm25_min', 'pm10_mean', 'pm10_max', 'pm10_min']
    df_wyniki = df_wyniki[kolumny]

    folder_wyniki = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'wyniki'))
    os.makedirs(folder_wyniki, exist_ok=True)

    sciezka_zapisu = os.path.join(folder_wyniki, 'statystyki_wszystkie_miasta.csv')
    df_wyniki.to_csv(sciezka_zapisu, index=False)

    print(f"✅ Zapisano statystyki do pliku: {sciezka_zapisu}")

if __name__ == '__main__':
    main()
