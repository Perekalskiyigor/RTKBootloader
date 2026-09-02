import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import cv2
import numpy as np
import os
import vlc
import time
from ultralytics import YOLO
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "operationsYOLO.log")


def log_operation(operation_no, operation_name, start_dt, end_dt, status="OK", details=None, error=None):
    """Одна строка лога на одну нумерованную операцию."""
    try:
        duration = (end_dt - start_dt).total_seconds()
        line = (
            f"[ОПЕРАЦИЯ {operation_no}] {operation_name} | "
            f"START={start_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
            f"END={end_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
            f"DURATION={duration:.3f} сек | STATUS={status}"
        )

        if details:
            line += f" | DETAILS={details}"
        if error:
            line += f" | ERROR={error}"

        with open(LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")
    except Exception as log_error:
        print(f"Ошибка записи лога: {log_error}", flush=True)


def run_operation(operation_no, operation_name, func):
    """Запускает операцию, измеряет время и пишет OK/ERROR в лог."""
    start_dt = datetime.now()
    try:
        result, details = func()
        end_dt = datetime.now()
        log_operation(operation_no, operation_name, start_dt, end_dt, "OK", details=details)
        return result
    except Exception as e:
        end_dt = datetime.now()
        log_operation(operation_no, operation_name, start_dt, end_dt, "ERROR", error=str(e))
        raise


class CellClassifier:
    def __init__(self, yolo_model_path, resnet_model_path, classes):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.yolo = YOLO(yolo_model_path)
        
        self.resnet = models.resnet18(pretrained=False)
        num_ftrs = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(num_ftrs, len(classes))
        self.resnet.load_state_dict(torch.load(resnet_model_path, map_location=self.device))
        self.resnet = self.resnet.to(self.device)
        self.resnet.eval()
        
        self.classes = classes
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def classify_cell(self, cell_image):
        cell_rgb = cv2.cvtColor(cell_image, cv2.COLOR_BGR2RGB)
        cell_pil = Image.fromarray(cell_rgb)
        cell_tensor = self.transform(cell_pil).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.resnet(cell_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
        
        class_name = self.classes[predicted.item()]
        confidence_value = confidence.item()
        
        return class_name, confidence_value
    
    def process_image(self, image):
        if image is None:
            return None
        
        original_image = image.copy()
        results = self.yolo(image, conf=0.45)
        
        cells_info = []
        
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            
            for idx, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box)
                
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(image.shape[1], x2)
                y2 = min(image.shape[0], y2)
                
                if x2 <= x1 or y2 <= y1:
                    continue
                
                cell_image = image[y1:y2, x1:x2]
                
                if cell_image.size == 0:
                    continue
                
                class_name, confidence = self.classify_cell(cell_image)
                
                cells_info.append({
                    'bbox': (x1, y1, x2, y2),
                    'class': class_name,
                    'confidence': confidence,
                    'cell_image': cell_image,
                    'center_y': (y1 + y2) // 2,
                    'center_x': (x1 + x2) // 2
                })
        
        cells_info.sort(key=lambda c: (c['center_y'], c['center_x']))
        
        return {
            'original_image': original_image,
            'cells': cells_info
        }
    
    def check_order(self, cells):
        if not cells:
            return True, []
        
        filled_status = []
        for cell in cells:
            if cell['class'] == 'filled':
                filled_status.append(1)
            else:
                filled_status.append(0)
        
        if not filled_status:
            return True, []
        
        first_filled = None
        for i, status in enumerate(filled_status):
            if status == 1:
                first_filled = i
                break
        
        if first_filled is None:
            return True, []
        
        if first_filled != 0:
            return False, [first_filled + 1]
        
        filled_positions = [i for i, status in enumerate(filled_status) if status == 1]
        
        is_sequential = True
        gaps = []
        
        for i in range(len(filled_positions) - 1):
            if filled_positions[i + 1] - filled_positions[i] > 1:
                is_sequential = False
                for pos in range(filled_positions[i] + 1, filled_positions[i + 1]):
                    gaps.append(pos + 1)
        
        return is_sequential, gaps
    
    def get_results(self, result):
        cells = result['cells']
        
        filled_positions = []
        empty_positions = []
        wrong_side_positions = []
        
        for i, cell in enumerate(cells):
            position = i + 1
            if cell['class'] == 'filled':
                filled_positions.append(position)
            elif cell['class'] == 'empty':
                empty_positions.append(position)
            elif cell['class'] == 'wrong_side':
                wrong_side_positions.append(position)
        
        count_new_board = len(filled_positions)
        
        is_sequential, gaps = self.check_order(cells)
        border_order = is_sequential
        
        return {
            'count_new_board': count_new_board,
            'occupied_positions': filled_positions,
            'bad_board_position': wrong_side_positions,
            'empty_positions': empty_positions,
            'border_order': border_order
        }
    
    def visualize_results(self, result):
        image = result['original_image'].copy()
        overlay = image.copy()
        
        class_colors = {
            'filled': (0, 200, 0),
            'empty': (200, 0, 0),
            'wrong_side': (0, 0, 200)
        }
        
        for cell in result['cells']:
            x1, y1, x2, y2 = cell['bbox']
            class_name = cell['class']
            
            color = class_colors.get(class_name, (200, 200, 200))
            
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        
        cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
        
        for cell in result['cells']:
            x1, y1, x2, y2 = cell['bbox']
            class_name = cell['class']
            
            color = class_colors.get(class_name, (200, 200, 200))
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        
        filled_count = sum(1 for cell in result['cells'] if cell['class'] == 'filled')
        total_cells = len(result['cells'])
        
        is_sequential, gaps = self.check_order(result['cells'])
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        
        if is_sequential:
            text = f"Загружено: {filled_count}"
        else:
            if gaps and len(gaps) == 1 and gaps[0] > 1:
                text = f"Загружено: {filled_count}  ВНИМАНИЕ! Заполнение начато с {gaps[0]}-й ячейки"
            else:
                text = f"Загружено: {filled_count}  ВНИМАНИЕ! Пропуски на позициях {gaps}"
        
        (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        padding = 8
        bg_width = text_w + padding * 2
        bg_height = text_h + padding * 2
        
        if is_sequential:
            cv2.rectangle(image, (10, 10), (10 + bg_width, 10 + bg_height), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (10 + bg_width, 10 + bg_height), (255, 255, 255), 1)
        else:
            cv2.rectangle(image, (10, 10), (10 + bg_width, 10 + bg_height), (0, 0, 255), -1)
            cv2.rectangle(image, (10, 10), (10 + bg_width, 10 + bg_height), (255, 255, 255), 2)
        
        cv2.putText(image, text, (10 + padding, 10 + padding + text_h), font, font_scale, (255, 255, 255), thickness)
        
        return image

def crop_image(image, crop_left=300, crop_right=400, crop_top=100, crop_bottom=200):
    height, width = image.shape[:2]
    
    left = crop_left
    top = crop_top
    right = width - crop_right
    bottom = height - crop_bottom
    
    if right <= left or bottom <= top:
        return image
    
    cropped = image[top:bottom, left:right]
    return cropped



def analyze_tray():

    player = None

    try:

        # --------------------------------------------------
        # 1. Старт
        # --------------------------------------------------

        def op1():
            print("1. Программа запущена", flush=True)
            return None, "Старт процесса"

        run_operation(
            1,
            "Программа запущена",
            op1
        )


        # --------------------------------------------------
        # 2. CUDA
        # --------------------------------------------------

        def op2():
            print("2. Проверяю CUDA...", flush=True)

            cuda_available = torch.cuda.is_available()

            device_name = (
                torch.cuda.get_device_name(0)
                if cuda_available
                else "CPU"
            )

            print("CUDA:", cuda_available, flush=True)
            print("Device:", device_name, flush=True)

            return (
                None,
                f"CUDA={cuda_available}; Device={device_name}"
            )

        run_operation(
            2,
            "Проверка CUDA",
            op2
        )


        # --------------------------------------------------
        # 3. Загружаем модели
        # --------------------------------------------------

        def op3():

            print(
                "3. Загружаю модели...",
                flush=True
            )

            obj = CellClassifier(

                yolo_model_path=(
                    '//SRV-NN/Users/i.perekalskii/'
                    'Desktop/DEVelopers/rtk/model_yolo.pt'
                ),

                resnet_model_path=(
                    '//SRV-NN/Users/i.perekalskii/'
                    'Desktop/DEVelopers/rtk/model_resnet.pth'
                ),

                classes=[
                    'empty',
                    'filled',
                    'wrong_side'
                ]
            )

            return obj, "YOLO + ResNet загружены"

        classifier = run_operation(
            3,
            "Загрузка моделей",
            op3
        )


        # --------------------------------------------------
        # 4
        # --------------------------------------------------

        def op4():

            print(
                "4. Модели загружены",
                flush=True
            )

            return None, "Модели готовы к работе"

        run_operation(
            4,
            "Модели загружены",
            op4
        )


        # --------------------------------------------------
        # Конфигурация
        # --------------------------------------------------

        RTSP_URL = 'rtsp://172.21.19.19:8554/live'

        PHOTO_DIR = (
            '//SRV-NN/Users/i.perekalskii/'
            'Desktop/DEVelopers/rtk/photo/'
        )

        RESULTS_DIR = (
            '//SRV-NN/Users/i.perekalskii/'
            'Desktop/DEVelopers/rtk/results/'
        )


        # --------------------------------------------------
        # 5. Каталоги
        # --------------------------------------------------

        def op5():

            print(
                "5. Создаю каталоги...",
                flush=True
            )

            os.makedirs(
                PHOTO_DIR,
                exist_ok=True
            )

            os.makedirs(
                RESULTS_DIR,
                exist_ok=True
            )

            return (
                None,
                f"PHOTO_DIR={PHOTO_DIR}; "
                f"RESULTS_DIR={RESULTS_DIR}"
            )

        run_operation(
            5,
            "Создание каталогов",
            op5
        )


        # --------------------------------------------------
        # 6
        # --------------------------------------------------

        def op6():

            print(
                "6. Каталоги OK",
                flush=True
            )

            return None, "Каталоги доступны"

        run_operation(
            6,
            "Проверка каталогов",
            op6
        )


        # --------------------------------------------------
        # 7. VLC
        # --------------------------------------------------

        def op7():

            print(
                "7. Создаю VLC...",
                flush=True
            )

            obj = vlc.Instance(
                "--vout=vdummy",
                "--no-audio",
                "--no-video-title-show",
                "--avcodec-hw=disable",
                "--no-osd",
                "--quiet"
            )

            return obj, "VLC Instance создан"

        instance = run_operation(
            7,
            "Создание VLC",
            op7
        )


        # --------------------------------------------------
        # 8
        # --------------------------------------------------

        def op8():

            print(
                "8. VLC создан",
                flush=True
            )

            p = instance.media_player_new()

            m = instance.media_new(
                RTSP_URL
            )

            m.add_option(
                '--avcodec-hw=disable'
            )

            p.set_media(m)

            return (
                (p, m),
                "MediaPlayer и Media созданы"
            )

        player, media = run_operation(
            8,
            "Настройка VLC",
            op8
        )


        # --------------------------------------------------
        # 9. RTSP
        # --------------------------------------------------

        def op9():

            print(
                "9. Запускаю RTSP:",
                RTSP_URL,
                flush=True
            )

            player.play()

            return (
                None,
                f"RTSP_URL={RTSP_URL}"
            )

        run_operation(
            9,
            "Запуск RTSP",
            op9
        )


        # --------------------------------------------------
        # 10. Ждем поток
        # --------------------------------------------------

        def op10():

            print(
                "10. Жду появления видеопотока...",
                flush=True
            )

            timeout = 15
            started = time.time()

            while time.time() - started < timeout:

                width, height = player.video_get_size(0)

                if width > 0 and height > 0:

                    print(
                        f"Поток появился: "
                        f"{width}x{height}",
                        flush=True
                    )

                    return (
                        (width, height),
                        f"Поток появился: "
                        f"{width}x{height}"
                    )

                print(
                    "Жду кадр...",
                    flush=True
                )

                time.sleep(1)

            raise RuntimeError(
                "Видеопоток так и не появился "
                "за 15 сек"
            )

        width, height = run_operation(
            10,
            "Ожидание видеопотока",
            op10
        )


        time.sleep(1)


        # --------------------------------------------------
        # 11. Фото
        # --------------------------------------------------

        timestamp = datetime.now().strftime(
            "%H%M%S"
        )

        snapshot_path = os.path.join(
            PHOTO_DIR,
            f"{timestamp}.png"
        )

        def op11():

            print(
                "11. Делаю снимок:",
                snapshot_path,
                flush=True
            )

            snapshot_result = (
                player.video_take_snapshot(
                    0,
                    snapshot_path,
                    0,
                    0
                )
            )

            if snapshot_result != 0:

                raise RuntimeError(
                    f"VLC не смог сохранить кадр, "
                    f"код={snapshot_result}"
                )

            return (
                snapshot_result,
                f"FILE={snapshot_path}"
            )

        snapshot_result = run_operation(
            11,
            "Создание снимка",
            op11
        )


        # --------------------------------------------------
        # 12
        # --------------------------------------------------

        def op12():

            print(
                "12. VLC snapshot result:",
                snapshot_result,
                flush=True
            )

            return (
                None,
                f"VLC_RESULT={snapshot_result}"
            )

        run_operation(
            12,
            "Результат VLC snapshot",
            op12
        )


        # --------------------------------------------------
        # 13. Читаем изображение
        # --------------------------------------------------

        def op13():

            print(
                "13. Читаю изображение...",
                flush=True
            )

            img = cv2.imread(
                snapshot_path
            )

            if img is None:

                raise RuntimeError(
                    "OpenCV не смог прочитать кадр"
                )

            return (
                img,
                f"FILE={snapshot_path}"
            )

        image = run_operation(
            13,
            "Чтение изображения",
            op13
        )


        # --------------------------------------------------
        # 14
        # --------------------------------------------------

        def op14():

            print(
                "14. Размер изображения:",
                image.shape,
                flush=True
            )

            return (
                None,
                f"SHAPE={image.shape}"
            )

        run_operation(
            14,
            "Определение размера изображения",
            op14
        )


        # --------------------------------------------------
        # crop
        # --------------------------------------------------

        cropped_image = crop_image(
            image,
            300,
            400,
            100,
            200
        )


        # --------------------------------------------------
        # 15. YOLO + ResNet
        # --------------------------------------------------

        def op15():

            print(
                "15. Запускаю YOLO + ResNet...",
                flush=True
            )

            data = classifier.process_image(
                cropped_image
            )

            if data is None:

                raise RuntimeError(
                    "Ошибка обработки кадра"
                )

            return (
                data,
                f"INPUT_SHAPE="
                f"{cropped_image.shape}"
            )

        result_data = run_operation(
            15,
            "YOLO + ResNet",
            op15
        )


        # --------------------------------------------------
        # 16
        # --------------------------------------------------

        def op16():

            print(
                "16. Нейросеть закончила обработку",
                flush=True
            )

            return (
                None,
                f"DETECTED_CELLS="
                f"{len(result_data['cells'])}"
            )

        run_operation(
            16,
            "Нейросеть закончила обработку",
            op16
        )


        # --------------------------------------------------
        # 17. Результат
        # --------------------------------------------------

        def op17():

            results = classifier.get_results(
                result_data
            )

            print("\nРЕЗУЛЬТАТ:")

            print(
                "count_new_board:",
                results['count_new_board']
            )

            print(
                "occupied_positions:",
                results['occupied_positions']
            )

            print(
                "bad_board_position:",
                results['bad_board_position']
            )

            print(
                "empty_positions:",
                results['empty_positions']
            )

            print(
                "border_order:",
                results['border_order']
            )

            details = (
                f"count_new_board="
                f"{results['count_new_board']}; "
                f"occupied_positions="
                f"{results['occupied_positions']}; "
                f"bad_board_position="
                f"{results['bad_board_position']}; "
                f"empty_positions="
                f"{results['empty_positions']}; "
                f"border_order="
                f"{results['border_order']}"
            )

            return results, details

        results = run_operation(
            17,
            "Формирование результата",
            op17
        )


        # --------------------------------------------------
        # ГЛАВНОЕ
        # --------------------------------------------------

        return results


    finally:

        # VLC обязательно гасим,
        # даже если где-то выше произошла ошибка

        if player is not None:

            try:
                player.stop()

            except Exception:
                pass



if __name__ == "__main__":

    result = analyze_tray()

    print("\nФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    print(result)