import logging


logging.basicConfig(
            filename='./retyeyery.log',  # Убедитесь, что путь правильный
            level=logging.INFO,
            format='%(asctime)s - SQLite - %(levelname)s - %(message)s',
            encoding='utf-8'  # Убедитесь, что кодировка указана
        )