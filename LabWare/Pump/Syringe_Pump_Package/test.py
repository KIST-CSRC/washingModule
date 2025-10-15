import multiprocessing
import time
import Syringe_Class


def call_Centris(addr, vol, USB, port, sp=5000, speed=9000, ini=False):
    Centris_obj = Syringe_Class.Pump_Class(addr, USB, port, sp, ini)
    Centris_obj.add(volume=vol, speed=speed)

    return 1


from Hardware.Syringe_Pump.XCaliburD import XCaliburD

from Hardware.Syringe_Pump.transport import TecanAPISerial, TecanAPINode, listSerialPorts


# Functions to return instantiated XCaliburD objects for testing

def returnSerialXCaliburD():
    test0 = XCaliburD(com_link=TecanAPISerial(7, '/dev/ttyUSB0', 9600))
    return test0


def returnNodeXCaliburD():
    test0 = XCaliburD(com_link=TecanAPINode(0, '192.168.1.140:80'), waste_port=6)
    return test0


def findSerialPumps():
    return TecanAPISerial.findSerialPumps(tecan_addrs=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], max_attempts=5)


def getSerialPumps():
    ''' Assumes that the pumps are XCaliburD pumps and returns a list of
    (<serial port>, <instantiated XCaliburD>) tuples
    '''
    return [("/dev/ttyUSB0", XCaliburD(com_link=TecanAPISerial(0, "/dev/ttyUSB0", 9600)))]


if __name__ == '__main__':
    print(listSerialPorts())
    pump_list = findSerialPumps()
    print("pump_list : ", pump_list)
    print(getSerialPumps())

# if __name__ == '__main__':
#     device_address = ["/dev/ttyUSB0", "/dev/ttyUSB0", "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB1",
#                       "/dev/ttyUSB1"]
#
#     pool = multiprocessing.Pool(processes=2)
#
#     status_1 = pool.apply_async(call_Centris, (1, 1000, device_address[0], 0, 5000, 9000, False))
#     time.sleep(2)
#     status_2 = pool.apply_async(call_Centris, (2, 1000, device_address[1], 1, 5000, 9000, False))
    # time.sleep(2)
    # status_3 = pool.apply_async(call_Centris, (3, 1000, device_address[2], 2, 5000, 9000, False))
    # time.sleep(2)
    # status_4 = pool.apply_async(call_Centris, (4, 1000, device_address[3], 3, 500, 9000, False))
    # time.sleep(2)
    # status_5 = pool.apply_async(call_Centris, (5, 1000, device_address[4], 4, 500, 9000, False))
    # time.sleep(2)
    # status_6 = pool.apply_async(call_Centris, (6, 1000, device_address[5], 5, 5000, 9000, False))
    #
    # pool.close()
    # pool.join()
