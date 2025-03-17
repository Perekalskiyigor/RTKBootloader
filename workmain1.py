import time
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import threading

dict_Table1 = {
    'Reg_move_Table': 0, 
    'sub_Reg_move_Table': 0, 
    'Reg_updown_Botloader': 0, 
    'sub_Reg_updown_Botloader': 0, 
    'Rob_Action': 0,
    'sub_Rob_Action': 0
}


################################################# START MODBUS Communication class with Modbus regul ###################################
class ModbusProvider:
    """Class MODBUS Communication with Modbus regul"""
    def __init__(self):
        self.store = ModbusSlaveContext(
            hr=ModbusSequentialDataBlock(0, [0] * 100)
        )
        self.lock = threading.Lock()

        self.Reg_move_Table = 0              # Move Table
        self.Reg_updown_Botloader = 0        # Move botloader
        self.Rob_Action = 0                  # Action to Robot

        self.server_thread = threading.Thread(target=self.run_modbus_server, daemon=True)
        self.server_thread.start()

        self.update_thread = threading.Thread(target=self.update_registers, daemon=True)
        self.update_thread.start()

    def run_modbus_server(self):
        context = ModbusServerContext(slaves=self.store, single=True)
        print("Starting Modbus TCP server on localhost:502")
        try:
            StartTcpServer(context, address=("localhost", 502))
        except Exception as e:
            print(f"Error starting Modbus server: {e}")

    
    # Modbus registers read/write
    def update_registers(self):
        global dict_Table1
        while True:
            try:
                with self.lock:
                    dict_Table1["sub_Reg_move_Table"] = self.store.getValues(3, 1, count=1)[0]
                    dict_Table1["sub_Reg_updown_Botloader"] = self.store.getValues(3, 3, count=1)[0]
                    dict_Table1["sub_Rob_Action"] = self.store.getValues(3, 5, count=1)[0]

                    self.Reg_move_Table = dict_Table1["Reg_move_Table"]
                    self.Reg_updown_Botloader = dict_Table1["Reg_updown_Botloader"]
                    self.Rob_Action = dict_Table1["Rob_Action"]

                    self.store.setValues(3, 0, [self.Reg_move_Table])
                    self.store.setValues(3, 2, [self.Reg_updown_Botloader])
                    self.store.setValues(3, 4, [self.Rob_Action])
            except Exception as e:
                print(f"Error updating registers: {e}")
            time.sleep(1)

################################################# START MODBUS Communication class with Modbus regul ###################################


################################################# START TABLE CLASS #####################################################################
class Table:
    """ TABLE CLASS"""
    def __init__(self, name, initial_dict):
        self.name = name
        self.data = initial_dict


    # Method write registers in modbus through modbus_provider
    def change_value(self, key, new_value):
        with modbus_provider.lock:
            if key in self.data:
                self.data[key] = new_value
                # print(f"Updated {key} to {new_value} in {self.name}.")
            else:
                print(f"Key '{key}' not found in {self.name}.")

    # Method read registers in modbus through modbus_provider
    def read_value(self, key):
        with modbus_provider.lock:
            if key in self.data:
                result = self.data[key]
                # print(f"Read {key}: {result} from {self.name}.")
            else:
                print(f"Key '{key}' not found in {self.name}.")
            return result

    # The first cycle Protect Table in the start work
    def defence_cycle(self):
        print("******ЦИКЛ DEFENCE*******")
        print("1 Регул <- Сдвинь плату освободив ложе1.")
        self.change_value('Reg_move_Table', 100)
        while True:
            result1 = self.read_value("sub_Reg_move_Table")
            if result1 != 100:
                print(f"Ждем ответ о том что стол сдвинут - сейчас значение = {result1}")
            elif result1 == 200:
                print(f"От регула получен код 200 на операции движения стола")
            else:
                break
            time.sleep(1)
        self.change_value('Reg_move_Table', 0)

        print("2 Робот <- Забери плату с ложе 1.")
        self.change_value('Rob_Action', 300)
        while True:
            result1 = self.read_value("sub_Rob_Action")

            if result1 != 100:
                print(f"Ждем ответ от робота, что плату забрал получено от робота = {result1}")
            elif result1 == 200:
                print(f"От робота получен код 200 на на операции взять плату с ложа")
            else:
                break
            time.sleep(1)
        self.change_value('Rob_Action', 0)

        print("3 Регул <- Сдвинь плату освободив ложе2.")
        self.change_value('Reg_move_Table', 100)
        while True:
            result1 = self.read_value("sub_Reg_move_Table")
            if result1 != 100:
                print(f"Ждем ответ о том что стол сдвинут - сейчас значение = {result1}")
            elif result1 == 200:
                print(f"От регула получен код 200 на операции движения стола")
            else:
                break
            time.sleep(1)
        self.change_value('Reg_move_Table', 0)

        print("4 Робот <- Забери плату с ложе 2.")
        self.change_value('Rob_Action', 300)
        while True:
            result1 = self.read_value("sub_Rob_Action")
            if result1 != 100:
                print(f"Ждем ответ от робота, что плату забрал получено от робота = {result1}")
            elif result1 == 200:
                print(f"От робота получен код 200 на на операции взять плату с ложа")
            else:
                break
            time.sleep(1)
        self.change_value('Rob_Action', 0)

        print("******ЦИКЛ DEFENCE Завершен*******")


    ############# ****ЦИКЛ SETUP ******"
    def setup_cycle(self):
        print("****ЦИКЛ SETUP******")

        # 5 Робот <- Забери плату из тары
        print("5 Робот <-  забрать плату из тары")
        self.change_value('Rob_Action', 300)
        while True:
            result1 = self.read_value("sub_Rob_Action")
            if result1 != 100:
                print(f"Ждем ответ от робота, что плату забрал из тары получено от робота = {result1}")
            elif result1 == 200:
                print(f"От робота получен код 200 на на операции забрать из тары плату")
            else:
                break
            time.sleep(1)
        self.change_value('Rob_Action', 0)

        # 6 Делаем фото платы
        print("6 Камера <- сделай фото")
        time.sleep(1)
        

        # 7 Робот <- Уложи плату в ложемент тетситрования
        print("7 Робот <- Уложи плату в ложемент тетситрования")
        self.change_value('Rob_Action', 300)
        while True:
            result1 = self.read_value("sub_Rob_Action")
            if result1 != 100:
                print(f"Ждем ответ от робота, что плату забрал из тары получено от робота = {result1}")
            elif result1 == 200:
                print(f"От робота получен код 200 на на операции забрать из тары плату")
            else:
                break
            time.sleep(1)
        self.change_value('Rob_Action', 0)



        # 8 Регул - Сдвигаем стол осовобождая ложе2
        print("8 Регул <- Сдвинь плату освободив ложе2.")
        self.change_value('Reg_move_Table', 100)
        while True:
            result1 = self.read_value("sub_Reg_move_Table")
            if result1 != 100:
                print(f"Ждем ответ о том что стол сдвинут - сейчас значение = {result1}")
            elif result1 == 200:
                print(f"От регула получен код 200 на операции движения стола")
            else:
                break
            time.sleep(1)
        self.change_value('Reg_move_Table', 0)


        # 9 Робот <- Забери плату из тары
        print("9 Робот <-  забрать плату из тары")
        self.change_value('Rob_Action', 300)
        while True:
            result1 = self.read_value("sub_Rob_Action")
            if result1 != 100:
                print(f"Ждем ответ от робота, что плату забрал из тары получено от робота = {result1}")
            elif result1 == 200:
                print(f"От робота получен код 200 на на операции забрать из тары плату")
            else:
                break
            time.sleep(1)
        self.change_value('Rob_Action', 0)

        # 10 Делаем фото платы
        print("10 Камера <- сделай фото")
        time.sleep(1)
        

        # 11 Робот <- Уложи плату в ложемент тетситрования
        print("11 Робот <- Уложи плату в ложемент тетситрования")
        self.change_value('Rob_Action', 300)
        while True:
            result1 = self.read_value("sub_Rob_Action")
            if result1 != 100:
                print(f"Ждем ответ от робота, что плату забрал из тары получено от робота = {result1}")
            elif result1 == 200:
                print(f"От робота получен код 200 на на операции забрать из тары плату")
            else:
                break
            time.sleep(1)
        self.change_value('Rob_Action', 0)

        print("Стол 1ложе занято")
        print("Стол 2ложе занято")

        # 12 "Регул <- Опусти прошивальщик ложе 1."
        print("12 Регул <- Опусти прошивальщик ложе 1.")
        
        # "13 РСервер <- Начни шить. ложе 1"
        print("13 РСервер <- Начни шить. ложе 1")

        # "14 Регул <- Подними прошивальщик. ложе 1"
        print("14 Регул <- Подними прошивальщик. ложе 1")
        self.pause()

        print("****ЦИКЛ SETUP Завершен******")
    ############# ****ЦИКЛ SETUP END ******"

    ############# ****ЦИКЛ MAIN ******"

    ############# ****ЦИКЛ MAIN END ******"




    
################################################# STOP TABLE CLASS #####################################################################


    def pause(self):
        time.sleep(2)

    


if __name__ == "__main__":
    modbus_provider = ModbusProvider()
    
    # Создание объекта и выполнение алгоритма
    table1 = Table("Table 1", dict_Table1)
    

    # Выполнение первого цикла 
    flag1 = True
    if flag1 == True:
        table1.defence_cycle()
        flag1 = False
    

    
    # Выполнение первого цикла
    flag = True
    if flag == True:
        table1.setup_cycle()
        flag = False

    