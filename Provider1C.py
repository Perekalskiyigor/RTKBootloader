import requests
import json
import logging
import sqlite3
from datetime import datetime
import SQLite


# Настройка логирования
logging.basicConfig(
    filename='RTK.log',  # Файл для логирования
    level=logging.INFO,           # Уровень логирования
    format='SQLITE - %(asctime)s - %(levelname)s - %(message)s',  # Формат логов
)

def getOrders():
    url = "https://black/erp_game_ivshin255/hs/rtk/orderlist/RTK_R050"
    headers = {
        'Authorization': 'Basic cnRrOnJ0azEyMw=='
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # выбросит исключение для кода ответа != 200

        data = response.json()  # преобразуем в словарь

        keys = list(data.keys())  # получаем только ключи

        if keys:
            print("Найденные ключи:", keys)
            return keys
        else:
            print("Ответ получен, но он пуст.")

    except requests.exceptions.RequestException as e:
        print("Ошибка при запросе:", e)
    except ValueError:
        print("Ошибка разбора JSON. Ответ не является допустимым JSON.")
    except Exception as e:
        print("Произошла неизвестная ошибка:", e)



def fetch_data(order):
    try:
        url = f"https://black/erp_game_ivshin255/hs/rtk/order/RTK_R050/{order}"
        payload = {}
        headers = {
        'Authorization': 'Basic cnRrOnJ0azEyMw=='
        }
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        print(response.text)
        data = response.json()

        order_id = data.get('order')
        components = data.get('components', {})
        components = ", ".join(f"{key}: {value}" for key, value in components.items())
        products = data.get('products', {})
        firmware = products.get('firmware', '')
        board_name = products.get('product', None)
        batch = products.get('batch', {})
        count = products.get('count', 0)
        version = products.get('version', None)

        # Вывод в консоль
        print(f"Order ID: {order_id}")
        print(f"Board Name: {board_name}")
        print(f"Firmware: {firmware}")
        print(f"Total Serials: {batch}")
        print("\nComponents:")

        logging.info("Data successfully fetched.")
        return order_id, board_name, firmware, batch, count, version, components
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        raise


"""
order_id, board_name, firmware, batch, count, version, components = fetch_data()
db_connection = SQLite.DatabaseConnection()
db_connection.get_order_insert_orders_frm1C(order_id, board_name, firmware, batch, count, version, components)



order_id, board_name, firmware, batch, count, version, components = fetch_data()
db_connection = SQLite.DatabaseConnection()
db_connection.get_order_insert_orders_frm1C(order_id, board_name, firmware, batch, count, version, components)

getOrders()

fetch_data("ЗНП-5972.1.1")
"""

