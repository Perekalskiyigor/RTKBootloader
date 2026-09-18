import gxipy as gx
import cv2
import numpy as np
import os
from datetime import datetime

# --- Настройки ---
SAVE_DIR = "photos"                # Папка для сохранения
CAMERA_IP = "192.168.1.51"        # IP вашей камеры
# -----------------

def save_single_photo():
    # Создаём папку, если её нет
    os.makedirs(SAVE_DIR, exist_ok=True)

    # 1. Инициализация менеджера устройств
    device_manager = gx.DeviceManager()
    device_manager.update_device_list()

    dev_num = device_manager.get_device_number()
    if dev_num == 0:
        raise Exception("Камера не найдена. Проверьте подключение.")

    # 2. Открытие камеры по IP (надёжнее, чем по индексу)
    print(f"Подключение к камере {CAMERA_IP}...")
    cam = device_manager.open_device_by_ip(CAMERA_IP)
    print("Успешно подключено.")

    # 3. Настройка камеры (отключаем авто-режимы для предсказуемости)
    cam.ExposureAuto.set(gx.GxAutoEntry.OFF)
    cam.GainAuto.set(gx.GxAutoEntry.OFF)

    # Устанавливаем полный размер сенсора (обязательно для полного разрешения)
    cam.Width.set(cam.WidthMax.get())
    cam.Height.set(cam.HeightMax.get())
    cam.OffsetX.set(0)
    cam.OffsetY.set(0)

    # Отключаем триггерный режим — захват по запросу
    cam.TriggerMode.set(gx.GxSwitchEntry.OFF)

    # 4. Запуск потока и захват кадра
    cam.stream_on()
    print("Захват изображения...")

    raw_image = cam.data_stream[0].get_image(timeout=5000)  # таймаут 5 сек

    if raw_image is None:
        cam.stream_off()
        cam.close_device()
        raise Exception("Не удалось получить изображение (таймаут).")

    # 5. Конвертация в numpy-массив
    numpy_image = raw_image.get_numpy_array()

    # 6. Сохранение в файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SAVE_DIR, f"capture_{timestamp}.png")

    # Важно: камера MER-630-16GM — монохромная (Mono), поэтому сохраняем как ч/б
    # Проверяем формат и конвертируем при необходимости
    pixel_format = raw_image.get_pixel_format()
    
    if pixel_format == gx.GxPixelFormatEntry.MONO8:
        # Монохромное 8-бит изображение
        cv2.imwrite(filename, numpy_image)
    elif pixel_format == gx.GxPixelFormatEntry.BAYER_GR8:
        # Байеровская мозаика — конвертируем в цвет
        rgb_image = cv2.cvtColor(numpy_image, cv2.COLOR_BAYER_GR2RGB)
        cv2.imwrite(filename, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
    else:
        # Для других форматов пробуем сохранить как есть
        cv2.imwrite(filename, numpy_image)

    print(f"Фото сохранено: {filename}")

    # 7. Очистка
    cam.stream_off()
    cam.close_device()
    print("Камера отключена.")

if __name__ == "__main__":
    save_single_photo()