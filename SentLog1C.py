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

# Отпроавка лога по успешной прошивке платы РЕГЛАБ
def SendSucessLog(order, version, components):
    now = datetime.datetime.now().isoformat()

    payload = {
        "product_info": {
            "rtk_id": "RTK_R500_CH_1",
            "order": order,
            "version": version,
            "components": components,
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
                    "factory_number": "25055656",
                    "serial_number": "082200425055656"
                },
                "board": {
                    "serial_number": "S00390116"
                },
                "operator": "A.Eliseeva",
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
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error sending request: %s", str(e))
        print(f"\nОшибка отправки: {e}")
        return None


# Ртправка лога по неуспешной прошивке платы РЕГЛАБ
def SendUNSucessLog(order, version, components, typeModule, pathTemplate, data_matrix, operator, errorCode, dm_code_time, firmware_finished_time, board_output_time ):
    now = datetime.datetime.now().isoformat()

    payload = {
        "product_info": {
            "rtk_id": "RTK_R500_CH_1",
            "order": order,
            "version": version,
            "components": components, # Номерклатура Nomenclature
            "marking_templates": [
                {
                    "type": typeModule,  # typeModule
                    "type_RU": "Передняя сторона",
                    "path": pathTemplate
                }    #pathTemplate
            ]
        },
        "good": [],
        "bad": [
            {
            "board": {
                "serial_number": data_matrix # data_matrix
            },
            "error": errorCode, # errorCode
            "operator": operator,
            "timestamps": {
                "dm_code_time": dm_code_time,
                "firmware_finished_time": firmware_finished_time,
                "board_output_time": board_output_time
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
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error sending request: %s", str(e))
        print(f"\nОшибка отправки: {e}")
        return None



############################Тестирование
components_example = {
        "3.182.922": "Крепление к DIN-рейке DF700 модуля ввода-вывода, ИП R050",
        "3.182.928": "Корпус (правая половина с экстрактором) DF700 модуля ввода-вывода, ИП R050",
        "3.182.927": "Корпус (левая половина) DF700 модуля ввода-вывода, ИП R050",
        "3.220.168": "Коробка из картона для модуля ввода/вывода R050",
        "2.180.531": "Световод 18 пин (с сепаратором) DF700 модуля ввода-вывода, ИП R050",
        "2.211.823": "Клеммник R050 с маркировкой",
        "3.182.921": "Лепесток извлечения DF700 модуля ввода-вывода, ИП R050",
        "2.142.935": "Плата PLC050_DI16_011_V4A"
    }

#SendSucessLog(order="ЗНП-9176.1.1", version="1.0.15.6", components=components_example)
SendUNSucessLog(order="ЗНП-9176.1.1", version="1.0.15.6", components=components_example)