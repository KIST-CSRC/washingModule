import serial 
import time
import sys, os 
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from Log.Logging_Class import NodeLogger


class Satorius():
    def __init__(self,  logger_obj,device_name="Satorius"):
        self.logger_obj = logger_obj
        self.info = {
            "PORT" : "/dev/ttyweighing",
            "BAUD_RATE" : 9600
        }
        self.device_name = device_name
        self.scale = serial.Serial(self.info["PORT"],self.info["BAUD_RATE"],bytesize=7,stopbits=1)

    def heartbeat(self):
            debug_msg="Hello World!! Succeed to connection to main computer!"
            debug_device_name="{} ({})".format(self.device_name, "heartbeat")
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
            return_res_msg="[{}] : {}".format(self.device_name, debug_msg)
            return return_res_msg
    
    def send_command(self, command, expect_response=False):
        """
        Sends a command to the scale through serial communication.

        Args:
        command (str): The command string to be sent to the scale.
        expect_response (bool): A flag indicating whether the command expects a response.

        Returns:
        str: The response from the scale if expect_response is True. Otherwise, returns None.
        """                
        self.scale.write(command.encode())
        if expect_response:
            return self.scale.readline().decode().strip()

    def execute_command(self, mode_type, command, expect_response=False, debug_message=""):
        """
        Executes a given command based on the mode of operation (real or virtual).

        In 'real' mode, it sends the command to the scale and optionally reads a response.
        In 'virtual' mode, it only logs the action without interacting with the scale.

        Args:
        mode_type (str): The mode of operation, 'real' or 'virtual'.
        command (str): The command to be executed.
        expect_response (bool): Indicates if the command expects a response from the scale.
        debug_message (str): The debug message to be logged.

        Returns:
        str: The response from the scale if expect_response is True and mode is 'real'. Otherwise, returns None.
        """
        if mode_type == "real":
            self.logger_obj.debug(device_name=self.device_name, debug_msg=debug_message)
            return self.send_command(command, expect_response)
        elif mode_type == "virtual":
            self.logger_obj.debug(device_name=self.device_name, debug_msg=debug_message)
            return debug_message
            ## (NY)virtual에 return 이 없어서 변수 대신 msg를 전달함

    def initialize_scale(self, mode_type="virtual"):
        self.execute_command(mode_type, '\x1BT', debug_message="Initialize Scale ({})".format(mode_type))
        self.execute_command(mode_type, '\x1BP', expect_response=True, debug_message="Initialized Weight Value ({})".format(mode_type))
        return "Initialized Weight Value ({})".format(mode_type)
        ## (NY)return이 없어서 무게값이 포함된 msg로 전달 virtual이든 real이든 둘 다 하드웨어 확인을 위해 나누지 않고 같은 method로 함 
    
    def get_value(self, mode_type="virtual"):
        response = self.execute_command(mode_type, '\x1BP', expect_response=True, debug_message="Get Weight ({})".format(mode_type))
        if response:
            # Use regular expression to find the numerical value in the response
            # The updated regex now also matches negative numbers
            match = re.search(r'-?\d+\.\d+', response)
            if match:
                # Convert the matched string to a float and return
                return float(match.group())
            else:
                # Handle the case where no numerical value is found
                self.logger_obj.error(f"No numerical value found in response: {response}")
                return f"No numerical value found in response: {response}"
        else:
            # Handle the case where there is no response
            self.logger_obj.error("No response received from scale.")
            return "No response received from scale."
        

    def status_draftshield(self, mode_type="real"):
        return self.execute_command(mode_type, '\x1Bw0_', expect_response=True, debug_message="Status Draftshield ({})".format(mode_type))

    ## (NY)아래에 있는 모든 함수들 return추가함 msg는 다시 확인 후 변경이 필요할 수 있음 
    def open_all_doors(self, mode_type="real"):
        self.execute_command(mode_type, '\x1Bw8_', debug_message="Open All Doors ({})".format(mode_type))
        return "Open All Doors ({})".format(mode_type)
    
    def open_upper_doors(self, mode_type="real"):
        self.execute_command(mode_type, '\x1Bw3_', debug_message="Open Upper Doors ({})".format(mode_type))
        return "Open Upper Doors ({})".format(mode_type)
    
    def open_left_doors(self, mode_type="real"):
        self.execute_command(mode_type, '\x1Bw1_', debug_message="Open Left Doors ({})".format(mode_type))
        return "Open Left Doors ({})".format(mode_type)
    
    def open_right_doors(self, mode_type="real"):
        self.execute_command(mode_type, '\x1Bw4_', debug_message="Open Left Doors ({})".format(mode_type))
        return "Open Left Doors ({})".format(mode_type)
    
    def close_all_doors(self, mode_type="real"):
        self.execute_command(mode_type, '\x1Bw2_', debug_message="Close All Doors ({})".format(mode_type))
        return "Close All Doors ({})".format(mode_type)


if __name__ == '__main__':
    NodeLogger_obj = NodeLogger(platform_name="Robot Platform", setLevel="DEBUG", SAVE_DIR_PATH="C:/Users/KIST/PycharmProjects/BatchPlatform")
    pip = Satorius(NodeLogger_obj, device_name="Satorius")

    at = pip.get_value(mode_type="real")
    at
    print(at)