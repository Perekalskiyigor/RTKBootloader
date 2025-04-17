"""Класс стола но буду вероятно использовать класс тэйбл там многопоточность"""

import requests
import json
import logging
import sqlite3
from datetime import datetime

class IgleTable:
    def __init__(self, urlIgleTabeControl, urlStatusFromIgleTabe, urlStopgleTabe, module_type, stand_id, serial_number_8, data_matrix, fw_type, fw_path, username, password):
        self.urlIgleTabeControl = urlIgleTabeControl
        self.urlStatusFromIgleTabe = urlStatusFromIgleTabe
        self.urlStopgleTabe = urlStopgleTabe
        self.module_type = module_type
        self.stand_id = stand_id
        self.serial_number_8 = serial_number_8
        self.data_matrix = data_matrix
        self.fw_type = fw_type
        self.fw_path = fw_path
        self.username = username
        self.password = password
        self.cookie = None
        
        # Настройка логирования
        logging.basicConfig(
            filename='RTK.log',
            level=logging.INFO,
            format='%(asctime)s - ProviderIgleTable - %(levelname)s - %(message)s'
        )

    
    """
    def login(self):
        logging.info(f"Attempting login with username: {self.username}")
        login_url = "http://127.0.0.1:5000/login"
        payload = json.dumps({
            "username": self.username,
            "password": self.password
        })
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(login_url, headers=headers, data=payload)
        
        if response.status_code == 200:
            logging.info(f"Login successful for username: {self.username}")
            self.cookie = response.cookies.get('session')
        else:
            logging.error(f"Login failed for username: {self.username}. Response: {response.text}")
    """
    
        
    
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
        
    # статус от иглостола
    def status_igle_table(self):
        """Метод для получения статуса стенда."""  
        url = self.urlStatusFromIgleTabe

        payload = json.dumps({
            "stand_id": self.stand_id
        })
        
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'session=.eJwljjkSwjAMAP_imkKHJUv5DGPZ8kCbkIrh74Sh2i222He5rz2PR9le-5m3cn_OspVkcmNTmU7elQWsTjBwkBZmyOag2ldSuA6vQ5NHG7N1c-pTAeuaaOsqL0ZHot7F62RaHhawEseqrQrEgErRlIMd00QCxMs1ch65_29-huXzBfFZL8A.Z8fMxg.3sF5O_20LPF__XrEzVAMgQoU0Wk'
        }

        try:
            logging.info("Отправка запроса на получение статуса стенда %s", url)
            response = requests.post(url, headers=headers, data=payload)
            logging.info("Код ответа: %d", response.status_code)
            logging.info("Ответ: %s", response.text)
            return response.text
        except requests.RequestException as e:
            logging.error("Ошибка при получении статуса стенда: %s", str(e))
            return None
        
    # статус от иглостола
    def stop_igle_table(self):
        """Метод для получения статуса стенда."""  
        url = self.urlStopgleTabe

        payload = json.dumps({
            "stand_id": self.stand_id
        })
        
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'session=.eJwljjkSwjAMAP_imkKHJUv5DGPZ8kCbkIrh74Sh2i222He5rz2PR9le-5m3cn_OspVkcmNTmU7elQWsTjBwkBZmyOag2ldSuA6vQ5NHG7N1c-pTAeuaaOsqL0ZHot7F62RaHhawEseqrQrEgErRlIMd00QCxMs1ch65_29-huXzBfFZL8A.Z8fMxg.3sF5O_20LPF__XrEzVAMgQoU0Wk'
        }

        try:
            logging.info("Отправка запроса стоп на стенд %s", self.stand_id)
            response = requests.post(url, headers=headers, data=payload)
            logging.info("Код ответа: %d", response.status_code)
            logging.info("Ответ: %s", response.text)
            return response.text
        except requests.RequestException as e:
            logging.error("Ошибка отправки стоп на стенд: %s", str(e))
            return None
    


if __name__ == "__main__":
    igle_table = IgleTable(
        urlIgleTabeControl="http://192.168.1.100:5000/nails_table/start_test_board_with_rtk",
        urlStatusFromIgleTabe="http://127.0.0.1:5000/get_stand_status",
        urlStopgleTabe="http://127.0.0.1:5000/stop_test_board_with_rtk",
        module_type="R050 DI 16 011-000-AAA",
        stand_id="123",
        serial_number_8="1234578",
        data_matrix="Z12323434",
        fw_type="MCU",
        fw_path="path/test_fw1.hex",
        username="admin",
        password="password123"
    )

    """
    #Управление иглостолом
    response = igle_table.control_igle_table()
    print(response)
    """

    """
    # Статус иглостола
    response = igle_table.status_igle_table()
    print(response)
    """

    """
    # Стоп иглостола
    response = igle_table.stop_igle_table()
    print(response)
    """
    
    """
    igle_table.db_connect()
    igle_table.login()
    
    """
    
