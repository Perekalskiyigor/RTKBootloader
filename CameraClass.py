import socket

class CameraConnection:
    def __init__(self, camera_ip, trigger_port=2001, camera_port=2002):
        self.camera_ip = camera_ip
        self.trigger_port = trigger_port
        self.camera_port = camera_port

    def send_start_command(self):
        """Отправляем команду для начала съемки."""
        try:
            # Создаем TCP-сокет для отправки команды "start"
            trigger_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            trigger_socket.connect((self.camera_ip, self.trigger_port))
            trigger_socket.sendall(b'start')
            print("CAM - Команда 'start' отправлена на порт 2001.")
            trigger_socket.close()
        except Exception as e:
            print(f"CAM - Ошибка при отправке команды: {e}")

    def receive_data(self):
        """Получаем три фотографии и проверяем их на совпадение."""
        try:
            # Создаем TCP-сокет для получения данных от камеры
            receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            receive_socket.connect((self.camera_ip, self.camera_port))
            print(f"CAM - Ожидание результата от камеры на порту {self.camera_port}...")

            pictures = []

            # Получаем три фотографии
            for i in range(3):
                picture_data = receive_socket.recv(4096)  # Размер буфера можно увеличить
                if not picture_data:
                    print(f"CAM - Ошибка при получении фото {i + 1}.")
                    receive_socket.close()
                    return 200, None  # Возвращаем ошибку, если не удалось получить фото
                pictures.append(picture_data)

            # Закрываем сокет после получения всех данных
            receive_socket.close()

            # Сравниваем фотографии между собой
            if pictures[0] == pictures[1] == pictures[2]:
                print("CAM - Фотографии одинаковы.")
                return 0, pictures[0]  # Возвращаем код 0 и первое совпавшее фото
            else:
                print("CAM - Ошибка: фотографии не совпадают.")
                return 200, None  # Возвращаем ошибку и None

        except Exception as e:
            print(f"CAM - Ошибка при получении данных: {e}")
            return 200, None  # Возвращаем ошибку при исключении

    def take_three_pictures(self):
        """Делаем три фото, проверяем их и возвращаем результат."""
        self.send_start_command()
        return self.receive_data()




"""
# Пример использования
camera_ip = '192.168.1.50'
camera = CameraConnection(camera_ip)

code, result = camera.take_three_pictures()

if code == 200:
    print("CAM - Ошибка: фотографии не совпадают или не получены.")
else:
    print("CAM -  Получено совпадающее фото:", result)

"""
