"""Связь с базой данных сделана классом"""
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
                    FOREIGN KEY (order_number) REFERENCES orders(order_number) ON DELETE CASCADE
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

    
    def getOrders(self):
        """ Запрос заказов всех """
        logging.info("Method 2 called.")
        print("Method 2")

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
# Instantiate the class and call methods
if __name__ == "__main__":
    try:
        # Create an instance of DatabaseConnection
        db_connection = DatabaseConnection()

        # Connect to the database and create tables
        db_connection.db_connect()

        # Call the methods that print to the console
        db_connection.method_1()
        db_connection.method_2()
        db_connection.method_3()
        db_connection.method_4()

        # Close the connection
        db_connection.close_connection()
    except Exception as e:
        logging.error(f"Error in main execution: {e}")

"""


