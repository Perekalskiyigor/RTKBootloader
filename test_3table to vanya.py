import logging
import time
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import threading
import socket
from opcua import Client
from opcua import ua
import logging
import yaml
import subprocess
import sys
import os

class TableTimeoutException(Exception):
    """Исключение при превышении таймаута работы со столом"""
    pass

class TableOperationFailed(Exception):
    """Исключение при ошибке выполнения команды столом"""
    pass


class RobActionManager:
    def __init__(self):
        self.lock = threading.Lock()  # Для атомарных операций
        self.current_table = None     # Какой стол сейчас владеет ресурсом

    def acquire(self, table_id):
        """Попытаться захватить Rob_Action для указанного стола."""
        with self.lock:
            if self.current_table is None:
                self.current_table = table_id
                return True
            return False

    def release(self, table_id):
        """Освободить Rob_Action."""
        with self.lock:
            if self.current_table == table_id:
                self.current_table = None
                return True
            return False    



# Пользовательский класс камеры
# mport CameraClass as CAM
import CameraSocket
 
 # Пользовательский класс БД
import Provider1C
import SQLite as SQL

# Поьзовательский класс провайдера Иглостола
import ProviderIgleTable as Igable

# Пользовательский калсс прошивальщика
import Botloader as Bot

# Глобальные ящик и ясейка 
Tray1 = 2
Tray2 = 1
Cell1 = 0
Order = "ЗНП-2160.1.1"
# данные с платы для цикла main и сетапа
photodata = None


dict_Table1 = {
    'Reg_move_Table': 0,
    'sub_Reg_move_Table': 0,
    'Reg_updown_Botloader': 0,
    'sub_Reg_updown_Botloader': 0,
    'Rob_Action': 0,
    'sub_Rob_Action': 0
    
}

shared_data = {
    1: {
        'DICT1': 0,
        'Reg_move_Table': 0,
        'sub_Reg_move_Table': 0,
        'Reg_updown_Botloader': 0,
        'sub_Reg_updown_Botloader': 0,
        'Rob_Action': 0,
        'sub_Rob_Action': 0,
        'workplace1': 0, # Какое ложе сейчас раочее. нужно для платы индикации

        'DB_order_number': "",
        'DB_module': "",
        'DB_fw_version': "",
        'DB_last_count': 0,
        'DB_common_count': 0,
        'DB_success_count': 0,
        'DB_nonsuccess_count': 0,

        'OPC_ButtonLoadOrders': False,
        'OPC_ButtonSelectOrder': False,
        'OPC_Order': "",
        'OPC_Orders': ""
        },
    2: {
        'DICT2': 0,
        'Reg_move_Table': 0,
        'sub_Reg_move_Table': 0,
        'Reg_updown_Botloader': 0,
        'sub_Reg_updown_Botloader': 0,
        'Rob_Action': 0,
        'sub_Rob_Action': 0,
        'workplace1': 0, # Какое ложе сейчас раочее. нужно для платы индикации

        'DB_order_number': "",
        'DB_module': "",
        'DB_fw_version': "",
        'DB_last_count': 0,
        'DB_common_count': 0,
        'DB_success_count': 0,
        'DB_nonsuccess_count': 0,

        'OPC_ButtonLoadOrders': False,
        'OPC_ButtonSelectOrder': False,
        'OPC_Order': "",
        'OPC_Orders': ""
        },
    3: {
        'DICT3': 0,
        'Reg_move_Table': 0,
        'sub_Reg_move_Table': 0,
        'Reg_updown_Botloader': 0,
        'sub_Reg_updown_Botloader': 0,
        'Rob_Action': 0,
        'sub_Rob_Action': 0,
        'workplace1': 0, # Какое ложе сейчас раочее. нужно для платы индикации

        'DB_order_number': "",
        'DB_module': "",
        'DB_fw_version': "",
        'DB_last_count': 0,
        'DB_common_count': 0,
        'DB_success_count': 0,
        'DB_nonsuccess_count': 0,

        'OPC_ButtonLoadOrders': False,
        'OPC_ButtonSelectOrder': False,
        'OPC_Order': "",
        'OPC_Orders': ""
        },
    'OPC-DB': {
        'DB_order_number': "пусто",
        'DB_module': "пусто",
        'DB_fw_version': "пусто",
        'DB_last_count': 0,
        'DB_common_count': 0,
        'DB_success_count': 0,
        'DB_nonsuccess_count': 0,

        'OPC_ButtonLoadOrders': False,
        'OPC_ButtonSelectOrder': False,
        'OPC_Order': "ЗНП-2160.1.1",
        'OPC_Orders': ""
        },

}

shared_data_lock = threading.Lock()





# Set up basic logging configuration
logging.basicConfig(
    filename='RTK.log',
    level=logging.INFO,
    format=' %(asctime)s - MAIN - %(levelname)s - %(message)s'
)

################################################# IgleTable Communication Class ###################################
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    # Берем адрес текущего хоста
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
finally:
    s.close()
print(f"Локальный IP-адрес: {ip}")
   
igle_table = Igable.IgleTable(
        urlIgleTabeControl=f"http://192.168.1.100:5000/nails_table/start_test_board_with_rtk",
        urlStatusFromIgleTabe=f"http://192.168.1.100:5003/get_test_results/1")

igle_table2 = Igable.IgleTable(
        urlIgleTabeControl=f"http://192.168.1.100:5000/nails_table/start_test_board_with_rtk",
        urlStatusFromIgleTabe=f"http://192.168.1.100:5003/get_test_results/2")

igle_table3 = Igable.IgleTable(
        urlIgleTabeControl=f"http://192.168.1.100:5000/nails_table/start_test_board_with_rtk",
        urlStatusFromIgleTabe=f"http://192.168.1.100:5003/get_test_results/3")

################################################# IgleTable Communication Class ###################################


################################################# START SQL Communication class ###################################
# Класс для синхронизации с базой данных и обновления глобального словаря
class DatabaseSynchronizer:
    def __init__(self, order, number, shared_dict) :
        self.order = order
        self.stop_event = threading.Event()  # Событие для остановки потока
        self.update_thread = threading.Thread(target=self.update_data, daemon=True)
        self.update_thread.start()
        self.lock = threading.Lock()
        self.number = number
        self.my_data = shared_dict.get('OPC-DB', {})  # Только своя часть словаря
        self.lock = threading.Lock()

    def update_data(self):
        """Метод для обновления данных в глобальном словаре с базы данных"""
        global shared_data
        while not self.stop_event.is_set():  # Проверка на остановку потока
            try:
                # Попытка получения данных по заказу из базы данных
                db_connection = SQL.DatabaseConnection()
                result = db_connection.getDatafromOOPC(self.order)
                
                if result:
                    order_number, module, fw_version, last_count, common_count, success_count, nonsuccess_count = result

                    # print(f"Номер заказа: {order_number}")
                    # print(f"Модуль: {module}")
                    # print(f"Версия ПО: {fw_version}")
                    # print(f"Количество оставшихся: {last_count}")
                    # print(f"Общее количество записей: {common_count}")
                    # print(f"С успешным report_path: {success_count}")
                    # print(f"С успешным log_path: {nonsuccess_count}")

                    # Обновление глобального словаря с данными из базы
                    with self.lock:
                        with shared_data_lock:
                            self.my_data["DB_order_number"] = order_number          # номер заказа
                            self.my_data["DB_module"] = module                      # имя платы
                            self.my_data["DB_fw_version"] = fw_version              # версия прошивки
                            self.my_data["DB_last_count"] = last_count              # колво непрошитых
                            self.my_data["DB_common_count"] = common_count          # общее колво плат
                            self.my_data["DB_success_count"] = success_count        # прошито ок
                            self.my_data["DB_nonsuccess_count"] = nonsuccess_count  # не прошито    
                else:
                    print(f"[DBSync {self.client_id}] Данные по заказу не найдены.")

            except Exception as e:
                logging.error(f"Ошибка при синхронизации с базой данных: {e}")
            
            # Пауза 1 секунда перед следующей попыткой
            time.sleep(1)

    def stop(self):
        """Метод для остановки потока"""
        self.stop_event.set()  # Устанавливаем событие, чтобы остановить поток

try:
        # Create an instance of DatabaseConnection
        db_connection = SQL.DatabaseConnection()
except Exception as e:
        logging.error(f"Error Create an instance of DatabaseConnection: {e}")
 ################################################# STOP SQL Communication class ###################################




################################################# START OPC Communication class ###################################

class OPCClient:
    def __init__(self, url, client_id, shared_dict):
        self.url = url
        self.lock = threading.Lock()
        self.shared_dict = shared_dict
        self.my_data = shared_dict.get(client_id, {})
        
        # инициализируем значениями по умолчанию
        self.my_data.setdefault("OPC_ButtonLoadOrders", False)
        self.my_data.setdefault("OPC_ButtonSelectOrder", False)
        self.my_data.setdefault("OPC_Order", "")
        
        self.client = None
        self.connected = False
        self.stop_event = threading.Event()
        
        # Start threads
        self.server_thread = threading.Thread(target=self.connection_manager, daemon=True)
        self.update_thread = threading.Thread(target=self.update_registers, daemon=True)
        self.server_thread.start()
        self.update_thread.start()

    def connection_manager(self):
        """Управление соединением по ОПС"""
        while not self.stop_event.is_set():
            try:
                if not self.connected:
                    self.client = Client(self.url)
                    self.client.connect()
                    self.connected = True
                    print(f"Connected to {self.url}")
                time.sleep(1)
            except Exception as e:
                print(f"Connection error: {e}")
                self.connected = False
                if self.client:
                    try:
                        self.client.disconnect()
                    except:
                        pass
                time.sleep(5)  # Wait before reconnection attempt

    def is_connected(self):
        """Check if client is properly connected"""
        return self.connected and self.client is not None

    def update_registers(self):
        """Method for updating OPC variables and dictionary"""
        global shared_data
        while not self.stop_event.is_set():
            try:
                if not self.is_connected():
                    time.sleep(1)
                    continue

                with self.lock:
                    with shared_data_lock:
                        try:
                            # Read ButtonLoadOrders with protection
                            ButtonLoadOrders = False  # Default value
                            try:
                                node = self.client.get_node('ns=2;s=Application.UserInterface.ButtonLoadOrders')
                                ButtonLoadOrders = node.get_value() or False
                            except Exception as e:
                                print(f"Error reading ButtonLoadOrders: {e}")
                            
                            shared_data['OPC-DB']["OPC_ButtonLoadOrders"] = ButtonLoadOrders
                            logging.debug(f"ButtonLoadOrders state - {ButtonLoadOrders}")

                            # Write values to OPC only if connected
                            if self.connected:
                                # Write interface values with protection
                                try:
                                    node = self.client.get_node('ns=2;s=Application.UserInterface.name_board')
                                    node.set_value(ua.DataValue(ua.Variant(shared_data['OPC-DB']['DB_module'], ua.VariantType.String)))
                                except Exception as e:
                                    print(f"Error setting name_board: {e}")

                                try:
                                    node = self.client.get_node('ns=2;s=Application.UserInterface.fw_version')
                                    node.set_value(ua.DataValue(ua.Variant(shared_data['OPC-DB']['DB_fw_version'], ua.VariantType.String)))
                                except Exception as e:
                                    print(f"Error setting fw_version: {e}")

                                # Other write operations similarly protected...

                                # Handle ButtonLoadOrders logic
                                if ButtonLoadOrders:
                                    try:
                                        orders = Provider1C.getOrders() or ['']  # Default empty list
                                        node = self.client.get_node('ns=2;s=Application.UserInterface.search_result')
                                        node.set_value(ua.DataValue(ua.Variant(orders, ua.VariantType.String)))
                                    except Exception as e:
                                        print(f"Error handling ButtonLoadOrders: {e}")

                                # Handle ButtonSelectOrder logic
                                # ... similar protection for other operations

                        except Exception as e:
                            print(f"Error in update_registers: {e}")

            except Exception as e:
                print(f"Critical error in update loop: {e}")
            
            time.sleep(1)

    def stop(self):
        """Clean shutdown"""
        self.stop_event.set()
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass



################################################# START OPC Communication class l ###################################


class ModbusProvider:
    """Class MODBUS Communication with Modbus regul"""
    global Tray1
    global Tray2
    global Cell1
    global command_toBOt
    def __init__(self):
        self.store = ModbusSlaveContext(
            hr=ModbusSequentialDataBlock(0, [0] * 100)
        )
        self.lock = threading.Lock()

        self.server_thread = threading.Thread(target=self.run_modbus_server, daemon=True)
        self.server_thread.start()

        self.update_thread = threading.Thread(target=self.update_registers, daemon=True)
        self.update_thread.start()

    def run_modbus_server(self):
        context = ModbusServerContext(slaves=self.store, single=True)
        print("Starting Modbus TCP server on localhost:502")
        try:
            StartTcpServer(context, address=("192.168.1.100", 502))
        except Exception as e:
            print(f"Error starting Modbus server: {e}")

    def update_registers(self):
        global shared_data, Tray1, Cell1, Tray2
        while True:
            try:
                with shared_data_lock:


                    # СТОЛ 1
                    # Получаем данные из регистров и записываем в shared_data[1]
                    shared_data[1]['sub_Reg_move_Table'] = self.store.getValues(3, 9, count=1)[0]
                    shared_data[1]['sub_Reg_updown_Botloader'] = self.store.getValues(3, 11, count=1)[0]
                    # shared_data[1]['sub_Rob_Action'] = self.store.getValues(3, 13, count=1)[0]
                    shared_data[1]['sub_Rob_Action'] = self.store.getValues(3, 5, count=1)[0]
                    shared_data[1]['workplace1'] = self.store.getValues(3, 15, count=1)[0]

                    # Логирование операций чтения регистров
                    logging.info(
                        "[Modbus] Команда получения данных из регистров (Стол 1):\n"
                        f"  sub_Reg_move_Table       = {shared_data[1]['sub_Reg_move_Table']}\n"
                        f"  sub_Reg_updown_Botloader = {shared_data[1]['sub_Reg_updown_Botloader']}\n"
                        f"  sub_Rob_Action           = {shared_data[1]['sub_Rob_Action']}\n"
                        f"  workplace1               = {shared_data[1]['workplace1']}"
                    )

                    # Записываем данные из shared_data[1] в регистры
                    self.store.setValues(3, 10, [shared_data[1]['Reg_move_Table']])
                    self.store.setValues(3, 12, [shared_data[1]['Reg_updown_Botloader']])
                    value = shared_data[1]["Rob_Action"]
                    if value != 0:
                        self.store.setValues(3, 4, [value])
                    

                    # Логирование операций записи регистров
                    logging.info(
                        "[Modbus] Команда записи данных в регистры (Стол 1):\n"
                        f"  Reg_move_Table       = {shared_data[1]['Reg_move_Table']}\n"
                        f"  Reg_updown_Botloader = {shared_data[1]['Reg_updown_Botloader']}\n"
                        f"  Rob_Action           = {shared_data[1]['Rob_Action']}"
                    )


                    # СТОЛ 2
                    # Получаем данные из регистров и записываем в shared_data[1]
                    shared_data[2]['sub_Reg_move_Table'] = self.store.getValues(3, 1, count=1)[0]
                    shared_data[2]['sub_Reg_updown_Botloader'] = self.store.getValues(3, 3, count=1)[0]
                    shared_data[2]['sub_Rob_Action'] = self.store.getValues(3, 5, count=1)[0]
                    shared_data[2]['workplace1'] = self.store.getValues(3, 7, count=1)[0]

                    # Логирование операций чтения регистров
                    logging.info(
                        "[Modbus] Команда получения данных из регистров (Стол 2):\n"
                        f"  sub_Reg_move_Table       = {shared_data[2]['sub_Reg_move_Table']}\n"
                        f"  sub_Reg_updown_Botloader = {shared_data[2]['sub_Reg_updown_Botloader']}\n"
                        f"  sub_Rob_Action           = {shared_data[2]['sub_Rob_Action']}\n"
                        f"  workplace1               = {shared_data[2]['workplace1']}"
                    )

                    # Записываем данные из shared_data[2] в регистры
                    self.store.setValues(3, 0, [shared_data[2]['Reg_move_Table']])
                    self.store.setValues(3, 2, [shared_data[2]['Reg_updown_Botloader']])
                    value = shared_data[2]["Rob_Action"]
                    if value != 0:
                        self.store.setValues(3, 4, [value])


                    # Логирование операций записи регистров
                    logging.info(
                        "[Modbus] Команда записи данных в регистры (Стол 2):\n"
                        f"  Reg_move_Table       = {shared_data[2]['Reg_move_Table']}\n"
                        f"  Reg_updown_Botloader = {shared_data[2]['Reg_updown_Botloader']}\n"
                        f"  Rob_Action           = {shared_data[2]['Rob_Action']}"
                    )

                    # СТОЛ 3
                    # Получаем данные из регистров и записываем в shared_data[1]
                    shared_data[3]['sub_Reg_move_Table'] = self.store.getValues(3, 17, count=1)[0]
                    shared_data[3]['sub_Reg_updown_Botloader'] = self.store.getValues(3, 19, count=1)[0]
                    # shared_data[3]['sub_Rob_Action'] = self.store.getValues(3, 21, count=1)[0]
                    shared_data[3]['sub_Rob_Action'] = self.store.getValues(3, 5, count=1)[0]
                    shared_data[3]['workplace1'] = self.store.getValues(3, 23, count=1)[0]

                    # Логирование операций чтения регистров
                    logging.info(
                        "[Modbus] Команда получения данных из регистров (Стол 3):\n"
                        f"  sub_Reg_move_Table       = {shared_data[3]['sub_Reg_move_Table']}\n"
                        f"  sub_Reg_updown_Botloader = {shared_data[3]['sub_Reg_updown_Botloader']}\n"
                        f"  sub_Rob_Action           = {shared_data[3]['sub_Rob_Action']}\n"
                        f"  workplace1               = {shared_data[3]['workplace1']}"
                    )

                    # Записываем данные из shared_data[1] в регистры
                    self.store.setValues(3, 18, [shared_data[3]['Reg_move_Table']])
                    self.store.setValues(3, 20, [shared_data[3]['Reg_updown_Botloader']])
                    value = shared_data[3]["Rob_Action"]
                    if value != 0:
                        self.store.setValues(3, 4, [value]) 

                    # Логирование операций записи регистров
                    logging.info(
                        "[Modbus] Команда записи данных в регистры (Стол 3):\n"
                        f"  Reg_move_Table       = {shared_data[3]['Reg_move_Table']}\n"
                        f"  Reg_updown_Botloader = {shared_data[3]['Reg_updown_Botloader']}\n"
                        f"  Rob_Action           = {shared_data[3]['Rob_Action']}"
                    )
                    
                    # Записываем глобальные переменные
                    self.store.setValues(3, 6, [Tray1])
                    self.store.setValues(3, 8, [Cell1])
                    self.store.setValues(3, 24, [Tray2])

                    logging.info(
                        "[Modbus] Запись глобальных переменных ящик-ячейка:\n"
                        f"  Tray1 = {Tray1}\n"
                        f"  Tray2 = {Tray2}\n"
                        f"  Cell1 = {Cell1}"
                    )

                    
                    # Выводим значения для проверки
                    print(f"Registers updated - Table1: {shared_data[1]['Rob_Action']}, "
                          f"SubTable1: {shared_data[1]['sub_Rob_Action']}, ")
                    
                    # Выводим значения для проверки
                    print(f"Registers updated - Table2: {shared_data[2]['Rob_Action']}, "
                          f"SubTable2: {shared_data[2]['sub_Rob_Action']}, ")


                    # Выводим значения для проверки
                    print(f"Registers updated - Table3: {shared_data[3]['Rob_Action']}, "
                          f"SubTable3: {shared_data[3]['sub_Rob_Action']}, ")
                    
                    


            except Exception as e:
                print(f"Error updating registers: {e}")
            time.sleep(1)   

################################################# START MODBUS Communication class with Modbus regul ###################################


################################################# START TABLE CLASS #####################################################################
class Table:
    """ TABLE CLASS"""
    global Tray1
    global Cell1
    global Order
    def __init__(self, name, shared_data, shared_data_lock, number, rob_manager):
        self.name = name
        self.data = shared_data.get(number, {})  # подсловарь объекта
        self.lock = shared_data_lock
        self.number = number
        self.rob_manager = rob_manager



    # Method write registers in modbus through modbus_provider
    def change_value(self, key, new_value):
        with self.lock:
            if key in self.data:
                self.data[key] = new_value
                # print(f"Updated {key} to {new_value} in {self.name}.")
            else:
                print(f"Key '{key}' not found in {self.name}.")

    # Method read registers in modbus through modbus_provider
    def read_value(self, key):
        with self.lock:
            if key in self.data:
                result = self.data[key]
                print(f"Read {key}: {result} from {self.name}.")
            else:
                print(f"Key '{key}' not found in {self.name}.")
            return result

    # The first cycle Protect Table in the start work

    def _send_robot_command(self, base_command, cell_num=None):
        """Отправляет команду роботу с явным разделением 220 (укладка) и 230 (забор).
        
        Args:
            base_command (int): Базовый код:
                - 210 → Забрать из тары общая для всех.
                - 220 → укладка в ложемпент тестирования (221-226).
                - 230 → забор из ложемента укладка в тару (231-236).
                - 241 →  укладка роботом в тару (241).
            cell_num (int, optional): Номер ячейки (1 или 2). Обязателен для 220/230.
        
        Returns:
            bool: True — успех, False — ошибка/таймаут.
        
        Raises:
            ValueError: Если некорректные данные.
        """
        # Проверка входных данных
        if base_command in (220, 230):
            if cell_num not in (1, 2):
                raise ValueError("Для команд 220/230 укажите cell_num: 1 или 2")
        if not (1 <= self.number <= 3):
            raise ValueError(f"Некорректный номер стола: {self.number}. Допустимо: 1-3")

        # Формирование команды
        if base_command == 210:
            command = 210
        elif base_command == 241:
            command = 241
        elif base_command == 242:
            command = 242
        elif base_command == 220:  # Укладка
            command = 220 + (self.number - 1) * 2 + cell_num  # 221-226
        elif base_command == 230:  # Забор
            command = 230 + (self.number - 1) * 2 + cell_num  # 231-236
        else:
            command = base_command + self.number  # Прочие команды

        # Отправка команды
        action_desc = "Укладка" if base_command == 220 else "Забор" if base_command == 230 else "Команда"
        logging.info(f"СТОЛ {self.number}, ЯЧЕЙКА {cell_num} → {action_desc}: {command}")
        self.change_value('Rob_Action', command)

        # Ожидание ответа (таймаут 30 сек)
        start_time = time.time()
        timeout = 120

        while time.time() - start_time < timeout:
            result = self.read_value("sub_Rob_Action")
            if result == command:
                self.change_value('Rob_Action', 0)
                logging.info(f"Успешно: {command}")
                return True
            elif result == 404:
                logging.error(f"Ошибка выполнения: {command}")
                return False
            time.sleep(1)

        logging.error(f"Таймаут команды: {command}")
        return False
            

    def _send_table_command(self, command, timeout=30):
        """
        Универсальный метод для отправки команд столу
        command: код команды 
            (101 - сдвинуть ложе1, 102 - сдвинуть ложе2, 
            103 - поднять ложе, 104 - опустить ложе)
        timeout: максимальное время ожидания ответа в секундах
        """
        start_time = time.time()
        command_name = {
            101: "Сдвинь плату освободив ложе1",
            102: "Сдвинь плату освободив ложе2",
            103: "Поднять ложе",
            104: "Опустить ложе"
        }.get(command, f"Команда {command}")

        print(f"СТОЛ {self.number} Регул <- {command_name}")
        logging.info(f"СТОЛ {self.number} Отправка команды {'Reg_updown_Botloader' if command in (103, 104) else 'Reg_move_Table'} = {command}")
        
        try: 
            # Отправляем команду
            if command in (103, 104):
                self.change_value('Reg_updown_Botloader', command)
                response_reg = 'sub_Reg_updown_Botloader'
            else:
                self.change_value('Reg_move_Table', command)
                response_reg = 'sub_Reg_move_Table'
            
            # Ожидаем подтверждения
            while time.time() - start_time < timeout:
                result = self.read_value(response_reg)
                
                if result == command:
                    logging.info(f"СТОЛ {self.number} Успешное завершение: команда {command_name} выполнена")
                    return True
                elif result == 404:
                    logging.warning(f"СТОЛ {self.number} От регула получен код 404")
                    raise TableOperationFailed("Ошибка выполнения команды стола")
                
                logging.debug(f"СТОЛ {self.number} Ожидание ответа... Текущее значение: {result}")
                time.sleep(0.5)
            
            # Если дошли сюда - таймаут
            logging.error(f"СТОЛ {self.number} ТАЙМАУТ: Стол не ответил на команду {command}")
            raise TableTimeoutException(f"Стол не ответил за {timeout} сек")
        finally:
            # Всегда сбрасываем команду
            if command in (103, 104):
                self.change_value('Reg_updown_bootloader', 0)
            else:
                self.change_value('Reg_move_Table', 0)
            logging.info(f"СТОЛ {self.number} Команда сброшена")

    def _take_photo(self, max_attempts=3, retry_delay=1):
        """
        Метод для выполнения фотосъемки с обработкой ошибок и повторных попыток
        :param max_attempts: максимальное количество попыток получения фото
        :param retry_delay: задержка между попытками в секундах
        :return: кортеж (result_code, photo_data)
        """
        print(f"2 Стол {self.number} Камера <- сделай фото")
        logging.info(f"Стол {self.number} Камера <- сделай фото")
        
        # Первоначальные попытки получить фото
        for attempt in range(max_attempts):
            try:
                logging.debug(f"Стол {self.number} Попытка {attempt + 1}: запрос фото с камеры")
                res, photodata = CameraSocket.photo()
                print(f"Стол {self.number} С камеры получен ID {photodata}")
                logging.debug(f"Стол {self.number} Успех: получен ID фото {photodata}")
                
                # Если фото получено успешно, возвращаем результат
                if res == 200 and photodata != "NoRead":
                    return res, photodata
                    
            except Exception as e:
                print(f"Ошибка: камера недоступна. Детали: {e}")
                logging.warning(f"Попытка {attempt + 1}: ошибка подключения к камере: {str(e)}")
            
            time.sleep(retry_delay)
        
        # Если фото не получено после попыток, продолжаем ожидание
        while True:
            try:
                res, photodata = CameraSocket.photo()
                logging.debug(f"Стол {self.number} Ожидание фото. Код {res}, данные {photodata}")
                
                if res == 200 and photodata != "NoRead":
                    print(f"Стол {self.number} Фото успешно получено: {photodata}")
                    logging.debug(f"[END] Камера <- сделай фото: {photodata}")
                    return res, photodata
                else:
                    print(f"Стол {self.number} Ошибка получения фото с камеры (код: {res}, данные: {photodata})")
                    logging.warning(f"Стол {self.number} Ошибка получения фото с камеры (код: {res}, данные: {photodata})")
                    
            except Exception as e:
                print(f"Стол {self.number} Ошибка при запросе фото: {e}")
                logging.error(f"Стол {self.number} Ошибка при запросе фото: {str(e)}")
                
            time.sleep(retry_delay)
        
    def start_sewing(self, photodata, loge, max_attempts=1, retry_delay=1):
        """
        Метод для инициализации процесса прошивки с обработкой ошибок
        
        Args:
            photodata: Данные фото (серийный номер)
            loge: Номер ложемента для прошивки
            max_attempts: Максимальное количество попыток (по умолчанию 3)
            retry_delay: Задержка между попытками в секундах (по умолчанию 1)
        
        Returns:
            bool: True если прошивка успешно начата, False в случае ошибки
        
        Raises:
            TableOperationFailed: Если прошивка не удалась после всех попыток
        """
        print(f"СТОЛ {self.number} Сервер <- Начни шить (ложемент {loge})")
        logging.info(f"[START2] Прошивка для стола {self.number}, ложемент {loge}")
        
        # Инициализируем загрузчик прошивки
        firmware_loader = Bot.FirmwareLoader(
            db_connection, 
            igle_table,
            1, 
            Order, 
            photodata, 
            loge
        )
        
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                result = firmware_loader.loader(photodata, loge)
                print(f"Ответ от прошивальщика (попытка {attempt}): {result}")
                logging.debug(f"Ответ от прошивальщика: {result}")
                
                if result == 200:
                    print(f"Прошивка успешно начата для ложемента {loge}")
                    logging.info(f"Прошивка успешно начата для стола {self.number}, ложемент {loge}")
                    return True
                elif result == 404:
                    logging.warning(f"Ошибка 404 от регула (попытка {attempt})")
                    if attempt == max_attempts:
                        raise TableOperationFailed(f"Ошибка прошивки: получен код 404 для ложемента {loge}")
            except Exception as e:
                print(f"Ошибка при запуске прошивки для ложемента {loge}: {e}")
                logging.error(f"Ошибка при запуске прошивки (попытка {attempt}): {str(e)}")
                if attempt == max_attempts:
                    raise TableOperationFailed(f"Не удалось начать прошивку для ложемента {loge} после {max_attempts} попыток")
            
            if attempt < max_attempts:
                time.sleep(retry_delay)
        
        return False
    
    #  # 1. Сдвигаем плату (ложе1)
    #     self._send_table_command(101)
        
    #     # 2. Забираем плату роботом
    #     self._send_robot_command(230)
        
    #     # 3. Сдвигаем плату (ложе2)
    #     self._send_table_command(102)
        
    #     # 4. Забираем плату с ложемента
    #     self._send_robot_command(233)

    


    ####################### DEFENCE START ############################################################
    def defence_robo_cycle(self):
        global photodata
        global Tray1
        Tray1 = 1
        Tray2 = 5
        global Cell1
        global Order
        print(f"[НАЧАЛО] ЦИКЛ DEFENCE для {self.number} стола старт")
        logging.info(f"[НАЧАЛО] ЦИКЛ DEFENCE для {self.number} стола старт")
        ######################################################

        print(f"СТОЛ {self.number} 1 Регул <- Сдвинь плату освободив ложе1.")
        logging.info(f"СТОЛ {self.number} Отправка команды Reg_move_Table = 101")
        self._send_table_command(101)
        time.sleep(1)

        # Робот забери плату
        while not self.rob_manager.acquire(self.number):
            logging.info(f"СТОЛ {self.number} ждет освобождения робота")
            time.sleep(1)  # Подождать 1 секунду

        try:
            print(f"[Начало] Стол {self.number} Захват робота столом")
            logging.info(f"[Начало] Стол {self.number} Захват робота столом")
            print(f"СТОЛ {self.number} 2 Робот <- Забери плату с ложе 1.")
            self._send_robot_command(230, cell_num=1)
            time.sleep(1)
        finally:
            print(f"[Конец] Стол {self.number} Робот освобожден столом")
            logging.info(f"[Конец] Стол {self.number} Робот освобожден столом")
            self.rob_manager.release(self.number)

        print(f"[Начало] Стол {self.number} Регул <- Сдвинь плату освободив ложе2.")
        logging.info(f"[Начало] Стол {self.number} Регул <- Сдвинь плату освободив ложе2.")
        self._send_table_command(102)
        time.sleep(1)
        
        # Робот забери плату
        while not self.rob_manager.acquire(self.number):
            logging.info(f"СТОЛ {self.number} ждет освобождения робота")
            time.sleep(1)  # Подождать 1 секунду

        try:
            print(f"[Начало] Стол {self.number} Захват робота столом")
            logging.info(f"[Начало] Стол {self.number} Захват робота столом")
            print(f"СТОЛ {self.number} 2 Робот <- Забери плату с ложе 1.")
            self._send_robot_command(230, cell_num=2)  # self.number=3
            time.sleep(1)
        finally:
            print(f"[Конец] Стол {self.number} Робот освобожден столом")
            logging.info(f"[Конец] Стол {self.number} Робот освобожден столом")
            self.rob_manager.release(self.number)
    ####################### DEFENCE STOP ############################################################

    ####################### SETUP START ############################################################

    def setup_robo_cycle(self):
        global photodata
        global photodata1
        global Tray1
        global Cell1
        global Order
        print(f"[НАЧАЛО] ЦИКЛ SETUP для {self.number} стола старт")
        logging.info(f"[НАЧАЛО] ЦИКЛ SETUP для {self.number} стола старт")
        ######################################################
        #input("нажми ентер")
        
        # Робот <- Забери плату из тары
        # Сделать фото
        # Робот <- Уложи плату в ложемент тетситрования

        while not self.rob_manager.acquire(self.number):
            logging.info(f"СТОЛ {self.number} ждет освобождения робота")
            time.sleep(1)  # Подождать 1 секунду

        try:
            print(f"[Начало] Стол {self.number} Захват робота столом")
            logging.info(f"[Начало] Стол {self.number} Захват робота столом")

            # 1. Забираем первую плату из тары
            print(f"1 Стол {self.number} Робот <- Забери плату из тары")
            logging.info(f"Стол {self.number} Робот <- Забери плату из тары")
            Cell1 = Cell1 + 1
            if not self._send_robot_command(210):
                raise TableOperationFailed("Ошибка забора первой платы из тары")
            time.sleep(1)
            
            # 2. Фотографируем первую плату
            _, photodata1 = self._take_photo()
            
            # 3. Укладываем первую плату на ложемент 2
            print(f"3 Стол {self.number} Робот <- Уложи плату в ложемент тетситрования 2")
            logging.info(f"3 Стол {self.number} Робот <- Уложи плату в ложемент тетситрования 2")
            if not self._send_robot_command(220, cell_num=2):
                raise TableOperationFailed("Ошибка укладки в ложемент 2")
    
        finally:
            print(f"[Конец] Стол {self.number} Робот освобожден столом")
            logging.info(f"[Конец] Стол {self.number} Робот освобожден столом")
            self.rob_manager.release(self.number)
        print(f"[СТОП] ЦИКЛ SETUP для {self.number} стола старт")
        logging.info(f"[СТОП] ЦИКЛ SETUP для {self.number} стола старт")
    
    ####################### SETUP END ##############################################################
    
    
    ####################### MAIN START ############################################################
    def robo_main_cycle(self):
        global Tray1
        Tray1 = 2
        global Cell1
        global photodata
        global photodata1
        print(f"[НАЧАЛО] ЦИКЛ MAIN для {self.number} стола старт")
        logging.info(f"[НАЧАЛО] ЦИКЛ MAIN для {self.number} стола старт")

        current_loge = 2  # Начинаем с ложемента 2
        # next_photodata = photodata1
        while True:
            try:
                print(f"\n=== Обработка ложемента {current_loge} ===")
            
                # 1. Сдвигаем стол под прошивальщик
                self._send_table_command(101 if current_loge == 1 else 102)
                
                # 2. Опускаем прошивальщик
                self._send_table_command(103)
                
                # 3. Запускаем прошивку (используем фото, сделанное заранее)
                # self.start_sewing(next_photodata, loge=current_loge)
                # Прошивка будет работать в фоне, пока мы готовим следующую плату
                """
                sewing_thread = threading.Thread(
                    target=self.start_sewing, 
                    args=(next_photodata, current_loge)
                )
                sewing_thread.start()
                """

                time.sleep(3)
                print(f"для {self.number}*******************************ШЬЕМ")
                
                
                # 4. Пока шьется на текущем ложементе, готовим следующий
                
                # 4.1 Определяем свободный ложемент
                free_loge = 2 if current_loge == 1 else 1
                
                while not self.rob_manager.acquire(self.number):
                    logging.info(f"СТОЛ {self.number} ждет освобождения робота")
                    time.sleep(1)  # Подождать 1 секунду
                try:
                    # 4.2 Забираем новую плату из тары
                    Cell1 = Cell1 + 1
                    if not self._send_robot_command(210):
                        raise TableOperationFailed("Ошибка забора платы из тары")
                    
                    # 4.3 Фотографируем новую плату
                    _, new_photodata = self._take_photo()
                    
                    # 4.4 Укладываем новую плату на свободный ложемент
                    if not self._send_robot_command(220, cell_num=free_loge):
                        raise TableOperationFailed(f"Ошибка укладки в ложемент {free_loge}")
                finally:
                    print(f"[Конец] Стол {self.number} Робот освобожден столом")
                    logging.info(f"[Конец] Стол {self.number} Робот освобожден столом")
                    self.rob_manager.release(self.number)

                # 5. ЖДЕМ ЗАВЕРШЕНИЯ ПРОШИВКИ
                # sewing_thread.join()  # Ждем окончания прошивки

                # 6. Поднимаем прошивальщик
                self._send_table_command(104)
                
                # 7. Сдвигаем стол для доступа к обработанной плате
                self._send_table_command(102 if current_loge == 1 else 101)
                
                # 8. Забираем обработанную плату и кладем в тару
                while not self.rob_manager.acquire(self.number):
                    logging.info(f"СТОЛ {self.number} ждет освобождения робота")
                    time.sleep(1)

                try:
                    # 8.1 Забираем обработанную плату
                    if not self._send_robot_command(230, cell_num=current_loge):
                        raise TableOperationFailed(f"Ошибка забора с ложемента {current_loge}")
                    
                    # 8.2 Укладываем в тару
                    if not self._send_robot_command(241):
                        raise TableOperationFailed("Ошибка укладки в тару")
                    
                finally:
                    print(f"[Конец] Стол {self.number} Робот освобожден столом")
                    logging.info(f"[Конец] Стол {self.number} Робот освобожден столом")
                    self.rob_manager.release(self.number)
                
                # 9. Подготавливаем данные для следующей итерации
                current_loge = free_loge  # Переключаемся на следующий ложемент
                # next_photodata = new_photodata  # Используем фото новой платы
                
                print(f"Готово! Следующая итерация: ложемент {current_loge}")
                
            except Exception as e:
                logging.error(f"Ошибка в цикле обработки: {str(e)}")
                # Здесь может быть логика восстановления
                time.sleep(5)
       
    ####################### MAIN STOP ############################################################

    def testcycle(self):
        result, photo_id = self._take_photo()
        if result == 200:
            print(f"Успешно получено фото с ID: {photo_id}")
        else:
            print("Не удалось получить фото")

        # self._send_table_command(101)
        # self._send_table_command(102)
        # self._send_table_command(103)
        # self._send_table_command(104)
        
        """
        # 2. Забираем плату роботом
        while not self.rob_manager.acquire(self.number):
            logging.info(f"СТОЛ {self.number} ждет освобождения робота")
            time.sleep(1)  # Подождать 1 секунду

        try:
            self._send_robot_command1(230)  
            self._send_robot_command1(231)
            self._send_robot_command1(232)
        finally:
            self.rob_manager.release(self.number)

        """

    
################################################# STOP TABLE CLASS #####################################################################


    def pause(self):
        time.sleep(2)

    


if __name__ == "__main__":

    modbus_provider = ModbusProvider()
    rob_manager = RobActionManager()
    

    # Создаем и запускаем процесс синхронизации с БД
    db_sync = DatabaseSynchronizer(Order, 1, shared_data)

    url = "opc.tcp://192.168.1.3:48010"
    opc_client = OPCClient(url, 2, shared_data)


    
    """
    # Имитируем изменение данных
    try:
        while True:
            # Меняем значения в shared_data
            shared_data[1]['Reg_move_Table'] = (shared_data[1]['Reg_move_Table'] + 1) % 10
            shared_data[1]['Reg_updown_Botloader'] = (shared_data[1]['Reg_updown_Botloader'] + 1) % 5
            shared_data[1]['Rob_Action'] = (shared_data[1]['Rob_Action'] + 1) % 3
            
            # Меняем глобальные переменные
            Tray1 = (Tray1 + 1) % 2
            Cell1 = (Cell1 + 1) % 4
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("Test stopped")
    """

    # Создаём столы
    table1 = Table("Table1", shared_data, shared_data_lock, 1, rob_manager)
    table2 = Table("Table2", shared_data, shared_data_lock, 2, rob_manager)
    table3 = Table("Table3", shared_data, shared_data_lock, 3, rob_manager)

    # Выполняем однократные методы для каждого стола
    for table in (table1, table2, table3):
        table.defence_robo_cycle()
        table.setup_robo_cycle()

    # Создаем потоки для основного цикла
    thread1 = threading.Thread(target=table1.robo_main_cycle)
    thread2 = threading.Thread(target=table2.robo_main_cycle)
    thread3 = threading.Thread(target=table3.robo_main_cycle)

    # Запускаем потоки
    print('__________________1 стол')
    thread1.start()
    time.sleep(5)

    print('__________________2 стол')
    thread2.start()
    time.sleep(5)

    print('__________________3 стол')
    thread3.start()
    time.sleep(5)

    # Ждем завершения всех потоков
    thread1.join()
    thread2.join()
    thread3.join()

    print("Все потоки завершены.")
    opc_client.stop()


    ################################################# START OPC Communication class l ###################################
    
 

    
