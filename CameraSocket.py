import socket
import logging

# Set up basic logging configuration
logging.basicConfig(
    filename='RTK.log',
    level=logging.INFO,
    format='%(asctime)s - CAM - %(levelname)s - %(message)s'
)


def get_qr_result():
    camera_ip = '192.168.1.50'
    trigger_port = 2001
    camera_port = 2002

    try:
        # Отправка команды "start"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as trigger_socket:
            trigger_socket.connect((camera_ip, trigger_port))
            trigger_socket.sendall(b'start')
            logging.info("Команда 'start' отправлена на порт %d.", trigger_port)

        # Получение QR-результата
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receive_socket:
            receive_socket.connect((camera_ip, camera_port))
            logging.info("Ожидание результата от камеры на порту %d...", camera_port)
            data = receive_socket.recv(1024)  # QR код вряд ли больше
            result = result = data.decode('utf-8').strip().strip(';')  # Удаляет пробелы и ';'
            logging.info("Получен QR результат: %s", result)
            return result if result else None

    except Exception as e:
        logging.error("Ошибка при получении QR: %s", str(e))
        return None

def photo():
    attempts = 3
    results = []

    for i in range(attempts):
        logging.info("Попытка №%d получения QR-кода...", i + 1)
        result = get_qr_result()
        if result:
            results.append(result)

    if not results:
        logging.error("QR-код не получен ни в одной из попыток.")
        QRresult = 404
        return QRresult, None

    unique_results = list(set(results))
    if len(unique_results) == 1:
        logging.info("QR-код стабильно считан: %s", unique_results[0])
        QRresult = 200
        data = unique_results[0]

        return QRresult, data 
    else:
        logging.warning("QR-коды отличаются между попытками: %s", unique_results)
        QRresult = 404
        return QRresult, None
    


# res,data = photo()
# print (f"Result={res}  Data = {data}")
