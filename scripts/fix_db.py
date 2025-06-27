import sqlite3

DB_PATH = '../scripts/dane_zanieczyszczenia.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("UPDATE pomiary SET miasto = 'bydgoszcz' WHERE miasto = 'bygdoszcz'")
conn.commit()

# Sprawdzenie, czy poprawnie zmieniono
cur.execute("SELECT DISTINCT miasto FROM pomiary")
miasta = cur.fetchall()
print("Miasta w bazie po zmianie:", miasta)

conn.close()
