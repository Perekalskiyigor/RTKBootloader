# python -m PyInstaller --onefile StrarterBotloader.py

import os
import sys
import time
import subprocess
from pathlib import Path
from opcua import Client, ua

OPC_URL = "opc.tcp://192.168.1.3:48010"
NODE_START   = "ns=2;s=Application.UserInterface.OPC_start_python"
NODE_RUNNING = "ns=2;s=Application.UserInterface.OPC_log"
POLL_SEC = 0.5

EXE1 = r"C:\nails_table_bridge_v_0_2_0_for_rtk\nails_table_bridge\nails_table_bridge.exe"
EXE2 = r"C:\Users\i.perekalskii\Desktop\DEV\RTKBootloader\dist\WORK_FILE_22_12.exe"
EXE3 = r"C:\Users\i.perekalskii\Desktop\DEV\RTKBootloader\dist\ServerRTK.exe"

CONNECT_TIMEOUT_SEC = 8.0
RECONNECT_DELAY_SEC = 2.0

proc1 = None
proc2 = None
proc3 = None


def _app_dir() -> Path:
    # для pyinstaller onefile: sys.executable = путь к exe
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent


LOG_DIR = _app_dir() / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "starter.log"


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def is_running(p: subprocess.Popen | None) -> bool:
    return p is not None and p.poll() is None


def _popen_new_console(exe_path: str):
    exe = Path(exe_path)
    return subprocess.Popen(
        [str(exe)],  # Запускаем напрямую, без cmd
        cwd=str(exe.parent),
        creationflags=subprocess.CREATE_NEW_CONSOLE,  # Всё равно откроет новое окно
    )


def start_procs_once():
    global proc1, proc2, proc3

    if not is_running(proc1):
        proc1 = _popen_new_console(EXE1)
        log(f"[APPS] started nails_table_bridge (new console), launcher pid={proc1.pid}")

    time.sleep(10)

    if not is_running(proc3):
        proc3 = _popen_new_console(EXE3)
        log(f"[APPS] started ServerRTK (new console), launcher pid={proc3.pid}")

    time.sleep(3)

    if not is_running(proc2):
        proc2 = _popen_new_console(EXE2)
        log(f"[APPS] started main.exe (new console), launcher pid={proc2.pid}")


def _taskkill_pid(pid: int):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def _taskkill_name(name: str):
    subprocess.run(["taskkill", "/IM", name, "/T", "/F"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def stop_procs_once():
    global proc1, proc2, proc3

    if is_running(proc2):
        log("[APPS] stopping main.exe (launcher PID)")
        _taskkill_pid(proc2.pid)

    if is_running(proc3):
        log("[APPS] stopping ServerRTK (launcher PID)")
        _taskkill_pid(proc3.pid)

    if is_running(proc1):
        log("[APPS] stopping nails_table_bridge (launcher PID)")
        _taskkill_pid(proc1.pid)

    # добиваем по именам (на случай если PID уже другой/порожденные процессы)
    _taskkill_name(Path(EXE2).name)
    _taskkill_name(Path(EXE3).name)
    _taskkill_name(Path(EXE1).name)

    proc1 = None
    proc2 = None
    proc3 = None


def read_bool(node) -> int:
    v = node.get_value()
    try:
        return 1 if int(v) == 1 else 0
    except Exception:
        return 1 if bool(v) else 0


def write_string(node, text: str):
    node.set_value(ua.DataValue(ua.Variant(text, ua.VariantType.String)))


def connect_with_timeout(url: str, timeout_sec: float) -> Client:
    client = Client(url)
    t0 = time.time()
    log(f"[OPC] connecting to {url} ...")

    # connect() может зависать, поэтому контролируем временем
    # (в python-opcua нет простого параметра timeout на connect во всех версиях)
    while True:
        try:
            client.connect()
            log("[OPC] connected")
            return client
        except Exception as e:
            # если сразу ошибка — выходим по таймауту
            if time.time() - t0 >= timeout_sec:
                raise TimeoutError(f"connect timeout after {timeout_sec}s: {e}")
            time.sleep(0.2)


def main():
    log(f"[BOOT] pid={os.getpid()} exe={sys.executable}")

    last_log = None

    while True:
        client = None
        try:
            client = connect_with_timeout(OPC_URL, CONNECT_TIMEOUT_SEC)

            node_start = client.get_node(NODE_START)
            node_log = client.get_node(NODE_RUNNING)

            last_state = None
            t_heartbeat = 0.0

            while True:
                state = read_bool(node_start)

                if state != last_state:
                    log(f"[OPC] START changed: {last_state} -> {state}")
                    if state == 1:
                        start_procs_once()
                    else:
                        stop_procs_once()
                    last_state = state

                running = is_running(proc1) and is_running(proc3) and is_running(proc2)
                msg = "RUNNING" if running else "STOPPED"
                if msg != last_log:
                    write_string(node_log, msg)
                    log(f"[OPC] wrote OPC_log='{msg}'")
                    last_log = msg

                # каждые 5 сек пишем что цикл жив
                if time.time() - t_heartbeat > 5:
                    log("[HB] alive")
                    t_heartbeat = time.time()

                time.sleep(POLL_SEC)

        except Exception as e:
            log(f"[OPC] error: {e}")
            stop_procs_once()
            try:
                if client:
                    client.disconnect()
            except Exception:
                pass
            time.sleep(RECONNECT_DELAY_SEC)


if __name__ == "__main__":
    main()