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
                    test_result INTEGER,
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
                SET stand_id = 1
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
            print("Method ConnectPhotoSerial called.")
            
            logging.debug(f"Input parameters: record_id={record_id}, loadresult={loadresult}, photodata=[{len(photodata)} bytes]")
            print(f"Input parameters: record_id={record_id}, loadresult={loadresult}, photodata={photodata}")

            update_query = """
            UPDATE order_details
            SET test_result = ?,
                data_matrix = ?
            WHERE id = ?
            """
            logging.debug(f"Executing SQL with values: ({loadresult}, [photodata], {record_id})")
            print(f"Executing SQL with values: ({loadresult}, [photodata], {record_id})")
            
            self.cursor.execute(update_query, (loadresult, photodata, record_id))
            self.conn.commit()

            if self.cursor.rowcount == 0:
                logging.warning(f"No record found with id={record_id}.")
                print(f"No record found with id={record_id}.")
                return 404  # Запись не найдена

            logging.info(f"Record {record_id} successfully updated.")
            print(f"Record {record_id} successfully updated.")
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
        
        
    

    

    def set_BoardTest_Result(self, result, record_id):
        """ Запрос заказов всех """
        logging.info("Method 2 called.")
        update_query = """
        UPDATE order_details
        SET test_result = ?
        WHERE id = ?
        """
        self.cursor.execute(update_query, (result, record_id))
        self.conn.commit()
        


        

    def get_order_detail(self):
        """ Запрос информации по заказам """
        logging.info("Method 3 called.")
        print("Method 3")
    
    
    
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

db_connection = DatabaseConnection()
db_connection.ConnectPhotoSerial(1, "VD4454564646", 200)