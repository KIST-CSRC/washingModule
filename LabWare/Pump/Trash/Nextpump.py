import os, sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))# from Log.Logging_Class import NodeLogger
from pymodbus.client import ModbusSerialClient

from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian
from Pump.Device_Exception import DeviceError

from Log.Logging_Class import NodeLogger


import time


             
class Next3000FJ(DeviceError):
    """ 
    [NEXT300FJ] NEXT300FJ Class for controlling in another computer (windows)


    # Variable
    :param logger_obj (obj): set logging object (from Logging_class import Loggger) 
    :param device_name="NEXT300FJ" (str): set pump model name (log name)
    :param ser_port="COM10" (str): set sonic bath USB port 
    
    """
    
    def __init__(self, logger_obj, device_name = "Next3000FJ50"):
        
        #logger object
        self.logger_obj=logger_obj

        self.info = {
            "PORT" : "/dev/ttyPump3",
            "BOUNDRATE" : 9600,
            "ADDRESS" : 2
            }
        self.device_name = device_name
        self.client = ModbusSerialClient(port=self.info['PORT'],baudrate=self.info['BOUNDRATE'],parity='N',stopbits=1,bytesize=8)

        
        # supported function param list
        self.function_param = {
            "operate" : {
                "target_time" : [0, 600],
                "target_flow" : [0.007, 1140],
                }
            }
    def heartbeat(self):
            debug_msg="Hello World!! Succeed to connection to main computer!"
            debug_device_name="{} ({})".format(self.device_name, "heartbeat")
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
            return_res_msg="[{}] : {}".format(self.device_name, debug_msg)
            return return_res_msg
    
    def _decodeResponse(self, data_type, response):
        """
        decode modbus resoponse data

        :param data_type(str) : response data type
        :param response(byte) : response data 

        :return: decoded response

        """
        decoder = BinaryPayloadDecoder.fromRegisters(response, wordorder = Endian.BIG, byteorder =Endian.BIG)
        decoded_dict = {
                "string": decoder.decode_string, 
                "bits" : decoder.decode_bits,  
                "8int" : decoder.decode_8bit_int, 
                "8uint" : decoder.decode_8bit_uint, 
                "16int" : decoder.decode_16bit_int, 
                "16uint" : decoder.decode_16bit_uint, 
                "32int" : decoder.decode_32bit_int, 
                "32uint" : decoder.decode_32bit_uint, 
                "16float" : decoder.decode_16bit_float, 
                "32float" : decoder.decode_32bit_float, 
                "64int" : decoder.decode_64bit_int, 
                "64uint" : decoder.decode_64bit_uint, 
                "ignore" : decoder.skip_bytes,  
                "64float" : decoder.decode_64bit_float,
                }

        value = decoded_dict[data_type]()
        
        return value
    
    def _checkConnection(self):
        """
        Check connection and open client
        
        :return: error code --> (int)
        """
        error_code = 0
        
        self.client.connect()
        
        print(self.client.is_socket_open())
        
        if not self.client.is_socket_open():
            error_code = 2
            error_msg = "Failed to connect to Modbus/RTU server"
            self.raiseError(error_code, error_msg)
        
        return error_code


    def _readCoil(self, register_address, count):
        """
        read coil (0x01)

        :param register_address(int) : function register address
        :param count(int) : number of coils to read

        :return: response --> (bool)
        """
        response = self.client.read_coils(register_address, count = count, slave = self.info['ADDRESS'])
        time.sleep(1)
        return response.bits[0]
        
    def _writeCoil(self, register_address, value):
        """
        write coil (0x05)

        :param register_address(int) : function register address
        :param value(bool) : boolen to write

        :return: response --> (bool)
        """
        response = self.client.write_coil(register_address, slave= self.info['ADDRESS'], value=value)
        time.sleep(1)
        return response.value
        
    def _readInputRegister(self, register_address, count, data_type):
        """
        read input registers (0x04)

        :param register_address(int) : function register address
        :param count(int) : number of coils to read
        :param data_type(str) : response data type

        :return: response --> (bool or int or float)
        """
        response = self.client.read_input_registers(register_address, count = count, slave= self.info['ADDRESS'])
        time.sleep(1)
        value = self._decodeResponse(data_type, response.registers)

        return value
    
    def _readHoldingRegister(self, register_address, count, data_type):
        """
        read input registers (0x03)

        :param register_address(int) : function register address
        :param count(int) : number of coils to read
        :param data_type(str) : response data type

        :return: response --> (bool or int or float)
        """
        response = self.client.read_holding_registers(register_address, count = count, slave= self.info['ADDRESS'],)
        time.sleep(1)
        value = self._decodeResponse(data_type, response.registers)


        return value
    
    def _writeRegister(self, register_address, value):
        """
        read input registers (0x06)

        :param register_address(int) : function register address
        :param value(int) : value to write

        :return: response --> (int)
        """
        response = self.client.write_register(register_address, slave= self.info['ADDRESS'], value=value)
        time.sleep(1)
        return response.value
    

    def _writeRegisters(self, register_address, count, value):
        """
        read input registers (0x10)

        :param register_address(int) : function register address
        :param count(int) : number of coils to read
        :param value(float) : value to write

        :return: register address--> (int)
        """
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
        builder.add_32bit_float(value)
        payload = builder.build()
        response = self.client.write_registers(register_address, payload, skip_encode = True, count = count, slave= self.info['ADDRESS'])
        time.sleep(1)
        
        return response.address


    ################################################################################
    #                              Report commands                                 #
    ################################################################################

    def _checkStatus(self, ):
        """
        check the device operation.

        :return: command received value --> (bool) Operating => True, Stop => False
        """
        data_bool = self._readCoil(1,1)
        if data_bool:
            return 'Operating'    
        else:
            return 'Waiting'
        
    
    def _checkFlowRate(self,):
        """
        check the device operation.

        :return: command received value --> (float)
        """
        data_float = self._readHoldingRegister(5, 2, data_type="32float")

        return data_float

    def _start(self, ):
        """
        start the device operation.

        :return: command received value --> (bool)
        """
        data_bool = self._writeCoil(1,True)
        
        return data_bool
    
    def _stop(self,):
        """
        stop the device operation.

        :return: command received value --> (bool)
        """
        data_bool = self._writeCoil(1,False)
        
        return data_bool
    
    def _setWorkMode(self, value):
        """
        set the device work mode.

        :param value (int): transfer mode => 0, filling mode => 1

        :return: command received value --> (int)
        """
        data_int = self._writeRegister(1,value)

        return data_int
    
    def _setDirection(self, value):
        """
        set the device work mode.

        :param value (int): Counter Clockwise => 0, Clockwise => 1

        :return: command received value --> (int)
        """
        data_int = self._writeRegister(4,value)

        return data_int
    
    def _setFlowRate(self, value):
        """
        set device flow rate.
        
        :param value (float): set the flow rate. [ml/min : 0.007 to 1140]

        :return: command received value --> (float)
        """
        self._writeRegisters(5, 2, value)
        data_float = self._checkFlowRate()

        return data_float
    
    def _setPumpTube(self, value):
        """
        set device pump tube number.
        
        :param value (int): set the pump tube no. 06 => 18# (Current Tube No)

        :return: command received value --> (float)
        """
        data_int = self._writeRegister(3, value)
        
        return data_int
    
    def operate(self, target_time:int, target_flow:float=500, mode_type='virtual'):
        """
        start Next300FJ
        
        :param target_time(int) : [s : 0 to inf ]
        :param target_flow(float) : [ml/min : 0.007 to 1140]
        :param mode_type="virtual" (str): set virtual or real mode
        
        :return: res_msg --> (str)
        """
        debug_device_name="{} ({})".format(self.device_name, mode_type)

        self.checkInputError("Target Time", target_time, self.function_param["operate"]["target_time"]) 
        self.checkInputError("Target Flow", target_flow, self.function_param["operate"]["target_flow"])

        msg = "Injection ... Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
        self.logger_obj.debug(debug_device_name, msg)


        if mode_type == "real":
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting',status)
            msg ="Pump Waiting? Receive signal! --> Waiting : {}, Status : {}".format(bool(status=='Waiting'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)

            set_direction = self._setDirection(1
                                               )
            msg = "Flow rate setting done --> Set Direction : {} ".format(set_direction)
            self.logger_obj.debug(debug_device_name, msg)            
            set_flow = self._setFlowRate(target_flow)
            msg = "Flow rate setting done --> Set Flow Rate : {} ml/min".format(set_flow)
            self.logger_obj.debug(debug_device_name, msg)

            self._start()
            status = self._checkStatus()
            error_dict = self.checkStatusError('Operating',status)
            msg = "Operation Start! --> Operating : {}, Status : {}".format(bool(status=='Operating'),error_dict)
            self.logger_obj.debug(debug_device_name, msg)

            time.sleep(target_time)
            
            self._stop()
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting',status)
            msg = "Operation Stop! --> Waiting : {}, Status : {}".format(bool(status=='Waiting'),error_dict)
            self.logger_obj.debug(debug_device_name, msg)
            
            msg= "Injection done, Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg
        
        elif mode_type == "virtual":
            msg= "Injection done, Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg
    def removeLiquid(self, mode_type='virtual'):
        """
        start Next300FJ
        
        :param target_time(int) : [s : 0 to inf ]
        :param target_flow(float) : [ml/min : 0.007 to 1140]
        :param mode_type="virtual" (str): set virtual or real mode
        
        :return: res_msg --> (str)
        """
        debug_device_name="{} ({})".format(self.device_name, mode_type)
        target_time = 10
        target_flow = 1000
        self.checkInputError("Target Time", target_time, self.function_param["operate"]["target_time"]) 
        self.checkInputError("Target Flow", target_flow, self.function_param["operate"]["target_flow"])

        msg = "Injection ... Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
        self.logger_obj.debug(debug_device_name, msg)


        if mode_type == "real":
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting',status)
            msg ="Pump Waiting? Receive signal! --> Waiting : {}, Status : {}".format(bool(status=='Waiting'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)

            set_direction = self._setDirection(1)
            msg = "Flow rate setting done --> Set Direction : {} ".format(set_direction)
            self.logger_obj.debug(debug_device_name, msg)            
            set_flow = self._setFlowRate(target_flow)
            msg = "Flow rate setting done --> Set Flow Rate : {} ml/min".format(set_flow)
            self.logger_obj.debug(debug_device_name, msg)

            self._start()
            status = self._checkStatus()
            error_dict = self.checkStatusError('Operating',status)
            msg = "Operation Start! --> Operating : {}, Status : {}".format(bool(status=='Operating'),error_dict)
            self.logger_obj.debug(debug_device_name, msg)

            time.sleep(target_time)
            
            self._stop()
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting',status)
            msg = "Operation Stop! --> Waiting : {}, Status : {}".format(bool(status=='Waiting'),error_dict)
            self.logger_obj.debug(debug_device_name, msg)
            
            msg= "Injection done, Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg
        
        elif mode_type == "virtual":
            msg= "Injection done, Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg
    
    
        
if __name__ == "__main__":
    NodeLogger_obj = NodeLogger(platform_name="Electrochemical Analysis", setLevel="DEBUG",
                            SAVE_DIR_PATH="../EVALUATIONPLATFORM")

    Device  = Next3000FJ(logger_obj=NodeLogger_obj)
# 
    Device.operate(target_time=5,target_flow=600,mode_type="real")
    # print(Device._stop())

    # time.sleep(5)

    
    
    # Device._stop()