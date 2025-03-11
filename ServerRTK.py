"""Действущий сервак. на него иглостол возвращает данные о прошивки"""
from flask import Flask, request, jsonify
import logging

# Настройка логирования
logging.basicConfig(
    filename='RTK.log',  # Лог будет записываться в этот файл
    level=logging.INFO,  # Уровень логирования: INFO, WARNING, ERROR и т.д.
    format='%(asctime)s - ServerRTK - %(levelname)s - %(message)s'  # Формат записи
)

app = Flask(__name__)

@app.route('/set_test_results', methods=['POST'])
def set_test_results():
    try:
        # Получаем данные из запроса
        data = request.get_json()

        # Логируем полученные данные
        logging.info(f"Received data: {data}")

        # Обработка данных (например, сохранить в базу данных, выполнить тесты и т.д.)
        stand_id = data.get("stand_id")
        serial_number_8 = data.get("serial_number_8")
        data_matrix = data.get("data_matrix")
        test_result = data.get("test_result")
        log_path = data.get("log_path")
        report_path = data.get("report_path")

        # Логируем полученные данные
        logging.info(f"stand_id: {stand_id}")
        logging.info(f"serial_number_8: {serial_number_8}")
        logging.info(f"data_matrix: {data_matrix}")
        logging.info(f"test_result: {test_result}")
        logging.info(f"log_path: {log_path}")
        logging.info(f"report_path: {report_path}")

        # Формируем ответ
        response = {
            "error description": "All very Good",
            "result": "OK"
        }

        # Логируем ответ
        logging.info(f"Sending response: {response}")

        # Возвращаем ответ клиенту
        return jsonify(response)

    except Exception as e:
        # Логируем ошибку, если она произошла
        logging.error(f"Error occurred: {str(e)}")

        # В случае ошибки возвращаем информацию о ней
        return jsonify({"error description": "FAIL", "result": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
