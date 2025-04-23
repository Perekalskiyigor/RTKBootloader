"""Класс стола но буду вероятно использовать класс тэйбл там многопоточность"""

import socket
import requests
import json
import logging
import sqlite3
from datetime import datetime

class IgleTable:
    def __init__(self, urlIgleTabeControl, urlStatusFromIgleTabe, module_type, stand_id, serial_number_8, data_matrix, firmwares):
        self.urlIgleTabeControl = urlIgleTabeControl
        self.urlStatusFromIgleTabe = urlStatusFromIgleTabe

        self.module_type = module_type
        self.stand_id = stand_id
        self.serial_number_8 = serial_number_8
        self.data_matrix = data_matrix
        self.firmwares = firmwares
        self.cookie = None
        
        # Настройка логирования
        logging.basicConfig(
            filename='RTK.log',
            level=logging.INFO,
            format='%(asctime)s - ProviderIgleTable - %(levelname)s - %(message)s'
        )

       
    # Запрос на прошивку
    def control_igle_table(self):
        """Метод для отправки команд иглостэнду.""" 
        logging.info("Method control_igle_table called.")
        logging.debug(f"Input parameters: stand_id=, module_type=, data_matrix=  serial_number_8 = firmwares = ")
        
        payload = json.dumps({
        "stand_id": "nt_kto_rtk_1",
        "module_type": "R050 DI 16 012-000-AAA",
        "data_matrix": [
            "11"
        ],
        "serial_number_8": "1",
        "firmwares": [
            {
            "fw_type": "MCU",
            "fw_path": "C:\\nails_table_bridge\\plc050_di16012-full.hex",
            "fw_version": "1.0.36.0"
            }
        ]
        })
        headers = {
        'Content-Type': 'application/json'
        }

        try:
            logging.info("Отправка запроса на %s", self.urlIgleTabeControl)
            response = requests.post(self.urlIgleTabeControl, headers=headers, data=payload)
            logging.info("Код ответа: %d", response.status_code)
            logging.info("Тело ответа: %s", response.text)
            return response.text
        except requests.RequestException as e:
            logging.error("Ошибка запроса: %s", str(e))
            return None
        

        
    # Перепарвка данных от иглостола в сервер ртк
    def recentData(self):
        url = self.urlStatusFromIgleTabe
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json().get("data", {})
                data2 = response.json()
                result = data2.get("result")
                test_result = data.get("test_result")
                #error_description = test_result.get("error_description")
                datamatrix = data.get("data_matrix")

                return {
                    "data_matrix": datamatrix[0],
                    "log_path": data.get("log_file_path"),
                    "report_path": data.get("report_file_path"),
                    "serial_number_8": data.get("serial_number_8"),
                    "stand_id": data.get("stand_id"),
                    "error_description": test_result,
                    "status_code": result
                }
            else:
                return {"status_code": 404}
        except Exception as e:
            # Можно залогировать ошибку при необходимости
            return {"status_code": 404}
        




    

"""
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    # Подключаемся к "левому" адресу — не важно, доступен он или нет
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
finally:
    s.close()
print(f"Локальный IP-адрес: {ip}")
   

igle_table = IgleTable(
        urlIgleTabeControl=f"http://192.168.1.100:5000/nails_table/start_test_board_with_rtk",
        urlStatusFromIgleTabe=f"http://192.168.1.100:5003/get_test_results",

        module_type="R050 DI 16 011-000-AAA",
        stand_id="nt_kto_rtk_1",
        serial_number_8="1",
        data_matrix=["11"],
        firmwares = [
            {
            "fw_type": "MCU",
            "fw_path": "C:\\nails_table_bridge\\plc050_di16012-full.hex",
            "fw_version": "1.0.36.0"
            }
        ]
    )
resultTest = igle_table.recentData()
print(f"Локальныйvvvv IP-адрес: {igle_table.urlStatusFromIgleTabe}")

# Выводим все данные
for key, value in resultTest.items():
    print(f"{key}: {value}")
# Проверяем, что ответ успешный
"""