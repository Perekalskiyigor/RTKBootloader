"""Связь с базой данных сделана классом"""
import datetime
import sqlite3
import logging

class DatabaseConnection:
    def __init__(self):
        # Initialize the connection
        self.conn = sqlite3.connect('orders.db')
        self.cursor = self.conn.cursor()
        
        # Set up basic logging configuration
        logging.basicConfig(
            filename='RTK.log',
            level=logging.INFO,
            format='%(asctime)s - SQLite - %(levelname)s - %(message)s'
        )
        logging.info("Database connection initialized.")

    def db_connect(self):
        """ Connect to the database and create tables """
        logging.info("Attempting to create tables in the database.")
        try:
            self.cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    order_number TEXT NOT NULL UNIQUE,
                    module TEXT NOT NULL
                );
            ''')
            logging.info("Orders table checked/created.")

            self.cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS order_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT NOT NULL,
                    serial_number TEXT NOT NULL,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_sent TIMESTAMP,
                    status INTEGER,
                    desk_id INTEGER,
                    firmware_link TEXT NOT NULL,
                    test_result TEXT,
                    report_path  TEXT,
                    log_path    TEXT,
                    error_description TEXT,      
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                );
            ''')
            logging.info("Order details table checked/created.")

            self.conn.commit()
            logging.info("Database connected and tables created successfully.")
        except Exception as e:
            logging.error(f"Error occurred while creating tables: {e}")
            raise

    
    def camera_photo(self, QRresult, serial_id):
        """Добавление данных по штрих коду с камеры в базу"""
    
        logging.info("Method camera_photo called.")
        print("Method 1")
        # Update the record
        self.cursor.execute('''
            UPDATE order_details 
            SET data_matrix = ? 
            WHERE serial_number_8 = ?
        ''', (QRresult, serial_id))

        # Check if any row was updated
        if self.cursor.rowcount == 0:
            print(f"Error: No record found with Serial = {serial_id}")
        else:
            # Commit changes if the update was successful
            self.conn.commit()
            print(f"Successfully updated record with Serial = {serial_id}")

    
    def setOrder(self, order_number, Module, Nomeclature, Value, Version_Loader, QRresult, serial_number_8):
        """ Запрос заказов всех """
        logging.info("Sent Order in DB")
        print("Method 1")
        current_time = datetime.now()
        # Update the record
        self.cursor.execute('''
            INSERT INTO order_details (
                time_added,
                order_number, 
                module, 
                nomenclature, 
                value, 
                version_loader, 
                data_matrix, 
                serial_number_8
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_time,
            order_number, 
            Module, 
            Nomeclature, 
            Value, 
            Version_Loader, 
            QRresult, 
            serial_number_8
        ))

        # Check if any row was updated
        if self.cursor.rowcount == 0:
            print(f"Error: No record found with Serial = {serial_number_8}")
        else:
            # Commit changes if the update was successful
            self.conn.commit()
            print(f"Successfully updated record with Serial = {serial_number_8}")

        print("Method 2")

    def setBoard(self,
            date_added,
            order_id,
            stand_id,
            serial_number_8,
            data_matrix,
            ERPMatrix,
            fw_type,
            fw_path,
            date_sent,
            stand_status,
            logStend,
            hard_stopToStand):

        try:
            self.cursor.execute('''
                INSERT INTO order_details (
                    date_added,
                    order_id, 
                    stand_id, 
                    serial_number_8, 
                    data_matrix, 
                    ERPMatrix, 
                    fw_type, 
                    fw_path,
                    date_sent,
                    stand_status,
                    logStend,
                    hard_stopToStand
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_added,
                order_id,
                stand_id,
                serial_number_8,
                data_matrix,
                ERPMatrix,
                fw_type,
                fw_path,
                date_sent,
                stand_status,
                logStend,
                hard_stopToStand
            ))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error inserting board: {e}")
            print(f"Error inserting record: {e}")

            print("Method 2")
    
    
    
    def setTable(self, order_number):
        """Поиск заказа и обновление одной записи в order_details."""
        logging.info("Метод setTable вызван с order_number = %s", order_number)
        print(f"Метод setTable вызван с order_number = {order_number}")

        # Получаем ID заказа
        self.cursor.execute('''
            SELECT id
            FROM orders
            WHERE order_number = ?
            ORDER BY id DESC
            LIMIT 1
        ''', (order_number,))
        row = self.cursor.fetchone()

        if not row:
            logging.warning("Заказ с номером %s не найден.", order_number)
            print(f"Заказ с номером {order_number} не найден.")
            return None

        order_id = row[0]
        logging.info("Найден ID заказа: %s", order_id)
        print(f"Найден ID заказа: {order_id}")

        # Ищем свободную строку в order_details
        self.cursor.execute('''
            SELECT id
            FROM order_details
            WHERE order_id = ? AND (stand_id IS NULL OR stand_id = 0)
            ORDER BY id ASC
            LIMIT 1
        ''', (order_id,))
        row = self.cursor.fetchone()

        if not row:
            logging.warning("Нет свободных записей в order_details для order_id = %s", order_id)
            print(f"Нет свободных записей в order_details для order_id = {order_id}")
            return None

        serial_id = row[0]
        logging.info("Найдена свободная запись в order_details: id = %s", serial_id)
        print(f"Найдена свободная запись в order_details: id = {serial_id}")

        try:
            self.conn.execute('BEGIN IMMEDIATE')  # Начинаем транзакцию с блокировкой
            self.cursor.execute('''
                UPDATE order_details
                SET stand_id = "nt_kto_rtk_1"
                WHERE id = ?
            ''', (serial_id,))

            if self.cursor.rowcount > 0:
                self.conn.commit()
                logging.info("Запись успешно обновлена: order_details.id = %s", serial_id)
                print(f"Заблокирована и обновлена запись order_details.id = {serial_id}")
                return serial_id
            else:
                self.conn.rollback()
                logging.warning("Обновление не затронуло ни одной строки.")
                print("Свободных записей не найдено.")
                return None

        except Exception as e:
            self.conn.rollback()
            logging.exception("Ошибка при обновлении записи order_details: %s", e)
            print(f"Ошибка при обновлении записи order_details: {e}")
            return None
        
    
    
    def ConnectPhotoSerial(self, record_id, photodata, loadresult):
        """ Связываем серийный номер и штрихкод на плате с результатом теста и фото """
        try:
            logging.info("Method ConnectPhotoSerial called.")
            #print("Method ConnectPhotoSerial called.")
            
            logging.debug(f"Input parameters: record_id={record_id}, loadresult={loadresult}, photodata=[{len(photodata)} bytes]")
            #print(f"Input parameters: record_id={record_id}, loadresult={loadresult}, photodata={photodata}")

            update_query = """
            UPDATE order_details
            SET test_result = ?,
                data_matrix = ?
            WHERE id = ?
            """
            logging.debug(f"Executing SQL with values: ({loadresult}, [photodata], {record_id})")
            #print(f"Executing SQL with values: ({loadresult}, [photodata], {record_id})")
            
            self.cursor.execute(update_query, (loadresult, photodata, record_id))
            self.conn.commit()

            if self.cursor.rowcount == 0:
                logging.warning(f"No record found with id={record_id}.")
                print(f"No record found with id={record_id}.")
                return 404  # Запись не найдена

            logging.info(f"Record {record_id} successfully updated.")
            #print(f"Record {record_id} successfully updated.")
            return 200  # Успех

        except Exception as e:
            logging.error(f"Failed to update record {record_id}: {e}", exc_info=True)
            print(f"Failed to update record {record_id}: {e}")
            return 404  # Ошибка выполнения



    
    
    def getBoard_id(self, order_number):
        """ Запрос заказов всех """
        logging.info("Method 2 called.")
        # Делаем с блокировкой записи
        self.cursor.execute('''
                    SELECT 
                        O.order_number, 
                        D.id, 
                        D.stand_id,
                        D.serial_number_8,
                        D.data_matrix, 
                        D.ERPMatrix, 
                        D.fw_type,
                        D.fw_path,
                        D.date_sent,
                        D.test_result
                    FROM orders AS O
                    JOIN order_details AS D ON O.id = D.order_id
                    WHERE D.test_result <> 200 OR D.test_result IS NULL AND O.order_number = ?
                    ORDER BY id DESC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
        ''', (order_number,))

        row = self.cursor.fetchone()

        if row:
            order_id = row[1]  # D.id
            print(f"Запись {order_id} занята успешно.")
        
        
    

    

    def set_BoardTest_Result(self, record_id, stand_id, serial_number_8, data_matrix, test_result, log_path, report_path, error_description):
        """ Установка результатов тестирования вызывается от Сервер РТК """
        logging.info(f"[RTK] Вызов метода set_BoardTest_Result для записи ID: {record_id}")
        print(f"[RTK] Установка результатов тестирования для записи ID: {record_id}")
        
        try:    
            update_query = """
            UPDATE order_details
            SET stand_id = ?,
                serial_number_8 = ?,
                data_matrix = ?,
                test_result = ?,
                log_path = ?,
                report_path = ?,
                error_description = ?
            WHERE id = ?
            """
            # Отладочная информация
            logging.debug(f"SQL: {update_query.strip()}")
            logging.debug(f"SQL values: ({stand_id}, {serial_number_8}, {data_matrix}, {test_result}, {log_path}, {report_path}, {record_id},{error_description})")
            print(f"[DB] Выполнение запроса с параметрами: ({stand_id}, {serial_number_8}, {data_matrix}, {test_result}, {log_path}, {report_path}, {record_id},{error_description})")

            # Выполнение запроса
            self.cursor.execute(update_query, (stand_id, serial_number_8, data_matrix, test_result, log_path, report_path, error_description, record_id))
            self.conn.commit()

            
            # Консольный вывод
            print("[DB]  Данные успешно сохранены:")
            print(f"   - stand_id: {stand_id}")
            print(f"   - serial_number_8: {serial_number_8}")
            print(f"   - data_matrix: {data_matrix}")
            print(f"   - test_result: {test_result}")
            print(f"   - log_path: {log_path}")
            print(f"   - report_path: {report_path}")

            # Логирование
            logging.info(" Данные успешно сохранены в базу:")
            logging.info(f"   - stand_id: {stand_id}")
            logging.info(f"   - serial_number_8: {serial_number_8}")
            logging.info(f"   - data_matrix: {data_matrix}")
            logging.info(f"   - test_result: {test_result}")
            logging.info(f"   - log_path: {log_path}")
            logging.info(f"   - report_path: {report_path}")

        except Exception as e:
            error_msg = f"[DB] Ошибка при сохранении в базу: {e}"
            print(error_msg)
            logging.error(error_msg)
            raise


        


        

    def get_order_insert_orders_frm1C(self, dictResult):
        """ Запрос информации по заказам и вставка данных в таблицы Orders и order_details """
        order_id = dictResult.get('order_id')
        components = dictResult.get('components', {})
        products = dictResult.get('products', {})
        firmware = products.get('firmware', '')
        board_name = products.get('board_name', None)
        batch = products.get('batch', {})
        count = products.get('count', 0)
        version = products.get('version', None)
        marking_templates = products.get('marking_templates', [])

        logging.info("Метод get_order_insert_orders_frm1C вызван.")
        logging.info(f"Входные данные - order_id: '{order_id}', board_name: '{board_name}', firmware: '{firmware}' count {count} version {version} components {components}")

        # Валидация входных данных
        if not order_id or not board_name or not firmware:
            logging.warning("Отсутствуют обязательные данные: order_id, board_name или firmware.")
            print("Ошибка: Отсутствуют обязательные данные.")
            return

        if not isinstance(batch, list) or not batch:
            logging.warning("Некорректные или пустые данные batch.")
            print("Ошибка: Некорректные или пустые данные batch.")
            return

        try:
            # Шаг 1: Вставка данных заказа в таблицу Orders
            logging.info("Вставка данных заказа в таблицу Orders.")
            self.cursor.execute('''
                INSERT INTO Orders (order_number, module, Nomenclature, Value, VersionLoadFile, fw_version, marking_templates)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, board_name, components, count, firmware, version, marking_templates))
            self.conn.commit()

            # Получение ID вставленного заказа
            self.cursor.execute('SELECT last_insert_rowid()')
            inserted_order_id = self.cursor.fetchone()[0]
            logging.info(f"Заказ вставлен с ID: {inserted_order_id}")


            for item in batch:
                serial = item["number"]
                serial_8 = item["number8"]
                serial_15 = item["number15"]
                self.cursor.execute('''
                    INSERT INTO order_details (order_id, serial_number, serial_number_8, serial_number_15)
                    VALUES (?, ?, ?, ?)
                ''', (inserted_order_id, serial, serial_8, serial_15))
                self.conn.commit()

            logging.info("Заказ и его детали успешно вставлены.")
            print("Заказ и его детали успешно вставлены.")

        except sqlite3.Error as e:
            logging.error(f"Ошибка SQLite при вставке данных: {e}")
            print(f"Ошибка SQLite: {e}")
            self.conn.rollback()

    
    def recievedata(self, id):
        """Запрос данных для прошивки по ID"""
        logging.info("Вызван метод recievedata: запрос данных для прошивки из базы данных")

        query = """
            SELECT 
                S.id,
                S.stand_id,
                O.module AS module_type,
                S.data_matrix,
                S.serial_number_8,
                S.fw_type,
                O.VersionLoadFile AS fw_path,
                O.fw_version
            FROM order_details AS S
            JOIN Orders AS O ON O.id = S.order_id
            WHERE S.id = ?
        """

        try:
            cur = self.conn.cursor()
            logging.debug("Выполняется SQL-запрос получения данных для ID: %s", id)
            cur.execute(query, (id,))
            result = cur.fetchone()

            if result is None:
                logging.warning("Данные по ID %s не найдены", id)
                return None

            (order_id, stand_id, module_type, data_matrix, serial_number_8,
            fw_type, fw_path, fw_version) = result

            logging.info("Данные успешно получены для ID: %s", id)
            logging.debug("Результаты: stand_id=%s, module_type=%s, fw_path=%s",
                        stand_id, module_type, fw_path)

            return {
                'id': order_id,
                'stand_id': stand_id,
                'module_type': module_type,
                'data_matrix': data_matrix,
                'serial_number_8': serial_number_8,
                'fw_type': fw_type,
                'fw_path': fw_path,
                'fw_version': fw_version
            }

        except sqlite3.Error as e:
            logging.error("SQLite ошибка в recievedata: %s", str(e))
            return None
        
    # Получение данных из базы для интерфейса ОПС
    def getDatafromOOPC(self, order_number):
        logging.info("OPC Метод получения данных для ОПС запущен")

        try:
            self.cursor.execute('''
                SELECT 
                    O.ID
                FROM orders AS O
                WHERE O.order_number = ?
                ORDER BY O.order_number DESC
            ''', (order_number,))

            row = self.cursor.fetchone()

            if row:
                order_id = row[0]
                logging.info(f"OPC Данные по заказу '{order_number}' получены успешно.")
            else:
                logging.warning(f"OPC Заказ с номером '{order_number}' не найден в базе данных.")

        except Exception as e:
            logging.error(f"OPC Ошибка при получении данных по заказу '{order_number}': {e}", exc_info=True)
            return None

        try:
            self.cursor.execute('''
                SELECT 
                    O.order_number,
                    O.module,
                    O.fw_version, 
                    COUNT(*) FILTER (WHERE D.stand_id IS NULL) AS Lastcount,
                    COUNT(D.id) AS CommonCount,
                    COUNT(*) FILTER (WHERE D.report_path IS NOT NULL) AS Sucesscount,
                    COUNT(*) FILTER (WHERE D.log_path IS NOT NULL) AS NonSucesscount
                FROM orders AS O
                JOIN order_details AS D ON O.id = D.order_id
                WHERE D.order_id = ?
                GROUP BY O.order_number, O.module, O.fw_version
                ORDER BY O.order_number DESC
            ''', (order_id,))

            row = self.cursor.fetchone()

            if row:
                order_number = row[0]
                module = row[1]
                fw_version = row[2]
                last_count = row[3]
                common_count = row[4]
                success_count = row[5]
                nonsuccess_count = row[6]

                logging.info(f"OPC Данные по заказу '{order_number}' получены успешно.")
                return order_number, module, fw_version, last_count, common_count, success_count, nonsuccess_count
            else:
                logging.warning(f"OPC Заказ с номером '{order_number}' не найден в базе данных.")
                return None

        except Exception as e:
            logging.error(f"OPC Ошибка при получении данных по заказу '{order_number}': {e}", exc_info=True)
            return None

        
        
    def close_connection(self):
        """ Close the connection to the database """
        logging.info("Closing database connection.")
        self.conn.close()
        logging.info("Database connection closed.")


    




"""
# Create an instance of DatabaseConnection
db_connection = DatabaseConnection()
Order = "ЗНП-0005747"
record_id = db_connection.setTable(Order)

"""

"""
# Create an instance of DatabaseConnection
db_connection = DatabaseConnection()
res = db_connection.recievedata(464)
print(res)
"""


"""
# Проверка функции OPC
db_connection = DatabaseConnection()
result = db_connection.getDatafromOOPC('ЗНП-2160.1.1')

if result:
    order_number, module, fw_version, last_count, common_count, success_count, nonsuccess_count = result

    print(f"Номер заказа: {order_number}")
    print(f"Модуль: {module}")
    print(f"Версия ПО: {fw_version}")
    print(f"Количество оставшихся: {last_count}")
    print(f"Общее количество записей: {common_count}")
    print(f"С успешным report_path: {success_count}")
    print(f"С успешным log_path: {nonsuccess_count}")
else:
    print("Данные по заказу не найдены или произошла ошибка.")
"""
