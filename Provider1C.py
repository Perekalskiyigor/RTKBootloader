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



class RTKRequest:
    def __init__(self, url, headers):
        self.url = url
        self.headers = headers
        self.data = None

    def fetch_data(self):
        try:
            response = requests.get(self.url, headers=self.headers, verify=False)
            response.raise_for_status()
            self.data = response.json()

            order_id = self.data.get('order')
            components = self.data.get('components', {})
            products = self.data.get('products', {})
            firmware = products.get('firmware', '')
            board_name = products.get('product', None)
            batch = products.get('batch', {})

            # Вывод в консоль
            #print(f"Order ID: {order_id}")
            #print(f"Board Name: {board_name}")
            #print(f"Firmware: {firmware}")
            #print(f"Total Serials: {batch}")
            #print("\nComponents:")

            logging.info("Data successfully fetched.")
            return order_id, board_name, firmware, batch
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            raise


if __name__ == '__main__':
    url = "https://black/erp_game_ivshin255/hs/rtk/order/RTK_R050/ЗНП-8372.1.1"
    headers = {
        'Authorization': 'Basic cnRrOnJ0azEyMw=='
    }

    rtk = RTKRequest(url, headers)
    order_id, board_name, firmware, batch = rtk.fetch_data()
    db_connection = SQLite.DatabaseConnection()

    db_connection.get_order_insert_orders_frm1C(order_id, board_name, firmware, batch)