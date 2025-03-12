from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import threading
import time

class ModbusProvider:
    def __init__(self):
        # Инициализация хранилища данных
        self.store = ModbusSlaveContext(
            hr=ModbusSequentialDataBlock(0, [0] * 100)  # 100 регистров, инициализированных значением 0
        )
        self.input1 = 0
        self.input2 = 0
        self.output1 = 0
        self.output2 = 0

        # Запуск Modbus TCP сервера в отдельном потоке
        self.server_thread = threading.Thread(target=self.run_modbus_server, daemon=True)
        self.server_thread.start()

        # Запуск потока для обновления регистров
        self.update_thread = threading.Thread(target=self.update_registers, daemon=True)
        self.update_thread.start()

    def run_modbus_server(self):
        """Запуск Modbus TCP сервера."""
        context = ModbusServerContext(slaves=self.store, single=True)
        print("Starting Modbus TCP server on localhost:502")
        StartTcpServer(context, address=("localhost", 502))

    def update_registers(self):
        """Обновление значений регистров."""
        while True:
            # Чтение значений из регистров 0 и 1 (input1 и input2)
            self.input1 = self.store.getValues(3, 0, count=1)[0]  # 3 - код функции для holding registers
            self.input2 = self.store.getValues(3, 1, count=1)[0]

            # Запись значений в регистры 2 и 3 (output1 и output2)
            self.store.setValues(3, 2, [self.output1])
            self.store.setValues(3, 3, [self.output2])

            time.sleep(1)

    def get_data(self):
        """Получение данных из регистров."""
        return self.input1, self.input2

    def set_data(self, output1, output2):
        """Установка данных в регистры."""
        self.output1 = output1
        self.output2 = output2
        print(f"Data set to output1: {self.output1}, output2: {self.output2}")

if __name__ == "__main__":
    modbus_provider = ModbusProvider()
    i=0
    # Пример использования
    while True:
        # Получение данных
        input1, input2 = modbus_provider.get_data()
        print(f"Received data - input1: {input1}, input2: {input2}")

        # Установка данных
        modbus_provider.set_data(i, 6)
        i=i+1
        time.sleep(2)