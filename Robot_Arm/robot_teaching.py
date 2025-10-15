#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [py example simple] Robot Arm motion for doosan robot, Preprocess Module
# @author   Heeseung Lee (092508@kist.re.kr)
# TEST 2024-06-07

import rospy
import os
import threading, time
import sys
sys.path.append('/home/preprocess/catkin_ws/src/doosan-robot/Robot_Arm')
sys.path.append('/home/preprocess/catkin_ws/src/doosan-robot/Robot_Arm/common/imp')
sys.dont_write_bytecode = True
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))  # get import path : DSR_ROBOT.py
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "/Robot_Arm/common/imp")))  # get import path : DSR_ROBOT.py
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "/Robot_Arm")))

from common.imp.DR_common import *
from common.imp.DSR_ROBOT import *
# for single robot

import common.imp.DR_init



import numpy as np


############################# Task Home #############################

INK_HOME = posx(138.730, 399.360, 458.970, 90, -180, 90)

DESK_HOME = posx(-277.760, 37.810, 395.400, 90, 180, 90)

XYZ_HOME = posx(253.880,-240.610,480.410,90,180,90)


######################### Safety Detection Angle ##############################

Safety = posx(-306.120, 87.760, 205.270, 0, -160.14, 93.74)

############################# Approach and Leave #############################

APPROACH_PLACEFALCON_VCG_ALIGN_HOLDER = posx(0,0,166,0,0,0)
LEAVE_PLACEFALCON_VCG_ALIGN_HOLDER = posx(0,0,- 166,0,0,0)

APPROACH_PICKFALCON_DeskLA = posx(0,0,125,0,0,0)
LEAVE_PICKFALCON_DeskLA = posx(0,0,-155,0,0,0)

APPROACH_PICKFALCON = posx(0,0,135,0,0,0)
LEAVE_PICKFALCON = posx(0,0,-135,0,0,0)

APPROACH_PLACEFALCON = posx(0,0,130,0,0,0)
LEAVE_PLACEFALCON = posx(0,0,-130,0,0,0)

APPROACH_PICK_XYZFALCON = posx(0,0,210,0,0,0)
LEAVE_PICK_XYZFALCON = posx(0,0,-210,0,0,0)

APPROACH_PLACE_XYZFALCON = posx(0,0,180,0,0,0)
LEAVE_PLACE_XYZFALCON = posx(0,0,-180,0,0,0)

APPROACH_PICK_XYZVIAL = posx(0,0,180,0,0,0)
LEAVE_PICK_XYZVIAL = posx(0,0,-180,0,0,0)

APPROACH_PLACE_XYZVIAL = posx(0,0,165,0,0,0)
LEAVE_PLACE_XYZVIAL = posx(0,0,-165,0,0,0)



APPROACH_PLACEWEIGH = posx(0, 0, 300, 0, 0, 0) #place
LEAVE_PLACEWEIGH= posx(0, 0, -300, 0, 0, 0)

APPROACH_PICKWEIGH = posx(0, 0, 310, 0, 0, 0) #place
LEAVE_PICKWEIGH= posx(0, 0, -310, 0, 0, 0)

APPROACH_SONIC_PLACEFALCON = posx(0,0,90,0,0,0)
LEAVE_SONIC_PLACEFALCON = posx(0,0,-90,0,0,0)

APPROACH_SONIC_PICKFALCON = posx(0,0,100,0,0,0)
LEAVE_SONIC_PICKFALCON = posx(0,0,-100,0,0,0)

APPROACH_PLACEFALCON_VCG = posx(0,0 , 170,0,0, 0)
APPROACH_PLACELEAVE_VCG =  posx(0,0 ,-150,0,0, 0)

APPROACH_HOLDER_PLACEFALCON_VCG = posx(0,0 , 200,0,0, 0)
APPROACH_HOLDER_PLACELEAVE_VCG =  posx(0,0 ,-200,0,0, 0)

falcon_weighing_pick = [APPROACH_PICKWEIGH, LEAVE_PICKWEIGH]





       


############################# Vessel Holder #############################
"""

"""
#--------------------------Falcon holder -----------------------
holder0_home = posx(-518.860, 164.650, 400, 90, 180,90)
# pick -506.86, 184.65, 180.29, 90, 180, 90
holder_falcon0 = posx(-509.960, 184.650, 310.290, 90, 180,90)
# pick -510.36, 133.65, 180.29, 90, 180, 90
holder_falcon1 = posx(-510.060, 134.650, 310.290, 90, 180,90)
# pick -512.36, 84.25, 180.29, 90, 180, 90
holder_falcon2 = posx(-511.50, 85.150, 310.290, 90, 180,90)
holder_falcon3 = posx(-570.060, 184.650, 310.290, 90, 180,90)
holder_falcon4 = posx(-571.360, 135.650, 310.290, 90, 180,90)
holder_falcon5 = posx(-571.960, 85.150, 310.290, 90, 180,90)
holder_falcon6 = posx(-628.000, 186.180, 310.290, 90, 180,90)
holder_falcon7 = posx(-631.000, 135.180, 310.290, 90, 180,90)
holder_falcon8 = posx(-632.000, 84.680, 310.290, 90, 180,90)
holder_falcon9 = posx(-691.000, 186.180, 310.290, 90, 180,90)
holder_falcon10 = posx(-691.000, 134.180, 310.290, 90, 180,90)
holder_falcon11 = posx(-691.000, 84.850, 310.290, 90, 180,90)
falcon_holder_0_list = [holder_falcon0, holder_falcon1, holder_falcon2, holder_falcon3, holder_falcon4,holder_falcon5,
                        holder_falcon6, holder_falcon7, holder_falcon8, holder_falcon9, holder_falcon10, holder_falcon11]

getFalconList = [DESK_HOME, holder0_home, falcon_holder_0_list,  holder0_home, DESK_HOME, INK_HOME]
placeFalconList =[DESK_HOME, holder0_home, falcon_holder_0_list, holder0_home, DESK_HOME, INK_HOME]
#--------------------------Vial Holder-----------------------
holder_Vial0 = posx(-518.850, 32.720, 310.490, 90, 180,90)
holder_Vial1 = posx(-518.850, -15.720, 310.490, 90, 180,90)
holder_Vial2 = posx(-519.850, -62.720, 310.49, 90, 180,90)
holder_Vial3 = posx(-572.840, 32.80, 310.49, 90, 180,90)
holder_Vial4 = posx(-574.340, -14.720, 310.49, 90, 180,90)
holder_Vial5 = posx(-574.830, -62.740, 310.49, 90, 180,90)
holder_Vial6 = posx(-628.340, 33.800, 310.49, 90, 180,90)
holder_Vial7 = posx(-629.240, -14.720, 310.49, 90, 180,90)
holder_Vial8 = posx(-630.330, -61.740, 310.49, 90, 180,90)
holder_Vial9 = posx(-684.174, 34.300, 310.49, 90, 180,90)
holder_Vial10 = posx(-684.640, -14.220, 310.49, 90, 180,90)
holder_Vial11 = posx(-685.43, -61.740, 310.49, 90, 180,90)
vial_holder_0_list = [holder_Vial0, holder_Vial1, holder_Vial2, holder_Vial3, holder_Vial4, holder_Vial5,
                        holder_Vial6, holder_Vial7, holder_Vial8, holder_Vial9, holder_Vial10, holder_Vial11]
getVialList = [DESK_HOME, holder0_home, vial_holder_0_list,  holder0_home, DESK_HOME,INK_HOME]
placeVialList =[DESK_HOME, holder0_home, vial_holder_0_list, holder0_home, DESK_HOME,INK_HOME]


############################# Capping Protocol #############################
CappingMachineHome = posx(-332.840, -27.500, 434.160, 90, 180, 90)
CapHome = posx(-277.760, 237.810, 200.00, 45, 180, 90)
Place_Cap_0 = posx(-350.690, 268.510, 188.500, 45, 180, 90)  #190->188
Place_Cap_1 = posx(-350.690, 218.510, 188.500, 45, 180, 90)
Place_Cap_2 = posx(-350.690, 168.510, 188.500, 45, 180, 90)
Place_Cap_3 = posx(-300.600, 268.510, 188.500, 45, 180, 90)
Place_Cap_4 = posx(-300.600, 218.510, 188.500, 45, 180, 90)
Place_Cap_5 = posx(-300.600, 168.510, 188.500, 45, 180, 90)
Place_Cap_list= [Place_Cap_0,Place_Cap_1,Place_Cap_2,Place_Cap_3,Place_Cap_4,Place_Cap_5]
Cap_0 = posx(-351.690, 267.510, 190.500, 45, 180, 90)
Cap_1 = posx(-351.690, 217.510, 190.500, 45, 180, 90)
Cap_2 = posx(-351.690, 167.510, 190.500, 45, 180, 90)
Cap_3 = posx(-301.600, 267.510, 190.500, 45, 180, 90)
Cap_4 = posx(-301.600, 217.510, 190.500, 45, 180, 90)
Cap_5 = posx(-301.600, 167.510, 190.500, 45, 180, 90)
Cap_list = [Cap_0,Cap_1,Cap_2,Cap_3,Cap_4,Cap_5]
CapApproach = posx(0,0,100, 0, 0, 0)
CapLeave = posx(0, 0,-100, 0, 0, 0)
#-------------------------- Open Cap --------------------------
Opencap= posx(-332.840, -27.500, 360.160, 90, 180, 90)
Opencap_init = posj(5.79, 4.21, -102.6,0,-81.6, -135)
# Opencap_2= posx(-332.840, -27.500, 370.160, 90, 180, 90) #원본
Opencap_2= posx(-332.840, -27.500, 371.160, 90, 180, 90)
Opencap_up= posx(-332.840, -27.500, 373.160, 90, 180, 90)
Opencap_j = posj(5.79, 4.05, -103.56,0,-80.49, 5.78)
#-------------------------- Close Cap --------------------------

# align_holder_RG6 = posx(-525.490, 287.620,270.430, 90, 180, 90)
# align_holder_RG6_Down = posx(-525.490, 287.620,  201.650, 90, 180, 90)
# align_holder_RG6_Down_J = posj(-28.09, -39.18, -73.5, 0, -67.31, 148.14)
# align_holder_RG6_Down_init = posj(-28.09, -39.18, -73.5, 0, -67.31, -28.14)
# align_holder_RG6_Down_Cap = posx(-525.490, 287.620,  185.650, 90, 180, 90)
# align_holder_RG6_Down_Cap_2 = posx(-532.690, 288.620, 190.650, 90, 180, 90)
# align_holder_RG6_Down_Cap_tok = posx(-530.690, 286.620, 190.650, 90, 180, 90)
# Closecap_j = posj(5.79, 4.1, -103.29, 0,-80.81, 0)
# Closecap__init = posj(5.79, 4.1, -103.29, 0,-80.81, -140)
# Closecap_0 = posx(-332.340, -27.000,  373.160, 90, 180,90)
# Closecap_1 = posx(-332.340, -27.500,  370.160, 90, 180,90)
# Closecap_2 = posx(-332.340, -27.500,  365.160, 90, 180,90)

align_holder_RG6 = posx(-524.500, 285.200, 270.430, 90, 180, 90)

align_holder_RG6_Down = posx(-524.590, 285.200,  198.430, 90, 180, 90)

align_holder_RG6_Down2 = posx(-525.090, 286.500,  202.430, 90, 180, 90)
# align_holder_RG6_Down_J = posj(-28.09, -39.18, -73.5, 0, -67.31, 148.14) # 원본
align_holder_RG6_Down_J = posj(-27.74, -38.77, -73.78, 0, -67.46, 120.26)
# align_holder_RG6_Down_init = posj(-28.09, -39.18, -73.5, 0, -67.31, -28.14) #원본
align_holder_RG6_Down_init = posj(-27.74, -38.77, -73.78, 0, -67.46, -27.74)
# align_holder_RG6_Down_Cap = posx(-525.490, 287.620,  185.650, 90, 180, 90) #원본
align_holder_RG6_Down_Cap = posx(-524.590, 285.200, 185.650, 90, 180, 90)
align_holder_RG6_Down_Cap_2 = posx(-532.690, 288.620, 190.650, 90, 180, 90)
align_holder_RG6_Down_Cap_tok = posx(-530.690, 286.620, 190.650, 90, 180, 90)
Closecap_j = posj(5.79, 4.1, -103.29, 0,-80.81, 0)
Closecap__init = posj(5.79, 4.1, -103.29, 0,-80.81, -140)
Closecap_0 = posx(-332.340, -27.000,  373.160, 90, 180,90)
Closecap_1 = posx(-332.340, -27.500,  370.160, 90, 180,90)
Closecap_2 = posx(-332.340, -27.500,  365.160, 90, 180,90)


pickplaceCaplist= [DESK_HOME, CapHome, Cap_list,CapHome,DESK_HOME]
placeCaplist= [DESK_HOME, CapHome, Place_Cap_list,CapHome,DESK_HOME]

############################# Transfer Liquid Location(XYZ) #############################
Desk_to_XYZ = posx(-353.880,-116.610, 490.410,90,180,90)

#-----------------------------XYZ Falcon ---------------------------
XYZ_falconholderHOME = posx(213.880, -380.610, 280.410, 90, 180, 90)
XYZ_falcon0 = posx(258.880, -453.610, 302.410, 90, 180, 49)
XYZ_falcon1 = posx(219.380, -452.610, 302.410, 90, 180, 45)
XYZ_falcon2 = posx(178.380, -449.610, 302.410, 90, 180, 45)
XYZ_falcon3 = posx(259.880, -401.110, 302.410, 90, 180, 45) # place 180 , pick 220
XYZ_falcon4 = posx(219.380, -401.110, 302.410, 90, 180, 45) 
XYZ_falcon5 = posx(177.880, -400.110, 302.410, 90, 180, 45)

XYZ_falconList= [XYZ_falcon0, XYZ_falcon1, XYZ_falcon2, XYZ_falcon3, XYZ_falcon4, XYZ_falcon5]

XYZ_falconTaskList = [Desk_to_XYZ, XYZ_HOME, XYZ_falconholderHOME, XYZ_falconList, XYZ_falconholderHOME,
                      XYZ_HOME, Desk_to_XYZ]

satorius_weighingHOME = posx(467.380, -419.610, 420.410, 90, 180, 90)
# satorius_weighingDown = posx(253.880, -200.610, 120.410, 90, 180, 90)

satorius_weighingList = [Desk_to_XYZ, XYZ_HOME,satorius_weighingHOME, XYZ_HOME, Desk_to_XYZ]

#----------------------------- XYZ Vial ---------------------------
XYZ_vialholderHOME = posx(213.880, -300.610, 280.410, 90, 180, 90)

XYZ_vial0 = posx(255.880, -359.110, 282.410, 90, 180, 45)
XYZ_vial1 = posx(217.880, -359.110, 282.410, 90, 180, 45)
XYZ_vial2 = posx(179.580, -359.110, 282.410, 90, 180, 45)
XYZ_vial3 = posx(256.380, -308.110, 282.410, 90, 180, 45)
XYZ_vial4 = posx(218.380, -308.110, 282.410, 90, 180, 45)
XYZ_vial5 = posx(181.380, -307.810, 282.410, 90, 180, 45)
XYZ_vialList= [XYZ_vial0, XYZ_vial1, XYZ_vial2, XYZ_vial3, XYZ_vial4, XYZ_vial5]
XYZ_vialTaskList = [Desk_to_XYZ, XYZ_HOME, XYZ_vialholderHOME, XYZ_vialList, XYZ_vialholderHOME,
                      XYZ_HOME, Desk_to_XYZ]
#----------------------------------------------------------------------------------------
#-----------------------------sonic Falcon ---------------------------
Sonic_SonicHOME = posx(564.630, 145.950, 374.660, 0, 180, 90)
Sonic_falcon0_down = posx(588.520, 129.320, 266.000, 12.98, 180, 67.98)
Sonic_falcon1_down = posx(546.460, 130.510, 266.000, 14, 180, 68.16)
Sonic_falcon2_down = posx(506.380, 130.480, 266.000, 18.98, 180, 79.97)
Sonic_falcon3_down = posx(585.680, 83.760, 266.000, 8.74, 180, 142.04) # place 180 , pick 220
Sonic_falcon4_down = posx(544.690, 84.780, 266.000, 9.37, 180, 142.67) 
Sonic_falcon5_down = posx(504.430, 86.470, 266.000, 10.67, 180, 145.84)

Sonic_falconList= [Sonic_falcon0_down, Sonic_falcon1_down, Sonic_falcon2_down,
                  Sonic_falcon3_down, Sonic_falcon4_down, Sonic_falcon5_down]
placeSonic_falconList = [DESK_HOME, INK_HOME, Sonic_SonicHOME, Sonic_falconList, Sonic_SonicHOME, INK_HOME, DESK_HOME,INK_HOME]


############################# Computer Vision With Centrifuge Task #############################

Centri_front = posx(-353.880, -116.600, 480.450, 90, 180,90)
rotor_front = posx(-353.880, -447.600, 400.450, 90, 180,90)
centerof_rotor = posx(-358.970, -540.510, 410.00, 90, 180, 90)
Centri_vision_task_list = [DESK_HOME, Centri_front, rotor_front, DESK_HOME,INK_HOME]
align_holder_VCG = posx(-523.440, 284.170, 253.600, 90, 180, 90)


############################# View Point Algorithm at DeskLA #############################
# DeskLA_Holder_HOME = posx(-424.560, 90.370, 450.260, 90,180, 90) #원본
# DeskLA_Holder = posx(-424.560, 90.370, 383.260, 90,180, 90) #원본
# DeskLA_Holder_HOME = posx(-424.000, 92.370, 450.260, 90,180, 90)
# DeskLA_Holder = posx(-424.000, 92.370, 373.260, 90,180, 90)

DeskLA_Holder_HOME = posx(-421.410, 348.280, 350.490, 90, 180, 90)
DeskLA_Holder = posx(-421.410, 348.280, 236.490, 90, 180, 90)

ViewPointHome = posx(-421.410, 348.280, 270.490, 90, 180, 90)
ViewPointHolder = posx(-421.410, 348.280, 236.490, 90, 180, 90)
ViewPoint_init_J = posj(-38.84,-29.68, -81.77, 0, -68.55, -38.78)
ViewPoint_init = posj(-38.84, -28.11, -78.64,0,-73.26,-38.84)















##########################################################################################
PIPETTE_HOME = posx(231.000, 572.310, 458.970, 90, -180, 90)

Pipette = posx(231.990, 571.300, 171.970, 90, -180, 90) #GRASP

Pipette_put = posx(231.990, 571.300, 180.970, 90, -180, 90) #GRASP

Pipette_up = posx(231.990, 571.30, 438.970, 90, -180, 90)

 #여기에 Compliance넣어야함.
 
TIP_HOME = posx(99.840, 500.970, 408.670, 90, -180, 90)

tip_approach = posx(0, 0, 37, 0,0,0) #pick Compliance 필수 원래 37
tip_leave =  posx(0, 0, -100, 0,0,0)
tip_pick = [tip_approach, tip_leave]

SOL_HOME = posx(108.730,400.340, 458.970, 90, -180, 90)

IPA = posx(75.720, 415.360, 458.990, 90, -180, 90)

Nafion = posx(153.720, 416.360, 458.960, 90, -180, 90)

H2O = posx(73.720, 348.340, 458.960, 90, -180, 90)

solution_4 = posx(153.720, 348.320, 458.960, 90, -180, 90) #tool 좌표로 -70 해야함 

solution_get1 = posx(0, 0, 150, 0, 0, 0)
solution_get2 = posx(0, 0, -150, 0, 0, 0)

get_solution = [solution_get1, solution_get2]
solution_positions = {
    "IPA": IPA,
    "Nafion": Nafion,
    "H2O": H2O
}

solution_list = [IPA, Nafion, H2O]

ink_home_with_pipette = posx(190.730, 399.360, 558.970, 90, -180, 90)


ink_home_with_pipette_2 = posx(190.730, 399.360, 438.970, 90, -180, 90)


sol2weighing = posx(340.000, 275.340, 609.970, 90, -180, 90)



inject2weighing = posx(340.000, 283.340, 409.600, 90, -180, 90)


###falcon holder to weighing###

falcon_holder_home = posx(-331.2, 69.63, 394.51,90, -180, 90)

######sonic#######

sonic_center= posx(500.000, 270.000 ,400.000 ,180 ,-180 ,90)

SONIC_0 = posx(522.630,245.580,360.060, 180, -180, 45) 
SONIC_1 = posx(562.630,245.580,360.060, 180, -180, 45)
SONIC_2 = posx(602.630,245.580,360.060, 180, -180, 45)
SONIC_3 = posx(521.630,201.580,360.060, 180, -180, 45)
SONIC_4 = posx(561.630,201.580,360.060, 180, -180, 45)
SONIC_5 = posx(601.630,201.580,360.060, 180, -180, 45)

Sonic_holder_list = [SONIC_0,SONIC_1,SONIC_2,SONIC_3,SONIC_4,SONIC_5]

APPROACH_PLACESONIC = posx(0, 0, 170,0,0,0)
LEAVE_PLACESONIC = posx(0, 0, -180,0,0,0)

APPROACH_PICKSONIC = posx(0, 0, 180,0,0,0)
LEAVE_PICKSONIC = posx(0, 0, -200,0,0,0)
place_to_sonic = [APPROACH_PLACESONIC, LEAVE_PLACESONIC]
pick_from_sonic = [APPROACH_PICKSONIC,LEAVE_PICKSONIC]
#### sonic_to_holder_list ####

sonic_to_holder_list = [INK_HOME, DESK_HOME]


Discard_TIP = posx(338.730, 490.340, 408.970, 90, -180, 90)
Discard_TIP2 = posx(138.730, 490.340, 408.970, 90, -180, 90)






Pipette_Put_list = [Pipette_up, Pipette_put, Pipette_up, INK_HOME]

InjectInkSolution_list = [SOL_HOME,ink_home_with_pipette, solution_list,ink_home_with_pipette,ink_home_with_pipette,SOL_HOME]




# weighing_to_sonic_list = [weighing_front, sonic_center, Sonic_holder_list, INK_HOME]


sonic_to_holder_list = [INK_HOME,sonic_center, Sonic_holder_list, INK_HOME, DESK_HOME, falcon_holder_0_list, DESK_HOME,INK_HOME ]

Pipette_list = [INK_HOME, PIPETTE_HOME, Pipette_up, Pipette]



####Washing Task#### 







#######Change Gripper########

NonetoolHome = posx(-12.530, 520.340, 156.120, 31.87, 179.08, -58.88)

VacuumGripperFront = posx(-5.960, 650.870, 21.540, 31.88, 179.08, -58.88)

VacuumGripper = posx(-168.960, 650.720, 21.650, 31.88, 179.08, -58.88)

VacuumGripperUp = posx(-169.200, 650.720, 39.550, 31.88, 179.08, -58.88)

RG6Gripper = posx(-165.470, 457.560, 21.260, 38.21, 179.22, -52.54)

RG6GripperUp = posx(-165.690, 457.380, 41.940, 38.21, 179.22, -52.55)

RG6GripperFront = posx(-7.390, 459.550, 22.970, 38.19, 179.22, -52.56)

putVacuumGripperlist = [INK_HOME, VacuumGripperFront, VacuumGripper, VacuumGripperUp, NonetoolHome]

equipRG6Gripperlist = [RG6GripperUp, RG6Gripper , RG6GripperFront, NonetoolHome, INK_HOME ]

putRG6Gripperlist = [INK_HOME, RG6GripperFront, RG6Gripper, RG6GripperUp, NonetoolHome]

equipVacuumGripperlist = [VacuumGripperUp, VacuumGripper, VacuumGripperFront, NonetoolHome, INK_HOME]




Home_bh = posx(-401.820, 91.430, 420.100, 90.0, 180.0, 90.0)

FalconHolder_Falcon0_bh = posx(-510.970, 185.290, 378.990, 90.0, 180.0, 90.0)



FalconAlign_Up_bh = posx(-522.940, 284.500, 378.990, 90.0, 180.0, 90.0)



FalconAlign_Approach_bh = posx(0,0,196.990,0,0,0)

FalconAlign_Leave_bh = posx(0,0,-196.990,0,0,0)


Home_bh = posx(-401.820, 91.430, 420.100, 90.0, 180.0, 90.0)

CapHolder_Up_bh = posx(-350.060, 266.940, 378.990, 90.0, 180.0, 45.0)

CapHolder_bh = posx(-352.000, 266.940, 87.000, 90.0, 180.0, 45.0)



CapHolder_Up_bh = posx(-350.060, 266.940, 378.990, 90.0, 180.0, 45.0)

CapHolder_Approach_bh = posx(0,0,291.990,0,0,0)

CapHolder_Leave_bh = posx(0,0,-291.990,0,0,0)

FalconAlign_Up_bh = posx(-522.940, 284.500, 378.990, 90.0, 180.0, 90.0)

FalconAlign_bh = posx(-522.940, 284.500, 192.000, 90.0, 180.0, 90.0)

# Release

FalconAlign_Up_bh = posx(-522.940, 284.500, 378.990, 90.0, 180.0, 90.0)


# Grasp

FalconAlign_Press_bh = posx(-522.940, 284.500, 206.500, 90.0, 180.0, 90.0)

FalconAlign_Up_bh = posx(-522.940, 284.500, 378.990, 90.0, 180.0, 90.0)

# Release

FalconAlign_bh = posx(-522.940, 285.000, 192.000, 90.0, 180.0, 90.0)

# Grasp

Twist1_bh = posx(-522.940, 285.000, 191.000, 90.0, -180.0, 180.0)

Twist2_bh = posx(-522.940, 285.000, 190.000, 90.0, -180.0, 260.0)

# Release

FalconAlign_Up_bh = posx(-522.940, 284.500, 378.990, 90.0, 180.0, 90.0)

# Grasp

FalconAlign_StrongPress_bh = posx(-522.940, 285.000, 203.500, 90.0, 180.0, 90.0)

FalconAlign_Up_bh = posx(-522.940, 284.500, 378.990, 90.0, 180.0, 90.0)

# Release

Home_bh = posx(-401.820, 91.430, 420.100, 90.0, 180.0, 90.0)



Falcon0_bh = posx(-510.000, 185.000, 178.990, 90.0, 180.0, 90.0)
Falcon0_up_bh = posx(-510.000, 185.000, 378.990, 90.0, 180.0, 90.0)

Falcon1_bh = posx(-510.000, 135.000, 178.990, 90.0, 180.0, 90.0)
Falcon1_up_bh = posx(-510.000, 135.000, 378.990, 90.0, 180.0, 90.0)

Falcon2_bh = posx(-510.000, 85.000, 178.990, 90.0, 180.0, 90.0)
Falcon2_up_bh = posx(-510.000, 85.000, 378.990, 90.0, 180.0, 90.0)

Falcon3_bh = posx(-570.000, 185.000, 178.990, 90.0, 180.0, 90.0)
Falcon3_up_bh = posx(-570.000, 185.000, 378.990, 90.0, 180.0, 90.0)

Falcon4_bh = posx(-570.000, 135.000, 178.990, 90.0, 180.0, 90.0)
Falcon4_up_bh = posx(-570.000, 135.000, 378.990, 90.0, 180.0, 90.0)

Falcon5_bh = posx(-570.000, 85.000, 178.990, 90.0, 180.0, 90.0)
Falcon5_up_bh = posx(-570.000, 85.000, 378.990, 90.0, 180.0, 90.0)

