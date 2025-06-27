import pandas as pd
import os

sciezka = "../dane"

for plik in os.listdir(sciezka):
    if plik.endswith(".csv"):
        df = pd.read_csv(os.path.join(sciezka, plik))
        print(f"{plik} → {list(df.columns)}")
