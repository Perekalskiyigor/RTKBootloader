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


# Настройка логирования
logging.basicConfig(
    filename='RTK.log',  # Файл для логирования
    level=logging.INFO,           # Уровень логирования
    format='SentLog1C - %(asctime)s - %(levelname)s - %(message)s',  # Формат логов
)

# УСПЕШНАЯ прошивка. Отпроавка лога по успешной прошивке платы РЕГЛАБ
# Функция для отправки лога о успешной прошивке
def send_success_log(board_dict):
    now = datetime.datetime.now().isoformat()

    # Подготовка данных для JSON-запроса
    payload = {
        "product_info": board_dict["product_info"],
        "good": [
            {
                "module": {
                    "number": board_dict["good"][0]["module"]["number"],
                    "number8": board_dict["good"][0]["module"]["number8"],
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

        # Логика для отметки в базе данных об успешной отправке лога
        # (например, можно записывать в БД информацию об успешной отправке)

        return response.json()
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
        "product_info": board_dict["product_info"],
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
    "good": [
        {
            "module": {
                "number": "V01114423",
                "number8": "25055656",
                "number15": "082200425055656"
            },
            "board": {
                "number": "S00390116"
            },
            "operator": "A.Eliseeva",
            "error": 0,
            "timestamps": {
                "dm_code_time": "2025-05-15 10:51:35.798732",
                "firmware_finished_time": "2025-05-15 10:52:12.725689",
                "board_output_time": "2025-05-15 10:52:15.725689"
            }
        }
    ],
    "bad": []
}

# Пример вызова функции
response = send_success_log(board_dict)

"""

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

# Пример вызова функции
response = send_unsuccess_log(board_dict)
"""
