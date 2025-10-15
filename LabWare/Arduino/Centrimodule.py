import serial
import time
import threading
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))

from Log.Logging_Class import NodeLogger

class CentrifugeManager:
    def __init__(self, logger_obj):
        self.logger_obj = logger_obj

        # --- 시리얼 포트 4개 열기 ---
        self.ser01 = serial.Serial("/dev/ttyCentri01", 9600, timeout=2)  # Xg, Time
        self.ser02 = serial.Serial("/dev/ttyCentri02", 9600, timeout=2)  # 1,4,5,6,7,8,9
        self.ser03 = serial.Serial("/dev/ttyCentri03", 9600, timeout=2)  # Start, Stop
        self.ser04 = serial.Serial("/dev/ttyCentri04", 9600, timeout=2)  # 0,2,3, cancel, enter

        # 아두이노 리셋 대기
        time.sleep(2)

        # --- 포트별 Lock 준비 ---
        self.lock01 = threading.Lock()
        self.lock02 = threading.Lock()
        self.lock03 = threading.Lock()
        self.lock04 = threading.Lock()

    def send_command(self, ser, lock, command):
        """
        이미 열려 있는 ser(Serial) 포트에 command를 write하는 함수.
        lock으로 동시 접근 방지.
        """
        with lock:
            if not ser.is_open:
                ser.open()  # 혹시 닫혀 있으면 다시 열기
            # 명령 전송
            ser.write((command + "\n").encode("utf-8"))
            self.logger_obj.debug("CentrifugeManager", f"Send command: {command}")

            # 필요한 경우, 여기서 응답을 읽거나 시간 대기
            # 예시로 1초만 대기
            time.sleep(1)

    # -------------------------------------------------------
    # 아래부터 '버튼' 하나당 '함수' 하나씩 작성
    # -------------------------------------------------------
    # ========== ttyCentri01 : Xg, Time ==========
    def button_xg(self):
        """ttyCentri01에 'Xg' 버튼 누르기"""
        self.send_command(self.ser01, self.lock01, "Xg")

    def button_time(self):
        """ttyCentri01에 'Time' 버튼 누르기"""
        self.send_command(self.ser01, self.lock01, "Time")

    # ========== ttyCentri02 : 1,4,5,6,7,8,9 ==========
    def button_1(self):
        self.send_command(self.ser02, self.lock02, "1")

    def button_4(self):
        self.send_command(self.ser02, self.lock02, "4")

    def button_5(self):
        self.send_command(self.ser02, self.lock02, "5")

    def button_6(self):
        self.send_command(self.ser02, self.lock02, "6")

    def button_7(self):
        self.send_command(self.ser02, self.lock02, "7")

    def button_8(self):
        self.send_command(self.ser02, self.lock02, "8")

    def button_9(self):
        self.send_command(self.ser02, self.lock02, "9")

    # ========== ttyCentri03 : Start, Stop ==========
    def button_start(self):
        self.send_command(self.ser03, self.lock03, "Start")

    def button_stop(self):
        self.send_command(self.ser03, self.lock03, "Stop")

    # ========== ttyCentri04 : 0,2,3, cancel, enter ==========
    def button_0(self):
        self.send_command(self.ser04, self.lock04, "0")

    def button_2(self):
        self.send_command(self.ser04, self.lock04, "2")

    def button_3(self):
        self.send_command(self.ser04, self.lock04, "3")

    def button_cancel(self):
        self.send_command(self.ser04, self.lock04, "cancel")

    def button_enter(self):
        self.send_command(self.ser04, self.lock04, "enter")

    def start(self):
        """호환용"""
        self.button_start()

    def CentriStart(self, set_time, mode_type="virtual"):
        """
        원심분리기 시작
        set_time (int): 분 단위
        mode_type (str): "real"이면 실제 동작, "virtual"이면 시뮬
        """
        debug_device_name = "Centrifuge ({})".format(mode_type)
        self.logger_obj.debug(debug_device_name, f"Centrifuge Start {set_time} min")

        set_time_seconds = set_time * 60
        operation_time = set_time_seconds + 240 # 안전 1분 추가

        if mode_type == "real":
            # start 버튼
            time.sleep(2)
            self.button_start()

            self.logger_obj.debug(debug_device_name, "Centrifuge is running")
            time.sleep(2)
                
            for remaining in range(operation_time, 0, -60):
                self.logger_obj.debug(debug_device_name, f"Remaining operation time: {remaining} seconds")
                time.sleep(60)

            self.logger_obj.debug(debug_device_name, "Centrifuge operation has been completed.")
            # time.sleep(2)
            # self.button_enter()
            # time.sleep(2)
            # self.button_enter()
            time.sleep(2)
            self.close_all_ports()
        else:
            self.logger_obj.debug(debug_device_name, f"Simulated centrifuge operation time {operation_time} seconds")

        return f"Centrifuge started for {set_time} minutes ({operation_time} seconds including safety time)"

    def close_all_ports(self):
        """모든 포트 안전히 닫기"""
        if self.ser01.is_open: self.ser01.close()
        if self.ser02.is_open: self.ser02.close()
        if self.ser03.is_open: self.ser03.close()
        if self.ser04.is_open: self.ser04.close()
        self.logger_obj.debug("CentrifugeManager", "All serial ports closed.")


if __name__ == "__main__":
    logger = NodeLogger(platform_name="Centrifuge", setLevel="DEBUG")

    manager = CentrifugeManager(logger)
    # manager.button_xg()
    # time.sleep(1)
    # manager.button_1()
    # time.sleep(1)
    # manager.button_0()
    # time.sleep(1)
    # manager.button_0()
    # time.sleep(1)
    # manager.button_0()
    # time.sleep(1)
    # manager.button_enter()


    # manager.button_time()
    # time.sleep(1)
    # manager.button_enter()
    # time.sleep(1)
    # manager.button_enter()
    # time.sleep(1)
    # manager.button_3
    # time.sleep(1)
    # manager.button_0
    # time.sleep(1)
    # manager.button_enter()

    # 예시: 실제 동작 모드로 1분 돌리기
    manager.CentriStart(set_time=20, mode_type="real")
    manager.close_all_ports()
