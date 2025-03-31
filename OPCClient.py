import threading
import time
from opcua import Client
from opcua import ua

# Глобальный словарь для хранения данных
global_data = {}

class OPCClient:
    def __init__(self, url, node_ids):
        self.url = url
        self.node_ids = node_ids  # Список узлов для чтения
        self.client = Client(url)
        self.client.timeout = 5  # Устанавливаем таймаут на 5 секунд
        self.running = False
        self.thread = None

    def connect(self):
        try:
            self.client.connect()
            print(f"Подключено к {self.url}")
        except Exception as e:
            print(f"Ошибка подключения: {e}")

    def disconnect(self):
        try:
            self.client.disconnect()
            print("Отключено от OPC сервера")
        except Exception as e:
            print(f"Ошибка отключения: {e}")

    def read_data(self):
        while self.running:
            try:
                for node_id in self.node_ids:
                    node = self.client.get_node(node_id)
                    value = node.get_value()
                    
                    # Сохраняем данные в глобальный словарь
                    global_data[node_id] = value
                    print(f"Считано значение {value} для узла {node_id}")

                    # Записываем значение 5 в VAL2, если это тот узел
                    if node_id == "ns=2;s=Application.PLC_PRG.VAL2":
                        self.write_data(node, 5)
                
            except Exception as e:
                print(f"Ошибка при чтении данных: {e}")
            
            time.sleep(1)  # Задержка между запросами

    def write_data(self, node, value):
        try:
            # Создаем объект DataValue с заданным значением и текущим временем
            data_value = ua.DataValue(ua.Variant(value, ua.VariantType.Float))
            # Записываем новое значение в узел
            node.set_value(data_value)
            print(f"Записано значение {value} в узел {node.nodeid}")
        except Exception as e:
            print(f"Ошибка при записи данных: {e}")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.read_data)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()

# Пример использования
if __name__ == "__main__":
    # Укажите адрес OPC сервера и Node ID для чтения данных
    url = "opc.tcp://172.21.10.219:48010"
    
    # Пример нескольких Node ID
    node_ids = [
        "ns=2;s=Application.PLC_PRG.VAL2", 
        "ns=2;s=Application.PLC_PRG.VAL1"
    ]

    # Создание и подключение OPC клиента
    opc_client = OPCClient(url, node_ids)
    opc_client.connect()

    # Запуск потока для чтения данных
    opc_client.start()

    try:
        # Работать клиент будет до тех пор, пока не нажмете Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Остановка клиента...")
    finally:
        # Остановка потока и отключение
        opc_client.stop()
        opc_client.disconnect()
