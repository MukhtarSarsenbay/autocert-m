import os
import django
from django.db import IntegrityError
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "labauto.settings")
django.setup()

from actus.models import Actus

from bs4 import BeautifulSoup
import re

import aiohttp
import asyncio

import pandas as pd

regular = r'\b\d{2}\.\d{2}\.\d{4}\b'


rs = [{'query_reg':u.carVincode} for u in Actus.objects.all() if len(u.isCalled) != 10]

async def fetch_data(data):
    connector = aiohttp.TCPConnector(limit=4)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for payload in data:
            tasks.append(fetch_url(session, payload))
        responses = await asyncio.gather(*tasks)
        return responses

async def fetch_url(session, payload):
    try:
        async with session.post("https://evak.online/search_reg.php", data=payload) as response:  # Отключение проверки SSL
            response.raise_for_status()  # Генерация исключения для HTTP ошибок
            return await response.text()  # Возвращаем JSON-ответ
    except Exception as e:
        print(f"An error occurred for {e}")
        return None  # Вернуть None в случае ошибки


async def main():
    df = pd.read_excel("list7.xlsx")
    print(len(df['ВИН']))
    rs = [{'query_reg':vin} for vin in df['ВИН']]
    print(len(rs))

    reg_data_arr = []
    call_data_arr = []

    res = await fetch_data(rs)
    for r in res:

        if r is None:
            reg_data_arr.append("Нет регистрации")
            call_data_arr.append("Не было прозвонаОшибка")
            continue

        soup = BeautifulSoup(r, 'html.parser')
        component = soup.find('div', {"id": "sp-component"})
        print(component)
        reg = component.findAll("h4")

        if reg is None:
            reg_data_arr.append("Нет регистрации")
            call_data_arr.append("Не было прозвона")
            continue

        if len(reg) == 0:
            reg_data_arr.append("Нет регистрации")
            call_data_arr.append("Не было прозвона")
            continue

        if len(reg) > 0:
            reg_data = reg[2].text
            call_data = reg[3].text
            reg_data_re = re.findall(regular, reg_data)
            call_data_re = re.findall(regular, call_data)
            if len(reg_data_re):
                # act.update(isRegistred=reg_data_re[0])
                reg_data_arr.append(reg_data_re[0])
                print(reg_data_re[0])
            else:
                reg_data_arr.append("Нет регистрации")

            if len(call_data_re):
                # act.update(isCalled=call_data_re[0])
                call_data_arr.append(call_data_re[0])
                print(call_data_re[0])
            else:
                call_data_arr.append("Не было прозвона")
            continue

    df["Регистрация"] = reg_data_arr
    df["Прозвон"] = call_data_arr

    df.to_excel("listv7.xlsx")

asyncio.run(main())