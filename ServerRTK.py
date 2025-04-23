from flask import Flask, request, jsonify
import logging
import socket

# Глобальная переменная для хранения последних данных
latest_data = None

# Настройка логирования
logging.basicConfig(
    filename='RTK.log',
    level=logging.INFO,
    format='%(asctime)s - ServerRTK - %(levelname)s - %(message)s'
)

app = Flask(__name__)

@app.route('/set_test_results', methods=['POST'])
def set_test_results():
    global latest_data
    try:
        data = request.get_json()

        if not data:
            logging.warning("No JSON data received.")
            return jsonify({"error description": "No data received", "result": "FAIL"}), 404

        logging.info(f"Received data: {data}")
        latest_data = data

        return jsonify({"error description": "All very Good", "result": "OK"})

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return jsonify({"error description": "FAIL", "result": str(e)}), 500


@app.route('/get_test_results', methods=['GET'])
def get_test_results():
    global latest_data
    try:
        if latest_data is None:
            logging.info("No data available to retrieve.")
            return jsonify({"error description": "No data available", "result": "FAIL"}), 404

        data_to_return = latest_data
        latest_data = None  # очищаем после получения

        logging.info("Data retrieved and cleared.")
        return jsonify({"result": "OK", "data": data_to_return})

    except Exception as e:
        logging.error(f"Error retrieving data: {str(e)}")
        return jsonify({"error description": "FAIL", "result": str(e)}), 500


if __name__ == '__main__':
    app.run(host="192.168.1.100", port=5003)  # Можно менять порт/IP при необходимости



