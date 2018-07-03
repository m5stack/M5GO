"""
MicroPython Motor driver
"""

from machine import I2C, Pin
import i2c_bus

a = (21,22)

class StepMotor:
    def __init__(self, addr=0x70):
        # self.i2c = 
        # self.i2c = I2C(id=0, sda=a[0], scl=a[1])    
        self.i2c = i2c_bus.get(i2c_bus.M_BUS)
        self.addr = addr
        self.speed = 500

    def StepMotor_XYZ(self, x, y, z, speed=None):   
        str_x = str(x)  
        str_y = str(y)
        str_z = str(z)
        str_speed = str(speed if speed else self.speed)
        RapidMoveCMD = 'G1 X'+str_x+' Y'+str_y+' Z'+str_z+' F'+str_speed
        self.write(RapidMoveCMD)

    # def StepMotor_X(self, speed=None):
    #     str_speed = str(speed if speed else self.speed)

    # def moveTo(self, absolute):
    #     pass
    
    # def move(self, relative):
    #     pass

    # def run(self):
    #     pass

    # def setMaxSpeed(self, MaxSpeed):
    #     pass

    # def runSpeed(self):
    #     pass

    # def getDistanceToGo(self):
    #     pass


    def write(self, buffer):
        self.i2c.writeto(self.addr, buffer + "\r\n")



class ServoMotor:
    def __init__(self, addr=0x70):
        pass
    