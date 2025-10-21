from flask import Flask, request, jsonify
import logging
import socket

import threading
import os
import time

# Глобальная переменная для хранения последних данных
latest_data = None
# Хранилище данных для каждого стенда
latest_data_by_stand = {}

# Настройка логирования
logging.basicConfig(
    filename='RTK.log',
    level=logging.INFO,
    format='%(asctime)s - ServerRTK - %(levelname)s - %(message)s'
)

app = Flask(__name__)

@app.route('/set_test_results', methods=['POST'])
def set_test_results():
    try:
        data = request.get_json()

        if not data:
            logging.warning("No JSON data received.")
            return jsonify({"error description": "No data received", "result": "FAIL"}), 400

        logging.info(f"Received data: {data}")

        stand_id = data.get("stand_id")
        if not stand_id:
            logging.warning("Missing 'stand_id' in the request.")
            return jsonify({"error description": "Missing stand_id", "result": "FAIL"}), 400

        latest_data_by_stand[stand_id] = data
        logging.info(f"Data stored for stand_id: {stand_id}")

        return jsonify({"error description": "All very Good", "result": "OK"})

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return jsonify({"error description": "FAIL", "result": str(e)}), 500


@app.route('/get_test_results/1', methods=['GET'])
def get_test_results1():
    try:
        stand_id = f"table_1"
        data = latest_data_by_stand.get(stand_id)

        if not data:
            logging.info(f"No data available for stand_id: {stand_id}")
            return jsonify({"error description": "No data available", "result": "FAIL"}), 404

        # Удаляем после получения
        del latest_data_by_stand[stand_id]

        logging.info(f"Data for {stand_id} retrieved and cleared.")
        return jsonify({"result": "OK", "data": data})

    except Exception as e:
        logging.error(f"Error retrieving data for stand 1: {str(e)}")
        return jsonify({"error description": "FAIL", "result": str(e)}), 500
    
@app.route('/get_test_results/2', methods=['GET'])
def get_test_results2():
    try:
        stand_id = f"table_2"
        data = latest_data_by_stand.get(stand_id)

        if not data:
            logging.info(f"No data available for stand_id: {stand_id}")
            return jsonify({"error description": "No data available", "result": "FAIL"}), 404

        # Удаляем после получения
        del latest_data_by_stand[stand_id]

        logging.info(f"Data for {stand_id} retrieved and cleared.")
        return jsonify({"result": "OK", "data": data})

    except Exception as e:
        logging.error(f"Error retrieving data for stand 1: {str(e)}")
        return jsonify({"error description": "FAIL", "result": str(e)}), 500
    
@app.route('/get_test_results/3', methods=['GET'])
def get_test_results3():
    try:
        stand_id = f"table_3"
        data = latest_data_by_stand.get(stand_id)

        if not data:
            logging.info(f"No data available for stand_id: {stand_id}")
            return jsonify({"error description": "No data available", "result": "FAIL"}), 404

        # Удаляем после получения
        del latest_data_by_stand[stand_id]

        logging.info(f"Data for {stand_id} retrieved and cleared.")
        return jsonify({"result": "OK", "data": data})

    except Exception as e:
        logging.error(f"Error retrieving data for stand 1: {str(e)}")
        return jsonify({"error description": "FAIL", "result": str(e)}), 500


if __name__ == '__main__':
    # app.run(host="172.21.10.182", port=5003)
    # проверка на то что у этого экземпляра сервера существует свой родитель если нет его надо убить иначе данные будут попадать в него.
    parent_pid = os.getppid()
    def monitor_parent():
        while True:
            # На Windows и Unix: если родительский процесс сменился — завершаемся
            if os.getppid() != parent_pid:
                os._exit(0)
            time.sleep(1)
    threading.Thread(target=monitor_parent, daemon=True).start()
    app.run(host="192.168.1.100", port=5003)


"""
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
    

@app.route('/get_test_results/<int:stand_number>', methods=['GET'])
def get_test_results(stand_number):
    try:
        stand_id = f"RTK_{stand_number}"
        data = latest_data.get(stand_id)

        if not data:
            logging.info(f"No data available for stand_id: {stand_id}")
            return jsonify({"error description": "No data available", "result": "FAIL"}), 404

        # Удаляем после получения
        del latest_data[stand_id]

        logging.info(f"Data for {stand_id} retrieved and cleared.")
        return jsonify({"result": "OK", "data": data})

    except Exception as e:
        logging.error(f"Error retrieving data for stand {stand_number}: {str(e)}")
        return jsonify({"error description": "FAIL", "result": str(e)}), 500


if __name__ == '__main__':
    app.run(host="192.168.1.100", port=5003)  # Можно менять порт/IP при необходимости

"""



 