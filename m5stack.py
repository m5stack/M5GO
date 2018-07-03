from micropython import const
import machine, ubinascii
import uos as os
import utime as time
import display as lcd
import utils
from button import Button

VERSION = "v0.4.3"

_BUTTON_A_PIN = const(39)
_BUTTON_B_PIN = const(38)
_BUTTON_C_PIN = const(37)
_SPEAKER_PIN  = const(25)


class Speaker:
  def __init__(self, pin=25, volume=5):
    self.pwm = machine.PWM(machine.Pin(pin), 1, 0, 0)
    self._timer = 0
    self._volume = volume
    self._blocking = True

  def _timeout_cb(self, timer):
    self._timer.deinit()
    self.pwm.duty(0)
    self.pwm.freq(1)
    self.pwm.deinit()

  def tone(self, freq=1800, duration=200, volume=None):
    if volume == None:
      self.pwm.init(freq=freq, duty=self._volume)
    else:
      self.pwm.init(freq=freq, duty=volume)
    if duration > 0:
      if self._blocking:
        time.sleep_ms(duration)
        self.pwm.duty(0)
        self.pwm.freq(1)
        self.pwm.deinit()
      else:
        self._timer = machine.Timer(3)
        self._timer.init(period=duration, mode=self._timer.ONE_SHOT, callback=self._timeout_cb)   

  def volume(self, val):
    self._volume = val

  def setblocking(self, val=True):
    self._blocking = val


def fimage(x, y, file, type=1):
  if file[:3] == '/sd':
    utils.filecp(file, '/flash/fcache', blocksize=8192)
    lcd.image(x, y, '/flash/fcache', 0, type)
    os.remove('/flash/fcache')
  else:
    lcd.image(x, y, file, 0, type)


def delay(ms):
  time.sleep_ms(ms)


# ------------------ M5Stack -------------------

# Node ID
node_id = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
print('\nDevice ID:' + node_id)
print('LCD initializing...', end='')


# LCD
lcd = lcd.TFT()
lcd.init(lcd.M5STACK, width=240, height=320, speed=40000000, rst_pin=33, backl_pin=32, miso=19, mosi=23, clk=18, cs=14, dc=27, bgr=True, backl_on=1, invrot=3)
lcd.setBrightness(10)
lcd.clear()
lcd.setColor(0xCCCCCC)
print('Done!')
# lcd.println('M5Stack MicroPython '+VERSION, 0, 0)
# lcd.println('Device ID:'+node_id)
# lcd.println('Boot Mode:')
# lcd.println('Hold button A to boot into SAFE mode.')
# lcd.println('Hold button B to boot into OFFLINE mode.')
# lcd.print('Boot...', 0, 0)
# try:
#   # lcd.image(0, 0, '/flash/img/m5.jpg')
#   lcd.image(0, 0, '/flash/img/1-1.jpg')
#   lcd.rect(0, 190, 320, 50, lcd.WHITE, lcd.WHITE)
#   lcd.setBrightness(500)
# except:
#   pass
if not utils.exists('/flash/img/1-1.jpg'):
  lcd.print('M5GO resource file not found!\n', 0, 0, color=lcd.RED)
  lcd.print('Please upload to the Internal Filesystem.\n', color=lcd.RED)
  lcd.print('https://github.com/m5stack/M5GO\n', color=lcd.RED)
  lcd.setBrightness(300)


# BUTTON
buttonA = Button(_BUTTON_A_PIN)
buttonB = Button(_BUTTON_B_PIN)
buttonC = Button(_BUTTON_C_PIN)


# SPEAKER
speaker = Speaker()

