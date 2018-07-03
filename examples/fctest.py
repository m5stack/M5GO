from m5stack import *
import machine, _thread

np = machine.Neopixel(machine.Pin(15), 10)
np.set(1, lcd.WHITE, num=10)

# def rainbow(loops=120, delay=20, sat=1.0, bri=0.2):
#     for pos in range(0, loops):
#         for i in range(0, 10):
#             dHue = 360.0/10*(pos+i);
#             hue = dHue % 360;
#             np.setHSB(i, hue, sat, bri, 1, False)
#         np.show()
#         if delay > 0:
#             time.sleep_ms(delay)

# def startup_led_show():
#   np.brightness(255)
#   rainbow(loops=10000, delay=40, sat=1.0, bri=0.2)
# _thread.start_new_thread('startup_led_show', startup_led_show, ())


# -------- microphone --------
mic_adc = 0
buffer = []
def microphone_enter():
  print('microphone_enter')
  global mic_adc, buffer
  try:
    mic_adc = machine.ADC(34)
    mic_adc.atten(mic_adc.ATTN_11DB)
    dac = machine.DAC(machine.Pin(25))
    dac.write(0)
  except:
    pass
  buffer = []
  for i in range(0, 55):
    buffer.append(0)


def microphone_loop():
  global mic_adc, buffer
  val = 0
  for i in range(0, 32):
    raw = (mic_adc.readraw() - 1845) // 10
    if raw > 20:
      raw = 20
    elif raw < -20:
      raw = -20
    val += raw
  val = val // 32
  buffer.pop()
  buffer.insert(0, val)
  for i in range(1, 50):
    lcd.line(i*2+44, 120+buffer[i+1], i*2+44+2, 120+buffer[i+2], lcd.WHITE)
    lcd.line(i*2+44, 120+buffer[i],   i*2+44+2, 120+buffer[i+1], lcd.BLACK)


lcd.image(0, 0, '/flash/img/3-2.jpg')
microphone_enter()

while 1:
  microphone_loop()
