import logging
import time

# Пользовательский класс БД
import SQLite as SQL

# Поьзовательский класс провайдера Иглостола
import ProviderIgleTable as Igable



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
            record_id = self.db_connection.setTable(self.Order)
            print(f"БД - получили свободный заказ {record_id}")
            #  получаем для него данные из бд для прошивки
            data = self.db_connection.recievedata(record_id)
            # Если данные были получены, напечатаем их
            # if data:
            #     print(f"ID: {data['id']}")
            #     print(f"Stand ID: {data['stand_id']}")
            #     print(f"Module Type: {data['module_type']}")
            #     print(f"Data Matrix: {data['data_matrix']}")
            #     print(f"Serial Number: {data['serial_number_8']}")
            #     print(f"Firmware Type: {data['fw_type']}")
            #     print(f"Firmware Path: {data['fw_path']}")
            #     print(f"Firmware Version: {data['fw_version']}")
            # else:
            #     print(f"Не удалось получить данные для прошивки")
        except Exception as e:
            logging.error(f"Ошибка при работе с базой данных: {e}")
            print("Ошибка при подключении или получении записи из БД")
            return
        
        # Блок прошивки
        time.sleep(2)
        try:
            self.igle_table.control_igle_table(data, photodata, loge)
        except Exception as e:
            logging.error(f"Ошибка при контроле через Иглостол: {e}")
            print("Ошибка при контроле через Иглостол")
            return
        
        while True:
            try:
                # Получаем данные о результате от стола через сервер RTK
                resultTest = self.igle_table.recentData()
                print("Результат запроса:")

                loadresult = resultTest.get('status_code', 'ERROR')
                print(f"Результат от IgleTable: {loadresult}")
                
                if loadresult != "OK":
                    print("Ждем ответ от прошивальщика")
                else:
                    break
                time.sleep(1)
            except Exception as e:
                logging.error(f"Ошибка при получении данных от Иглостола: {e}")
                print("Ошибка при получении данных от Иглостола")
                break

        # Обработка данных и запись результатов в БД
        if resultTest.get("status_code") == "OK":
            # Извлекаем необходимые данные
            data_matrix = resultTest.get("data_matrix")
            log_path = resultTest.get("log_path")
            report_path = resultTest.get("report_path")
            serial_number_8 = resultTest.get("serial_number_8")
            stand_id = resultTest.get("stand_id")
            test_result = resultTest.get("status_code")
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
                return 200
            except Exception as e:
                logging.error(f"Ошибка при записи в БД: {e}")
                print("Ошибка при записи в БД")
                # Очищаем переменные
                self.cleanup()
                return 404
        else:
            print("Ошибка: не удалось получить данные, запись в БД не выполнена.")
            logging.error(f"Ошибка прошивки: {resultTest.get('error_description', 'Неизвестная ошибка')}")

            # Если не удалось, сообщаем роботу переместить в брак
            self.db_connection.set_BoardTest_Result(record_id, None, None, None, "404", None, None, "Ошибка прошивки")
            print("Робот, перемести в брак.")
            self.cleanup()
            return 500

        

    def cleanup(self):
        # Очищаем перменные после выполнения
        self.db_connection = None
        self.igle_table = None
        print("Переменные очищены.")

"""
if __name__ == "__main__":
    ################################################# IgleTable Communication Class ###################################
    
    igle_table = Igable.IgleTable(
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
    ################################################# IgleTable Communication Class ###################################


    ################################################# START SQL Communication class ###################################
    
    try:
            # Create an instance of DatabaseConnection
            db_connection = SQL.DatabaseConnection()
    except Exception as e:
            logging.error(f"Error Create an instance of DatabaseConnection: {e}")
    ################################################# STOP SQL Communication class ###################################

    Order = "ЗНП-0005747"
    photodata = "45654465"
    firmware_loader = FirmwareLoader(db_connection,igle_table,1, Order, photodata)
    res = firmware_loader.loader()
    print (f"***************{res}")
"""


"""
Order = "ЗНП-9087.2.1"
photodata = "45654465"
firmware_loader = FirmwareLoader(db_connection,igle_table,1, Order, photodata)
res = firmware_loader.loader()
print (f"***************{res}")
"""

