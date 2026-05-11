import os
import django
from django.db import IntegrityError
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labauto.settings")
django.setup()
import uuid

from actus.models import Actus, Button
import json
#from subuser.models import SubUser
from datetime import datetime
from store.models import Store


# for st in Store.objects.all():
# 	st.date = datetime.now()
# 	st.save()

#Actus.objects.filter(id=20332).update(creator=27)
btn = Button.objects.filter(user=7, createDate__range=["2025-04-12", "2025-04-12"]).update(hwname="FALCON 004901")
print(len(btn))


# for i in range(5110, 5117+1):
# 	act = Actus.objects.filter(number=str(i))
# 	if len(act) > 0:
# 		crt = act[0].createDate
# 		newcrt = crt.replace(day=crt.day - 1)
# 		act.update(createDate=newcrt)

# with open("button.txt", "r") as file:
# 	for i in file.read().split("\n"):
# 		if i == "": continue
# 		model = json.loads(i)
# 		model['user_id'] = USER_ID
# 		#Button.objects.filter(iccid=model.get('iccid')).delete()
# 		try:
# 			Button(**model).save()
# 			if model.get("createDate") is not None:
# 				Button.objects.filter(iccid=model.get('iccid')).update(createDate=datetime.strptime(model.get("createDate"), '%Y-%m-%d'))
# 		except:
# 			pass

# with open("actus.txt", "r") as file:
# 	for i in file.read().split("\n"):
# 		if i == "": continue
# 		model = json.loads(i)

# 		btn = Button.objects.filter(iccid = model.get("iccid"))
# 		del model["iccid"]
# 		del model["imei"]
# 		del model["serial"]
# 		del model["hwname"]
# 		del model["user_id"]
# 		if len(btn) == 0: continue
# 		model['button_id'] = btn[0].id
# 		model['creator_id'] = USER_ID
# 		#Actus.objects.filter(carVincode=model.get('carVincode')).delete()
# 		Actus(**model).save()

# 		try:
# 			Actus.objects.filter(carVincode=model.get('carVincode')).update(createDate=datetime.strptime(model.get("createDate"), '%Y-%m-%d %H:%M:%S%z'))
# 		except:
# 			pass
