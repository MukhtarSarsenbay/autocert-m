import os
import json
import pandas as pd

BASE_DIR = os.getcwd()
DIR_PATH = "res/"

arr = []
files = os.listdir(os.path.join(BASE_DIR, DIR_PATH))
for file in files:
    with open(os.path.join(BASE_DIR, DIR_PATH, file), "r") as f:
        txt = json.loads(f.read())
        for cert in txt:
            arr.append(cert)

#glav = ["Номер сертификата", "Статус", "Марка", "Модель", "ТИП", "VIN", "ГОД"]
#arr = [glav, *arr]
df = pd.DataFrame(arr)
df.to_excel("outputv3.xlsx")