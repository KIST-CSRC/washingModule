import serial
import time
import os, sys
import threading
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))

from Log.Logging_Class import NodeLogger

class Centri_LA():
    def __init__(self,logger_obj,device_name="CentriLA"):
    
        self.info={
            "Port" : "/dev/ttyCentriLA",
            "baud_rate" : 9600
        }
        self.logger_obj=logger_obj
        self.operation_lock = threading.Lock()
        self.device_name =device_name
        self.CentriLA = serial.Serial(self.info["Port"], self.info["baud_rate"])
    def heartbeat(self):
            debug_msg="Hello World!! Succeed to connection to main computer!"
            debug_device_name="{} ({})".format(self.device_name, "heartbeat")
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
            return_res_msg="[{}] : {}".format(self.device_name, debug_msg)
            return return_res_msg

    def send_command_to_arduino(self, command, timeout=2):
        '''
        Sends a command to the Arduino and waits for a response.

        Args:
            command (str): The command to send to the Arduino.
            timeout (int): Timeout for the serial communication in seconds.

        Returns:
            str: The response message received from the Arduino.
        '''
        ser = serial.Serial(self.info["Port"], self.info["baud_rate"], timeout=timeout)
        time.sleep(2)  # Wait for Arduino reset

        # Send the command
        ser.write((command + '\n').encode())

        # Wait for Arduino response
        while True:
            response = ser.readline().decode('utf-8').strip()
            if response == "open OK" or response == "close OK" or response == "CentriStop" or response == "CentriStart":
                break  
        ser.close()  # 시리얼 포트를 닫는다.
        return response  # 응답 반환                

    def LA_OPEN(self, mode_type="virtual"):
        '''
        Opens the centrifuge door.

        Args:
            mode_type (str): The mode of operation, "virtual" for simulation or "real" for actual operation.

        Returns:
            str: The response from the Arduino if in "real" mode.
        '''

        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        self.logger_obj.debug(debug_device_name, "Centrifuge door opening")

        if mode_type == "real":
            response = self.send_command_to_arduino('open')
        else: 
            response = "Centrifuge Door opening (virtual)"
        return response

    def LA_CLOSE(self, mode_type="virtual"):
        '''
        Closes the centrifuge door.

        Args:
            mode_type (str): The mode of operation, "virtual" for simulation or "real" for actual operation.

        Returns:
            str: The response from the Arduino if in "real" mode.
        '''
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        self.logger_obj.debug(debug_device_name, "Centrifuge door closing")

        if mode_type == "real":
            response = self.send_command_to_arduino('close')
        else: 
            response = "Centrifuge Door closing (virtual)"
    
        return response

    def CentriStart(self, set_time, mode_type="virtual"):
        '''
        원심분리기 시작

        Args:
            set_time (int): 작동 시간(분).
            mode_type (str): 작동 모드. 시뮬레이션을 위한 "virtual" 또는 실제 작동을 위한 "real".
        '''

        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        self.logger_obj.debug(debug_device_name, f"Centrifuge Start {set_time} min")

        # set_time을 분에서 초로 변환하고 안전을 위해 300초 추가
        set_time_seconds = set_time * 60
        operation_time = set_time_seconds + 300

        if mode_type == "real":
            with self.operation_lock:
                response = self.send_command_to_arduino('relay3_on')
                self.logger_obj.debug(debug_device_name, "Centrifuge is running")
                time.sleep(2)
                response = self.send_command_to_arduino('relay3_off')
                
                for remaining in range(operation_time, 0, -60):
                    self.logger_obj.debug(debug_device_name, f"Remaining operation time: {remaining} seconds")
                    time.sleep(60)
                
                self.logger_obj.debug(debug_device_name, "Centrifuge operation has been completed.")
        else:
            response = "Centrifuge Start"
            self.logger_obj.debug(debug_device_name, f"Simulated centrifuge operation time {operation_time} seconds")

        return f"Centrifuge started for {set_time} minutes ({operation_time} seconds including safety time)"

    
    def CentriStop(self,mode_type="virtual"):
        '''
        Stop the Centrifuge 

        Args:
            mode_type (str): The mode of operation, "virtual" for simulation or "real" for actual operation.
        '''

        debug_device_name="{} ({})".format(self.device_name, mode_type)
        
        msg = self.logger_obj.debug(debug_device_name, "Centrifuge Stop")
        if mode_type =="real":
            response = self.send_command_to_arduino('relay2_on')            
            time.sleep(2)
            response = self.send_command_to_arduino('relay2_off')            
        else: 
            response = "Centrifuge stop"            
        return msg    

if __name__ == "__main__":

    # NodeLogger_obj=NodeLogger(platform_name="preprocess platform", setLevel="DEBUG", SAVE_DIR_PATH="/home/preprocess/catkin_ws/src/doosan-robot/Log")    
    NodeLogger_obj = NodeLogger(platform_name="Washing module", setLevel="DEBUG",
                            SAVE_DIR_PATH="../washing")

  
    centri = Centri_LA(NodeLogger_obj)
    #sunmi kim 
    # time.sleep(2)
    
    # centri.CentriStart(set_time=3,mode_type="real") 
    # time.sleep(5)
    # centri.CentriStop(mode_type="real")
    # for i in range(5):
    centri.LA_OPEN(mode_type="real") # 문열XCVF기
    #     time.sleep(2)
    # centri.LA_CLOSE(mode_type="real") # 문닫기

    

