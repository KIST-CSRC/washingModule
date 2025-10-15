import os, sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))# from Log.Logging_Class import NodeLogger
import time
from pymodbus.client import ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian
from Pump.Device_Exception import DeviceError
from Log.Logging_Class import NodeLogger

# 경로 설정

class NextPumpParemter():
    def __init__(self):
        self.info = {
            "Remove": {
                "PORT": "/dev/ttyPump1",
                "BAUDRATE": 9600,
                "ADDRESS": 7,
                "set_direction": 1,
                "DeviceName": "NextPump",
                "Solvent_type": "Remove"
            },
            "H2O": {
                "PORT": "/dev/ttyPump2",
                "BAUDRATE": 9600,
                "ADDRESS": 2,
                "set_direction": 1,
                "DeviceName": "NextPump",
                "Solvent_type": "H2O"
            },
            "Ethanol": {
                "PORT": "/dev/ttyPump4",
                "BAUDRATE": 9600,
                "ADDRESS": 9,
                "set_direction": 1,
                "DeviceName": "NextPump",
                "Solvent_type": "Ethanol"
            }
        }
        
        self.pump_connection_info = {}

    def preprocessPumpInformation(self):
        self.solution_name_list = list(self.info.keys())
        self.solution_addr_list = list(self.info.values())
        self.solution_type_list = []

        for solution_addr_dict in self.solution_addr_list:
            self.solution_type_list.append(solution_addr_dict["Solvent_type"])
        
        preprocess_info_dict = {
            "solutionNameList": self.solution_name_list,
            "solutionAddrList": self.solution_addr_list
        }
        
        return preprocess_info_dict  

class Next3000FJ(DeviceError):
    def __init__(self, logger_obj, device_name="Next3000FJ", Nextpump_Addr=0, baudrate=9600, solution_name="", PORT="/dev/ttyPump2", set_direction=0):
        self.logger_obj = logger_obj
        self.device_name = "{} pump {}".format(device_name, str(Nextpump_Addr))
        self.solution_name = solution_name
        self.Nextpump_Addr = Nextpump_Addr
        self.PORT = PORT
        self.baudrate = baudrate
        self.set_direction = set_direction

        self.client = ModbusSerialClient(
            port=self.PORT,
            baudrate=self.baudrate,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=5  # 타임아웃 설정
        )

        self.function_param = {
            "operate": {
                "target_time": [0, 600],
                "target_flow": [0.007, 1140],
                "target_volume": [0.001, 9999000]
            }
        }

    def ensure_connection(self):
        if not self.client.is_socket_open():
            self.client.connect()
            if not self.client.is_socket_open():
                self.raiseError(2, "Failed to reconnect to Modbus/RTU server")

    def _retry_operation(self, func, max_retries=3, *args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.logger_obj.error(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        self.raiseError(1, "Max retries exceeded.")

    def heartbeat(self):
        debug_msg = "Hello World!! Succeed to connection to main computer!"
        debug_device_name = "{} ({})".format(self.device_name, "heartbeat")
        self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
        return_res_msg = "[{}] : {}".format(self.device_name, debug_msg)
        return return_res_msg

    def _decodeResponse(self, data_type, response):
        decoder = BinaryPayloadDecoder.fromRegisters(response, wordorder=Endian.BIG, byteorder=Endian.BIG)
        decoded_dict = {
            "string": decoder.decode_string, 
            "bits": decoder.decode_bits,  
            "8int": decoder.decode_8bit_int, 
            "8uint": decoder.decode_8bit_uint, 
            "16int": decoder.decode_16bit_int, 
            "16uint": decoder.decode_16bit_uint, 
            "32int": decoder.decode_32bit_int, 
            "32uint": decoder.decode_32bit_uint, 
            "16float": decoder.decode_16bit_float, 
            "32float": decoder.decode_32bit_float, 
            "64int": decoder.decode_64bit_int, 
            "64uint": decoder.decode_64bit_uint, 
            "ignore": decoder.skip_bytes,  
            "64float": decoder.decode_64bit_float,
        }

        value = decoded_dict[data_type]()
        return value

    def _readCoil(self, register_address, count):
        self.ensure_connection()
        response = self._retry_operation(self.client.read_coils, 3, register_address, count=count, slave=self.Nextpump_Addr)
        time.sleep(0.1)
        return response.bits[0]

    def _writeCoil(self, register_address, value):
        self.ensure_connection()
        response = self._retry_operation(self.client.write_coil, 3, register_address, value=value, slave=self.Nextpump_Addr)
        time.sleep(0.1)
        return response.value

    def _readInputRegister(self, register_address, count, data_type):
        self.ensure_connection()
        response = self._retry_operation(self.client.read_input_registers, 3, register_address, count=count, slave=self.Nextpump_Addr)
        time.sleep(0.1)
        value = self._decodeResponse(data_type, response.registers)
        return value

    def _readHoldingRegister(self, register_address, count, data_type):
        self.ensure_connection()
        response = self._retry_operation(self.client.read_holding_registers, 3, register_address, count=count, slave=self.Nextpump_Addr)
        time.sleep(0.1)
        value = self._decodeResponse(data_type, response.registers)
        return value

    def _writeRegister(self, register_address, value):
        self.ensure_connection()
        response = self._retry_operation(self.client.write_register, 3, register_address, value=value, slave=self.Nextpump_Addr)
        time.sleep(0.1)
        return response.value

    def _writeRegisters(self, register_address, count, value):
        self.ensure_connection()
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
        builder.add_32bit_float(value)
        payload = builder.build()
        response = self._retry_operation(self.client.write_registers, 3, register_address, payload, skip_encode=True, count=count, slave=self.Nextpump_Addr)
        time.sleep(0.1)
        return response.address

    def _checkStatus(self):
        data_bool = self._readCoil(1, 1)
        return 'Operating' if data_bool else 'Waiting'
        
    def _checkFlowRate(self):
        data_float = self._readHoldingRegister(5, 2, data_type="32float")
        return data_float

    def _checkFillingVolume(self):
        data_float = self._readHoldingRegister(9, 2, data_type="32float")
        return data_float

    def _checkFillingTime(self):
        data_float = self._readHoldingRegister(11, 2, data_type="32float")
        return data_float
    
    def _checkRegister(self, ad, count):
        data_float = self._readHoldingRegister(ad, count, data_type="32float")
        return data_float
    
    def _start(self):
        data_bool = self._writeCoil(1, True)
        return data_bool
    
    def _stop(self):
        data_bool = self._writeCoil(1, False)
        return data_bool
    
    def _setWorkMode(self, value):
        data_int = self._writeRegister(1, value)
        return data_int
    
    def _setDirection(self, value):
        data_int = self._writeRegister(4, value)
        return data_int
    
    def _setFlowRate(self, value):
        self._writeRegisters(5, 2, value)
        data_float = self._checkFlowRate()
        return data_float
    
    def _setFillingVolume(self, value):
        self._writeRegisters(9, 2, value)
        data_float = self._checkFillingVolume()
        return data_float
    
    def _setFillingTime(self, value):
        self._writeRegisters(11, 2, value)
        data_float = self._checkFillingTime()
        return data_float
    
    def _setPumpTube(self, value):
        data_int = self._writeRegister(3, value)
        return data_int

    def operate(self, target_time:int, target_flow:float=500, mode_type='virtual'):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        self.checkInputError("Target Time", target_time, self.function_param["operate"]["target_time"]) 
        self.checkInputError("Target Flow", target_flow, self.function_param["operate"]["target_flow"])

        msg = "Injection ... Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
        self.logger_obj.debug(debug_device_name, msg)

        if mode_type == "real":
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting', status)
            msg = "Pump Waiting? Receive signal! --> Waiting : {}, Status : {}".format(bool(status == 'Waiting'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)

            set_tupe = self._setPumpTube(6)
            msg = "Flow rate setting done --> Set Tube : {} ".format(set_tupe)
            self.logger_obj.debug(debug_device_name, msg)

            set_direction = self._setDirection(self.set_direction)
            msg = "Flow rate setting done --> Set Direction : {} ".format(set_direction)
            self.logger_obj.debug(debug_device_name, msg)
            
            set_flow = self._setFlowRate(target_flow)
            msg = "Flow rate setting done --> Set Flow Rate : {} ml/min".format(set_flow)
            self.logger_obj.debug(debug_device_name, msg)

            self._start()
            status = self._checkStatus()
            error_dict = self.checkStatusError('Operating', status)
            msg = "Operation Start! --> Operating : {}, Status : {}".format(bool(status == 'Operating'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)

            time.sleep(target_time)
            
            self._stop()
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting', status)
            msg = "Operation Stop! --> Waiting : {}, Status : {}".format(bool(status == 'Waiting'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)
            
            msg = "Injection done, Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg
        
        elif mode_type == "virtual":
            msg = "Injection done, Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_flow)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg

    def Filling(self, target_time:int, target_volume:float=10.0, mode_type='virtual'):
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        self.checkInputError("Target Time", target_time, self.function_param["operate"]["target_time"]) 
        self.checkInputError("Target Volume", target_volume, self.function_param["operate"]["target_volume"])
        msg = "Injection ... Set Time: {} s, Filling Volume : {} ml".format(target_time, target_volume)
        self.logger_obj.debug(debug_device_name, msg)

        if mode_type == "real":
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting', status)
            msg = "Pump Waiting? Receive signal! --> Waiting : {}, Status : {}".format(bool(status == 'Waiting'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)

            set_mode = self._setWorkMode(1)
            msg = "Work mode setting done --> Set Mode : {} ".format(set_mode)
            self.logger_obj.debug(debug_device_name, msg)     
            
            set_tupe = self._setPumpTube(5)
            msg = "Pumptube setting done --> Set Tube : {} ".format(set_tupe)
            self.logger_obj.debug(debug_device_name, msg)

            set_direction = self._setDirection(self.set_direction)
            msg = "Direction setting done --> Set Direction : {} ".format(set_direction)
            self.logger_obj.debug(debug_device_name, msg)

            set_time = self._setFillingTime(target_time)
            msg = "Filling Time setting done --> Set Filling Time : {} s".format(set_time)
            self.logger_obj.debug(debug_device_name, msg)

            set_volume = self._setFillingVolume(target_volume)
            msg = "Filling Volume setting done --> Set Filling Volume : {} ml".format(set_volume)
            self.logger_obj.debug(debug_device_name, msg)

            status = self._checkStatus()
            msg = "Operation Start! --> Operating : {}, Status : {}".format(bool(status == 'Operating'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)
            
            self._start()
            
            time.sleep(target_time)
            
            self._stop()
            
            status = self._checkStatus()
            error_dict = self.checkStatusError('Waiting', status)
            msg = "Operation Stop! --> Waiting : {}, Status : {}".format(bool(status == 'Waiting'), error_dict)
            self.logger_obj.debug(debug_device_name, msg)
            
            msg = "Injection done, Set Time: {} s, Filling Volume : {} ml".format(target_time, target_volume)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg
        
        elif mode_type == "virtual":
            msg = "Injection done, Set Time: {} s, Flow Rate : {} ml/min".format(target_time, target_volume)
            self.logger_obj.debug(device_name=debug_device_name, debug_msg=msg)
            res_msg = debug_device_name + " : " + msg

            return res_msg

if __name__ == "__main__":
    NodeLogger_obj = NodeLogger(platform_name="Electrochemical Analysis", setLevel="DEBUG", SAVE_DIR_PATH="../EVALUATIONPLATFORM")
    param_pump_obj = NextPumpParemter()
    param_info_dict = param_pump_obj.info

    pumps = {}

    # 각 펌프 인스턴스 생성
    for Solvent_type, pump_info in param_info_dict.items():
        pump_instance = Next3000FJ(
            logger_obj=NodeLogger_obj, 
            device_name=pump_info["DeviceName"],
            Nextpump_Addr=pump_info["ADDRESS"],
            solution_name=Solvent_type, 
            PORT=pump_info["PORT"], 
            baudrate=pump_info["BAUDRATE"], 
            set_direction=pump_info["set_direction"]
        )
        pumps[Solvent_type] = pump_instance

    # 펌프 사용 예시
    ethanol_pump = pumps["Ethanol"]
    RemoveLiquid_pump = pumps["Remove"]
    H2O_pump = pumps["H2O"]
    # for j in range(3):
    #     for i in range(2):
    #         ethanol_pump.Filling(3, 3, "real")
    #     for i in range(2):
    # RemoveLiquid_pump.Filling(10,10,"real")
        # for i in range(2):
    ethanol_pump.Filling(10,10,"real")