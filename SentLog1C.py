import requests
import json
import logging
import sqlite3
from datetime import datetime
import SQLite
import configparser
import os
from requests.auth import HTTPBasicAuth
import datetime

# Загрузка конфигурации
config = configparser.ConfigParser()
config.read('config.ini')

url_send_data = config['server']['url']
username = config['server']['username']
password = config['server']['password']
url_token = config['server']['url_token']

# Функция для получения токена
def get_token():
    payload = 'grant_type=CLIENT_CREDENTIALS'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic VnFuaHFPd1pGak16Y0czTFY5d3VSLXhtdlgxX29oWFBjbDRCWXc3cXJSND06N08zNFV6QXpuaVAxOE9RM0VQUGNqWFlya3BmUEFySkpfeHdMcmNDdXRsOD0='
    }
    try:
        # Отключение проверки SSL сертификата, если необходимо
        response = requests.post(url_token, data=payload, headers=headers, verify=False)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('id_token', token_data.get('access_token'))
            logging.info("API1C - Recieve new Token")
            return access_token
        else:
            logging.error(f"API1C - Token request failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logging.error(f"API1C - Error Recieve new Token: {str(e)}")
        return None



# УСПЕШНАЯ прошивка. Отпроавка лога по успешной прошивке платы РЕГЛАБ
# Функция для отправки лога о успешной прошивке
def send_success_log(board_dict):
    now = datetime.datetime.now().isoformat()
    token = get_token()

    if not token:
        logging.error("Не удалось получить токен")
        print("Не удалось получить токен")
        return None

    payload = {
    "rtk_id": board_dict["rtk_id"],
    "order": board_dict["order"],
    "version": board_dict["version"],
    "message_type": board_dict["message_type"],
    "good": [
        {
            "module": {
                "number":   board_dict["good"][0]["module"]["number"],
                "number8":  board_dict["good"][0]["module"]["number8"],
                "number15": board_dict["good"][0]["module"]["number15"]
            },
            "board": {
                "number": board_dict["good"][0]["board"]["number"]
            },
            "operator": board_dict["good"][0]["operator"],
            "error": 0,
            "timestamps": {
                "dm_code_time": now,
                "firmware_finished_time": now,
                "board_output_time": now
            }
        }
    ],
    "bad": []
}


    print("== JSON Request Body ==")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.post(
            url_send_data,
            json=payload,
            headers=headers,
            verify=False,
            timeout=10
        )
        response.raise_for_status()

        logging.info("Request successful. Status: %s", response.status_code)
        logging.info("Response: %s", response.text)
        print(f"\nУспешно отправлено: {response.status_code}")

        try:
            return response.json()
        except ValueError:
            logging.warning("Response is not JSON or empty")
            return response.text

    except requests.exceptions.RequestException as e:
        logging.error("Error sending request: %s", str(e))
        print(f"\nОшибка отправки: {e}")
        return None



# Ртправка лога по неуспешной прошивке платы РЕГЛАБ
# Функция для отправки неуспешного лога
def send_unsuccess_log(board_dict):
    now = datetime.datetime.now().isoformat()

    # Подготовка данных для JSON-запроса
    payload = {
        "rtk_id": board_dict["rtk_id"],
        "order": board_dict["order"],
        "version": board_dict["version"],
        "message_type": board_dict["message_type"],
        "good": [],
        "bad": [
            {
                "board": {
                    "number": board_dict["bad"][0]["board"]["number"]
                },
                "operator": board_dict["bad"][0]["operator"],
                "error": board_dict["bad"][0]["error"],
                "timestamps": {
                    "dm_code_time": now,
                    "firmware_finished_time": now,
                    "board_output_time": now
                }
            }
        ]
    }


    # Печатаем JSON-запрос в консоль
    print("== JSON Request Body ==")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            url_send_data,
            json=payload,
            auth=HTTPBasicAuth(username, password),
            verify=False,
            timeout=10
        )
        response.raise_for_status()

        logging.info("Request successful. Status: %s", response.status_code)
        logging.info("Response: %s", response.text)
        print(f"\nУспешно отправлено: {response.status_code}")

        # Логика для отметки в базе данных о неуспешной отправке лога
        # (например, можно записывать в БД информацию об ошибке)

        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error sending request: %s", str(e))
        print(f"\nОшибка отправки: {e}")
        return None



############################Тестирование

# Пример использования:
board_dict = {
  "rtk_id": "RTK_R050_BoardsIO_2",
  "order": "ЗНП-25778.1.1",
  "version": "1.0.15.6",
  "message_type": "firmware_log",
  "good": [
    {
      "module": {
        "number": "V01250888",
        "number8": "25052859",
        "number15": "089391025052859"
      },
      "board": {
        "number": "S00390116"
      },
      "operator": "A.Eliseeva",
      "error": 0,
      "timestamps": {
        "dm_code_time": "2025-10-17 10:51:35.798732",
        "firmware_finished_time": "2025-10-17 10:52:12.725689",
        "board_output_time": "2025-10-17 10:52:15.725689"
      }
    }
  ],
  "bad": []
}



# Пример вызова функции
response = send_success_log(board_dict)


"""

# Пример использования:
board_dict = {
    "product_info": {
        "rtk_id": "RTK_R500_CH_1",
        "order": "ЗНП-9176.1.1",
        "version": "1.0.15.6",
        "components": {
            "3.182.922": "Крепление к DIN-рейке DF700 модуля ввода-вывода, ИП R050",
            "3.182.928": "Корпус (правая половина с экстрактором) DF700 модуля ввода-вывода, ИП R050",
            "3.182.927": "Корпус (левая половина) DF700 модуля ввода-вывода, ИП R050",
            "3.220.168": "Коробка из картона для модуля ввода/вывода R050",
            "2.180.531": "Световод 18 пин (с сепаратором) DF700 модуля ввода-вывода, ИП R050",
            "2.211.823": "Клеммник R050 с маркировкой",
            "3.182.921": "Лепесток извлечения DF700 модуля ввода-вывода, ИП R050",
            "2.142.935": "Плата PLC050_DI16_011_V4A"
        },
        "marking_templates": [
            {
                "type": "front",
                "type_RU": "Передняя сторона",
                "path": "\\\\prosyst.ru@ssl\\davwwwroot\\1cfiles\\ERP\\20250709\\3.210.707 - Лицевая правая крышка R500 CU 00 151 с фрезеровкой и маркировкой (без GNS).le"
            }
        ]
    },
    "good": [],
    "bad": [
        {
            "board": {
                "number": "Z01137499T"
            },
            "error": 3,
            "operator": "A.Eliseeva",
            "timestamps": {
                "dm_code_time": "2025-03-14 08:21:02.653260",
                "firmware_finished_time": "2025-03-14 08:21:33.371907",
                "board_output_time": "2025-03-11 15:00:33.587027"
            }
        }
    ]
}
"""
# Пример вызова функции
# response = send_unsuccess_log(board_dict)

# token = get_token()
# print("Полученный токен:", token)