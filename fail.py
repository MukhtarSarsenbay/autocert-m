import os
import django
import pandas as pd
from django.db import IntegrityError
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labauto.settings")
django.setup()

from actus.models import Actus

arr = []

for act in Actus.objects.all():
	arr.append([act.button.iccid, act.button.imei])

df = pd.DataFrame(arr)
df.to_excel("text.xlsx")


# imeis = []
# with open("imeis.txt", "r") as file:
# 	for r in file.read().split("\n"):
# 		imeis.append(r)


# unice_imei = []
# for button in Button.objects.all():
# 	for imei in imeis:
# 		if button.imei == imei:
# 			#print(imei)
# 			unice_imei.append(imei)


# for i in set(unice_imei):
# 	print(i)