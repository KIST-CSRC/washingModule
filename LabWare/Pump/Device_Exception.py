#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [Device_Exception] Class for handling device exception 
# @author   Daeho Kim (r4576@kist.re.kr)
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))# from Log.Logging_Class import NodeLogger
from Log.Logging_Class import NodeLogger

from Log.Logging_Class import NodeLogger

class OperationError(Exception):
    pass

class CommandError(Exception):
    pass

class DeviceError():
    
    def __init__(self, logger_obj, device_name):
        #logger object
        self.logger_obj=logger_obj


        self.device_name = device_name


    ERROR_DICT = {
        0 : "Non Error",
        1 : "Connection Error",
        2 : "Operation Error",
        3 : "Invaild Command",
        4 : "Value Error",
        }


    def raiseError(self, code, msg) :
        """
        raise error message

        :param code(int) : error code
        :param msg(str) : input error massage
        """
        error_device_name="{} (error)".format(self.device_name,)

        if code == 0 :    
            pass
        elif code == 1 :
            msg = "Error code --> {} : {}".format(code,msg)
            self.logger_obj.error(error_device_name, msg)
            raise ConnectionError (msg)
        elif code == 2 :
            msg = "Error code --> {} : {}".format(code,msg)
            self.logger_obj.error(error_device_name, msg)
            raise OperationError (msg)
        elif code == 3 :
            msg = "Error code --> {} : {}".format(code,msg)
            self.logger_obj.error(error_device_name, msg)
            raise CommandError (msg)
        elif code == 4 :
            msg = "Error code --> {} : {}".format(code,msg)
            self.logger_obj.error(error_device_name, msg)
            raise ValueError (msg)
        
    def checkCondition(self, condition, error_code, error_msg):
        if not condition :
            self.raiseError(error_code, error_msg)
            
        else :
            error_code = 0

            return error_code

    def checkInputError(self, cmd, value, supported_values):
        """
        check input value of command

        :param cmd(str) : command
        :param value(str or int) : value
        :param spported_values(list) : supported value list

        :return: error code --> (int)
        """
        if type(value) == str :
            if value in supported_values :
                error_code = 0

            else :
                error_code = 4
                error_msg = "{} parameter input error " + " (avilable input list : {})".format(cmd, supported_values)
                self.raiseError(error_code, error_msg)

            return error_code
        
        elif type(value) == int:                        
            min_value = supported_values[0]
            max_value = supported_values[1]
            if value >= min_value and value <= max_value :
                error_code = 0

            else :
                error_code = 2
                error_msg = "{} function value out of range (min value : {}, max value : {})".format(cmd, min_value, max_value)
                self.raiseError(error_code, error_msg)
                
            return self.ERROR_DICT[error_code]


    def checkStatusError(self, send_status, receive_status):
        """
        check status error
        
        :param send_status(str) : input status
        :param receive_status(str) : output status

        :return: error massage --> (str)
        """
        if send_status == receive_status :
            error_code=0

        else :
            error_code=2
            error_msg = "Status mismatch : {}".format(receive_status)
            self.raiseError(error_code, error_msg)

        return self.ERROR_DICT[error_code]
    
