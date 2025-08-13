import random
import threading

# Списки команд для каждого стола
command_toBOt = []    # Стол 1
command_toBOt2 = []   # Стол 2
command_toBOt3 = []   # Стол 3

# Блокировка для потокобезопасности
command_toBOt_lock = threading.Lock()

# Флаги обработки для каждого списка
processing_list1 = False
processing_list2 = False
processing_list3 = False

# Текущий активный список (1, 2 или 3)
current_active_list = 1

def insertincommand_toBOt(command, listnumber):
    global command_toBOt, command_toBOt2, command_toBOt3
    
    with command_toBOt_lock:
        if listnumber == 1:
            command_toBOt.append(command)
            print(f"Добавлена команда {command} в список 1")
        elif listnumber == 2:
            command_toBOt2.append(command)
            print(f"Добавлена команда {command} в список 2")
        elif listnumber == 3:
            command_toBOt3.append(command)
            print(f"Добавлена команда {command} в список 3")
        else:
            raise ValueError("listnumber должен быть 1, 2 или 3")

def get_next_command():
    global current_active_list, processing_list1, processing_list2, processing_list3
    
    with command_toBOt_lock:
        # Проверяем текущий активный список
        if current_active_list == 1 and not processing_list1 and command_toBOt:
            processing_list1 = True
            cmd = command_toBOt[-1]
            print(f"Начинаем обработку списка 1 (команда: {cmd})")
            return cmd, 1
            
        elif current_active_list == 2 and not processing_list2 and command_toBOt2:
            processing_list2 = True
            cmd = command_toBOt2[-1]
            print(f"Начинаем обработку списка 2 (команда: {cmd})")
            return cmd, 2
            
        elif current_active_list == 3 and not processing_list3 and command_toBOt3:
            processing_list3 = True
            cmd = command_toBOt3[-1]
            print(f"Начинаем обработку списка 3 (команда: {cmd})")
            return cmd, 3
            
        # Если текущий список обрабатывается или пуст, ищем следующий
        for next_list in [1, 2, 3]:
            if next_list == 1 and not processing_list1 and command_toBOt:
                current_active_list = 1
                processing_list1 = True
                cmd = command_toBOt[-1]
                print(f"Переключились на список 1 (команда: {cmd})")
                return cmd, 1
                
            elif next_list == 2 and not processing_list2 and command_toBOt2:
                current_active_list = 2
                processing_list2 = True
                cmd = command_toBOt2[-1]
                print(f"Переключились на список 2 (команда: {cmd})")
                return cmd, 2
                
            elif next_list == 3 and not processing_list3 and command_toBOt3:
                current_active_list = 3
                processing_list3 = True
                cmd = command_toBOt3[-1]
                print(f"Переключились на список 3 (команда: {cmd})")
                return cmd, 3
        
        # Все списки либо обрабатываются, либо пусты
        print("Нет доступных команд для обработки")
        return None, None

def eracecommandBot(command, listnumber):
    global command_toBOt, command_toBOt2, command_toBOt3
    global processing_list1, processing_list2, processing_list3
    
    with command_toBOt_lock:
        if listnumber == 1 and command in command_toBOt:
            command_toBOt.remove(command)
            processing_list1 = False
            print(f"Завершена обработка команды {command} из списка 1")
            print(f"Осталось команд в списке 1: {len(command_toBOt)}")
            
        elif listnumber == 2 and command in command_toBOt2:
            command_toBOt2.remove(command)
            processing_list2 = False
            print(f"Завершена обработка команды {command} из списка 2")
            print(f"Осталось команд в списке 2: {len(command_toBOt2)}")
            
        elif listnumber == 3 and command in command_toBOt3:
            command_toBOt3.remove(command)
            processing_list3 = False
            print(f"Завершена обработка команды {command} из списка 3")
            print(f"Осталось команд в списке 3: {len(command_toBOt3)}")
            
        else:
            print(f"Команда {command} не найдена в списке {listnumber}")

# Тестовые команды
insertincommand_toBOt("cmd1_1", 1)
insertincommand_toBOt("cmd1_2", 1)
insertincommand_toBOt("cmd2_1", 2)
insertincommand_toBOt("cmd3_1", 3)

print("\nНачинаем обработку команд:")
while True:
    cmd, num = get_next_command()
    if cmd is None and num is None:
        # Проверяем, есть ли вообще команды во всех списках
        total_commands = len(command_toBOt) + len(command_toBOt2) + len(command_toBOt3)
        if total_commands == 0:
            break
        continue
    
    # Имитация обработки команды
    print(f"Обрабатывается команда {cmd} из списка {num}")
    eracecommandBot(cmd, num)
    
    # Имитация поступления новых команд
    if random.random() > 0.7:  # 30% вероятность
        new_list = random.randint(1, 3)
        new_cmd = f"new_cmd{new_list}_{random.randint(1, 100)}"
        insertincommand_toBOt(new_cmd, new_list)

print("\nФинальное состояние списков:")
print(f"Список 1: {command_toBOt}")
print(f"Список 2: {command_toBOt2}")
print(f"Список 3: {command_toBOt3}")