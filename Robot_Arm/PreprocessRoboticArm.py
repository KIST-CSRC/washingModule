#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##

# @brief    [py example simple] Robot Arm motion for doosan robot
# @author    Heeseung Lee (092508@kist.re.kr)


import socket
import os, sys
import time
import json

sys.dont_write_bytecode = True

# Normalize repository root and add only existing, repo-relative module paths.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
POTENTIAL_PATHS = [
    os.path.join(REPO_ROOT, "Robot_Arm"),
    os.path.join(REPO_ROOT, "Robot_Arm", "common", "imp"),
    os.path.join(
        REPO_ROOT, "Robot_Arm", "common", "imp"
    ),  # duplicate removed but kept for clarity
    os.path.join(REPO_ROOT, "detectron2"),
    os.path.join(REPO_ROOT, "detectron2", "RobotVisionCode"),
    os.path.join(REPO_ROOT, "yolact_vision"),
    os.path.join(REPO_ROOT, "Log"),
    os.path.join(REPO_ROOT, "BaseUtils"),
    os.path.join(REPO_ROOT, "LabWare"),
]

for p in POTENTIAL_PATHS:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

import cv2
from Log.Logging_Class import NodeLogger
from BaseUtils.Preprocess import PreprocessJSON
from BaseUtils.TCP_Node import BaseTCPNode

sys.dont_write_bytecode = True
# get import path : DSR_ROBOT.py

sys.path.append("../yolact_vision/")


from yolact_vision.yolact_CentriTask import YolactCentrifugeTask

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
import DR_init


DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL
from common.imp.DSR_ROBOT import *
from Robot_Arm.robot_teaching import *

# from preprocessVision import camera
import pandas as pd
import datetime

from LabWare.Arduino.CappingMachine import CappingMachine
from LabWare.Arduino.DeskLA import DeskLA
from LabWare.Arduino.DispenserLA import DispenserLA
from LabWare.Pump.Nextpump_3ea import Next3000FJ, NextPumpParemter

from detectron2.RobotVisionCode.Detector_Precipiate_Liquid import ObjectDetector

# Fundermental componant--------------------
#


class ParameterRobot:
    """
    general Actuator IP, PORT, location dict, move_z

    :param self.WINDOWS1_HOST = '161.122.22.146'  # The server's hostname or IP address
    :param self.PORT_UV = 54011       # The port used by the UV server (54011)
    """

    def __init__(self):
        self.info = {"HOST_ROBOT": "161.122.22.214", "PORT_ROBOT": 54011}


class Robot_Class(object):

    def __init__(self, logger_obj, device_name="PRE_ROBOT"):
        self.info = {
            "ROBOT_NAME": "PREPROCESS",
            # "ROBOT_HOST" : 54011
        }
        # ParameterRobocalculate_robot_coordinatest.__init__(self)
        BaseTCPNode.__init__(self)
        PreprocessJSON().__init__()
        self.logger_obj = logger_obj

        self.device_name = device_name
        self.YolactCentriTask = YolactCentrifugeTask()

    def _callServer_Robot(self, command_byte):
        res_msg = self.callServer(
            self.info["HOST_ROBOT"], self.info["PORT+ROBOT"], command_byte
        )

    def heartbeat(self):
        debug_msg = "Hello World!! Succeed to connection to main computer!"
        debug_device_name = "{} ({})".format(self.device_name, "heartbeat")
        self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)
        return_res_msg = "[{}] : {}".format(self.device_name, debug_msg)
        return return_res_msg

    def getRobotData(self, client_socket, action_type, mode_type="virtual"):
        """
        get Absorbance data using TCP/IP (socket)

        :param client_socket (str): input sockect object (main computer)
        :param action_type (str): chemical element (Ag,Au....)
        :param mode_type="virtual" (str): set virtual or real mode

        :return res_msg (bool): response_message --> [UV] : ~~~
        """
        debug_device_name = "{} ({})".format(self.device_name, mode_type)
        self.logger_obj.debug(
            device_name=debug_device_name,
            debug_msg="start get {} data".format(action_type),
        )
        # if mode_type == "real":
        command_byte = str.encode("{},{}".format(action_type, "NP"))

        # get json file name through Robot server
        file_name_decoded = self._callServer_Robot(command_byte)

        # open json content using open function
        total_json = self.openJSON(filename=file_name_decoded)
        ourbyte = self.encodeJSON(json_obj=total_json)

        # send big json file using parsing
        if len(ourbyte) > self.BUFF_SIZE:
            self.sendTotalJSON(client_socket=client_socket, ourbyte=ourbyte)
        else:
            client_socket.sendall(json.dumps(total_json).encode("utf-8"))

        # send finish message to main computer
        time.sleep(3)
        finish_msg = "finish"
        client_socket.sendall(finish_msg.encode())

        self.logger_obj.debug(device_name=debug_device_name, debug_msg=finish_msg)
        return_res_msg = "[{}] : {}".format(debug_device_name, finish_msg)
        return return_res_msg


def shutdown():
    print("shutdown time!")
    print("shutdown time!")
    print("shutdown time!")

    pub_stop.publish(stop_mode=STOP_TYPE_QUICK)
    return 0


def msgRobotState_cb(msg):
    msgRobotState_cb.count += 1

    if 0 == (msgRobotState_cb.count % 100000):
        rospy.loginfo("________ ROBOT STATUS ________")
        print("  robot_state           : %d" % msg.robot_state)
        print("  robot_state_str       : %s" % msg.robot_state_str)
        print("  actual_mode           : %d" % msg.actual_mode)
        print("  actual_space          : %d" % msg.actual_space)
        print(
            "  current_posj          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_posj[0],
                msg.current_posj[1],
                msg.current_posj[2],
                msg.current_posj[3],
                msg.current_posj[4],
                msg.current_posj[5],
            )
        )
        print(
            "  current_velj          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_velj[0],
                msg.current_velj[1],
                msg.current_velj[2],
                msg.current_velj[3],
                msg.current_velj[4],
                msg.current_velj[5],
            )
        )
        print(
            "  joint_abs             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.joint_abs[0],
                msg.joint_abs[1],
                msg.joint_abs[2],
                msg.joint_abs[3],
                msg.joint_abs[4],
                msg.joint_abs[5],
            )
        )
        print(
            "  joint_err             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.joint_err[0],
                msg.joint_err[1],
                msg.joint_err[2],
                msg.joint_err[3],
                msg.joint_err[4],
                msg.joint_err[5],
            )
        )
        print(
            "  target_posj           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.target_posj[0],
                msg.target_posj[1],
                msg.target_posj[2],
                msg.target_posj[3],
                msg.target_posj[4],
                msg.target_posj[5],
            )
        )
        print(
            "  target_velj           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.target_velj[0],
                msg.target_velj[1],
                msg.target_velj[2],
                msg.target_velj[3],
                msg.target_velj[4],
                msg.target_velj[5],
            )
        )
        print(
            "  current_posx          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_posx[0],
                msg.current_posx[1],
                msg.current_posx[2],
                msg.current_posx[3],
                msg.current_posx[4],
                msg.current_posx[5],
            )
        )
        print(
            "  current_velx          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_velx[0],
                msg.current_velx[1],
                msg.current_velx[2],
                msg.current_velx[3],
                msg.current_velx[4],
                msg.current_velx[5],
            )
        )
        print(
            "  task_err              : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.task_err[0],
                msg.task_err[1],
                msg.task_err[2],
                msg.task_err[3],
                msg.task_err[4],
                msg.task_err[5],
            )
        )
        print("  solution_space        : %d" % msg.solution_space)
        sys.stdout.write("  rotation_matrix       : ")
        for i in range(0, 3):
            sys.stdout.write("dim : [%d]" % i)
            sys.stdout.write("  [ ")
            for j in range(0, 3):
                sys.stdout.write("%d " % msg.rotation_matrix[i].data[j])
            sys.stdout.write("] ")
        print  # end line
        print(
            "  dynamic_tor           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.dynamic_tor[0],
                msg.dynamic_tor[1],
                msg.dynamic_tor[2],
                msg.dynamic_tor[3],
                msg.dynamic_tor[4],
                msg.dynamic_tor[5],
            )
        )
        print(
            "  actual_jts            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_jts[0],
                msg.actual_jts[1],
                msg.actual_jts[2],
                msg.actual_jts[3],
                msg.actual_jts[4],
                msg.actual_jts[5],
            )
        )
        print(
            "  actual_ejt            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_ejt[0],
                msg.actual_ejt[1],
                msg.actual_ejt[2],
                msg.actual_ejt[3],
                msg.actual_ejt[4],
                msg.actual_ejt[5],
            )
        )
        print(
            "  actual_ett            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_ett[0],
                msg.actual_ett[1],
                msg.actual_ett[2],
                msg.actual_ett[3],
                msg.actual_ett[4],
                msg.actual_ett[5],
            )
        )
        print("  sync_time             : %7.3f" % msg.sync_time)
        print(
            "  actual_bk             : %d %d %d %d %d %d"
            % (
                msg.actual_bk[0],
                msg.actual_bk[1],
                msg.actual_bk[2],
                msg.actual_bk[3],
                msg.actual_bk[4],
                msg.actual_bk[5],
            )
        )
        print(
            "  actual_bt             : %d %d %d %d %d "
            % (
                msg.actual_bt[0],
                msg.actual_bt[1],
                msg.actual_bt[2],
                msg.actual_bt[3],
                msg.actual_bt[4],
            )
        )
        print(
            "  actual_mc             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_mc[0],
                msg.actual_mc[1],
                msg.actual_mc[2],
                msg.actual_mc[3],
                msg.actual_mc[4],
                msg.actual_mc[5],
            )
        )
        print(
            "  actual_mt             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_mt[0],
                msg.actual_mt[1],
                msg.actual_mt[2],
                msg.actual_mt[3],
                msg.actual_mt[4],
                msg.actual_mt[5],
            )
        )

        # print digital i/o
        sys.stdout.write("  ctrlbox_digital_input : ")
        for i in range(0, 16):
            sys.stdout.write("%d " % msg.ctrlbox_digital_input[i])
        print  # end line
        sys.stdout.write("  ctrlbox_digital_output: ")
        for i in range(0, 16):
            sys.stdout.write("%d " % msg.ctrlbox_digital_output[i])
        print
        sys.stdout.write("  flange_digital_input  : ")
        for i in range(0, 6):
            sys.stdout.write("%d " % msg.flange_digital_input[i])
        print
        sys.stdout.write("  flange_digital_output : ")
        for i in range(0, 6):
            sys.stdout.write("%d " % msg.flange_digital_output[i])
        print
        # print modbus i/o
        sys.stdout.write("  modbus_state          : ")
        if len(msg.modbus_state) > 0:
            for i in range(0, len(msg.modbus_state)):
                sys.stdout.write("[" + msg.modbus_state[i].modbus_symbol)
                sys.stdout.write(", %d] " % msg.modbus_state[i].modbus_value)
        print

        print("  access_control        : %d" % msg.access_control)
        print("  homming_completed     : %d" % msg.homming_completed)
        print("  tp_initialized        : %d" % msg.tp_initialized)
        print("  mastering_need        : %d" % msg.mastering_need)
        print("  drl_stopped           : %d" % msg.drl_stopped)
        print("  disconnected          : %d" % msg.disconnected)


def msgRobotState_cb(msg):
    msgRobotState_cb.count += 1

    if 0 == (msgRobotState_cb.count % 100000):
        rospy.loginfo("________ ROBOT STATUS ________")
        print("  robot_state           : %d" % msg.robot_state)
        print("  robot_state_str       : %s" % msg.robot_state_str)
        print("  actual_mode           : %d" % msg.actual_mode)
        print("  actual_space          : %d" % msg.actual_space)
        print(
            "  current_posj          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_posj[0],
                msg.current_posj[1],
                msg.current_posj[2],
                msg.current_posj[3],
                msg.current_posj[4],
                msg.current_posj[5],
            )
        )
        print(
            "  current_velj          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_velj[0],
                msg.current_velj[1],
                msg.current_velj[2],
                msg.current_velj[3],
                msg.current_velj[4],
                msg.current_velj[5],
            )
        )
        print(
            "  joint_abs             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.joint_abs[0],
                msg.joint_abs[1],
                msg.joint_abs[2],
                msg.joint_abs[3],
                msg.joint_abs[4],
                msg.joint_abs[5],
            )
        )
        print(
            "  joint_err             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.joint_err[0],
                msg.joint_err[1],
                msg.joint_err[2],
                msg.joint_err[3],
                msg.joint_err[4],
                msg.joint_err[5],
            )
        )
        print(
            "  target_posj           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.target_posj[0],
                msg.target_posj[1],
                msg.target_posj[2],
                msg.target_posj[3],
                msg.target_posj[4],
                msg.target_posj[5],
            )
        )
        print(
            "  target_velj           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.target_velj[0],
                msg.target_velj[1],
                msg.target_velj[2],
                msg.target_velj[3],
                msg.target_velj[4],
                msg.target_velj[5],
            )
        )
        print(
            "  current_posx          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_posx[0],
                msg.current_posx[1],
                msg.current_posx[2],
                msg.current_posx[3],
                msg.current_posx[4],
                msg.current_posx[5],
            )
        )
        print(
            "  current_velx          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.current_velx[0],
                msg.current_velx[1],
                msg.current_velx[2],
                msg.current_velx[3],
                msg.current_velx[4],
                msg.current_velx[5],
            )
        )
        print(
            "  task_err              : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.task_err[0],
                msg.task_err[1],
                msg.task_err[2],
                msg.task_err[3],
                msg.task_err[4],
                msg.task_err[5],
            )
        )
        print("  solution_space        : %d" % msg.solution_space)
        sys.stdout.write("  rotation_matrix       : ")
        for i in range(0, 3):
            sys.stdout.write("dim : [%d]" % i)
            sys.stdout.write("  [ ")
            for j in range(0, 3):
                sys.stdout.write("%d " % msg.rotation_matrix[i].data[j])
            sys.stdout.write("] ")
        print  ##end line
        print(
            "  dynamic_tor           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.dynamic_tor[0],
                msg.dynamic_tor[1],
                msg.dynamic_tor[2],
                msg.dynamic_tor[3],
                msg.dynamic_tor[4],
                msg.dynamic_tor[5],
            )
        )
        print(
            "  actual_jts            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_jts[0],
                msg.actual_jts[1],
                msg.actual_jts[2],
                msg.actual_jts[3],
                msg.actual_jts[4],
                msg.actual_jts[5],
            )
        )
        print(
            "  actual_ejt            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_ejt[0],
                msg.actual_ejt[1],
                msg.actual_ejt[2],
                msg.actual_ejt[3],
                msg.actual_ejt[4],
                msg.actual_ejt[5],
            )
        )
        print(
            "  actual_ett            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_ett[0],
                msg.actual_ett[1],
                msg.actual_ett[2],
                msg.actual_ett[3],
                msg.actual_ett[4],
                msg.actual_ett[5],
            )
        )
        print("  sync_time             : %7.3f" % msg.sync_time)
        print(
            "  actual_bk             : %d %d %d %d %d %d"
            % (
                msg.actual_bk[0],
                msg.actual_bk[1],
                msg.actual_bk[2],
                msg.actual_bk[3],
                msg.actual_bk[4],
                msg.actual_bk[5],
            )
        )
        print(
            "  actual_bt             : %d %d %d %d %d "
            % (
                msg.actual_bt[0],
                msg.actual_bt[1],
                msg.actual_bt[2],
                msg.actual_bt[3],
                msg.actual_bt[4],
            )
        )
        print(
            "  actual_mc             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_mc[0],
                msg.actual_mc[1],
                msg.actual_mc[2],
                msg.actual_mc[3],
                msg.actual_mc[4],
                msg.actual_mc[5],
            )
        )
        print(
            "  actual_mt             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f"
            % (
                msg.actual_mt[0],
                msg.actual_mt[1],
                msg.actual_mt[2],
                msg.actual_mt[3],
                msg.actual_mt[4],
                msg.actual_mt[5],
            )
        )

        # print digital i/o
        sys.stdout.write("  ctrlbox_digital_input : ")
        for i in range(0, 16):
            sys.stdout.write("%d " % msg.ctrlbox_digital_input[i])
        print  ##end line
        sys.stdout.write("  ctrlbox_digital_output: ")
        for i in range(0, 16):
            sys.stdout.write("%d " % msg.ctrlbox_digital_output[i])
        print
        sys.stdout.write("  flange_digital_input  : ")
        for i in range(0, 6):
            sys.stdout.write("%d " % msg.flange_digital_input[i])
        print
        sys.stdout.write("  flange_digital_output : ")
        for i in range(0, 6):
            sys.stdout.write("%d " % msg.flange_digital_output[i])
        print
        # print modbus i/o
        sys.stdout.write("  modbus_state          : ")
        if len(msg.modbus_state) > 0:
            for i in range(0, len(msg.modbus_state)):
                sys.stdout.write("[" + msg.modbus_state[i].modbus_symbol)
                sys.stdout.write(", %d] " % msg.modbus_state[i].modbus_value)
        print

        print("  access_control        : %d" % msg.access_control)
        print("  homming_completed     : %d" % msg.homming_completed)
        print("  tp_initialized        : %d" % msg.tp_initialized)
        print("  mastering_need        : %d" % msg.mastering_need)
        print(
            "  drl_sfrom Robot_Arm.common.imp.topped           : %d" % msg.drl_stopped
        )
        print("  disconnected          : %d" % msg.disconnected)


def Robot_initialize():
    rospy.init_node("single_robot_simple_py", log_level=rospy.ERROR)
    rospy.on_shutdown(shutdown)
    global set_robot_mode
    set_robot_mode = rospy.ServiceProxy(
        "/" + ROBOT_ID + ROBOT_MODEL + "/system/set_robot_mode", SetRobotMode
    )
    t1 = threading.Thread(target=thread_subscriber)
    t1.daemon = True
    t1.start()
    global pub_stop
    pub_stop = rospy.Publisher(
        "/" + ROBOT_ID + ROBOT_MODEL + "/stop", RobotStop, queue_size=10
    )


msgRobotState_cb.count = 0


def get_status():
    robot_position = get_current_posx()
    return robot_position


def thread_subscriber():
    rospy.Subscriber(
        "/" + ROBOT_ID + ROBOT_MODEL + "/state", RobotState, msgRobotState_cb
    )
    rospy.spin()
    # rospy.spinner(2)


def VCGGripper(action_type="pick"):
    if action_type == "pick":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 500)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 1000)
        set_modbus_output("ONROBOT_CONTROL_2", 1000)
    elif action_type == "place":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 0)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 0)
        set_modbus_output("ONROBOT_CONTROL_2", 0)


def openGripper(action_type="Vial"):
    """
        ONROBOT_TARGET_FORCE_1: 0
        ONROBOT_TARGET_WIDTH_1: 0 (600 == 60mm)
        ONROBOT_CONTROL_1: 1 (1 == action)
        ONROBOT_ACTUAL_
    udevadm , with this command line, you need to u1: 0
    """
    if action_type == "Vial":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 500)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 200)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "Falcon":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 600)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 200)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "pipette":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 600)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 550)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "Capping":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 600)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 550)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "Falcon_Cap_bh":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 600)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 550)
        set_modbus_output("ONROBOT_CONTROL_2", 1)


def closeGripper(action_type="Vial"):
    if action_type == "Vial":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 250)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 250)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "test":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 100)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 350)
        set_modbus_output("ONROBOT_CONTROL_2", 1)

    elif action_type == "Falcon":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 400)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 350)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "pipette":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 350)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 750)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "Capping":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 400)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 250)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "Falcon_Cap_bh":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 380)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 550)
        set_modbus_output("ONROBOT_CONTROL_2", 1)
    elif action_type == "Falcon_PressCap_bh":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 150)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 550)
        set_modbus_output("ONROBOT_CONTROL_2", 1)


def pick(approach, leave, object_type):
    """
    pick (bird coordination(before pick) -> approach -> close gripper -> leave -> bird coordination)

    :param approach (int): approch distance
    :param leave (int): leave distance
    :param object_type (str): object type for gripper distance
        ex) Vial, Cuvette
    """
    movel(approach, vel=400, acc=50, ref=DR_TOOL)
    time.sleep(2)
    closeGripper(action_type=object_type)
    time.sleep(2)
    movel(leave, vel=400, acc=50, ref=DR_TOOL)


def place(approach, leave, object_type):
    """
    place (bird coordination(before pick) -> approach -> open gripper -> leave -> bird coordination)

    :param approach (int): approch distance
    :param leave (int): leave distance
    :param object_type (str): object type for gripper distance
        ex) Vial, Cuvette
    """
    # compliance_ctrl(action_type="on")
    movel(approach, vel=400, acc=50, ref=DR_TOOL)
    time.sleep(2)
    openGripper(action_type=object_type)
    time.sleep(2)
    movel(leave, vel=400, acc=50, ref=DR_TOOL)
    # compliance_ctrl(action_type="off")


def pick_VCG(approach, leave):
    """
    place (bird coordination(before pick) -> approach -> pick VCG -> leave -> bird coordination)
    :param approach (int): approch distance
    :param leave (int): leave distance
    """
    movel(approach, vel=400, acc=50, ref=DR_TOOL)
    time.sleep(3)
    VCGGripper(action_type="pick")
    movel(leave, vel=400, acc=50, ref=DR_TOOL)


def place_VCG(approach, leave):
    """
    pick (bird coordination(before place) -> approach -> place VCG -> leave -> bird coordination)

    :param approach (int): approch distance
    :param leave (int): leave distance
    """

    movel(approach, vel=400, acc=150, ref=DR_TOOL)
    VCGGripper(action_type="place")
    movel(leave, vel=400, acc=150, ref=DR_TOOL)


def insert(approach, object_type):
    movel(insert, vel=700, acc=200, ref=DR_TOOL)
    openGripper(action_type=object_type)


def compliance_ctrl(action_type="on"):
    if action_type == "on":
        task_compliance_ctrl(stx=[3000, 3000, 1000, 200, 200, 200])
    elif action_type == "off":
        release_compliance_ctrl()


def down(approach):
    movel(approach, vel=200, acc=50, ref=DR_TOOL)


def getcurrentpos():
    """
    Received the current robot position
    "holder0_falcon0 -> posx(-672.640, 181.580, 291.25, 90, 180, 90)"
    """
    return get_current_posx()


def pickandplacefalcon(
    NodeLogger_obj, pick_num, action_type="get_falcon", mode_type="virtual"
):
    """
    Performs pick and place operations for a falcon tube using a robot from vessel holder.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        pick_num (int): The index number of the falcon tube to be picked or placed.
        action_type (str, optional): The type of action to perform. It can be "get_falcon" to pick a falcon tube or "put_falcon" to place a falcon tube. Default is "get_falcon".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A success message indicating the completion of the pick and place operation.

    Note:
        - This function needs to be modified for RG6 and VCG cases.

    """

    if action_type == "get_falcon":
        if mode_type == "real":
            msg = "get falcon tube from holder ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
            for position in getFalconList:
                if position == falcon_holder_0_list:
                    msg = "Get falcontube{} ({})".format(pick_num, mode_type)
                    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
                    movel(position[pick_num], vel=800, acc=400, ref=DR_BASE)
                    pick(APPROACH_PICKFALCON, LEAVE_PICKFALCON, "Falcon")
                else:
                    movel(position, vel=800, acc=400, ref=DR_BASE)
    elif action_type == "put_falcon":
        if mode_type == "real":
            msg = "put falcon tube to holder ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
            if mode_type == "real":
                for position in placeFalconList:
                    if position == falcon_holder_0_list:
                        msg = "Place falcon tube {}th ({})".format(pick_num, mode_type)
                        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
                        movel(position[pick_num], vel=800, acc=400, ref=DR_BASE)
                        place(APPROACH_PLACEFALCON, LEAVE_PICKFALCON, "Falcon")

                    else:
                        movel(position, vel=800, acc=400, ref=DR_BASE)
    res_msg = "pickandplacefalcon-success {}".format(pick_num)
    return res_msg


def pickandplacevial(
    NodeLogger_obj, pick_num, action_type="get_vial", mode_type="virtual"
):
    """
    Performs pick and place operations for a vial using a robot from vessel holder.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        pick_num (int): The index number of the vial to be picked or placed.
        action_type (str, optional): The type of action to perform. It can be "get_vial" to pick a vial or "put_vial" to place a vial. Default is "get_vial".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A success message indicating the completion of the pick and place operation.

    Note:
        - This function needs to be modified for RG6 and VCG cases.

    """
    if action_type == "get_vial":
        if mode_type == "real":
            msg = "get vial tube from holder ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
            for position in getVialList:
                if position == vial_holder_0_list:
                    msg = "Get vialtube{} ({})".format(pick_num, mode_type)
                    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
                    movel(position[pick_num], vel=700, acc=300, ref=DR_BASE)
                    pick(APPROACH_PICKFALCON, LEAVE_PICKFALCON, "Vial")
                else:
                    movel(position, vel=700, acc=300, ref=DR_BASE)
    elif action_type == "put_vial":
        if mode_type == "real":
            msg = "put vial tube to holder ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
            if mode_type == "real":
                for position in placeVialList[::-1]:
                    if position == vial_holder_0_list:
                        msg = "Place vial tube {}th ({})".format(pick_num, mode_type)
                        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
                        movel(position[pick_num], vel=700, acc=300, ref=DR_BASE)
                        place(APPROACH_PLACEFALCON, LEAVE_PICKFALCON, "Vial")
                movel(DESK_HOME, vel=400, acc=150, ref=DR_BASE)
                # movel(INK_HOME, vel = 400, acc= 150, ref =DR_BASE)
    res_msg = "pickandplacevial-success {}".format(pick_num)
    return res_msg


def pickandplaceXYZActuator(
    NodeLogger_obj, pick_num, action_type="holder_to_XYZ_falcon", mode_type="virtual"
):
    """
    Performs pick and place operations for a falcon tube using a robot from holder to XYZ Actuator or XYZ to holder.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        pick_num (int): The index number of the falcon tube to be picked or placed.
        action_type (str, optional): The type of action to perform. It can be "holder_to_XYZ_falcon" to pick a falcon tube or "XYZ_to_holder_falcon" to place a falcon tube. Default is "get_falcon".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A success message indicating the completion of the pick and place operation.

    Note:
        - This function needs to be modified for RG6 and VCG cases.

    """
    msg = "{} {}th ({})".format(action_type, pick_num, mode_type)
    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
    if action_type == "holder_to_XYZ_falcon":
        if mode_type == "real":
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="get_falcon", mode_type=mode_type
            )
            for position in XYZ_falconTaskList:
                if position == XYZ_falconList:
                    movel(position[pick_num], vel=800, acc=300, ref=DR_BASE)
                    place(
                        APPROACH_PLACE_XYZFALCON,
                        LEAVE_PLACE_XYZFALCON,
                        object_type="Falcon",
                    )
                else:
                    movel(position, vel=800, acc=200, ref=DR_BASE)

    elif action_type == "XYZ_to_holder_falcon":
        if mode_type == "real":
            for position in XYZ_falconTaskList[::-1]:
                if position == XYZ_falconList:
                    movel(position[pick_num], vel=800, acc=300, ref=DR_BASE)
                    pick(
                        APPROACH_PICK_XYZFALCON,
                        LEAVE_PICK_XYZFALCON,
                        object_type="Falcon",
                    )

                else:
                    movel(position, vel=800, acc=200, ref=DR_BASE)
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="put_falcon", mode_type=mode_type
            )

    elif action_type == "holder_to_XYZ_vial":
        if mode_type == "real":
            pickandplacevial(
                NodeLogger_obj, pick_num, action_type="get_vial", mode_type=mode_type
            )
            for position in XYZ_vialTaskList:
                if position == XYZ_vialList:
                    movel(position[pick_num], vel=800, acc=300, ref=DR_BASE)
                    place(
                        APPROACH_PLACE_XYZVIAL, LEAVE_PLACE_XYZVIAL, object_type="Vial"
                    )

                else:
                    movel(position, vel=800, acc=300, ref=DR_BASE)
    elif action_type == "XYZ_to_holder_vial":
        if mode_type == "real":
            for position in XYZ_vialTaskList[::-1]:
                if position == XYZ_vialList:
                    movel(position[pick_num], vel=800, acc=300, ref=DR_BASE)
                    pick(APPROACH_PICK_XYZVIAL, LEAVE_PICK_XYZVIAL, object_type="Vial")
                else:
                    movel(position, vel=800, acc=300, ref=DR_BASE)
            pickandplacevial(
                NodeLogger_obj, pick_num, action_type="put_vial", mode_type=mode_type
            )
    res_msg = "XYZ{}-success {}".format(action_type, pick_num)
    return res_msg


def pickandplaceWeighing(
    NodeLogger_obj, pick_num, action_type="holder_to_weighing", mode_type="virtual"
):  # cycle_num추가 예정
    """
    Performs pick and place operations for a falcon tube or vial using a robot from a holder to an XYZ Actuator or vice versa.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        pick_num (int): The index number of the falcon tube or vial to be picked or placed.
        action_type (str, optional): The type of action to perform. It can be "holder_to_XYZ_falcon" to pick a falcon tube from the holder to the XYZ Actuator,
                                     "XYZ_to_holder_falcon" to place a falcon tube from the XYZ Actuator to the holder,
                                     "holder_to_XYZ_vial" to pick a vial from the holder to the XYZ Actuator,
                                     or "XYZ_to_holder_vial" to place a vial from the XYZ Actuator to the holder. Default is "holder_to_XYZ_falcon".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A success message indicating the completion of the pick and place operation.

    """
    msg = "{} {}th ({})".format(action_type, pick_num, mode_type)
    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
    if action_type == "holder_to_weighing":
        if mode_type == "real":
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="get_falcon", mode_type=mode_type
            )
            for position in satorius_weighingList:
                if position == satorius_weighingHOME:
                    movel(position, vel=800, acc=300, ref=DR_BASE)
                    place(APPROACH_PLACEWEIGH, LEAVE_PLACEWEIGH, object_type="Falcon")
                else:
                    movel(position, vel=800, acc=300, ref=DR_BASE)

    elif action_type == "weighing_to_holder":
        msg = "holder_to_weighing {}".format(pick_num)
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
        for position in satorius_weighingList[::-1]:
            if position == satorius_weighingHOME:
                movel(position, vel=800, acc=300, ref=DR_BASE)
                pick(APPROACH_PICKWEIGH, LEAVE_PICKWEIGH, object_type="Falcon")
            else:
                movel(position, vel=800, acc=300, ref=DR_BASE)
        pickandplacefalcon(
            NodeLogger_obj, pick_num, action_type="put_falcon", mode_type=mode_type
        )
    res_msg = "pickandplaceWeighing-success {}".format(pick_num)
    return res_msg


def pickandplaceSonic(
    NodeLogger_obj, pick_num, action_type="action_type ", mode_type="virtual"
):
    """
    Performs pick and place operations for a falcon tube using a robot from a holder to a sonic device or from the sonic device to a holder.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        pick_num (int): The index number of the falcon tube to be picked or placed.
        action_type (str, optional): The type of action to perform. It can be "holder_to_sonic" to place a falcon tube from the holder to the sonic device,
                                     or "sonic_to_holder" to place a falcon tube from the sonic device to the holder. Default is "holder_to_sonic".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A success message indicating the completion of the pick and place operation.

    Note:
        - This function may require future updates.

    """
    if action_type == "holder_to_sonic":
        if mode_type == "real":
            msg = "place the falcon tube to sonic holder {} ({})(추후 업데이트)".format(
                pick_num, mode_type
            )
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="get_falcon", mode_type=mode_type
            )
            for position in placeSonic_falconList:
                if position == Sonic_falconList:
                    msg = "Get falcontube{} ({})".format(pick_num, mode_type)
                    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
                    movel(position[pick_num], vel=800, acc=300, ref=DR_BASE)
                    place(APPROACH_SONIC_PLACEFALCON, LEAVE_SONIC_PLACEFALCON, "Falcon")
                else:
                    movel(position, vel=800, acc=300, ref=DR_BASE)
    elif action_type == "sonic_to_holder":
        if mode_type == "real":
            msg = "place the falcon tube to holder from sonic {}  ({})(추후 업데이트)".format(
                pick_num, mode_type
            )
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
            for position in placeSonic_falconList:
                if position == Sonic_falconList:
                    msg = "Get falcontube{} ({})".format(pick_num, mode_type)
                    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
                    movel(position[pick_num], vel=700, acc=300, ref=DR_BASE)
                    pick(APPROACH_SONIC_PICKFALCON, LEAVE_SONIC_PICKFALCON, "Falcon")
                else:
                    movel(position, vel=700, acc=300, ref=DR_BASE)
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="put_falcon", mode_type=mode_type
            )
    res_msg = "pickandplaceSonic-success {}".format(pick_num)
    return res_msg


def changetheGripper(
    NodeLogger_obj, action_type="change_the_gripper_to_RG6", mode_type="virtual"
):
    """
    Changes the gripper from VCG to RG6 or from RG6 to VCG.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        action_type (str, optional): The type of action to perform. It can be "change_the_gripper_to_RG6" to change the gripper from VCG to RG6,
                                     or "change_the_gripper_to_VCG" to change the gripper from RG6 to VCG. Default is "change_the_gripper_to_RG6".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A success message indicating the completion of the gripper change operation.

    Note:
        - The lists putVacuumGripperlist and equipRG6Gripperlist are not combined for safety reasons.

    """
    if action_type == "change_the_gripper_to_RG6":
        msg = "Change gripper from VCG to RG6 ({})".format(mode_type)
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
        if mode_type == "real":
            for position in putVacuumGripperlist:
                if position == VacuumGripperFront:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
                    time.sleep(3)
                else:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
            for position in equipRG6Gripperlist:
                if position == RG6GripperUp:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
                    time.sleep(2)
                elif position == RG6Gripper:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
                    time.sleep(1)
                else:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
        msg = "Complete change gripper from VCG to RG6!!! {}".format(mode_type)
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
        closeGripper(action_type="Falcon")
        openGripper(action_type="Falcon")

    elif action_type == "change_the_gripper_to_VCG":
        msg = "Change gripper from RG6 to VCG ({})".format(mode_type)
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
        if mode_type == "real":
            for position in putRG6Gripperlist:
                if position == RG6GripperFront:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
                    time.sleep(3)
                else:
                    movel(position, vel=300, acc=200, ref=DR_BASE)
            for position in equipVacuumGripperlist:
                if position == VacuumGripperUp:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
                    time.sleep(2)
                elif position == VacuumGripper:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
                    time.sleep(1)
                else:
                    movel(position, vel=500, acc=300, ref=DR_BASE)
            msg = "Complete change gripper from RG6 to VCG!!!({})".format(mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
            VCGGripper(action_type="pick")
            time.sleep(5)
            VCGGripper(action_type="place")
        else:
            msg = "Complete change gripper from RG6 to VCG!!! ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
    movel(DESK_HOME, vel=500, acc=300, ref=DR_BASE)
    res_msg = "changetheGripper-success "
    return res_msg


def CentriTaskwithVision(
    NodeLogger_obj, pick_num, action_type="place_falcon_to_centri", mode_type="virtual"
):
    """
    Performs tasks involving placing or picking falcon tubes into or from a centrifuge using vision guidance.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        pick_num (int): The index number of the falcon tube to be picked or placed.
        action_type (str, optional): The type of action to perform. It can be "place_falcon_to_centri" to place a falcon tube into the centrifuge,
                                     or "pick_falcon_from_centri" to pick a falcon tube from the centrifuge. Default is "place_falcon_to_centri".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A success message indicating the completion of the centrifuge task with vision guidance.

    Note :

    """
    msg = "{} {}th ({})".format(action_type, pick_num, mode_type)
    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
    if action_type == "place_falcon_to_centri":
        if mode_type == "real":
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="get_falcon", mode_type=mode_type
            )
            for position in Centri_vision_task_list:
                if position == rotor_front:
                    movel(rotor_front, vel=500, acc=150, ref=DR_BASE)
                    msg = "Detecting the objects falcon or hole"
                    yolact_instance = YolactCentrifugeTask()
                    current_point = yolact_instance.convert_robot_coordinates("Place")
                    transformed_holes = []
                    for current_hole in current_point["hole"]:
                        transformed_holes.append(posx(*current_hole))
                    print(transformed_holes)
                    movel(centerof_rotor, vel=100, acc=50, ref=DR_BASE)
                    movel(transformed_holes[0], vel=100, acc=50, ref=DR_BASE)
                    approach_hole = posx(0, 0, 45, 0, 0, 0)
                    movel(approach_hole, vel=50, acc=10, ref=DR_TOOL)
                    openGripper(action_type="Falcon")
                    time.sleep(1)
                    rf_jpos = posj(52.29, -29.55, -59.07, 0, -91.38, 52.29)
                    movej(rf_jpos, vel=100, acc=20)
                else:
                    movel(position, vel=700, acc=300, ref=DR_BASE)
            msg = "Complete the task insert falcon tube to Centrifuge ({})".format(
                mode_type
            )

    elif action_type == "pick_falcon_from_centri":
        if mode_type == "real":
            msg = "Pick falcon tube {}th from Centrfigue with VCG Gripper({})".format(
                pick_num, mode_type
            )

            if mode_type == "real":
                for position in Centri_vision_task_list:
                    if position == rotor_front:
                        movel(rotor_front, vel=500, acc=150, ref=DR_BASE)
                        msg = "Detecting the objects falcon or hole"

                        yolact_instance = YolactCentrifugeTask()
                        current_point = yolact_instance.convert_robot_coordinates(
                            "Pick"
                        )
                        transformed_falcons = []
                        for current_hole in current_point["falcon"]:
                            transformed_falcons.append(posx(*current_hole))

                        movel(transformed_falcons[0], vel=100, acc=50, ref=DR_BASE)
                        approach = posx(0, 0, 40, 0, 0, 0)
                        VCGGripper(action_type="pick")
                        movel(approach, vel=50, acc=10, ref=DR_TOOL)
                        leave = posx(0, 0, -60, 0, 0, 0)
                        movel(leave, vel=100, acc=40, ref=DR_TOOL)
                        rf_jpos = posj(52.29, -29.55, -59.07, 0, -91.38, 52.29)
                        movej(rf_jpos, vel=100, acc=20)
                    else:
                        movel(position, vel=700, acc=300, ref=DR_BASE)
                msg = "Align the falcon tube at align Falcon holder"

                movel(align_holder_VCG, vel=500, acc=150, ref=DR_BASE)
                place_VCG(
                    APPROACH_PLACEFALCON_VCG_ALIGN_HOLDER,
                    LEAVE_PLACEFALCON_VCG_ALIGN_HOLDER,
                )
                time.sleep(1)
                pick_VCG(
                    APPROACH_PLACEFALCON_VCG_ALIGN_HOLDER,
                    LEAVE_PLACEFALCON_VCG_ALIGN_HOLDER,
                )
                for position in placeFalconList:
                    if position == falcon_holder_0_list:
                        msg = "Place the falcon tube {}th ({}) ".format(
                            pick_num, mode_type
                        )

                        movel(position[pick_num], vel=700, acc=300, ref=DR_BASE)
                        place_VCG(
                            APPROACH_HOLDER_PLACEFALCON_VCG,
                            APPROACH_HOLDER_PLACELEAVE_VCG,
                        )
                    else:
                        movel(position, vel=700, acc=300, ref=DR_BASE)
            else:
                msg = "Place the falcon tube {}th ({}) ".format(pick_num, mode_type)
                NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
    res_msg = "CentriTaskwithVision-success "
    return res_msg


def pickandplaceDeskLA(
    NodeLogger_obj, pick_num, action_type="holder_to_DeskLA", mode_type="virtual"
):
    if action_type == "holder_to_DeskLA":
        msg = "Move container holder to DeskLA for washing task {}".format(mode_type)
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
        if mode_type == "real":
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="get_falcon", mode_type=mode_type
            )
            movel(DESK_HOME, vel=700, acc=300, ref=DR_BASE)
            movel(DeskLA_Holder_HOME, vel=700, acc=300, ref=DR_BASE)

            place(APPROACH_PICKFALCON_DeskLA, LEAVE_PICKFALCON_DeskLA, "Falcon")
            movel(INK_HOME, vel=700, acc=300, ref=DR_BASE)
            msg = "Place falcon tube{} ({})".format(pick_num, mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
    elif action_type == "DeskLA_to_holder":
        msg = "Finish the washing task, Move container DeskLA to holder ({})".format(
            mode_type
        )
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)
        if mode_type == "real":
            movel(DESK_HOME, vel=700, acc=300, ref=DR_BASE)
            movel(DeskLA_Holder_HOME, vel=700, acc=300, ref=DR_BASE)

            pick(APPROACH_PICKFALCON_DeskLA, LEAVE_PICKFALCON_DeskLA, "Falcon")
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="put_falcon", mode_type=mode_type
            )
            movel(INK_HOME, vel=700, acc=300, ref=DR_BASE)
            msg = "Place falcon tube{} ({})".format(pick_num, mode_type)
            NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)

    res_msg = "pickandplaceDeskLA-success "
    return res_msg


def OperateTheCentrifuge(
    NodeLogger_obj, action_type="start_centrifuge", mode_type="virtual"
):
    if action_type == "start_centrifuge":
        if mode_type == "real":
            msg = "Centrifuge Start ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="Centrifuge", debug_msg=msg)
            set_digital_output(1, OFF)
            time.sleep(0.1)
            set_digital_output(1, ON)
            time.sleep(0.1)
            set_digital_output(1, OFF)
            time.sleep(0.1)
        else:
            msg = "Centrifuge Start ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="Centrifuge", debug_msg=msg)
    elif action_type == "stop_centrifuge":
        if mode_type == "real":
            msg = "Centrifuge Stop ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="Centrifuge", debug_msg=msg)
            set_digital_output(2, OFF)
            time.sleep(0.1)
            set_digital_output(2, ON)
            time.sleep(0.1)
            set_digital_output(2, OFF)
            time.sleep(0.1)
        else:
            msg = "Centrifuge Stop ({})".format(mode_type)
            NodeLogger_obj.debug(device_name="Centrifuge", debug_msg=msg)

    res_msg = "OperateTheCentrifuge-success "
    return res_msg


def CappingProtocol(
    NodeLogger_obj, pick_num, action_type="OpenCap", mode_type="virtual"
):
    """
    Performs capping and uncapping operations on falcon tubes using a capping machine.

    Args:
        NodeLogger_obj (object): The logger object used for logging debug messages.
        pick_num (int): The index number of the falcon tube to be capped or uncapped.
        action_type (str, optional): The type of action to perform. It can be "OpenCap" to uncap the falcon tube,
                                     or "CloseCap" to cap the falcon tube. Default is "OpenCap".
        mode_type (str, optional): The mode of operation. It can be "real" for real-world operations or "virtual" for simulated operations. Default is "virtual".

    Returns:
        str: A message indicating the completion of the capping protocol.

    """
    Capping = CappingMachine(NodeLogger_obj, device_name="CappingMachine")
    msg = "Capping Protocol {}".format(mode_type)
    NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)

    if action_type == "OpenCap":
        msg = "Open Falcon tube Cap {}".format(mode_type)
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)

        if mode_type == "real":
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="get_falcon", mode_type=mode_type
            )
            movel(CappingMachineHome, vel=700, acc=300, ref=DR_BASE)
            movel(Opencap, vel=700, acc=300, ref=DR_BASE)
            Capping.Chuck_close(mode_type)
            time.sleep(3)
            openGripper(action_type="Falcon")
            time.sleep(2)

            for _ in range(1):
                movel(Opencap_2, vel=700, acc=300, ref=DR_BASE)
                time.sleep(1)
                closeGripper(action_type="Falcon")
                time.sleep(1)
                movej(Opencap_init, vel=100, acc=100)
                time.sleep(2)
                openGripper(action_type="Falcon")
                time.sleep(1)
                movej(Opencap_j, vel=100, acc=100)
                time.sleep(1)
                movel(Opencap_2, vel=700, acc=300, ref=DR_BASE)
                time.sleep(1)

            closeGripper(action_type="Falcon")
            compliance_ctrl(action_type="on")
            time.sleep(2)
            Capping.OpenCap(mode_type)
            time.sleep(3)
            time.sleep(1)
            movel(Opencap_up, vel=700, acc=300, ref=DR_BASE)
            time.sleep(1)
            closeGripper(action_type="Capping")
            time.sleep(1)

            movel(CappingMachineHome, vel=700, acc=300, ref=DR_BASE)
            compliance_ctrl(action_type="off")

            for position in placeCaplist:
                if position == Place_Cap_list:
                    movel(Place_Cap_list[pick_num], vel=700, acc=300, ref=DR_BASE)
                    place(CapApproach, CapLeave, object_type="Capping")
                else:
                    movel(position, vel=700, acc=300, ref=DR_BASE)

            time.sleep(3)
            movel(CappingMachineHome, vel=700, acc=300, ref=DR_BASE)
            time.sleep(3)
            movel(Opencap, vel=700, acc=300, ref=DR_BASE)
            time.sleep(3)
            closeGripper(action_type="Capping")
            Capping.Chuck_open(mode_type)
            movel(CappingMachineHome, vel=700, acc=300, ref=DR_BASE)
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="put_falcon", mode_type=mode_type
            )

    elif action_type == "CloseCap":
        msg = "Close Falcon tube Cap {}".format(mode_type)
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)

        if mode_type == "real":
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="get_falcon", mode_type=mode_type
            )
            movel(align_holder_RG6, vel=700, acc=300)
            movel(align_holder_RG6_Down, vel=700, acc=300)
            openGripper(action_type="Capping")

            for position in pickplaceCaplist[::1]:
                if position == Cap_list:
                    movel(Cap_list[pick_num], vel=700, acc=300, ref=DR_BASE)
                    pick(CapApproach, CapLeave, object_type="Falcon")
                else:
                    movel(position, vel=700, acc=300, ref=DR_BASE)

            movel(FalconAlign_Up_bh, vel=800, acc=600, ref=DR_BASE)
            place(FalconAlign_Approach_bh, FalconAlign_Leave_bh, object_type="Falcon")
            time.sleep(1)
            closeGripper(action_type="Falcon_PressCap_bh")
            time.sleep(1)
            movel(FalconAlign_Press_bh, vel=800, acc=600, ref=DR_BASE)
            movel(FalconAlign_Up_bh, vel=800, acc=600, ref=DR_BASE)
            time.sleep(1)
            openGripper(action_type="Falcon")
            time.sleep(1)
            movel(FalconAlign_bh, vel=800, acc=600, ref=DR_BASE)
            time.sleep(1)
            closeGripper(action_type="Falcon_Cap_bh")
            time.sleep(1)
            movel(Twist1_bh, vel=600, acc=400, ref=DR_BASE)
            movel(Twist2_bh, vel=600, acc=400, ref=DR_BASE)
            time.sleep(1)
            openGripper(action_type="Falcon")
            time.sleep(1)
            movel(FalconAlign_Up_bh, vel=600, acc=400, ref=DR_BASE)
            time.sleep(1)
            closeGripper(action_type="Falcon_PressCap_bh")
            time.sleep(1)
            movel(FalconAlign_StrongPress_bh, vel=600, acc=400, ref=DR_BASE)
            movel(FalconAlign_Up_bh, vel=800, acc=600, ref=DR_BASE)
            openGripper(action_type="Falcon")
            time.sleep(1)
            movel(FalconAlign_Up_bh, vel=800, acc=600, ref=DR_BASE)

            movel(align_holder_RG6_Down_Cap, vel=500, acc=300, ref=DR_BASE)
            closeGripper(action_type="test")
            time.sleep(2)
            movel(align_holder_RG6, vel=500, acc=300, ref=DR_BASE)

            movel(CappingMachineHome, vel=500, acc=300, ref=DR_BASE)
            movel(Closecap_0, vel=500, acc=300, ref=DR_BASE)
            Capping.Chuck_close(mode_type)
            time.sleep(2)
            Capping.CloseCap(mode_type)
            Capping.Chuck_open(mode_type)
            compliance_ctrl(action_type="off")
            movel(CappingMachineHome, vel=500, acc=300, ref=DR_BASE)
            pickandplacefalcon(
                NodeLogger_obj, pick_num, action_type="put_falcon", mode_type=mode_type
            )
        return msg


def ViewPointAlgorithm(NodeLogger_obj, mode_type="virtual"):
    """
    View Point Algorithm:
    - Performs vision-based centrifugation success/failure detection.
    - DeskLA first moves to the washing (camera) position before capturing images.
    - If uncertainty is high, the system changes viewpoints and retries (up to 6 times).
    - Returns "success" or "failure" based on visual detection.
    """
    if mode_type == "real":
        msg = f"View Point Algorithm for Washing Task ({mode_type})"
        NodeLogger_obj.debug(device_name="PRE_ROBOT", debug_msg=msg)

        # ----------------------------- #
        # Initialization
        # ----------------------------- #
        detector = ObjectDetector()
        detector.register_datasets()
        param_pump_obj = NextPumpParemter()
        DeskLA_obj = DeskLA(NodeLogger_obj, device_name="DeskLA")
        param_info_dict = param_pump_obj.info

        initial_View = [-38.84, -28.11, -78.64, 0, -73.26, -38.84]
        increments = 60  # degrees to rotate for each retry

        # ----------------------------- #
        # Move DeskLA to Washing (camera) position first
        # ----------------------------- #
        NodeLogger_obj.debug(
            device_name="PRE_ROBOT",
            debug_msg="Moving DeskLA to washing (camera) position...",
        )
        DeskLA_obj.DeskLA_To_Washing(mode_type=mode_type)
        time.sleep(1)

        # ----------------------------- #
        # Helper function: Vision detection
        # ----------------------------- #
        def perform_detection():
            """Capture image and detect precipitate or liquid."""
            NodeLogger_obj.debug(
                device_name="PRE_ROBOT",
                debug_msg="Capturing image for vision detection...",
            )
            image_path = detector.capture_and_save_image()
            filtered_instances, uncertainty_values = detector.perform_prediction(
                image_path
            )
            frame = cv2.imread(image_path)
            result_image = detector.visualize_predictions(frame, filtered_instances)
            detector.save_images_with_predictions(frame, result_image)
            detection_results = detector.extract_coordinates_and_classes(
                filtered_instances
            )
            detected_classes = detection_results.keys()
            high_uncertainty = any(
                value >= 0.1 for value in uncertainty_values.values()
            )
            return detected_classes, high_uncertainty

        # ----------------------------- #
        # Step 1: Initial detection (after DeskLA moved)
        # ----------------------------- #
        detected_classes, high_uncertainty = perform_detection()

        # ----------------------------- #
        # Step 2: Retry loop if uncertainty is high
        # ----------------------------- #
        if high_uncertainty:
            for attempt in range(6):
                NodeLogger_obj.debug(
                    device_name="PRE_ROBOT",
                    debug_msg=f"[Retry {attempt+1}/6] High uncertainty detected — rotating camera viewpoint",
                )

                # Move DeskLA and adjust camera viewpoint
                DeskLA_obj.ViewPointFromWashing(mode_type=mode_type)
                movel(ViewPointHome, vel=200, acc=100, ref=DR_BASE)
                movel(ViewPointHolder, vel=200, acc=100, ref=DR_BASE)
                closeGripper(action_type="Falcon")

                # Adjust the last joint (yaw rotation)
                new_posj = initial_View.copy()
                new_posj[-1] += increments * (attempt + 1)
                if new_posj[-1] > 180:
                    new_posj[-1] -= 360
                elif new_posj[-1] < -180:
                    new_posj[-1] += 360

                movej(posj(*new_posj), vel=100, acc=50)
                time.sleep(2)
                movel(posx(0, 0, 20, 0, 0, 0), vel=200, acc=100, ref=DR_TOOL)
                openGripper(action_type="Falcon")
                movej(ViewPoint_init_J, vel=200, acc=100)

                DeskLA_obj.WashingHOMEFromView(mode_type=mode_type)
                DeskLA_obj.DeskLA_To_Washing(mode_type=mode_type)
                time.sleep(1)
                detected_classes, high_uncertainty = perform_detection()

                if not high_uncertainty and "precipitate" in detected_classes:
                    NodeLogger_obj.debug(
                        device_name="PRE_ROBOT",
                        debug_msg="Centrifugation success after retries (vision confirmed)",
                    )
                    return "success"

            # After 6 retries still uncertain or failed
            NodeLogger_obj.debug(
                device_name="PRE_ROBOT",
                debug_msg="Centrifugation failed after 6 uncertain attempts",
            )
            return "failure"

        # ----------------------------- #
        # Step 3: Low uncertainty — determine success/failure
        # ----------------------------- #
        if not high_uncertainty:
            if "precipitate" in detected_classes:
                NodeLogger_obj.debug(
                    device_name="PRE_ROBOT",
                    debug_msg="Centrifugation success (vision confirmed)",
                )
                return "success"
            else:
                NodeLogger_obj.debug(
                    device_name="PRE_ROBOT",
                    debug_msg="No precipitate detected — centrifugation failed",
                )
                return "failure"

    # ----------------------------- #
    # Default (e.g., virtual mode)
    # ----------------------------- #
    NodeLogger_obj.debug(
        device_name="PRE_ROBOT",
        debug_msg=f"Running in virtual mode — returning default failure.",
    )
    return "failure"


if __name__ == "__main__":

    import os, sys

    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../Log"))
    )  # get import path : Logging_Class.py
    from Log.Logging_Class import NodeLogger

    NodeLogger_obj = NodeLogger(
        platform_name="preprocess platform",
        setLevel="DEBUG",
        SAVE_DIR_PATH="/home/preprocess/catkin_ws/src/doosan-robot/Log",
    )
    DeskLA_obj = DeskLA(NodeLogger_obj, device_name="DeskLA")
    DispenserLA_obj = DispenserLA(NodeLogger_obj, device_name="DispenserLA")

    movel(DESK_HOME, vel=800, acc=500, ref=DR_BASE)

    changetheGripper(
        NodeLogger_obj, action_type="change_the_gripper_to_VCG", mode_type="real"
    )

    changetheGripper(
        NodeLogger_obj, action_type="change_the_gripper_to_RG6", mode_type="real"
    )
