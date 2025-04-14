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

    
    def camera_photo(self, QRresult, serial_number_8):
        """Добавление данных по штрих коду с камеры в базу"""
    
        logging.info("Method camera_photo called.")
        print("Method 1")
        # Update the record
        self.cursor.execute('''
            UPDATE order_details 
            SET data_matrix = ? 
            WHERE serial_number_8 = ?
        ''', (QRresult, serial_number_8))

        # Check if any row was updated
        if self.cursor.rowcount == 0:
            print(f"Error: No record found with Serial = {serial_number_8}")
        else:
            # Commit changes if the update was successful
            self.conn.commit()
            print(f"Successfully updated record with Serial = {serial_number_8}")

    
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
    
    def getBoard_id(self, order_number):
        """ Запрос заказов всех """
        logging.info("Method 2 called.")
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
        ''', (order_number,))

        row = self.cursor.fetchone()

        if row:
            record_id = row[1]  # D.id
            print(f"Найдена запись для order_number '{order_number}', id: {record_id}")
        return record_id
    

    def set_TableForBoard(self, new_stand_id ,record_id):
        """ Запрос заказов всех """
        logging.info("Method 2 called.")
        update_query = """
        UPDATE order_details
        SET test_result = 0,
            stand_id = ?
        WHERE id = ?
        """
        self.cursor.execute(update_query, (new_stand_id, record_id))
        self.conn.commit()

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




# Create an instance of DatabaseConnection
db_connection = DatabaseConnection()

# Connect to the database and create tables
db_connection.db_connect()

# Call the methods that print to the console
record_id = db_connection.getBoard_id("ЗНП-0005747")

# Назначаем стол плате по id записи
new_stand_id = 1
db_connection.set_TableForBoard(new_stand_id ,record_id)

result = 500

db_connection.set_BoardTest_Result(result, record_id)