import logging
import time
from datetime import datetime

# Пользовательский класс БД
import SQLite as SQL

# Поьзовательский класс провайдера Иглостола
import ProviderIgleTable as Igable

# Отправка данных в 1С. Сделал этот модуль здесь
import SentLog1C



 # Set up basic logging configuration
logging.basicConfig(
    filename='RTK.log',
    level=logging.INFO,
    format=' %(asctime)s - Botloader - %(levelname)s - %(message)s'
)






################################################# Botloader class ###################################
class FirmwareLoader:
    def __init__(self,db_connection,igle_table,stand_id, Order, photodata, loge):
        try:
            # Создаем экземпляр подключения к базе данных
            self.db_connection = db_connection
            logging.info("Соединение с базой данных установлено")
        except Exception as e:
            logging.error(f"Ошибка при создании подключения с базой данных: {e}")
            raise

        try:
            # Создаем экземпляр провайдера
            self.igle_table = igle_table
            logging.info("Соединение с провайдером Иглостола установлено")
        except Exception as e:
            logging.error(f"Ошибка при создании подключения с провайдером: {e}")
            raise
        self.stand_id = stand_id
        self.Order = Order
        self.photodata = photodata
        self.loge = loge

    def loader(self, photodata, loge):
        print("3 Прошивальщик <- Команда на прошивку")
        
        # Блок начала работы с БД: получаем свободный id для заказа
        try:
            self.db_connection.db_connect()
            # Берем свовобоный заказ
            record_id = self.db_connection.setTable(self.Order, self.stand_id)
            print(f"БД - получили свободный заказ {record_id}")
            if record_id is None:
                print("Свободная запись не найдена")
                return 404, None
            #  получаем для него данные из бд для прошивки
            data = self.db_connection.recievedata(record_id)
            # Если данные были получены, напечатаем их
            if data:
                 print(f"ID: {data['id']}")
                 print(f"Stand ID: {data['stand_id']}")
                 print(f"Module Type: {data['module_type']}")
                 print(f"Data Matrix: {data['data_matrix']}")
                 print(f"Serial Number_8: {data['serial_number_8']}")
                 print(f"Serial Number_9: {data['serial_number_9']}")
                 print(f"Serial Number_15: {data['serial_number_15']}")
                 print(f"Firmware Type: {data['fw_type']}")
                 print(f"Firmware Path: {data['fw_path']}")
                 print(f"Firmware Version: {data['fw_version']}")
                 print(f"Order_number: {data['order_name']}")
            else:
                 print(f"Не удалось получить данные для прошивки")
        except Exception as e:
            logging.error(f"Ошибка при работе с базой данных: {e}")
            print("Ошибка при подключении или получении записи из БД")
            return
        
        # Блок прошивки
        time.sleep(2)
        try:
            print (data, photodata, loge)
            self.igle_table.control_igle_table(data, photodata, loge)
        except Exception as e:
            logging.error(f"Ошибка при контроле через Иглостол: {e}")
            print("Ошибка при контроле через Иглостол")
            return


        resultTest = {}
        loadresult = None

        while True:
            try:
                # Получаем данные о результате от стола через сервер RTK
                resultTest = self.igle_table.recentData()
                
                if not isinstance(resultTest, dict):
                    logging.error(f"Некорректный ответ recentData: {resultTest}")
                    print("Некорректный ответ от Иглостола, ждем дальше")
                    continue
                print("Результат запроса:")

                loadresult = resultTest.get('test_result', None)
                print(f"Результат от IgleTable: {loadresult}")
                
                if loadresult is None:
                    print("Ждем ответ от прошивальщика")
                    time.sleep(2)
                    continue
                
                # Как только получили любой итоговый ответ (True/False) — сразу шлем в 1С
                self.send_log_to_1c_safe(data, resultTest)
                break


            except Exception as e:
                logging.error(f"Ошибка при получении данных от Иглостола: {e}")
                print("Ошибка при получении данных от Иглостола")
                break


        # Обработка данных и запись результатов в БД
        if resultTest.get("test_result") == True:
            # Извлекаем необходимые данные
            data_matrix = resultTest.get("data_matrix")
            log_path = resultTest.get("log_path")
            report_path = resultTest.get("report_path")
            serial_number_8 = resultTest.get("serial_number_8")
            stand_id = resultTest.get("stand_id")
            test_result = resultTest.get("test_result")
            error_description = resultTest.get("error_description")

            try:
                # Записываем результаты прошивки в БД
                self.db_connection.set_BoardTest_Result(record_id, stand_id, serial_number_8, data_matrix, test_result, log_path, report_path, error_description)
                print(f"Результаты прошивки успешно записаны в БД для заказа {record_id}")
                
                # Привязываем Data matrix к серийнику
                self.db_connection.ConnectPhotoSerial(record_id, self.photodata, loadresult)
                print("Привязали Data matrix к серийному номеру")

                
                # Очищаем переменные
                self.cleanup()
                # Если с ошибкой прошивка возращаем статус error_description
                return 200, test_result
            except Exception as e:
                logging.error(f"Ошибка при записи в БД: {e}")
                print("Ошибка при записи в БД")
                # Очищаем переменные
                self.cleanup()
                return 404, test_result
        else:
            print("Ошибка: не удалось получить данные, запись в БД не выполнена.")
            logging.error(f"Ошибка прошивки: {resultTest.get('test_result', 'Неизвестная ошибка')}")

            # Если не удалось, сообщаем роботу переместить в брак
            try:
                log_path = resultTest.get("log_path")
                report_path = resultTest.get("report_path")
                serial_number_8 = resultTest.get("serial_number_8")
                error_description = resultTest.get("error_description") or "Ошибка прошивки"

                self.db_connection.set_BoardTest_Result(
                    record_id, self.stand_id, None, None, "404", log_path, report_path, error_description
                )
                print("Робот, перемести в брак.")
            except Exception as e:
                logging.exception(f"Не удалось записать брак в БД: {e}")
                print("Не удалось записать брак в БД")

            self.cleanup()
            return 500, False
        

    def send_log_to_1c_safe(self, data, resultTest):
        """Отправка лога в 1С. Логи разные взависмоисти от успеха не успеха прошивки. Фомируеются 2 словаря"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            test_result = resultTest.get("test_result", None)
            serial_number = data.get("serial_number_9", "")


            board_info = {
                "board": {
                    "number": serial_number,
                    "tray_number": "123455"
                },
                "operator": "I.Perekalskii",
                "timestamps": {
                    "dm_code_time": now,
                    "firmware_finished_time": now,
                    "board_output_time": now
                }
            }

            common_payload = {
                "rtk_id": "RTK_R050_BoardsIO_1",
                "order": data.get('order_name'),
                "version": data.get('fw_version'),
                "message_type": "firmware_log",
            }

            if test_result == True:
                payload = {
                    **common_payload,
                    "good": [
                        {
                            **board_info,
                            "error": 0
                        }
                    ],
                    "bad": []
                }
                response = SentLog1C.send_success_log(payload)
            else:
                payload = {
                    **common_payload,
                    "good": [],
                    "bad": [
                        {
                            **board_info,
                            "error": 2
                        }
                    ]
                }
                response = SentLog1C.send_unsuccess_log(payload)

            print("Ответ сервера 1С:", response)
            logging.info("Лог в 1С успешно отправлен")
            return True

        except Exception as e:
            logging.exception(f"1С недоступна или ошибка отправки лога: {e}")
            print("1С недоступна, продолжаем без отправки лога")
            return False
        

        

    def cleanup(self):
        # Очищаем перменные после выполнения
        # self.db_connection = None
        # self.igle_table = None
        print("Переменные очищены.")


if __name__ == "__main__":

    """

    ################################################# IgleTable Communication Class ###################################
    
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
    
    try:
            # Create an instance of DatabaseConnection
            db_connection = SQL.DatabaseConnection()
    except Exception as e:
            logging.error(f"Error Create an instance of DatabaseConnection: {e}")
    ################################################# STOP SQL Communication class ###################################

    Order = "ЗНП-2160.1.1"
    photodata = "45654465"
    stand_id = "table_3"
    loge = 1
    firmware_loader = FirmwareLoader(db_connection,igle_table3,stand_id, Order, photodata, loge)
    res = firmware_loader.loader(photodata, loge)
    print (f"***************{res}")


    """
"""
Order = "ЗНП-9087.2.1"
photodata = "45654465"
firmware_loader = FirmwareLoader(db_connection,igle_table,1, Order, photodata)
res = firmware_loader.loader()
print (f"***************{res}")
"""


# Тест отправки данных на прошивку
# igle_table3 = Igable.IgleTable(
#         urlIgleTabeControl=f"http://192.168.1.100:5000/nails_table/start_test_board_with_rtk",
#         urlStatusFromIgleTabe=f"http://192.168.1.100:5003/get_test_results/1")

# db_connection = SQL.DatabaseConnection()
# Order = "ЗНП-241.1.1"
# photodata = "45654465"
# stand_id = "table_3"
# loge = 1
# firmware_loader = FirmwareLoader(db_connection,igle_table3,stand_id, Order, photodata, loge)
# res = firmware_loader.loader(photodata, loge)
# print (f"***************{res}")

####################################################
# Тестирование лога 1С
# firmware_loader = FirmwareLoader(
#         db_connection=None,
#         igle_table=None,
#         stand_id="table_3",
#         Order="ЗНП-37025.1.1",
#         photodata="45654465",
#         loge=1
#     )

# data = {
#         "order_name": "ЗНП-37025.1.1",
#         "fw_version": "1.0.0"
#     }

# resultTest = {
#         "status_code": "OK",
#         "serial_number_8": "Z01745814T",
#         "error_description": 1
#     }

# res = firmware_loader.send_log_to_1c_safe(data, resultTest)
# print("Результат вызова:", res)