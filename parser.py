import aiohttp
import asyncio

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

# url парсера
url = "https://eokno.gov.kz/public-register/register-ktrm2.xhtml"
RANGE = 100#1640
DEF = 1
FILTER = ".2589.05"
DIR = "res5"

async def fetch_data(urls):
    timeout = aiohttp.ClientTimeout(
        total=70,  # Общее максимальное время выполнения запроса (секунды)
        #connect=20,  # Время ожидания на подключение (секунды)
        #sock_read=20,  # Время ожидания чтения данных (секунды)
        #sock_connect=20  # Время ожидания на установление сокета (секунды)
    )
 
    async with aiohttp.ClientSession(timeout = timeout) as session:
        tasks = []
        for url in urls:
            #res = fetch_url(session, url)
            #if res is None: continue
            tasks.append(fetch_url(session, url))
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses

async def fetch_url(session, url):
    try:
        async with session.get(url, ssl=False) as response:  # Отключение проверки SSL
            response.raise_for_status()  # Генерация исключения для HTTP ошибок
            return await response.text()  # Возвращаем JSON-ответ
    except Exception as e:
        print(f"An error occurred for {url}: {e}")
        return None  # Вернуть None в случае ошибки

async def get_info_cert(p_index: int, urls: str):
    results = await fetch_data(urls)
    arr = []
    for result in results:
        if result is None: return None
        soup = BeautifulSoup(result, 'html.parser')
        table = soup.find("table", {"id": "reportDataForm:reportDataPG"})

        rows = table.find_all('tr')

        keys = []
        values = []

        # Проходим по каждой строке
        for index, row in enumerate(rows):
            #if index in [0,3,7]: continue

            cells = row.find_all('td')
            keys.append(cells[0].text.strip())
            values.append(cells[1].text.strip())

        arr.append(values)

    with open(f"{DIR}/{p_index}.txt", "w") as file:
        file.write(json.dumps(arr))

        


def parse_response(response: bytes):
    # Парсим XML-ответ
    soup = BeautifulSoup(response, 'xml')

    update_tag = soup.find('update')
    cdata_content = update_tag.string

    cdata_soup = BeautifulSoup(cdata_content, 'html.parser')

    # Находим все строки (tr) с данными
    rows = cdata_soup.find_all('tr')

    parsed_data = []

    # Проходим по каждой строке
    for row in rows:
        # Извлекаем все ячейки (td) в строке
        # print(row)
        cells = row.find_all('td')

        # Декодируем данные из байтов в читаемый вид
        vehicle_data = {
            'vehicle_id': cells[0].text.strip(),
            'eac_code': cells[1].text.strip(),
            'vin': cells[2].text.strip(),
            'status': cells[3].text.strip(),
            'date': cells[4].text.strip(),
            'applicant': cells[8].text.strip(),
            'cert_id': cells[9].text.strip(),
            'type': cells[10].text.strip()
        }

        parsed_data.append(vehicle_data)

    return parsed_data

def get_view_state(url: str):

    # Заголовки для GET-запроса
    headers_get = {
        'Host': 'eokno.gov.kz',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    }

    # GET-запрос для получения страницы
    session = requests.Session()
    response = session.get(url, headers=headers_get, verify=False)

    # Парсинг HTML-ответа для получения ViewState
    soup = BeautifulSoup(response.content, 'html.parser')
    view_state = soup.find('input', {'name': 'javax.faces.ViewState'})['value']

    return session, view_state

# def get_info_cert(res):
#     #res = requests.get(url, verify=False)
#     #res_async = async.get(url)
	
#    	#if (res.status_code != 200): return None
#     soup = BeautifulSoup(res.content, 'html.parser')

#     table = soup.find("table", {"id": "reportDataForm:reportDataPG"})

#     rows = table.find_all('tr')

#     keys = []
#     values = []

#     # Проходим по каждой строке
#     for index, row in enumerate(rows[:10]):
#         if index in [0,3,7]: continue

#         cells = row.find_all('td')
#         keys.append(cells[0].text.strip())
#         values.append(cells[1].text.strip())

#     return keys, values

#     #df = pd.DataFrame([keys, values])
#     #df.to_excel("output.xlsx")




def parsing(session, view_state: str):
    # Теперь можно выполнить POST-запрос с обновленным ViewState
    headers_post = {
        'Host': 'eokno.gov.kz',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://eokno.gov.kz',
        'Connection': 'keep-alive',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Accept': 'application/xml, text/xml, */*; q=0.01',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Faces-Request': 'partial/ajax',
        'X-Requested-With': 'XMLHttpRequest',
    }

    cookies = {
        'sessId': '7uxbslJ7sldd_H8Fs4ee7t1FedfY9892PlAAqaMV',
        'cookiesession1': '678B76A1306EBFACB4B9D362468ACF40',
    }

    first_keys = True
    arr = []
    index = 0


    for i in range(RANGE):
        data = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "dApplicationListOpenedKtrm2:ktrmListForm:listTable",
            "javax.faces.partial.execute": "dApplicationListOpenedKtrm2:ktrmListForm:listTable",
            "javax.faces.partial.render": "dApplicationListOpenedKtrm2:ktrmListForm:listTable",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable": "dApplicationListOpenedKtrm2:ktrmListForm:listTable",

            # для получение по след страницы
            # "dApplicationListOpenedKtrm2:ktrmListForm:listTable_pagination": "true",
            # "dApplicationListOpenedKtrm2:ktrmListForm:listTable_first": "5", # те страницы для 2 - 5, для 3 - 10 и т.д
            # "dApplicationListOpenedKtrm2:ktrmListForm:listTable_rows": "5",
            # "dApplicationListOpenedKtrm2:ktrmListForm:listTable_skipChildren": "true",
            # "dApplicationListOpenedKtrm2:ktrmListForm:listTable_encodeFeature": "true",
            # "dApplicationListOpenedKtrm2:ktrmListForm": "dApplicationListOpenedKtrm2:ktrmListForm",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable_reflowDD": "0_0",


            # Для получение первый страницы
            # "dApplicationListOpenedKtrm2:ktrmListForm:listTable_filtering": True,
            # "dApplicationListOpenedKtrm2:ktrmListForm:listTable_encodeFeature": True,

            # фильтр
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt32:filter": FILTER,

            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt35_focus": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt35_input": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt41:filter": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt44_focus": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt44_input": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:filterValueRegistrationDate_input": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:filterValueValidFrom_input": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:filterValueValidTo_input": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt64_focus": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt64_input": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt71:filter": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt73:filter": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable:j_idt75:filter": "",
            "dApplicationListOpenedKtrm2:ktrmListForm:listTable_selection": "",

            "dApplicationListOpenedKtrm2:ktrmListForm:listTable_scrollState": "0,0",
            "javax.faces.ViewState": view_state  # Используем полученный ViewState
        }

        if i == 0:
            data = {
                #для получение по след страницы
                "dApplicationListOpenedKtrm2:ktrmListForm:listTable_filtering": True,
                "dApplicationListOpenedKtrm2:ktrmListForm:listTable_encodeFeature": True,

                **data,
            }
        else:
            data = {
                #для получение по след страницы
                "dApplicationListOpenedKtrm2:ktrmListForm:listTable_pagination": "true",
                "dApplicationListOpenedKtrm2:ktrmListForm:listTable_first": str(i*5),
                "dApplicationListOpenedKtrm2:ktrmListForm:listTable_rows": "5",
                "dApplicationListOpenedKtrm2:ktrmListForm:listTable_skipChildren": "true",
                "dApplicationListOpenedKtrm2:ktrmListForm:listTable_encodeFeature": "true",
                "dApplicationListOpenedKtrm2:ktrmListForm": "dApplicationListOpenedKtrm2:ktrmListForm",

                **data,
            }


        # Выполняем POST-запрос
        res = session.post(url, headers=headers_post, cookies=cookies, data=data, verify=False)
        for parse in parse_response(res.content):
            print(parse)
        if res.status_code != 200: continue 
        urls = [f"https://eokno.gov.kz/ktrm/ktrm2OpenedApp.xhtml?id={parse.get('cert_id')}" for parse in parse_response(res.content)]
        #print(urls)
        asyncio.run(get_info_cert(i, urls))

#         for parse in parse_response(res.content):
#             if parse.get("cert_id") is None: continue
#             keys, values = get_info_cert(f"https://eokno.gov.kz/ktrm/ktrm2OpenedApp.xhtml?id={parse.get('cert_id')}")
#             values.append(parse.get("date"))

#             if first_keys:
#                 arr.append(keys)					
#                 arr.append(values)
#                 first_keys = False
#             else:
#                 arr.append(values)

#             index += 1
#             print(i, parse.get("vehicle_id"), "OK", index)

    #df = pd.DataFrame(arr)
    #df.to_excel("output.xlsx")


session, view_state = get_view_state(url)
parsing(session, view_state)
