
# Projekt analityczny: Jakość powietrza w polskich miastach

## 📌 Opis projektu

Celem projektu jest stworzenie systemu analitycznego, który umożliwia interaktywną analizę danych dotyczących jakości powietrza (PM2.5 i PM10) w wybranych miastach w Polsce. System przetwarza dane z plików CSV, zapisuje je do bazy danych, a następnie prezentuje użytkownikowi w postaci tabel, wykresów oraz prognoz dziennych i jutrzejszych opartych na modelach uczenia maszynowego.

---

## 🧱 Struktura systemu

Projekt składa się z trzech głównych warstw:

### 1. Warstwa danych (data ingestion)
- Dane historyczne w formacie CSV znajdują się w katalogu `dane/`.
- Skrypt `scripts/import_csv.py` umożliwia automatyczny import tych danych do bazy SQLite.

### 2. Warstwa przekształceń (ETL)
- Dane są przekształcane i zapisywane do lokalnej bazy danych `dane_zanieczyszczenia.db`.
- Skrypt `scripts/init_db.py` tworzy strukturę bazy danych.
- Skrypt `scripts/train_model.py` trenuje modele ML na podstawie danych historycznych i zapisuje je do katalogu `models/`.

### 3. Warstwa wynikowa (wizualizacja + API)
- Backend oparty na Flasku (`backend/app.py`) udostępnia API REST do pobierania danych.
- Frontend (czysty HTML + JS) umożliwia interaktywne:
  - wybieranie miasta,
  - filtrowanie miesiąca,
  - analizę danych pomiarowych (tabela + wykres),
  - wyświetlanie prognozy dziennej i jutrzejszej.

---

## 🧪 Zastosowanie uczenia maszynowego

W projekcie zastosowano prosty model regresyjny do prognozowania dzisiejszego i jutrzejszego poziomu zanieczyszczeń (PM2.5 i PM10) na podstawie danych z poprzednich dni. Modele są zapisane jako `.joblib` i wykorzystywane w backendzie do generowania prognoz.

---

## ✅ Wymagania

Do uruchomienia projektu wymagane są:

- Python 3.10+
- Biblioteki: `Flask`, `pandas`, `joblib`, `matplotlib`, `scikit-learn`, `sqlite3` (wbudowana)

Instalacja zależności:

```bash
pip install -r requirements.txt
```

---

##  Uruchomienie projektu


1. **Uruchomienie aplikacji:**

cd backend

python app.py

 Uwaga: Backend należy uruchamiać z poziomu katalogu backend, ponieważ ścieżki do bazy danych i modeli są względne względem tej lokalizacji.

2. **Otworzenie interfejsu frontendowego:**

W przeglądarce: `file://ścieżka_do_projektu/frontend/index.html`

---

##  Przykład użycia

- Wybierz miasto (np. Kraków)
- Wybierz miesiąc (np. maj)
- Odczytaj dane z tabeli i wykresu
- Na dole strony zobaczysz prognozowane wartości PM2.5 i PM10

---

## 📝 Źródło danych
Główny Inspektorat Ochrony Środowiska (GIOŚ) — dane o jakości powietrza.
