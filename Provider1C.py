import requests
import json
import logging
import sqlite3
from datetime import datetime


# Настройка логирования
logging.basicConfig(
    filename='RTK.log',  # Файл для логирования
    level=logging.INFO,           # Уровень логирования
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
)







# Функция для логина
def login(username, password):
    logging.info(f"Provider1C - Attempting login with username: {username}")  # Логируем попытку логина
    url = "http://127.0.0.1:5000/login"
    payload = json.dumps({
        "username": username,
        "password": password
    })
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        logging.info(f"Provider1C - Login successful for username: {username}")  # Логируем успешный логин
        print("Login successful")
    else:
        logging.error(f"Provider1C - Login failed for username: {username}. Response: {response.text}")  # Логируем ошибку при логине
        print(f"Login failed: {response.text}")
    
    return response.cookies  # Возвращаем cookies для использования в дальнейшем

#######################################################
# Функция для получения заказов (Запрос перечня ЗНП)
def get_orders(cookies):
    logging.info(f"Provider1C - Fetching orders with cookies: {cookies}")  # Логируем запрос заказов
    url = "http://127.0.0.1:5000/orders"
    headers = {'Cookie': f'session={cookies["session"]}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        logging.info(f"Provider1C - Orders fetched successfully: {response.json()}")  # Логируем успешный запрос заказов
        print("Orders:", response.json())
    else:
        logging.error(f"Provider1C - Failed to get orders. Response: {response.text}")  # Логируем ошибку при получении заказов
        print(f"Failed to get orders: {response.text}")
    
    return response.json()
#######################################################


#######################################################
# Функция для получения деталей заказа Получение деталей ЗНП в формате номер номенклатура и тд
def get_order_details(order_id, cookies):
    logging.info(f"Provider1C - Fetching details for order {order_id} with cookies: {cookies}")  # Логируем запрос деталей заказа
    url = f"http://127.0.0.1:5000/order/{order_id}"
    headers = {'Cookie': f'session={cookies["session"]}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        logging.info(f"Provider1C - Order {order_id} details fetched successfully: {response.json()}")  # Логируем успешный запрос деталей
        print(f"Order {order_id} details:", response.json())
    else:
        logging.error(f"Provider1C - Failed to get details for order {order_id}. Response: {response.text}")  # Логируем ошибку
        print(f"Failed to get details for order {order_id}: {response.text}")
    
    return response.json()
#######################################################

#######################################################
# Функция для проверки серийного номера в заказе Sn для валидации с ЕРП
def check_order(order_id, serial_number, cookies):
    logging.info(f"Provider1C - Checking order {order_id} with serial number {serial_number} using cookies: {cookies}")  # Логируем запрос на проверку
    url = "http://127.0.0.1:5000/check_order"
    payload = json.dumps({
        "order_id": order_id,
        "serial_number": serial_number
    })
    headers = {'Content-Type': 'application/json', 'Cookie': f'session={cookies["session"]}'}
    
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        logging.info(f"Provider1C - Serial number {serial_number} found in order {order_id}: {response.json()}")  # Логируем успешную проверку
        print(response.text)
    else:
        logging.error(f"Provider1C - Failed to check order {order_id} with serial number {serial_number}. Response: {response.text}")  # Логируем ошибку
        print(response.text)

#######################################################
# Лог в 1С. Все нормально прошил
def mark_order_to1C(cookies):
    logging.info(f"Provider1C - Marking order as 'to1C' using cookies: {cookies}")  # Логируем запрос маркировки
    url = "http://127.0.0.1:5000/mark_order/to1C"
    headers = {'Cookie': f'session={cookies["session"]}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        logging.info(f"Provider1C - Order marked as 'to1C' successfully: {response.text}")  # Логируем успешную маркировку
        print(response.text)
    else:
        logging.error(f"Provider1C - Failed to mark order as 'to1C'. Response: {response.text}")  # Логируем ошибку при маркировке
        print(response.text)
#######################################################


#######################################################
# Лог из 1С ЕРП. Все хорошо принято
def mark_order_from1C(cookies):
    logging.info(f"Provider1C - Marking order as 'from1C' using cookies: {cookies}")  # Логируем запрос маркировки
    url = "http://127.0.0.1:5000/mark_order/from1C"
    headers = {'Cookie': f'session={cookies["session"]}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        logging.info(f"Provider1C - Order marked as 'from1C' successfully: {response.text}")  # Логируем успешную маркировку
        print(response.text)
    else:
        logging.error(f"Provider1C - Failed to mark order as 'from1C'. Response: {response.text}")  # Логируем ошибку при маркировке
        print(response.text)
#######################################################





# Пример вызова всех функций

# 1. Логин
cookies = login('user1', 'password123')  # Пример логина с правильными данными

# 2. Получение заказов
get_orders(cookies)

"""

# 3. Получение деталей заказа
get_order_details(558, cookies)

# 4. Проверка наличия серийного номера в ЕРП
check_order(558, 'SN1234', cookies)

# 5. Лог в 1С ЕРП'
mark_order_to1C(cookies)

# 6. Ответ от 1С'
mark_order_from1C(cookies)

"""
