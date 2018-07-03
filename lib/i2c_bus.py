from machine import I2C

PORTA = (21,22)
PORTC = (16,17)
M_BUS = PORTA

bus_0 = None
bus_1 = None


def get(port):
    global bus_0, bus_1
    if port == PORTA or port == M_BUS:
        if bus_0 == None:
            bus_0 = I2C(id=0, sda=port[0], scl=port[1])
        return bus_0
    elif port == PORTC:
        if bus_1 == None:
            bus_1 = I2C(id=1, sda=port[0], scl=port[1])
        return bus_1
