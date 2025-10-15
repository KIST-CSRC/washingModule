import serial
import time
import socket
import os, sys 
import time
import json
# from click import command
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))# from Log.Logging_Class import NodeLogger
from Log.Logging_Class import NodeLogger


class DeskLA():
    def __init__(self,logger_obj,device_name="DeskLA"):
        self.info={
            "Port" : "/dev/ttyDeskLA",
            "baud_rate" : 9600
        }
        self.logger_obj = logger_obj
        self.device_name =device_name
        self.DeskLA = serial.Serial(self.info["Port"], self.info["baud_rate"])

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
        # 시리얼 포트를 연다.
        ser = serial.Serial(self.info["Port"], self.info["baud_rate"], timeout=timeout)
        time.sleep(2)  # 아두이노가 재설정될 때까지 기다린다.

        # 명령을 보낸다.
        ser.write((command + '\n').encode())
        while True:
        # 아두이노의 응답을 기다리고 출력한다.
            response = ser.readline().decode('utf-8').strip()
            print(response)
            time.sleep(5)
            break
        # ser.close()  # 시리얼 포트를 닫는다.
        # msg = 'finish'
        return response  # 응답 반환                       

    def DeskLA_To_Washing(self, mode_type="virtual"):
        '''
        Moves the DeskLA from its home position to the Washing home position.

        Args:
            mode_type (str): The mode of operation, "virtual" for simulation or "real" for actual operation.

        Returns:
            str: The response from the Arduino if in "real" mode.
        '''        
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Moving DeskLA from home to Washing home")

        if mode_type == "real":
            command = "WashingHOMEFromView"
            self.send_command_to_arduino(command)
            return msg
        else: 
            return msg
          

    def DeskLA_To_HOME(self, mode_type="virtual"):
        '''
        Moves the DeskLA from the Washing home position back to its original home position.

        Args:
            mode_type (str): The mode of operation, "virtual" for simulation or "real" for actual operation.

        Returns:
            str: The response from the Arduino if in "real" mode.
        '''
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Moving DeskLA from Washing home to home")                

        if mode_type == "real":
            command = "ViewPointFromWashing"
            self.send_command_to_arduino(command)
            return msg
        else: 
            return msg

    def ViewPointFromWashing(self, mode_type="virtual"):
        '''
        Moves the DeskLA from the Washing home position back to its original home position.

        Args:
            mode_type (str): The mode of operation, "virtual" for simulation or "real" for actual operation.

        Returns:
            str: The response from the Arduino if in "real" mode.
        '''
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Moving DeskLA from Washing home to ViewPointHome")                

        if mode_type == "real":
            command = "ViewPointFromWashing"
            self.send_command_to_arduino(command)
            return msg
        else: 
            return msg

    def WashingHOMEFromView(self, mode_type="virtual"):
        '''
        Moves the DeskLA from the Washing home position back to its original home position.

        Args:
            mode_type (str): The mode of operation, "virtual" for simulation or "real" for actual operation.

        Returns:
            str: The response from the Arduino if in "real" mode.
        '''
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Moving DeskLA from ViewPoint to Washinghome")                

        if mode_type == "real":
            command = "WashingHOMEFromView"
            self.send_command_to_arduino(command)
            return msg
        else: 
            return msg

        
if __name__ == "__main__":
    
    import os, sys
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../Log")))  # get import path : Logging_Class.py
    from Log.Logging_Class import NodeLogger
    NodeLogger_obj=NodeLogger(platform_name="preprocess platform", setLevel="DEBUG", SAVE_DIR_PATH="/home/preprocess/catkin_ws/src/doosan-robot/Log")
    DeskLA = DeskLA(NodeLogger_obj)
    
    # time.sleep(1)            

    
    # 연결확인  
    DeskLA.DeskLA_To_Washing(mode_type="real") 

    DeskLA.DeskLA_To_HOME(mode_type="real") 

    
    

