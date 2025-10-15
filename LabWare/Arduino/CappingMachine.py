import serial

import socket
import os, sys 
import time
import json

# from click import command
import sys
import os
sys.path.append('/home/preprocess/catkin_ws/src/doosan-robot')

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))

from Log.Logging_Class import NodeLogger


class CappingMachine():
    def __init__(self,logger_obj,device_name="PreprocessArduino"):
        '''
        DispenserLA can be used in conjunction with YolactionWashingTask.py. 
        After Yolact performs detection in the Pipetting Line, 
        DispenserLA can adjust its steps to move down and up accordingly. The basic DispenserLA_Down and DispenserLA_UP functions can operate based on the number of steps to move and the mode type.
        '''
        self.logger_obj = logger_obj
        self.info={
            "Port" : "/dev/ttyCapping",
            "baud_rate" : 115200
        }
        self.logger_obj = logger_obj
        self.device_name =device_name
        self.CentriLA = serial.Serial(self.info["Port"], self.info["baud_rate"],timeout=1)
        self.CentriLA.reset_input_buffer()
        
    def heartbeat(self):
            debug_msg="Hello World!! Succeed to connection to main computer!"
            debug_device_name="{} ({})".format(self.device_name, "heartbeat")
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
            return_res_msg="[{}] : {}".format(self.device_name, debug_msg)
            return return_res_msg
            
    def send_command_to_arduino(self, command):
        '''
        아두이노에 명령을 전송하고 "complete!!" 응답을 기다립니다.
        '''
        try:
            
            time.sleep(3)
            bytes_written = self.CentriLA.write((command + ';').encode())
            print(f"Bytes written: {bytes_written}")
            self.CentriLA.flush()  # 즉시 전송을 보장합니다.
            time.sleep(1)  # 아두이노가 응답을 준비하는 데 필요한 시간을 제공합니다.
            start_time = time.time()
            incoming_data = ''  # 초기화
            while time.time() - start_time < 5:  # 최대 5초간 응답 대기
                if self.CentriLA.in_waiting:
                    incoming_data = self.CentriLA.readline().decode('utf-8').rstrip() # 응답 받기
                    if incoming_data:  # 예상 응답이 도착하면 루프 종료
                        break
        except serial.SerialException as e:
            self.logger_obj.error(f"Error sending command to {self.device_name}: {e}")
            raise

    def InitializeChuck(self,mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Chuck Opening")
        if mode_type =="real":
            command = "AA@2,0,0"
            self.send_command_to_arduino(command)
            time.sleep(1)
        else: 
            pass
        return msg
    
    def Chuck_open(self,mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Chuck Opening")
        if mode_type =="real":
            command = "AA@1,100,4500"
            self.send_command_to_arduino(command)
            time.sleep(1)
        else: 
            pass
        return msg
    
    def Chuck_close(self,mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Chuck Close")
        if mode_type =="real":
            command = "AA@0,100,4500"
            self.send_command_to_arduino(command)
            time.sleep(1)
            
        else: 
            pass
        return msg    
    
    def OpenCap(self,mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Cap Opening")
        if mode_type =="real":
            command = "BB@1,100,2000"
            self.send_command_to_arduino(command)
            time.sleep(1)
        
        else: 
            pass
        return msg    


    def CloseCap(self,mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Cap Closing")
        if mode_type =="real":
            command = "BB@0,100,3000"
            self.send_command_to_arduino(command)
            time.sleep(1)
            
        else: 
            pass
        return msg    


if __name__ == "__main__":
    import os, sys
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../Log")))  # get import path : Logging_Class.py
    NodeLogger_obj=NodeLogger(platform_name="preprocess platform", setLevel="DEBUG", SAVE_DIR_PATH="/home/preprocess/catkin_ws/src/doosan-robot/Log")
    Capping = CappingMachine(NodeLogger_obj)

    ##연결확인
    
    Capping.OpenCap(mode_type="real")
    time.sleep(2)
    Capping.CloseCap(mode_type="real")
    # Capping.InitializeChuck(mode_type="real") 

    # 
    # Capping.Chuck_open(mode_type="real") 
    # time.sleep(2)
    # Capping.Chuck_close(mode_type="real")
# # #   
    

