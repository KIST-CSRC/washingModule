#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [XCaliburD] Tecan Cavro Pump Class for controlling Syringe Pump (XCaliburD)
# 수정 버전: logger, device_name 만 받아서 객체 생성하도록 변경
# 기존 함수 로직은 동일, 나머지 파라미터는 device_config에서 로드

import os
import sys
import time
import copy
import os, sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Log")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "Syringe_Pump_Package")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from LabWare.Pump.Syringe_Pump_Package.transport import TecanAPISerial
from LabWare.Pump.Syringe_Pump_Package.tecanapi import TecanAPI, TecanAPITimeout


from Log import Logging_Class


class ParameterPump:
    """
    기존 내용 동일
    """
    def __init__(self):
        self.pump_info={
            "AgNO3":
                {"solutionType":"Metal",
                 "pumpAddress":1,
                 "pumpUsbAddr":"dev/ttyUSB7",
                 "deviceName":"XCaliburD"},
        }

    def preprocessPumpInformation(self):
        self.solution_name_list=list(self.pump_info.keys()) 
        self.solution_addr_list=list(self.pump_info.values()) 
        self.solution_type_list=[]
        for solution_addr_dict in self.solution_addr_list:
            self.solution_type_list.append(solution_addr_dict["solutionType"])

        preprocess_pump_info_dict={}
        preprocess_pump_info_dict["solutionNameList"]=self.solution_name_list
        preprocess_pump_info_dict["solutionAddrList"]=self.solution_addr_list
        preprocess_pump_info_dict["solutionTypeList"]=self.solution_type_list

        return preprocess_pump_info_dict


class XCaliburD(object):
    """
    [XCaliburD] 변경 사항:
      - __init__()에서 logger, device_name만 인자로 받음
      - 나머지 파라미터는 내부 device_config에서 불러옴
    """

    # 에러 사전(기존 동일)
    ERROR_DICT = {
        0: "Non Error",
        1: 'Initialization Error',
        2: 'Invalid Command',
        3: 'Invalid Operand',
        4: 'Invalid Command Sequence',
        6: 'EEPROM Failure',
        7: 'Device Not Initialized',
        9: 'Plunger Overload',
        10: 'Valve Overload',
        11: 'Plunger Move Not Allowed',
        15: 'Command Overflow'
    }

    # 장치별 설정값을 담아두는 사전 예시
    device_config = {
        # 원하는 device_name에 맞춰서 구성
        "Ethanol": {
            "solution_name": "Ethanol",
            "tecan_addr": 1,
            "ser_port": "/dev/ttyPumpSyrius",
            "baud_offset": 0,
            "syringe_volume": 5000,
            "ini": False,
            "max_attempts": 10
        },
        "Acetone": {
            "solution_name": "Acetone",
            "tecan_addr": 2,
            "ser_port": "/dev/ttyPumpSyrius",
            "baud_offset": 0,
            "syringe_volume": 5000,
            "ini": False,
            "max_attempts": 10
        },
        "H2O": {
            "solution_name": "H2O",
            "tecan_addr": 6,
            "ser_port": "/dev/ttyPumpSyrius",
            "baud_offset": 0,
            "syringe_volume": 5000,
            "ini": False,
            "max_attempts": 10
        },        
        # 필요하다면 다른 장치명을 추가로 정의
        # "XCaliburD_3": { ... }
    }

    def __init__(self, logger_obj, device_name="XCaliburD"):
        """
        user는 logger와 device_name만 넘겨주면 됨.
        나머지는 device_config에서 불러온다.
        """
        self.logger_obj = logger_obj
        self.device_name_only = device_name

        # device_config에서 설정 불러오기
        cfg = self.device_config.get(device_name, None)
        if cfg is None:
            raise ValueError(f"[XCaliburD] device_config에 '{device_name}' 키가 정의되어 있지 않습니다.")

        self.solution_name = cfg["solution_name"]
        self.tecan_addr = cfg["tecan_addr"]
        self.ser_port = cfg["ser_port"]
        # Baud rate는 9600 + 오프셋
        self.baud = 9600 + cfg["baud_offset"]
        self.syringe_volume = cfg["syringe_volume"]
        self.ini = cfg["ini"]
        self.max_attempts = cfg["max_attempts"]

        # 내부 변수들
        self.cmd_string = ""
        self.microstep = False
        self.base_increment = 3000

        # 실제 시리얼 객체 생성
        self.syringe_pump = TecanAPISerial(
            self.tecan_addr,
            self.ser_port,
            self.baud,
            max_attempts=self.max_attempts
        )

        self.setMicrostep(self.microstep)
        self.state = {
            'plunger_pos': None,
            'port': None,
            'microstep': self.microstep,
            'start_speed': None,
            'top_speed': None,
            'cutoff_speed': None,
        }

        # 초기화
        self.initialize()
        # 현재 속도값 업데이트
        self.updateSpeeds()

    #########################################################################
    # Report commands (cannot be chained)                                   #
    #########################################################################

    def updateSpeeds(self):
        self.getStartSpeed()
        self.getTopSpeed()
        self.getCutoffSpeed()
        self.getPlungerPos()
        self.getCurPort()

    def getStatus(self):
        cmd_string = "?29"
        status_dict = self.syringe_pump.sendRcv(cmd_string)
        return status_dict

    def getConfiguration(self):
        cmd_string = "?76"
        configuration_dict = self.syringe_pump.sendRcv(cmd_string)
        return configuration_dict

    def getPlungerPos(self):
        cmd_string = '?'
        data = self.syringe_pump.sendRcv(cmd_string)
        self.state['plunger_pos'] = int(data["data"])
        return self.state['plunger_pos']

    def getStartSpeed(self):
        cmd_string = '?1'
        data = self.syringe_pump.sendRcv(cmd_string)
        self.state['start_speed'] = int(data["data"])
        return self.state['start_speed']

    def getTopSpeed(self):
        cmd_string = '?2'
        data = self.syringe_pump.sendRcv(cmd_string)
        self.state['top_speed'] = int(data["data"])
        return self.state['top_speed']

    def getCutoffSpeed(self):
        cmd_string = '?3'
        data = self.syringe_pump.sendRcv(cmd_string)
        self.state['cutoff_speed'] = int(data["data"])
        return self.state['cutoff_speed']

    def getEncoderPos(self):
        cmd_string = '?4'
        data = self.syringe_pump.sendRcv(cmd_string)
        return int(data["data"])

    def getCurPort(self):
        cmd_string = '?6'
        data = self.syringe_pump.sendRcv(cmd_string)
        return data["data"]

    def getBufferStatus(self):
        cmd_string = '?10'
        data = self.syringe_pump.sendRcv(cmd_string)
        return data["data"]

    def getBackSlashIncrements(self):
        cmd_string = '?12'
        data = self.syringe_pump.sendRcv(cmd_string)
        return data["data"]

    def getNumberOfInitialization(self):
        cmd_string = '?15'
        data = self.syringe_pump.sendRcv(cmd_string)
        return int(data["data"])

    def getNumberOfPlungerMovements(self):
        cmd_string = '?16'
        data = self.syringe_pump.sendRcv(cmd_string)
        return int(data["data"])

    def getNumberOfValveMovements(self):
        cmd_string = '?17'
        data = self.syringe_pump.sendRcv(cmd_string)
        return int(data["data"])

    def getNumberOfLastValveMovements(self):
        cmd_string = '?18'
        data = self.syringe_pump.sendRcv(cmd_string)
        return int(data["data"])

    #########################################################################
    # Config commands                                                       #
    #########################################################################

    def setMicrostep(self, on=False):
        cmd_string = f'N{int(on)}'
        self.microstep = on
        if on:
            self.base_increment = 24000
        else:
            self.base_increment = 3000
        # 실제 실행
        self.syringe_pump.sendRcv(cmd_string)
        return self.syringe_pump.sendRcv(cmd_string)

    #########################################################################
    # Control commands                                                      #
    #########################################################################

    def terminateCmd(self):
        cmd_string = 'T'
        return self.syringe_pump.sendRcv(cmd_string)    

    def _ulToSteps(self, volume_ul, microstep=None):
        if microstep is None:
            microstep = self.state['microstep']
        if microstep:
            steps = int(volume_ul * (24000 / self.syringe_volume))
        else:
            steps = int(volume_ul * (3000 / self.syringe_volume))
        return steps

    def _checkStatus(self, status_byte):
        status_byte = status_byte["status_byte"]
        error_code = int(status_byte[4:8], 2)
        ready = int(status_byte[2])
        if ready == 1:
            self._ready = True
        else:
            self._ready = False
        error_dict = self.__class__.ERROR_DICT[error_code]
        if error_code != 0:
            raise ConnectionError("{} : {}".format(error_code, error_dict))
        return ready, error_dict

    def initialize(self, flow_rate=50, mode_type="virtual"):
        self.device_name = f"{self.device_name_only} pump {self.tecan_addr} ({mode_type})"
        if self.ini:
            self.cmd_string = f"ZV{flow_rate}BR"
            status_dic = self.syringe_pump.sendRcv(self.cmd_string)
            ready, error_msg = self._checkStatus(status_dic)
            msg = "Initializing..."
            self.logger_obj.debug(self.device_name, msg)

            while True:
                status_dic = self.getStatus()
                ready, error_msg = self._checkStatus(status_dic)
                if ready == 1:
                    break
                else:
                    time.sleep(5)
            msg = f"Initialization completed! : {status_dic}"
            ready, error_msg = self._checkStatus(status_dic)
            msg = f"Ready: {bool(ready)}, Status: {error_msg}"
            self.logger_obj.debug(self.device_name, msg)
        else:
            msg = "Intialization already finished!"
            data = self.syringe_pump.sendRcv("?17R")
            self.logger_obj.debug(self.device_name, f"msg:{msg}, data:{data}")

    def _divideSpeed(self, initSpeed):
        return int(round(initSpeed / 20))

    def add(self, volume, flow_rate, mode_type="virtual"):
        """
        add solution and inject syringe pump
        volume 단위 : ul
        flow_rate 단위 : ul/s (사용자가 던진다고 가정)
        """
        flow_rate = self._divideSpeed(flow_rate)
        temp_device_name = self.device_name + f" ({mode_type})"
        msg = f"Injecting... Solution: {self.solution_name}, Volume:{volume}, Speed:{flow_rate}"
        self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)

        if mode_type == "real":
            if volume <= self.syringe_volume:
                step = self._ulToSteps(volume)
                # I -> aspirate, O -> dispense, V -> speed(steps/s), A -> absolute step
                self.cmd_string = f"V1000IA{step}V{flow_rate}OA{0}R"
                status_dic = self.syringe_pump.sendRcv(self.cmd_string)
                ready, error_msg = self._checkStatus(status_dic)
                msg = f"Receive signal! --> Ready: {bool(ready)}, Status: {error_msg}"
                self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)

                while True:
                    status_dic = self.getStatus()
                    ready, error_msg = self._checkStatus(status_dic)
                    if ready:
                        msg = f"Injection done: {self.solution_name}!"
                        self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
                        break
                    else:
                        time.sleep(5)
                status_dic = self.getStatus()
                ready, error_msg = self._checkStatus(status_dic)
                msg = f"Pump Ready? Receive signal! --> Ready: {bool(ready)}, Status: {error_msg}"
                self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
                self.cmd_string = ""

            else:
                # syringe 용량 초과 시 여러 번에 나누어 주사
                cycle = int(volume / self.syringe_volume)
                last_volume = volume - (self.syringe_volume * cycle)
                cycle_step = self._ulToSteps(self.syringe_volume)
                last_step = self._ulToSteps(last_volume)
                # g, G : 반복문
                self.cmd_string = f"gV1000IA{flow_rate}V{cycle_step}OA0G{cycle}IA{last_step}OA0R"
                status_dic = self.syringe_pump.sendRcv(self.cmd_string)
                ready, error_msg = self._checkStatus(status_dic)
                msg = f"Receive signal! --> Ready: {bool(ready)}, Status: {error_msg}"
                self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)

                while True:
                    status_dic = self.getStatus()
                    ready, error_msg = self._checkStatus(status_dic)
                    if ready:
                        msg = f"Injection done: {self.solution_name}!"
                        self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
                        break
                    else:
                        time.sleep(5)
                status_dic = self.getStatus()
                msg = f"Pump Ready? Receive signal! --> Ready: {bool(ready)}, Status: {error_msg}"
                self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
                self.cmd_string = ""

            msg = f"Injection done, Solution: {self.solution_name}, Volume:{volume}, flow_rate:{flow_rate}"
            self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
            res_msg = temp_device_name + " : " + msg
            return res_msg

        elif mode_type == "virtual":
            msg = f"Injecting... Solution: {self.solution_name}, Volume:{volume}, Speed:{flow_rate}"
            self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
            msg = f"Injection done, Solution: {self.solution_name}, Volume:{volume}, flow_rate:{flow_rate}"
            self.logger_obj.debug(device_name=temp_device_name, debug_msg=msg)
            res_msg = temp_device_name + " : " + msg
            return res_msg

    def moveMaintainencePoint(self):
        self.cmd_string = "A3000R"
        status_dic = self.syringe_pump.sendRcv(self.cmd_string)
        return str(status_dic['status_byte'][2])

    def moveInputPoint(self):
        self.cmd_string = "V1000IR"
        status_dic = self.syringe_pump.sendRcv(self.cmd_string)
        return str(status_dic['status_byte'][2])

    def test(self):
        self.cmd_string = "V1000IA1000V20OA0R"
        status_dic = self.syringe_pump.sendRcv(self.cmd_string)
        return str(status_dic['status_byte'][2])


# 간단 호출 예시
if __name__ == '__main__':
    # logger 생성
    log_obj = Logging_Class.NodeLogger(setLevel="DEBUG")

    # user는 다음처럼 logger와 device_name만 넘겨서 객체 생성
    # obj_1 = XCaliburD(log_obj,device_name="XCaliburD", tecan_addr=1, ser_port="/dev/ttyPumpSyrius", baud=0, syringe_volume=5000, ini=True)
    # obj_2 = XCaliburD(log_obj,device_name="XCaliburD", tecan_addr=2, ser_port="/dev/ttyPumpSyrius", baud=0, syringe_volume=5000, ini=True)
    # obj_3 = XCaliburD(log_obj,device_name="XCaliburD", tecan_addr=5, ser_port="/dev/ttyPumpSyrius", baud=0, syringe_volume=5000, ini=True)
    Acetone = XCaliburD(logger_obj=log_obj, device_name="Acetone")  
    Ethanol = XCaliburD(logger_obj=log_obj, device_name="Ethanol")
    # Ethanol.add(volume=5000, flow_rate=40000, mode_type="real")
    H2O = XCaliburD(logger_obj=log_obj, device_name="H2O")
    # H2O.add(volume=5000, flow_rate=40000, mode_type="real")
    # self.cmd_string = f"V1000IA{step}V{flow_rate}OA{0}R"
    # 실제 동작(예시)
    for i in range(4):
        Acetone.add(volume=5000, flow_rate=40000, mode_type="real")
        Ethanol.add(volume=5000, flow_rate=40000, mode_type="real")
        # H2O.add(volume=5000, flow_rate=40000, mode_type="real")
    #     time.sleep(10)
    # pump_obj_2.moveMaintainencePoint()
