import socket
import os, sys
import json
import time


class BaseTCPNode(object):

    def __init__(self):
        self.BUFF_SIZE = 4096
    
    def checkSocketStatus(self, client_socket, res_msg, hardware_name, action_type):
        if bool(res_msg) == True:
            if type(res_msg)==dict: # 
                ourbyte=b''
                ourbyte = json.dumps(res_msg).encode("utf-8")
                self._sendTotalJSON(client_socket, ourbyte)
                # send finish message to main computer
                time.sleep(3)
                finish_msg="finish"
                client_socket.sendall(finish_msg.encode())
            else:
                cmd_string_end = "[{}] {} succeed to finish action".format(hardware_name, action_type)
                client_socket.sendall(cmd_string_end.encode())
        elif bool(res_msg) == False:
            cmd_string_end = "[{}] {} action error".format(hardware_name, action_type)
            client_socket.sendall(cmd_string_end.encode())
            raise ConnectionError("{} : Please check".format(cmd_string_end))

    def _callServer(self, host, port, command_byte):
        res_msg=""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # receive filename (XXXXXX.json)
            s.connect((host, port))
            time.sleep(1)
            s.sendall(command_byte)
            msg = b''
            while True:
                part = s.recv(self.BUFF_SIZE)
                msg += part
                if len(part) < self.BUFF_SIZE:
                    s.close()
                    break
            res_msg=msg.decode('UTF-8')
        return res_msg
    
    def _sendTotalJSON(self, client_socket, ourbyte):
        cnt=0
        while (cnt+1)*self.BUFF_SIZE < len(ourbyte):
            msg_temp = b""+ourbyte[cnt * self.BUFF_SIZE: (cnt + 1) * self.BUFF_SIZE]
            # print("length : {}".format(len(msg_temp)))
            # print(msg_temp)
            client_socket.sendall(msg_temp)
            cnt += 1
            print(msg_temp)
        msg_temp = b"" + ourbyte[cnt * self.BUFF_SIZE: len(ourbyte)]
        client_socket.sendall(msg_temp)

class ParamterTCP:
    """
    TCP information : to protect our system due to hacker
    
    - (__HOST : Syringe pump) 

    """
    def __init__(self):
        self.HOST_PORT={

        }
        
class TCP_Class(ParamterTCP, BaseTCPNode):
    """
    [TCP_Connection] TCP Class for controlling another computer

    # (PUMP : Syringe pump)
    - Centris, XCaliburD (Syringe pump)

    # function
    - callServer(command_byte=b'PUMP,single,AgNO3,1500,2000,virtual')
    """

    def __init__(self, hardware_name, NodeLogger_obj):
        ParamterTCP.__init__(self,)
        BaseTCPNode.__init__(self,)
        self.hardware_name=hardware_name
        self.NodeLogger_obj=NodeLogger_obj

        command_byte=str.encode("{}/{}/{}/{}/{}".format(9999,hardware_name, "INFO", "None", "virtual"))
        res_str=self._callServer(self.HOST_PORT[self.hardware_name]["HOST"], self.HOST_PORT[self.hardware_name]["PORT"], command_byte)
        res_str = res_str.replace("'", "\"") # path 중에 "`"가 있고, '"'가 있음. 이를 수정하기위함
        self.info=json.loads(res_str)

    def heartbeat(self):
        """
        get connection status using TCP/IP (socket)
        
        :return res_msg (str): "Hello World!! Succeed to connection to main computer!"
        """
        debug_device_name="{} ({})".format(self.hardware_name, "heartbeat")

        command_byte = str.encode("{}/{}/{}/{}/{}".format(9999, self.hardware_name, "heartbeat", "None", "virtual"))
        res_msg=self._callServer(self.HOST_PORT[self.hardware_name]["HOST"], self.HOST_PORT[self.hardware_name]["PORT"], command_byte)

        self.NodeLogger_obj.debug(device_name=debug_device_name, debug_msg=res_msg)

        return res_msg

    def callServer(self, command_byte=b'DS_B/stirrer_to_holder/pick_num,place_num/virtual'):
        """
        receive command_byte & send tcp packet using socket

        :param command_byte (byte) =b'PUMP/single/AgNO3,1500,2000/virtual' or
                                    b'DS_B/stirrer_to_holder/pick_num,place_num/virtual'
        :return: status_message (str)
        """
        debug_device_name="{} ({})".format(self.hardware_name, "callServer")
        
        res_msg=self._callServer(self.HOST_PORT[self.hardware_name]["HOST"], self.HOST_PORT[self.hardware_name]["PORT"], command_byte)
        self.NodeLogger_obj.debug(device_name=debug_device_name, debug_msg=res_msg)
        return res_msg