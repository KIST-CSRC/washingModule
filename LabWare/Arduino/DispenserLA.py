import serial
import time
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
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../yolact_vision")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))
from yolact_vision.yolact_WashingTask import YolactWashingTask
from Log.Logging_Class import NodeLogger


class DispenserLA():
    def __init__(self,logger_obj,device_name="PreprocessArduino"):
        '''
        DispenserLA can be used in conjunction with YolactionWashingTask.py. 
        After Yolact performs detection in the Pipetting Line, 
        DispenserLA can adjust its steps to move down and up accordingly. The basic DispenserLA_Down and DispenserLA_UP functions can operate based on the number of steps to move and the mode type.
        '''
        self.logger_obj = logger_obj
        self.info={
            "Port" : "/dev/ttyDispenserLA",
            "baud_rate" : 9600
        }
        self.logger_obj = logger_obj
        self.device_name =device_name
        self.DispenserLA = serial.Serial(self.info["Port"], self.info["baud_rate"])
        self.servo_position = "HOME"
        
        
    def heartbeat(self):
        debug_msg="Hello World!! Succeed to connection to main computer!"
        debug_device_name="{} ({})".format(self.device_name, "heartbeat")
        self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
        return_res_msg="[{}] : {}".format(self.device_name, debug_msg)
        return return_res_msg
        
    def send_command_to_arduino(self,command,  timeout=2):
        # 시리얼 포트를 연다.
        ser = serial.Serial(self.info["Port"], self.info["baud_rate"], timeout=timeout)
        time.sleep(2)  # 아두이노가 재설정될 때까지 기다린다.

        # 명령을 보낸다.
        ser.write((command + '\n').encode())
        
        while True:
        # 아두이노의 응답을 기다리고 출력한다.
            response = ser.readline().decode('utf-8').strip()
            if response == "complete!!":
                break

    def DispenserLA_Down(self, step ,mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Moving DispenserLA for Removing or injecting the liquid")
        if mode_type =="real":
            command = f"DOWN, {step}"
            self.send_command_to_arduino(command)
            self.send_command_to_arduino(self.servo_position) # 서보 위치 복구
        
        else: 
            pass
        return msg
    

    def DispenserLA_UP(self, step, mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "After removing the liquid or injecting the liquid, moving Dispenser UP ")
        if mode_type =="real":
            command = f"UP, {step}"
            self.send_command_to_arduino(command)
            self.send_command_to_arduino(self.servo_position) # 서보 위치 복구
        else: 
            pass
        return msg
    def DispenserLA_Action(self, action_type="RemoveLiquid" ,mode_type="virtual"):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Moving DispenserLA for {}".format(action_type))
        if mode_type =="real":
            if action_type =="RemoveLiquid":
                self.DispenserLA_Down(53000, mode_type=mode_type)
            elif action_type =="AddSolution":
                self.DispenserLA_Down(18000, mode_type=mode_type)
            elif action_type =="HOME_RemoveLiquid":
                self.DispenserLA_UP(53000, mode_type=mode_type)
            elif action_type =="HOME_AddSolution":
                self.DispenserLA_UP(18000, mode_type=mode_type)
            elif action_type =="InitialPoint": # Initial point 맨위에서부터 
                self.DispenserLA_Down(18000, mode_type=mode_type)                
        else: 
            pass
        return msg    


    def DispenserServo(self, action_type, mode_type="virtual"):
        """
        Controls the servo motor for different actions:
        - 'Remove' for removing liquid (Center Tip)
        - 'Ethanol' for adding Ethanol (Right Tip)
        - 'H2O' for adding H2O (Left Tip)
        """

        if action_type == "Remove":
            msg = self.logger_obj.debug(f"{self.device_name} ({mode_type})", "Turn on the servo motor for Removing liquid (Center Tip)")
        elif action_type == "Ethanol":
            msg = self.logger_obj.debug(f"{self.device_name} ({mode_type})", "Turn on the servo motor for adding Ethanol (Right Tip)")
        elif action_type == "H2O":
            msg = self.logger_obj.debug(f"{self.device_name} ({mode_type})", "Turn on the servo motor for adding H2O (Left Tip)")
        elif action_type == "Acetone":
            msg = self.logger_obj.debug(f"{self.device_name} ({mode_type})", "Turn on the servo motor for adding H2O (Left Tip)")            
        else:
            raise ValueError(f"Invalid action_type: {action_type}. Must be 'Remove', 'Ethanol', or 'H2O'.")

        if mode_type == "real":
            self.send_command_to_arduino(action_type)
            self.servo_position = action_type

        return msg



    def DispenserServo_Remove(self, mode_type="virtual"):
        """
        Pump1
        Center
        """
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Turn on the servo motor for Removing liquid (Center Tip)")       
        if mode_type =="real":
            command = "Remove"
            self.send_command_to_arduino(command)
            self.servo_position = command
        else: 
            pass             
        return msg
        
    def DispenserServo_Ethanol(self, mode_type="virtual"):
        """
        Pump3
        Right
        """
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        
        msg = self.logger_obj.debug(debug_device_name, "Turn on the servo motor for adding Ethanol (Right Tip)")         
        if mode_type =="real":
            command = "Ethanol"
            self.send_command_to_arduino(command)
            self.servo_position = command
        else: 
            pass

        return msg    
    
    def DispenserServo_H2O(self, mode_type="virtual"):
        """
        Pump2
        Left 
        """
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Turn on the servo motor for adding H2O (Left Tip)")        
        if mode_type =="real": 
            command = "H2O"
            self.send_command_to_arduino(command)
            self.servo_position = command
        else: 
            pass    
        return msg    
    def DispenserServo_Acetone(self, mode_type="virtual"):
        """
        Pump2
        Left 
        """
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        msg = self.logger_obj.debug(debug_device_name, "Turn on the servo motor for adding H2O (Left Tip)")        
        if mode_type =="real": 
            command = "Acetone"
            self.send_command_to_arduino(command)
            self.servo_position = command
        else: 
            pass    
        return msg    



   


if __name__ == "__main__":
    import os, sys
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../Log")))  # get import path : Logging_Class.py
    
    NodeLogger_obj=NodeLogger(platform_name="preprocess platform", setLevel="DEBUG", SAVE_DIR_PATH="/home/preprocess/catkin_ws/src/doosan-robot/Log")
    DispenserLA = DispenserLA(NodeLogger_obj)

    # step = DispenserLA.Step_from_liquid_level()
    # print(step)
    # DispenserLA.DispenserLA_UP(100, mode_type="real")
    #sunmi kim 
    # steps =DispenserLA.actuator_param_from_image_y_value(233)
    # print(steps)
    # PreprocessArduino.DeskLA_To_Washing(mode_type="real") # 문열기
    # time.sleep(1)
    # DispenserLA.DispenserLA_UP(500,mode_type="real") # 문열기
    # time.sleep(1)0
    # DispenserLA.DispenserServo_Pump2(mode_type="real")
    # DispenserLA.DispenserServo_Pump3(mode_type="real")
    # DispenserLA.DispenserLA_Action(action_type="RemoveLiquid",mode_type="real")
    # DispenserLA.DispenserLA_Action(action_type="HOME_RemoveLiquid",mode_type="real")
    
    ## 연결 확인
    # DispenserLA.DispenserLA_Action(action_type="AddSolution",mode_type="real")

    # DispenserLA.DispenserLA_Action(action_type="HOME_AddSolution",mode_type="real")

    # DispenserLA.DispenserServo_Remove(mode_type="real")
    # time.sleep(1)
    # DispenserLA.DispenserServo_Remove(mode_type="real")
    
    # DispenserLA.DispenserServo_H2O(mode_type="real")
    # # time.sleep(1)
    # DispenserLA.DispenserServo_Ethanol(mode_type="real")
    # # time.sleep(1)
    # DispenserLA.DispenserServo_Remove(mode_type="real")

    # DispenserLA.DispenserServo_Acetone(mode_type="real")
    # # 

    # DispenserLA.DispenserServo_Remove(mode_type="real")