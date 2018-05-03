from micropython import const
from machine import I2C, Pin

PORTA = (21,22)
PORTB = (26,36)
PORTC = (16,17)
i2c_used_0 = None

class ENV():
  def __init__(self, port=PORTA):
    from dht12 import DHT12
    from bmp280 import BMP280
    global i2c_used_0
    if i2c_used_0:
      self.i2c = i2c_used_0
    else:
      i2c_used_0 = I2C(id=0, sda=port[0], scl=port[1])
      self.i2c = i2c_used_0
    self.dht12 = DHT12(self.i2c)
    self.bmp280 = BMP280(self.i2c)

  def available(self):
    if 92 in i2c_used_0.scan():
      return True
    else:
      return False

  def pressure(self):
    return self.bmp280.read_compensated_data()[1] / 25600

  def temperature(self):
    return self.bmp280.read_compensated_data()[0] / 100

  def humidity(self):
    self.dht12.measure()
    return self.dht12.humidity()

  @property
  def values(self):
    """ readable values """
    self.dht12.measure()
    h = self.dht12.humidity()
    t, p = self.bmp280.read_compensated_data()
    t /= 100
    p /= 25600
    return t, p, h


class PIR(): # 1 OUT
  def __init__(self, port=PORTB):
    self.pin = Pin(PORTB[1], Pin.IN)
    self.cb = None

  def callback(self, cb):
    self.cb = cb
    self.pin.irq(self._irq_cb, (Pin.IRQ_RISING | Pin.IRQ_FALLING))

  def _irq_cb(self, pin):
    self.cb(pin.value())

  def read(self):
    return self.pin.value()


class RGB(): # 0 IN 1 OUT
  def __init__(self, port=PORTB, nums=1):
    from machine import Neopixel
    self.nums = nums*3
    self.np = Neopixel(Pin(port[0]), self.nums)
    # self.np = Neopixel(Pin(port[0]), self.nums, Neopixel.TYPE_RGBW)

  def setColor(self, color, pos=None):
    if pos == None:
      self.np.set(1, color, num=self.nums)
    else:
      self.np.set(pos, color)

  def setHSB(self, hue, saturation, brightness, pos=None):
    if pos == None:
      self.np.setHSB(1, hue, saturation, brightness, num=self.nums)
    else:
      self.np.setHSB(pos, hue, saturation, brightness)

  def deinit(self):
    self.np.deinit()


class ANGLE(): # 1
  def __init__(self, port=PORTB):
    from machine import ADC
    self.adc = ADC(36)
    self.adc.atten(ADC.ATTN_11DB)

  def deinit(self):
    self.adc.deinit()

  def readraw(self):
    return 4095 - self.adc.readraw()

  def read(self):
    data = 0
    max = 0
    min = 4096
    for i in range(0, 10):
      newdata = 4095 - self.adc.readraw()
      data += newdata
      if newdata > max:
        max = newdata
      if newdata < min:
        min = newdata
    data -= (max + min)
    data >>= 3
    return 100 * data / 4095

class IR():  # 1
  def __init__(self, port=PORTB):
    pass
