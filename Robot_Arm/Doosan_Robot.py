#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [py example simple] Robot Arm motion for doosan robot
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr) // Nayeon Kim (kny@kist.re.kr)
# @version 1_2
# TEST 2021-09-23
# Test 2022-04-13

import rospy
import os
import threading, time
import sys

sys.dont_write_bytecode = True
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "./common/imp")))  # get import path : DSR_ROBOT.py
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../Robot_Arm")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) 

# for single robot
ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
import DR_init
DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL
from DSR_ROBOT import *
from robot_teaching import *
# from TCP_Connection.TCP import TCP_Class
# Fundermental componant-----------------------------------------------------------------------------------------------
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
        print("  current_posj          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.current_posj[0], msg.current_posj[1], msg.current_posj[2], msg.current_posj[3], msg.current_posj[4],
            msg.current_posj[5]))
        print("  current_velj          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.current_velj[0], msg.current_velj[1], msg.current_velj[2], msg.current_velj[3], msg.current_velj[4],
            msg.current_velj[5]))
        print("  joint_abs             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.joint_abs[0], msg.joint_abs[1], msg.joint_abs[2], msg.joint_abs[3], msg.joint_abs[4], msg.joint_abs[5]))
        print("  joint_err             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.joint_err[0], msg.joint_err[1], msg.joint_err[2], msg.joint_err[3], msg.joint_err[4], msg.joint_err[5]))
        print("  target_posj           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.target_posj[0], msg.target_posj[1], msg.target_posj[2], msg.target_posj[3], msg.target_posj[4],
            msg.target_posj[5]))
        print("  target_velj           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.target_velj[0], msg.target_velj[1], msg.target_velj[2], msg.target_velj[3], msg.target_velj[4],
            msg.target_velj[5]))
        print("  current_posx          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.current_posx[0], msg.current_posx[1], msg.current_posx[2], msg.current_posx[3], msg.current_posx[4],
            msg.current_posx[5]))
        print("  current_velx          : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.current_velx[0], msg.current_velx[1], msg.current_velx[2], msg.current_velx[3], msg.current_velx[4],
            msg.current_velx[5]))
        print("  task_err              : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.task_err[0], msg.task_err[1], msg.task_err[2], msg.task_err[3], msg.task_err[4], msg.task_err[5]))
        print("  solution_space        : %d" % msg.solution_space)
        sys.stdout.write("  rotation_matrix       : ")
        for i in range(0, 3):
            sys.stdout.write("dim : [%d]" % i)
            sys.stdout.write("  [ ")
            for j in range(0, 3):
                sys.stdout.write("%d " % msg.rotation_matrix[i].data[j])
            sys.stdout.write("] ")
        print  ##end line
        print("  dynamic_tor           : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.dynamic_tor[0], msg.dynamic_tor[1], msg.dynamic_tor[2], msg.dynamic_tor[3], msg.dynamic_tor[4],
            msg.dynamic_tor[5]))
        print("  actual_jts            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.actual_jts[0], msg.actual_jts[1], msg.actual_jts[2], msg.actual_jts[3], msg.actual_jts[4],
            msg.actual_jts[5]))
        print("  actual_ejt            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.actual_ejt[0], msg.actual_ejt[1], msg.actual_ejt[2], msg.actual_ejt[3], msg.actual_ejt[4],
            msg.actual_ejt[5]))
        print("  actual_ett            : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.actual_ett[0], msg.actual_ett[1], msg.actual_ett[2], msg.actual_ett[3], msg.actual_ett[4],
            msg.actual_ett[5]))
        print("  sync_time             : %7.3f" % msg.sync_time)
        print("  actual_bk             : %d %d %d %d %d %d" % (
            msg.actual_bk[0], msg.actual_bk[1], msg.actual_bk[2], msg.actual_bk[3], msg.actual_bk[4], msg.actual_bk[5]))
        print("  actual_bt             : %d %d %d %d %d " % (
            msg.actual_bt[0], msg.actual_bt[1], msg.actual_bt[2], msg.actual_bt[3], msg.actual_bt[4]))
        print("  actual_mc             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.actual_mc[0], msg.actual_mc[1], msg.actual_mc[2], msg.actual_mc[3], msg.actual_mc[4], msg.actual_mc[5]))
        print("  actual_mt             : %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            msg.actual_mt[0], msg.actual_mt[1], msg.actual_mt[2], msg.actual_mt[3], msg.actual_mt[4], msg.actual_mt[5]))

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
        print("  drl_stopped           : %d" % msg.drl_stopped)
        print("  disconnected          : %d" % msg.disconnected)

def Robot_initialize():
    rospy.init_node('single_robot_simple_py', log_level=rospy.ERROR)
    rospy.on_shutdown(shutdown)
    global set_robot_mode
    set_robot_mode = rospy.ServiceProxy('/' + ROBOT_ID + ROBOT_MODEL + '/system/set_robot_mode', SetRobotMode)
    t1 = threading.Thread(target=thread_subscriber)
    t1.daemon = True
    t1.start()

    global pub_stop
    pub_stop = rospy.Publisher('/' + ROBOT_ID + ROBOT_MODEL + '/stop', RobotStop, queue_size=10)

    set_robot_mode(ROBOT_MODE_AUTONOMOUS)

    # global parameter
    set_velx(2500, 800.63)  # set global task speed: 30(mm/sec), 20(deg/sec)
    set_accx(100, 300)  # set global task accel: 60(mm/sec2), 40(deg/sec2)
    print("!!!")
    # openGripper()
    # closeGripper(action_type="Vial")

msgRobotState_cb.count = 0

def get_status():
    robot_position = get_current_posx()
    return robot_position

def thread_subscriber():
    rospy.Subscriber('/' + ROBOT_ID + ROBOT_MODEL + '/state', RobotState, msgRobotState_cb)
    rospy.spin()
    # rospy.spinner(2)


def openGripper(action_type="Vial"):
    """
    ONROBOT_TARGET_FORCE_1: 0
    ONROBOT_TARGET_WIDTH_1: 0 (600 == 60mm)
    ONROBOT_CONTROL_1: 1 (1 == action)
    ONROBOT_ACTUAL_DEPTH_1: 211
    ONROBOT_ACTUAL_REL_DEPTH_1: 211
    ONROBOT_ACTUAL_WIDTH_1: 918
    ONROBOT_STATUS_1: 0
    """
    if action_type == "Vial":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 500) 
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 200)
        set_modbus_output("ONROBOT_CONTROL_2", 1)

    elif action_type == "Falcon":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 700)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 250)
        set_modbus_output("ONROBOT_CONTROL_2", 1)


def closeGripper(action_type="Vial"):
    if action_type == "Vial":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 350)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 250)
        set_modbus_output("ONROBOT_CONTROL_2", 1)

    elif action_type == "Falcon":
        set_modbus_output("ONROBOT_TARGET_WIDTH_2", 350)
        set_modbus_output("ONROBOT_TARGET_FORCE_2", 250)
        set_modbus_output("ONROBOT_CONTROL_2", 1)





def pick(approach, leave, object_type):
    '''
    pick (bird coordination(before pick) -> approach -> close gripper -> leave -> bird coordination)
    
    :param approach (int): approch distance 
    :param leave (int): leave distance  
    :param object_type (str): object type for gripper distance 
        ex) Vial, Cuvette
    '''
    movel(approach, vel = 500, acc = 50, ref = DR_TOOL)
    closeGripper(action_type = object_type)
    movel(leave, vel = 500, acc = 50, ref = DR_TOOL)

def place(approach, leave, object_type):
    '''
    place (bird coordination(before pick) -> approach -> open gripper -> leave -> bird coordination)
    
    :param approach (int): approch distance 
    :param leave (int): leave distance  
    :param object_type (str): object type for gripper distance 
        ex) Vial, Cuvette
    '''
    
    movel(approach, vel = 500, acc = 50, ref = DR_TOOL)
    openGripper(action_type = object_type)
    movel(leave, vel = 500, acc = 50, ref = DR_TOOL)

def move_Centri_home(action_type='virtual'):
    
    movel(Centri_front, vel= 700, acc= 200, ref= DR_BASE)

def move_Holder_home(action_type="virtual"):
    movel(Holder_home, vel= 700,acc=200, ref=DR_BASE)

def move_Rotor_home(action_type="virtual"):
    
    for i in range(len(rotor_home_list)):
        movel(rotor_home_list[i], vel= 700, acc= 200, ref= DR_BASE)


def move_Rotor_to_Holder(action_type='virtual'):
    closeGripper(action_type="Vial")

    # movel(Rotor_to_holder_list[0],vel= 700, acc=200, ref=DR_BASE)

    for i in range(len(Rotor_to_holder_list[1])):
        movel(Rotor_to_holder_list[1][i],vel=700, acc=200, ref=DR_BASE)

    for i in range(len(holder_list)):
        movel(holder_list[i], vel=700, acc=200, ref=DR_BASE) 

    openGripper(action_type='Vial')   


    
    



def insert(approach, object_type):
    movel(insert, vel= 700, acc= 200, ref = DR_TOOL)
    openGripper(action_type=object_type)

def compliance_ctrl(action_type='on',mode_type = "virtual"):
    if action_type == "on":
        task_compliance_ctrl()
    
    elif action_type == "off":

        release_compliance_ctrl()





def Open_Rotor_cap(action_type="virtual"):
    '''
    Open_Rotor_cap

    
    '''
    move_Rotor_home()


    for i in range(15):
        openGripper(action_type='Vial')
        
        movej(Arrange_Gripper, vel=200,acc=50)
        
        closeGripper(action_type='Vial')
        
        task_compliance_ctrl()
        
        fd = [0, 0, 10, 10, 10, 10]
        
        fctrl_dir= [0, 0, 1, 0, 0, 0]
        
        set_desired_force(fd, dir=fctrl_dir, mod=DR_FC_MOD_REL)
        
        amovel(Open_Rotor, vel = 200 ,acc=100)
        
        movel(Open_Rotor2, vel = 200 ,acc=100)
        
        release_force()
        
        release_compliance_ctrl()

    movel(pick_cap_from_rotor, vel = 200, acc=100)


def From_Rotor_to_Centri(action_type="virtual"):
    for i in range(len(Holder_to_Rotor_list[0])):
        movel(Holder_to_Rotor_list[0][i], vel=700, acc=200 )



#대호 작성 코드 falcon 이동용
def DH_pick(approach, leave, timesleep, object_type):
    '''
    pick (bird coordination(before pick) -> approach -> close gripper -> leave -> bird coordination)
    
    :param approach (int): approch distance 
    :param leave (int): leave distance  
    :param object_type (str): object type for gripper distance 
        ex) Vial, Cuvette
    '''
    
    openGripper(action_type = object_type)
    movel(approach, vel = 500, acc = 50, ref = DR_TOOL)
    time.sleep(timesleep)
    closeGripper(action_type = object_type)
    time.sleep(timesleep)
    movel(leave, vel = 500, acc = 50, ref = DR_TOOL)

def DH_place(approach, leave, timesleep, object_type):
    '''
    place (bird coordination(before pick) -> approach -> open gripper -> leave -> bird coordination)
    
    :param approach (int): approch distance 
    :param leave (int): leave distance  
    :param object_type (str): object type for gripper distance 
        ex) Vial, Cuvette
    '''
    movel(approach, vel = 500, acc = 50, ref = DR_TOOL)
    time.sleep(timesleep)
    openGripper(action_type = object_type)
    time.sleep(timesleep)
    movel(leave, vel = 500, acc = 50, ref = DR_TOOL)


def Falcon_from_Batch_to_Single(falcon_num = 0, action_type="virtual"):
    Falcon_move_list = [falcon_position_list[falcon_num][1],falcon_position_list[falcon_num][0]] + Batch_to_single_falcon_move_list
    
    for i in reversed(range(len(Falcon_move_list)-1)):
        movel(Falcon_move_list[i], vel=900, acc=500 )

    task_compliance_ctrl()

    DH_pick( posx(0,0,120.000,0,0,0), posx(0,0,-120.000,0,0,0), 1,object_type= 'Falcon')

    release_compliance_ctrl()

    for i in range(1,len(Falcon_move_list)):
        movel(Falcon_move_list[i], vel=900, acc=500 )

    task_compliance_ctrl() 

    DH_place(posx(0,0,120.000,0,0,0), posx(0,0,-120.000,0,0,0), 1, object_type= 'Falcon')

    time.sleep(1)

    DH_pick( posx(0,0,120.000,0,0,0), posx(0,0,-120.000,0,0,0), 1,object_type= 'Falcon')

    release_compliance_ctrl()

    for i in reversed(range(len(Falcon_move_list)-1)):
        movel(Falcon_move_list[i], vel=900, acc=500 )

    task_compliance_ctrl()

    DH_place(posx(0,0,120.000,0,0,0), posx(0,0,-120.000,0,0,0), 1, object_type= 'Falcon')


    release_compliance_ctrl()


def move_before_pick_point(temp_location_dict):
    '''
    move before pick point

    :temp_location_dict (list): sequence of each action
        ex) storage_empty_to_stirrer_list = [[pos_XYZ, pos_storage, storage_empty_center], 
                            storage_empty_pick_1,
                            storage_empty_pick_2, 
                            [pos_storage, pos_XYZ, stirrer_center],
                            stirrer_place_1,
                            stirrer_place_2, 
                            [stirrer_center, pos_XYZ]
                            ]
        -> ONLY USE [pos_XYZ, pos_storage, storage_empty_center] part.
    '''
    for i in range(len(temp_location_dict["location_list"][0])):
        movel(temp_location_dict["location_list"][0][i], vel = temp_location_dict["vel"]["linear"], acc = temp_location_dict["acc"]["linear"])





def pick_and_place( pick_num, place_num, action_type='storage_empty_to_stirrer', mode_type="virtual"):
    """
        Pick and place function for moving object with DOOSAN robot

        :param NodeLogger_obj (NodeLogger): NodeLogger object to control log message
        :param pick_num (int) : pick number of each hardware location (0-7) 
        :param place_num (int) : place number of each hardware loaction (0-7)
        :param action_type (str) : Key of input_location_dict. 
            ex) storage_empty_to_stirrer
                stirrer_to_holder
                holder_to_storage_filled
                cuvette_storage_to_cuvette_holder
                cuvette_holder_to_UV
                UV_to_cuvette_storage
        :return: None
        
        temp_info_dict = 
        {
            "location_list" : Storage_empty_to_Stirrer_list,
            "pick_loc_list" : storage_empty_list,
            "place_loc_list" : stirrer_list,
            "object_type" : 'Vial',
            "ref" : "DR_BASE",
            "vel":{
                "linear":250,
                "radious":80
            },
            "acc":{
                "linear":1,
                "radious":332
            }
        }
    """
    temp_info_dict=location_dict[action_type]
    device_name = "{} ({})".format("Doosan Arm m0609",mode_type)
    # change later
    if mode_type=="real":
        openGripper(action_type = temp_info_dict['object_type'])
    msg = "Pick and place : Gripper is opened."
    

    if mode_type=="real":
        move_before_pick_point(temp_info_dict) # move before pick point
    msg = "Pick and place : Move before pick point."


    if mode_type=="real":
        movel(temp_info_dict["pick_loc_list"][pick_num], vel=temp_info_dict['vel']['general'], acc = temp_info_dict["acc"]['general'])
    msg = "Pick and place : Move pick point."


    if mode_type=="real":
        pick(temp_info_dict["location_list"][1], temp_info_dict["location_list"][2], velocity=temp_info_dict['vel']['pick'], acceleration=temp_info_dict["acc"]['pick'], object_type=temp_info_dict["object_type"]) # go below -> pick -> go up
    msg = "Pick and place : Pick."
    

    if mode_type=="real":
        move_place_point_during_picking_vial(temp_info_dict) # move place point during picking vial
    msg = "Pick and place : Move before place point during picking vial."


    if mode_type=="real":
        movel(temp_info_dict["place_loc_list"][place_num], vel=temp_info_dict['vel']['general'], acc = temp_info_dict["acc"]['general'])
    msg = "Pick and place : Move place point during picking vial."
    

    if mode_type=="real":
        place(temp_info_dict["location_list"][4], temp_info_dict["location_list"][5],velocity=temp_info_dict['vel']['place'],acceleration=temp_info_dict['acc']['place'], object_type=temp_info_dict["object_type"]) # go below -> place -> go up
    msg = "Pick and place : Place."
    

    if mode_type=="real":
        move_ending_point(temp_info_dict) # move ending point
    msg = "Pick and place : Move home"
    

    



if __name__ == "__main__":


        
    openGripper(action_type="Falcon")
    movel(Centri_front, vel=700, acc=500, ref=DR_BASE)



    # for i in range(len(rotor_home_list)):
    #     movel(rotor_home_list[i],  vel = 700, acc = 500, ref = DR_BASE)

    # # # # openGripper()

    # # # movej(Arrange_Gripper,vel= 200,acc=50)
    # # # closeGripper(action_type="Vial")




    # for i in range(15):
    #     print("task")

    #     openGripper(action_type="Vial")
        
    #     movej(Arrange_Gripper,vel= 200,acc=50)
        
    #     time.sleep(2)
        
        
        

    #     closeGripper(action_type="Vial")
    #     # set_desired_force(fd=[40,40,40,10,10,10],dir =[0,0,1,0,0,0])
    #     task_compliance_ctrl()
    #     fd = [0, 0, 10, 10, 10, 10]
    #     fctrl_dir= [0, 0, 1, 0, 0, 0]
    #     set_desired_force(fd, dir=fctrl_dir, mod=DR_FC_MOD_REL)
    #     amovel(Open_Rotor, vel = 200 ,acc=100)
    #     movel(Open_Rotor2, vel = 200 ,acc=100)
    #     # amovel(Open_Rotor3, vel = 200 ,acc=100)
    #     # res = is_done_bolt_tightening(10, 5, DR_AXIS_Z)
    #     release_force()
        

    # #     #
    # #     # print(get_tool_force())
    #     release_compliance_ctrl()

        



        

    # #     time.sleep(2)
        
    # #     openGripper(action_type="Vial")
    # #     # release_force()

    # #     # release_compliance_ctrl()

    # time.sleep(1)


    # closeGripper(action_type="Vial")
    # # movel(Open_Rotor, vel = 100 ,acc=50)




    # for i in range(len(rotor_pick_list)):
    #     movel(rotor_pick_list[i], vel=700, acc=500 ,ref=DR_BASE)

    # task_compliance_ctrl()

    # for i in range(len(rotor_to_holder_list)):
    #     movel(rotor_to_holder_list[i], vel=300, acc=200 ,ref=DR_BASE)
    # openGripper(action_type="Vial")

    # release_compliance_ctrl()

    # movel(right_put_holder, vel=700, acc=500 ,ref=DR_BASE)


