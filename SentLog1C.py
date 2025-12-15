import requests
import json
import logging
import configparser
import datetime
from requests.auth import HTTPBasicAuth

# Загрузка конфигурации
config = configparser.ConfigParser()
config.read('config.ini')

url_send_data = config['server']['url']
username = config['server']['username']
password = config['server']['password']
url_token = config['server']['url_token']

def get_token():
    payload = 'grant_type=CLIENT_CREDENTIALS'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic VnFuaHFPd1pGak16Y0czTFY5d3VSLXhtdlgxX29oWFBjbDRCWXc3cXJSND06N08zNFV6QXpuaVAxOE9RM0VQUGNqWFlya3BmUEFySkpfeHdMcmNDdXRsOD0='
    }
    try:
        response = requests.post(url_token, data=payload, headers=headers, verify=False)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('id_token', token_data.get('access_token'))
            logging.info("API1C - Recieve new Token")
            return access_token
        else:
            logging.error(f"API1C - Token request failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logging.error(f"API1C - Error Recieve new Token: {str(e)}")
        return None


# ====================== УСПЕШНАЯ ПРОШИВКА ======================
def send_success_log(board_dict):
    """
    Формируем JSON вида:

    {
      "rtk_id": "...",
      "order": "...",
      "version": "...",
      "good": [{
        "board": {
          "number": "Z00390116",
          "tray_number": "123455"
        },
        "operator": "A.Eliseeva",
        "error": 0,
        "dm_code_time": "...",
        "firmware_finished_time": "...",
        "board_output_time": "..."
      }],
      "bad": []
    }
    """

    token = get_token()
    if not token:
        logging.error("Не удалось получить токен")
        print("Не удалось получить токен")
        return None

    now = datetime.datetime.now().isoformat()

    good_item = board_dict["good"][0]

    # Берём таймстемпы из словаря, если есть, иначе ставим now
    ts = good_item.get("timestamps", {})
    dm_code_time = ts.get("dm_code_time", now)
    firmware_finished_time = ts.get("firmware_finished_time", now)
    board_output_time = ts.get("board_output_time", now)

    payload = {
        "rtk_id": board_dict["rtk_id"],
        "order": board_dict["order"],
        "version": board_dict["version"],
        "message_type": board_dict.get("message_type"),  # если нужно — раскомментировать
        "good": [
            {
                "board": {
                    "number": good_item["board"]["number"],
                    # tray_number можем брать, если он есть
                    "tray_number": good_item["board"].get("tray_number")
                },
                "operator": good_item["operator"],
                "error": good_item.get("error", 0),
                "timestamps":ts,
                "dm_code_time": dm_code_time,
                "firmware_finished_time": firmware_finished_time,
                "board_output_time": board_output_time
            }
        ],
        "bad": []
    }

    print("== JSON Request Body (SUCCESS) ==")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    try:
        response = requests.post(
            url_send_data,
            json=payload,
            headers=headers,
            verify=False,
            timeout=10
        )
        response.raise_for_status()

        logging.info("Request successful. Status: %s", response.status_code)
        logging.info("Response: %s", response.text)
        print(f"\nУспешно отправлено: {response.status_code}")

        try:
            return response.json()
        except ValueError:
            logging.warning("Response is not JSON or empty")
            return response.text

    except requests.exceptions.RequestException as e:
        logging.error("Error sending request: %s", str(e))
        print(f"\nОшибка отправки: {e}")
        return None


# ====================== НЕУСПЕШНАЯ ПРОШИВКА ======================
def send_unsuccess_log(board_dict):
    """
    Формируем JSON вида:

    {
      "rtk_id": "...",
      "order": "...",
      "version": "...",
      "good": [],
      "bad": [{
        "board": {"number": "Z01137499"},
        "error": 6,
        "operator": "A.Eliseeva",
        "dm_code_time": "...",
        "firmware_finished_time": "...",
        "board_output_time": "..."
      }]
    }
    """

    now = datetime.datetime.now().isoformat()

    bad_item = board_dict["bad"][0]

    ts = bad_item.get("timestamps", {})
    dm_code_time = ts.get("dm_code_time", now)
    firmware_finished_time = ts.get("firmware_finished_time", now)
    board_output_time = ts.get("board_output_time", now)

    payload = {
        "rtk_id": board_dict["rtk_id"],
        "order": board_dict["order"],
        "version": board_dict["version"],
        "message_type": board_dict.get("message_type"),
        "good": [],
        "bad": [
            {
                "board": {
                    "number": bad_item["board"]["number"]
                },
                "operator": bad_item["operator"],
                "error": bad_item["error"],
                "timestamps":ts,
                "dm_code_time": dm_code_time,
                "firmware_finished_time": firmware_finished_time,
                "board_output_time": board_output_time
            }
        ]
    }

    print("== JSON Request Body (UNSUCCESS) ==")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Лучше тоже через токен, чтобы было одинаково,
    # но если сервер ждёт BasicAuth — можно вернуть как у тебя было.
    token = get_token()
    if not token:
        logging.error("Не удалось получить токен")
        print("Не удалось получить токен")
        return None

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    try:
        response = requests.post(
            url_send_data,
            json=payload,
            headers=headers,
            verify=False,
            timeout=10
        )
        response.raise_for_status()

        logging.info("Request successful. Status: %s", response.status_code)
        logging.info("Response: %s", response.text)
        print(f"\nУспешно отправлено: {response.status_code}")

        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error sending request: %s", str(e))
        print(f"\nОшибка отправки: {e}")
        return None


board_dict_success = {
    "rtk_id": "RTK_R050_BoardsIO_1",
    "order": "ЗНП-25466.1.1",
    "version": "",
    "message_type": "firmware_log",
    "good": [
        {
            "board": {
                "number": "Z01777327",
                "tray_number": "123455"
            },
            "operator": "A.Eliseeva",
            "error": 0,
            "timestamps": {
                "dm_code_time": "2025-11-28 10:51:35.798732",
                "firmware_finished_time": "2025-11-28 10:52:12.725689",
                "board_output_time": "2025-11-28 10:52:15.725689"
            }
        }
    ],
    "bad": []
}

# Вызов
# response = send_success_log(board_dict_success)
# print("Ответ сервера:", response)


board_dict_fail = {
    "rtk_id": "RTK_R050_BoardsIO_1",
    "order": "ЗНП-25466.1.1",
    "version": "",
    "message_type": "firmware_log",
    "good": [],
    "bad": [
        {
            "board": {
                "number": "Z01777339",
                "tray_number": "123455"
            },
            "operator": "A.Eliseeva",
            "error": 6,
            "timestamps": {
                "dm_code_time": "2025-11-28 08:21:02.653260",
                "firmware_finished_time": "2025-11-28 08:21:33.371907",
                "board_output_time": "2025-11-28 15:00:33.587027"
            }
        }
    ]
}

# Вызов
response = send_unsuccess_log(board_dict_fail)
print("Ответ сервера:", response)