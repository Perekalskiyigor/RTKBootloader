import subprocess
import threading
import time
import signal
import os
from opcua import Client, ua

# === Настройки ===
BRIDGE_DIR  = r"C:\nails_table_bridge_v_0_2_0_for_rtk\nails_table_bridge"
BRIDGE_EXE  = "nails_table_bridge.exe"
WORKER_EXE  = r"C:\Users\i.perekalskii\Desktop\DEV\RTKBootloader\3table_Worfiletray2810.exe"

# === Глобальные процессы ===
proc_bridge = None
proc_worker = None

# === Флаги OPC (глобальные) ===
PLAY = False
STOP = False
RESTART = False



# ===================== OPC UA КЛИЕНТ =====================

class OPCClient:
    def __init__(self, url):
        self.url = url
        self.lock = threading.Lock()
        self.nodes = {}  # {nodeid: Node}
        self.client = None
        self.connected = False
        self.stop_event = threading.Event()

        # Имена узлов
        self.OPC_RESTART_RTK = 'ns=2;s=Application.UserInterface.OPC_restart_RTK'
        self.OPC_STOP_RTK    = 'ns=2;s=Application.UserInterface.OPC_pause_RTK'
        self.OPC_PLAY_RTK    = 'ns=2;s=Application.UserInterface.OPC_start_RTK'

        # Заготовки под обратную связь (раскомментируешь при необходимости):
        # self.OPC_STATUS_TEXT = 'ns=2;s=Application.UserInterface.OPC_status_text'
        # self.OPC_BUSY        = 'ns=2;s=Application.UserInterface.OPC_busy'

        self.server_thread = threading.Thread(target=self.connection_manager, daemon=True)
        self.update_thread = threading.Thread(target=self.update_registers, daemon=True)
        self.server_thread.start()
        self.update_thread.start()

    # -------------------- утилиты OPC --------------------
    def _get_node(self, nodeid):
        if nodeid is None:
            return None
        node = self.nodes.get(nodeid)
        if node is None and self.client:
            try:
                node = self.client.get_node(nodeid)
                self.nodes[nodeid] = node
            except Exception as e:
                print(f"[OPC] can't resolve node {nodeid}: {e}")
                return None
        return node

    def _write(self, nodeid, value, vtype):
        node = self._get_node(nodeid)
        if not node:
            return
        try:
            node.set_value(ua.DataValue(ua.Variant(value, vtype)))
        except Exception as e:
            print(f"[OPC] write fail {nodeid}: {e}")

    def _read_bool(self, nodeid, default=0):
        node = self._get_node(nodeid)
        if not node:
            return default
        try:
            v = node.get_value()
            return bool(int(v))
        except Exception as e:
            print(f"[OPC] read bool fail {nodeid}: {e}")
            return default

    # -------------------- соединение --------------------
    def connection_manager(self):
        while not self.stop_event.is_set():
            try:
                if not self.connected:
                    self.client = Client(self.url)
                    self.client.connect()
                    self.connected = True
                    print(f"Connected to {self.url}")

                    # прогрев узлов
                    for nid in (self.OPC_RESTART_RTK, self.OPC_STOP_RTK, self.OPC_PLAY_RTK):
                        self._get_node(nid)
                    # self._get_node(self.OPC_STATUS_TEXT)
                    # self._get_node(self.OPC_BUSY)
                time.sleep(1)
            except Exception as e:
                print(f"Connection error: {e}")
                self.connected = False
                if self.client:
                    try:
                        self.client.disconnect()
                    except:
                        pass
                self.client = None
                time.sleep(5)

    def is_connected(self):
        return self.connected and self.client is not None

    # -------------------- опрос флагов --------------------
    def update_registers(self):
        global RESTART, STOP, PLAY
        while not self.stop_event.is_set():
            try:
                if not self.is_connected():
                    time.sleep(0.5)
                    continue
                with self.lock:
                    try:
                        STOP    = self._read_bool(self.OPC_STOP_RTK, False)
                        RESTART = self._read_bool(self.OPC_RESTART_RTK, False)
                        PLAY    = self._read_bool(self.OPC_PLAY_RTK, False)
                    except Exception as e:
                        print(f"[OPC] read START/STOP/RESTART failed: {e}")
            except Exception as e:
                print(f"Critical error in update loop: {e}")
            time.sleep(1)

    def stop(self):
        self.stop_event.set()
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass

# ===================== ГЛАВНЫЙ ЦИКЛ =====================

# --- запуск процесса с выводом в общую консоль ---
def start_process(path, cwd=None, tag="[PROC]"):
    try:
        proc = subprocess.Popen(
            [path],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        threading.Thread(
            target=pipe_output,
            args=(proc, tag),
            daemon=True
        ).start()
        print(f"{tag} started pid={proc.pid}")
        return proc
    except Exception as e:
        print(f"{tag} failed to start: {e}")
        return None


# --- поток вывода ---
def pipe_output(proc, tag):
    for line in proc.stdout:
        print(f"{tag} {line.strip()}")
    print(f"{tag} exited with code {proc.wait()}")


# --- мягкая остановка ---
def stop_process(proc, tag):
    if proc and proc.poll() is None:
        print(f"{tag} stopping pid={proc.pid}")
        try:
            os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        print(f"{tag} stopped")


# --- запуск обеих программ ---
def start_both():
    global proc_bridge, proc_worker
    proc_bridge = start_process(os.path.join(BRIDGE_DIR, BRIDGE_EXE), BRIDGE_DIR, "[BRIDGE]")
    time.sleep(1)
    proc_worker = start_process(WORKER_EXE, None, "[WORKER]")


# --- остановка обеих ---
def stop_both():
    stop_process(proc_worker, "[WORKER]")
    stop_process(proc_bridge, "[BRIDGE]")


# --- рестарт обеих ---
def restart_both():
    print("[MAIN] Restart requested")
    stop_both()
    time.sleep(1)
    start_both()


# === Главный цикл с OPC ===
def main_loop():
    global PLAY, STOP, RESTART

    url = "opc.tcp://192.168.1.3:48010"
    opc_client = OPCClient(url)

    # стартуем сразу
    start_both()

    prev_restart = False
    while True:
        time.sleep(0.5)

        if RESTART and not prev_restart:
            restart_both()

        prev_restart = RESTART


if __name__ == "__main__":
    main_loop()




# #nssm install Botloader
# Удаление службы
# Для удаления службы выполните:

# text
# nssm remove MyPythonService confirm
# & "C:/Program Files/Python311/python.exe" -m pip install opcua