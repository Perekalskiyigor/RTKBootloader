import requests
import json
import logging
import sqlite3
from datetime import datetime
import SQLite
import configparser


# Загрузка конфигурации
config = configparser.ConfigParser(interpolation=None)
config.read(r"config.ini", encoding="utf-8")

getOrders_url = config['serverOrder']['getOrders_url']
username = config['serverOrder']['password']
fetch_data_url = config['serverOrder']['fetch_data_url']


# Настройка логирования
logging.basicConfig(
    filename='RTK.log',  # Файл для логирования
    level=logging.INFO,           # Уровень логирования
    format='SQLITE - %(asctime)s - %(levelname)s - %(message)s',  # Формат логов
)

def getOrders():
    headers = {
        'Authorization': 'Basic bWFya19EUEE6MTIzNDU2elo='
    }

    try:
        response = requests.get(getOrders_url, headers=headers, verify=False)
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
    logging.info("Вызвана функция получения данных по заказу в бд def fetch_data(order) и провайдера SQL")

    try:
        url = f"{fetch_data_url}{order}"
        payload = {}
        headers = {
        'Authorization': 'Basic bWFya19EUEE6MTIzNDU2elo='
        }
        response = requests.request("GET", url, headers=headers, data=payload, verify=False)
        #print(response.text)
        data = response.json()

        order_id = data.get('order')
        components = data.get('components', {})
        components_str = json.dumps(components, ensure_ascii=False)
        products = data.get('products', {})
        firmware = products.get('firmware', '')
        board_name = products.get('product', None)
        batch = products.get('batch', {})
        count = products.get('count', 0)
        version = products.get('version', None)
        marking_templates = products.get('marking_templates', [])
        marking_templates_str = json.dumps(marking_templates, ensure_ascii=False)

        result = {
            'order_id': order_id,
            'components': components_str,
            'products': {
                'firmware': firmware,
                'board_name': board_name,
                'batch': batch,
                'count': count,
                'version': version,
                'marking_templates': marking_templates_str
            }
        }

        # Извлекаем данные первого шаблона (если он есть)
        if marking_templates:
            first_template = marking_templates[0]
            template_type = first_template.get('type')
            template_type_ru = first_template.get('type_RU')
            template_path = first_template.get('path')
        else:
            template_type = None
            template_type_ru = None
            template_path = None

        """
        # Вывод в консоль
        print("="*50)
        print(f"Order ID: {order_id}")
        print(f"Board Name: {board_name}")
        print(f"Version: {version}")
        print(f"Quantity: {count}")
        print(f"Firmware: {firmware}")
        print("\nComponents:")
        for comp_code, comp_desc in components.items():
            print(f"  {comp_code}: {comp_desc}")

        print("\nMarking Templates:")
        if marking_templates:
            print(f"  Type: {template_type}")
            print(f"  Type (RU): {template_type_ru}")
            print(f"  Path: {template_path}")
        else:
            print("  No marking templates available")

        print("\nBatch Numbers:")
        for i, item in enumerate(batch, 1):
            print(f"  {i}. Full: {item['number']} | 8-digit: {item['number8']} | 15-digit: {item['number15']}")
        print("="*50)
        """
        
        

        logging.info("Data successfully fetched.")
        return result
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        raise


"""
dict = fetch_data("ЗНП-5972.1.1")
db_connection = SQLite.DatabaseConnection()
db_connection.get_order_insert_orders_frm1C(dict)

""" 
#getOrders()


# getOrders()
fetch_data("ЗНП-24576.1.1")


