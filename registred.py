import os
import django
from django.db import IntegrityError
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labauto.settings")
django.setup()

from actus.models import Actus
import grequests

from bs4 import BeautifulSoup
import re

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

regular = r'\b\d{2}\.\d{2}\.\d{4}\b'


almaty_tz = ZoneInfo("Asia/Almaty")
now = datetime.now(almaty_tz)

rs = [grequests.post("https://evak.online/search_reg.php", data={'query_reg':u.carVincode}) for u in Actus.objects.all() if len(u.isCalled) != 10 and now - u.createDate < timedelta(days=7)]

for r in grequests.imap(rs, size=100):
	if r.status_code == 200:
		soup = BeautifulSoup(r.text, 'html.parser')
		component = soup.find('div', {"id": "sp-component"})
		#reg = component.find("h3")
		reg = component.findAll("h4")
		print(reg)
		if len(reg) > 0:
			reg_data = reg[2].text
			call_data = reg[3].text
			reg_data_re = re.findall(regular, reg_data)
			call_data_re = re.findall(regular, call_data)

			act = Actus.objects.filter(carVincode = r.request.body.split("=")[1])

			if len(reg_data_re):
				act.update(isRegistred=reg_data_re[0])
				print(reg_data_re[0])

			if len(call_data_re):
				act.update(isCalled=call_data_re[0])
				print(call_data_re[0])
