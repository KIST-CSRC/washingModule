#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [Sonic_Bath] Class for controlling Sonic bath (Sonorex Digitec)
# @author   Daeho Kim (r4576@kist.re.kr)


import serial
import time
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from Log.Logging_Class import NodeLogger

class OperationError(Exception):
    pass

class CommandError(Exception):
    pass


class SonorexDigitec():
    """
    Class to control 'Sonrex Digitec' sonicbath.
    It provides functions for remote control via a serial interface.
    see DT remote-control 1339d GB BANDELIN for more information.    
    """

    ERROR_DICT = {
        0 : "Non Error",
        1 : "Connection Error",
        2 : "Operation Error",
        3 : "Invaild Command",
        4 : "Value Error",
         
    }

    STATUS_DICT = {
        0 : "<reserved> Remote contorl",
        1 : "<reserved> Service Mode",
        2 : "Ultrasound or Degas started",
        3 : "Degas on",
        4 : "<reserved> Heating regulation",
        5 : "Interruption of ultrasound output (pause)",
        6 : "standby",
        7 : "<not assigned>",
        8 : "Ultrasound power output (current output)",
        9 : "Heating power output",
        10 : "Calibation fuction: 20ms",
        11 : "<not assigned>",
        12 : "<not assigned>",
        13 : "<not assigned>",
        14 : "<not assigned>",
        15 : "Service function 'full access'",
        
    }



    def __init__(self, logger_obj, device_name = "Sonorex_Digitec") :
        """
        Initializer of the SonorexDigitec class.

        Args:
            device_name (str): A descriptive name for the device, used mainly in debug prints.
            ser_port (str): The serial port name connected to the device
        
        """



        # logger object
        self.logger_obj=logger_obj
        # serial settings
        self.info = { 
            "PORT" : "/dev/ttysonic",
            "BAUD_RATE" : 9600
        }
        self.device_name=device_name
        self.Sonic = serial.Serial(self.info["PORT"],self.info["BAUD_RATE"],bytesize=7,stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_EVEN, timeout=1)
        
        # operating commands
        self.POWER_ON = "P1"
        self.POWER_OFF = "P0"
        self.STANDBY = "Pz"
        self.TEMP_TARGET = "Hn"
        self.GET_TEMP_ACTUAL = "Hm"
        self.HEAT_OFF = "H0"
        self.GET_ID = "I"
        self.QUERY_ERROR = "Je"
        self.QUERY_STATUS = "Js"
        self.TIME_TARGET = "Tn"
        self.ELAPSED_TIME = "Tm"
        self.REMAIN_TIME = "Ts"
        self.DEGAS_ON = "Tp1"
        self.DEGAS_OFF = "Tp0"
        self.TIMEOUT = "Tt"
        self.CURRENT_LENGTH = "Tl"
        self.TOTAL_LENGTH = "Th"
        self.VERSION = "V"
        self.RESET = "X"
        self.TURN_OFF = "Zz"
        
    def heartbeat(self):
            debug_msg="Hello World!! Succeed to connection to main computer!"
            debug_device_name="{} ({})".format(self.device_name, "heartbeat")
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
            return_res_msg="[{}] : {}".format(self.device_name, debug_msg)
            return return_res_msg
    
    def _checkConnection(self,):  
        """
        reconnect serial port

        :return: first character of receive value

        Not connected : "#"
        connceted : "J"
        """
        self.Sonic.close()
        self.Sonic.open()
        status_rcv = self._command(self.QUERY_STATUS) # 

        return status_rcv[0]

    def _command(self, cmd) :
        """
        send message to device
        
        :param cmd(str) : operating command
        
        :return: serial_res_rcv --> (str)
        """
        input = "#" + cmd + "\r\n"
        byte_data = bytes(input, encoding="utf-8")
        self.Sonic.write(byte_data)
        data = self.Sonic.readline()
        serial_res_rcv = "{}".format(data.decode('utf-8').strip())
        serial_res_rcv = serial_res_rcv.replace(" ", "")
        if serial_res_rcv == "" :

            error_msg = "{} : {}".format(1, self.ERROR_DICT[1])
            self._raiseError(code=1, msg=error_msg)
        else :
            return serial_res_rcv


    def _inspectRcv(self, rcv, cmd):
        """
        check connection of serial port

        :param rcv(str) : return value of self._command
        :param cmd(str) : input command

        :return: rcv --> (str)
        """
        if rcv == "" :
            error_msg = "Check IrDA Transceiver"
            self._raiseError(1,error_msg)

        elif rcv[0] == "#" : # 맨 처음 자리에 #이 있으면 port가 안열린 것임 
            rcv_head = self._checkConnection()
            if rcv_head == "#" :        
                error_msg = "{} : {}".format(1, self.ERROR_DICT[1])
                self._raiseError(code=1, msg=error_msg)
            else : # port가 열린것 확인 후 다시 command 실행 하는 부분 
                regenerated_rcv = self._command(cmd)
                
                return self._inspectRcv(regenerated_rcv,cmd)
        
        else :
            
            return rcv
    
    def _processRcv(self, rcv, cmd):
        """
        process response (raw message -> dictionary)
        key : command, data
                
        :param rcv(str) : return value of self._inspectRcv
        :param cmd(str) : input command

        :return: data_dict --> (Dict)
        """
        if rcv == cmd : # value가 없는 경우 
            data = None
        elif cmd ==  self.RESET : # value가 있는 경우 
            data = rcv
        elif cmd ==  self.GET_ID or cmd == self.VERSION : # value가 있는 경우 
            data = rcv[len(cmd):]
        else : # value가 있는 경우
            data = int(rcv[len(cmd):],16)
        data_dict = {
            "Command" : cmd,
            "Data" : data
        }
        return data_dict


    def _sendRcv(self, cmd, value = ""):
        """
        send command, value and receive respond
        use this function to operate command

        :param cmd(str) : input command
        :param value(str) : target value

        :return: data_dict --> (Dict)
        """
        ser_res_rcv = self._command(cmd+value)
        print(ser_res_rcv)
        inspected_rcv = self._inspectRcv(ser_res_rcv, cmd)
        progressed_rcv = self._processRcv(inspected_rcv, cmd)
        return progressed_rcv

    ################################################################################
    #                              Report commands                                 #
    ################################################################################
    
    def getTotalStatus(self, ):
        """
        get status in dictionary format
        """
        status_value =  self._sendRcv(self.QUERY_STATUS)
        binary_value=format(status_value["Data"], '016b')
        status_dict = {}
        for idx, value in enumerate(binary_value[::-1]):
            if value == '0':
                binary_status = 'off'
                
            else: 
                binary_status = 'on'
            status_dict[idx] = binary_status
        return status_dict
    
    def reset(self, ):
        """
        reset device
        """
        Data = self._sendRcv(self.RESET)
        self._checkConnection()
        return Data

    def getId(self, ):
        """
        get device id
        """
        Data = self._sendRcv(self.GET_ID)
        return Data

    def getVersion(self, ):
        """
        get device version
        """
        Data = self._sendRcv(self.VERSION)
        return Data

    def powerOn(self,):
        """
        change device status to power on (status must be power off) 
        """
        Data = self._sendRcv(self.POWER_ON)
        return Data
    
    def powerOff(self,):
        """
        change device status to power off 
        """
        Data = self._sendRcv(self.POWER_OFF)
        return Data

    def standby(self,):
        """
        change device status to power off (to escape this status use power off command)
        """
        Data = self._sendRcv(self.STANDBY)
        return Data

    def setTemp(self, temp ):
        """
        Heat sonic bath

        Param temp(numeric types) : target temp value
        """
        Data = self._sendRcv(self.TEMP_TARGET, format(int(temp*256), 'x'))
        return Data
    
    def getSetTemp(self, ):
        """
        get set heating tempetature
        """
        Data = self._sendRcv(self.TEMP_TARGET)
        return Data
    
    def getActualTemp(self, ):
        """
        get actual tempetature
        """
        Data = self._sendRcv(self.GET_TEMP_ACTUAL)
        return Data
    
    def heatOff(self, ):
        """
        heating off
        """
        Data = self._sendRcv(self.HEAT_OFF)
        return Data
    
    def queryError(self, ):
        """
        recall error
        """
        Data = self._sendRcv(self.QUERY_ERROR)
        return Data

    def setTime(self, settime):
        """
        set oprating time
        """
        Data = self._sendRcv(self.TIME_TARGET, format(int(settime), 'x'))
        return Data

    def getSetTime(self,):
        """
        get set time
        """
        Data = self._sendRcv(self.TIME_TARGET)
        return Data

    def getElapsedTime(self, ):
        """
        get elapsed time
        """
        Data = self._sendRcv(self.ELAPSED_TIME)
        return Data

    def getRemainTime(self, ):
        """
        get remain time
        """
        Data = self._sendRcv(self.REMAIN_TIME)
        return Data

    def degasOn(self, ):
        """
        degas on (use with power on command) 
        """
        Data = self._sendRcv(self.DEGAS_ON)
        return Data

    def degasOff(self, ):
        """
        degas off
        """
        Data = self._sendRcv(self.DEGAS_OFF)
        return Data

    def setTimeout(self, timeout):
        Data = self._sendRcv(self.TIMEOUT, format(int(timeout), 'x'))
        return Data
    
    def getSetTimeout(self, ):
        Data = self._sendRcv(self.TIMEOUT, )
        return Data

    def getCurrentLength(self, ):
        Data = self._sendRcv(self.CURRENT_LENGTH)
        return Data

    def getTotalLength(self, ):
        Data = self._sendRcv(self.TOTAL_LENGTH)
        return Data

    def turnOff(self, ):
        Data = self._sendRcv(self.TURN_OFF)
        return Data
    ###############################################################################

    def _raiseError(self, code, msg=str()) :
        """
        raise error message

        :param code(int) : error code
        :param msg(str) : input error massage
        """
        if code == 0 :    
            pass
        elif code == 1 :
            raise ConnectionError (msg)
        elif code == 2 :
            raise OperationError (msg)
        elif code == 3 :
            raise CommandError (msg)
        elif code == 4 :
            raise ValueError (msg)
    
    
    def _checkStatus(self, ):
        """
        check device status : stadby, ready(off), on

        :return: status --> (str)
        """
        time.sleep(1)
        status_dict = self.getTotalStatus()
        if status_dict[6] == 'on':
            status = 'Standby'
        elif status_dict[2] == 'on' :
            status = 'Operating'
        else :
            status = 'Ready'
        # msg = "Current Sonic Status : {}".format(status)
        # print(msg)
        return status

    
    def _ready(self, iter:int = 0 ):
        """
        change device status to ready
        
        :param iter(int) : No need to provide input

        :return: status, error massage --> (str)
        """
        status = self._checkStatus()
        error_code = 0
        if status == "Standby" :
            self.powerOff()
            iter += 1
            if iter == 2 :
                error_code = 2
                error_msg = "The device is unable to exit standby mode."
                self._raiseError(code=error_code, msg=error_msg)
            return self._ready(iter = iter)

        elif status == "Operating" :
            error_code = 2
            error_msg = "Sonic is already working!"
            self._raiseError(code=error_code, msg=error_msg)

        else :           
            pass
        time.sleep(3)
        return status, self.ERROR_DICT[error_code]


    def _checkValueError(self, cmd, value ):
        """
        check input value of command
        
        :param cmd(str) : command
        :param value(str or int) : value

        :return: error code --> (int)
        """
        if cmd == "Operate mode" :
            if value == "Degas Off" or value == "Degas On" :
                error_code = 0
            else :
                error_code = 4
                error_msg = "Invaild Operate mode" + " ({}->{})".format(value,'"Degas Off" or"Degas On"')
                self._raiseError(code= error_code, msg=error_msg)
            return error_code

        else:
            if cmd == "Target temp" :
                cmd = cmd + "(°C)"
                min_value = 0
                max_value = 80

            elif cmd == "Set time" :
                cmd = cmd + "(s)"
                min_value = 0
                max_value = 64800

            elif cmd == "Set timeout" :
                cmd = cmd + "(s)"
                min_value = 0
                max_value = 255

            if value < min_value or value > max_value:
                error_code = 4
                error_msg = "{} out of range (min value : {}, max value : {})".format(cmd,min_value, max_value)
                self._raiseError(code= error_code, msg=error_msg)
            else:
                error_code = 0
            return error_code
    
    def _checkStatusError(self, send_status, receive_status):
        """
        check status error
        
        :param send_status(str) : input status
        :param receive_status(str or int) : output status

        :return: error massage --> (str)
        """
        if send_status != receive_status :
            error_code=2
            self._raiseError(code=2, msg= "Status mismatch")
        else :
            error_code=0
        return self.ERROR_DICT[error_code]
            
    def operate(self, set_time:int, target_temp:int,  mode_type = "virtual"):
        """
        operate sonic bath
        
        :param set_time(int) : [s : 0 to 64800]
        :param target_temp(int) : [°C : 0 to 80]
        :param operate_mode(str) : "Degas Off" or Degas On"
        :param mode_type="virtual" (str): set virtual or real mode
        
        :return: res_msg --> (str)
        """
        operate_mode:str  = "Degas Off"
        self._checkValueError("Set time", set_time)
        self._checkValueError("Target temp", target_temp)        
        self._checkValueError("Operate mode", operate_mode)
        msg = "Sonication ... Operate Mode: {}, Set Time: {} s, Heating Temp: {} °C".format(operate_mode ,set_time, target_temp)
        self.logger_obj.debug(self.device_name, msg)


        if mode_type == "real":
            msg = "Sonication done, Operate Mode: {}, Set Time: {} s, Heating Temp: {} °C".format(operate_mode ,set_time, target_temp)
            self.logger_obj.debug(device_name=self.device_name, debug_msg=msg)
            res_msg = self.device_name + " : " + msg
            print(res_msg)            
            status, error_dict = self._ready()
            msg ="Sonic Ready? Receive signal! --> Ready : {}, Status : {}".format(bool(status=='Ready'), error_dict)
            self.logger_obj.debug(self.device_name, msg)
            settime = self.setTime(set_time)
            msg = "Time setting done --> Time : {} s".format(settime['Data'])
            self.logger_obj.debug(self.device_name, msg)
            settemp = self.setTemp(target_temp)
            msg = "Heating temp setting done --> Temp : {} °C ".format(settemp['Data'])
            self.logger_obj.debug(self.device_name, msg)
            if operate_mode == "Degas On":
                degason = self.degasOn()
                msg = "Degas On"
            power_on = self.powerOn()
            status = self._checkStatus()
            error_dict = self._checkStatusError('Operating',status)
            msg = "Sonic Start! --> Operating : {}, Status : {}".format(bool(status=='Operating'),error_dict)
            self.logger_obj.debug(self.device_name, msg)

            while True:
                status = self._checkStatus()
                if status == "Operating":
                    time.sleep(5)
                else:
                    msg = "Sonication done"
                    break
            
            standbymode = self.standby()
            status = self._checkStatus()
            error_dict = self._checkStatusError('Standby',status)
            msg = "Sonic Standby? --> Standby : {}, Status : {}".format(bool(status=='Standby'),error_dict)
            self.logger_obj.debug(self.device_name, msg)
            
            msg= "Sonication done, Operate Mode: {}, Set Time: {} s, Heating Temp: {} °C".format(operate_mode ,set_time, target_temp)
            # self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
            res_msg = self.device_name + " : " + msg
            
            return res_msg


            

            
            # # self.logger_obj.debug(s3elf.device_name, msg)
        
        elif mode_type == "virtual":
            msg = "Sonication done, Operate Mode: {}, Set Time: {} s, Heating Temp: {} °C".format(operate_mode ,set_time, target_temp)
            self.logger_obj.debug(self.device_name, debug_msg=msg)
            res_msg = self.device_name + " : " + msg
            

            return msg
    


if __name__ == '__main__':
    NodeLogger_obj = NodeLogger(platform_name="Batch Synthesis", setLevel="DEBUG",
                            SAVE_DIR_PATH="/home/preprocess/Log")
    print(1)
    sonic = SonorexDigitec(logger_obj=NodeLogger_obj)

    # sonic.turnOff()
    # for i in range(10):
    sonic.operate(set_time = 10, target_temp = 0,mode_type="real")


    