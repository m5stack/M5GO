from micropython import const
import gc
import network
import machine
import units
import ujson as json
import utime as time
from utils import *
from m5stack import *
from mstate import *
# import _thread
# from M5GUI import *

VERSION = "0.11"
COLOR_GRAY = const(0xd7ceca)

# -------- Neopixel LED ---------
# np = machine.Neopixel(machine.Pin(15), 10)

# ------------- I2C -------------
i2c = machine.I2C(sda=21, scl=22)
units.i2c_used_0 = i2c

# ------------ WLAN -------------
wlan_sta = network.WLAN(network.STA_IF); 
wlan_sta.active(True)

# Define the WiFi events callback function
def wlan_evnet_cb(info):
  print("[WiFi] event: {} ({})".format(info[0], info[1]))
  if (info[2]):
    print("        info: {}".format(info[2]))
  event = info[0]
  if event == 7:    # Station got IP from connected AP
    import m5go_cloud
    m5go_cloud.mqtt.start()
  elif event == 15: # Station connected to soft-AP
    lcd.image(0,0, '/flash/img/4-2.jpg')
    lcd.qrcode('http://192.168.4.1', 126, 46, 175)

network.WLANcallback(wlan_evnet_cb)

def read_wificonfig():
  ssid = ''
  password = ''
  data = ''
  try:
    with open('config.json') as f:
      data = json.loads(f.read())
    ssid = data['wifi']['ssid']
    password = data['wifi']['password']
  except:
    return ['', '']
  else:
    return [ssid, password]

# ------------ Loading flash ------------
circ_time = 0
pt = 0
def loading_animat():
  global circ_time, pt
  if time.ticks_ms() > circ_time:
    circ_time = time.ticks_ms() + 300
  else:
    return
  d = ((1,0,0), (0,1,0), (0,0,1))
  c = (0xd7ceca, 0xf5be2b)
  pt = pt + 1 if pt < 2 else 0
  lcd.circle(147, 201, 4, c[d[pt][0]], c[d[pt][0]])
  lcd.circle(159, 201, 4, c[d[pt][1]], c[d[pt][1]])
  lcd.circle(171, 201, 4, c[d[pt][2]], c[d[pt][2]])

# ================ Next Prew Machine =================
prew_state_list = (
  "PREW_SPEAKER",
  "PREW_MICRO",
  "PREW_GYRO",
  "PREW_RGB",
  "PREW_ENV",
  "PREW_MOTION",
  "PREW_EXRGB",
  "PREW_IR",
  "PREW_ANGLE",
  "PREW_R2CODE"
)

prewstate = MStateManager()

# -------- PREW_SPEAKER --------
def speaker_start(obj):
  lcd.image(0, 0, '/flash/img/3-1.jpg', type=lcd.JPG)
  obj['isPlaying'] = False
  obj['wav'] = None
  obj['i2s'] = None

def speaker_loop(obj):
  global ii2s
  import wave
  i2s = obj['i2s']
  wav = obj['wav']
  if obj['isPlaying']:
    while True:
      data = wav.readframes(256)
      if len(data) > 0:
        i2s.write(data)
      if buttonA.isPressed() or buttonB.wasPressed() or buttonC.isPressed() or (len(data) <= 0):
        wav.close()
        i2s.deinit()
        obj['isPlaying'] = False
        break
  else:
    if buttonB.wasPressed() and (not obj['isPlaying']):
      wav = wave.open('res/mix.wav')
      from machine import I2S
      i2s = I2S( mode = I2S.MODE_MASTER | I2S.MODE_TX | I2S.MODE_DAC_BUILT_IN )
      i2s.set_dac_mode(i2s.DAC_RIGHT_EN)
      i2s.sample_rate(wav.getframerate())
      i2s.bits(wav.getsampwidth() * 8)
      i2s.nchannels(wav.getnchannels()) 
      i2s.volume(70)    
      while not buttonB.isReleased(): # wait release button
        pass
      obj['i2s'] = i2s
      ii2s = i2s
      obj['wav'] = wav
      obj['isPlaying'] = True

def speaker_end(obj):
  try:
    obj['i2s'].deinit()
    obj['wav'].close()
  except:
    pass

prewstate.register("PREW_SPEAKER", MState(start=speaker_start, loop=speaker_loop, end=speaker_end))

# -------- PREW_MICRO --------
def micro_start(obj):
  lcd.image(0, 0, '/flash/img/3-2.jpg', type=lcd.JPG)
  adc = machine.ADC(34)
  adc.atten(adc.ATTN_11DB)
  obj['adc'] = adc
  buffer = []
  for i in range(0, 55):
    buffer.append(0)
  obj['buf'] = buffer

def micro_loop(obj):
  adc = obj['adc']
  buffer = obj['buf']
  val = 0
  for i in range(0, 32):
    raw = (adc.readraw() - 1845) // 10
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

def micro_end(obj):
  obj['adc'].deinit()
  obj = {}

prewstate.register("PREW_MICRO", MState(start=micro_start, loop=micro_loop, end=micro_end))

# -------- PREW_GYRO --------
_pos = [0, 0]
def ball_move(x, y):
  global _pos
  if x > 42:
    x = 42
  elif x < -42:
    x = -42
  if y > 42:
    y = 42
  elif y < -42:
    y = -42
  global _pos
  x += 93
  y += 93
  if (not x == _pos[0]) or (not y == _pos[1]):
    lcd.rect(_pos[0]-11, _pos[1]-11, 22, 22, lcd.WHITE, lcd.WHITE) # clean
    lcd.circle(x, y, 10, lcd.BLACK, lcd.BLACK) # draw
    _pos[0] = x
    _pos[1] = y

def gyro_start(obj):
  lcd.image(0, 0, '/flash/img/3-3.jpg', type=lcd.JPG)
  global _pos
  _pos = [0 , 0]
  from mpu9250 import MPU9250
  obj['imu'] = MPU9250(i2c)
  buffer = []
  for i in range(0, 6):
    buffer.append([0 , 0])
  obj['buf'] = buffer
  lcd.rect(65, 65, 60, 60, lcd.WHITE, lcd.WHITE) # old pic dot clean

def gyro_loop(obj):
  imu = obj['imu']
  buffer = obj['buf']
  val_x = 0
  val_y = 0
  for i in range(0, 4):
    raw = imu.acceleration
    val_x += raw[0]
    val_y += raw[1]
  buffer.pop()
  buffer.insert(0, [int(val_x//4), int(val_y//4)])
  val_x = 0
  val_y = 0
  for i in range(0, 6):
    val_x += buffer[i][0]
    val_y += buffer[i][1]
  ball_move(val_x, -val_y)
  obj['buf'] = buffer

def gyro_end(obj):
  obj = {}

prewstate.register("PREW_GYRO", MState(start=gyro_start, loop=gyro_loop, end=gyro_end))

# -------- RGB LED --------
def rgbled_start(obj):
  lcd.image(0, 0, '/flash/img/3-4.jpg', type=lcd.JPG)
  np = machine.Neopixel(machine.Pin(15), 10)
  np.brightness(1)
  np.set(1, lcd.RED, num=5)
  np.set(6, lcd.BLUE, num=10)
  obj['np'] = np
  obj['upinc'] = True
  obj['led_right'] = 0

def rgbled_loop(obj):
  led_right = obj['led_right']
  np = obj['np']
  if obj['upinc']:
    led_right += 1
    if led_right >= 255*4:
      obj['upinc'] = False
  else:
    led_right -= 1
    if led_right <= 1:
      obj['upinc'] = True
  np.brightness(led_right//4)
  obj['led_right'] = led_right

def rgbled_end(obj):
  np = obj['np']
  np.set(1, 0, num=5)
  np.set(6, 0, num=10)
  np.deinit()

prewstate.register("PREW_RGB", MState(start=rgbled_start, loop=rgbled_loop, end=rgbled_end))

# -------- PREW_ENV --------
def env_start(obj):
  lcd.image(0, 0, '/flash/img/3-5.jpg', type=lcd.JPG)
  # obj['env'] = units.ENV(units.PORTA)
  lcd.font(lcd.FONT_Default)

def env_loop(obj):
  # env = obj['env']
  if time.ticks_ms() % 100 == 0:
    # if env.available():
    if 92 in i2c.scan():
      try:
        env = units.ENV(units.PORTA)
        lcd.print("%.1f"%env.temperature()+"'C", 210, 120)
        lcd.print("%.1f"%env.humidity()+"%",     210, 138)
        lcd.print("%.1f"%env.pressure()+"Pa",     208, 156)
      except:
        pass
    else:
      lcd.rect(205, 105, 70, 70, lcd.WHITE, lcd.WHITE)

def env_end(obj):
  obj = {}
  pass

prewstate.register("PREW_ENV", MState(start=env_start, loop=env_loop, end=env_end))

# -------- PREW_MOTION --------
def motion_start(obj):
  lcd.image(0, 0, '/flash/img/3-6.jpg', type=lcd.JPG)
  obj['pir'] = units.PIR(units.PORTB)

def motion_loop(obj):
  if time.ticks_ms() % 200 == 0:
    val = obj['pir'].read()
    if val:
      lcd.circle(230, 150, 20, lcd.RED, lcd.RED)
    else:
      lcd.circle(230, 150, 20, COLOR_GRAY, COLOR_GRAY)

prewstate.register("PREW_MOTION", MState(start=motion_start, loop=motion_loop))

# TODO
# -------- PREW_EXRGB --------
def exrgb_start(obj):
  lcd.image(0, 0, '/flash/img/3-7.jpg', type=lcd.JPG)
  obj['rgb'] = units.RGB(units.PORTB)

def exrgb_loop(obj):
  if time.ticks_ms() % 200 == 0:
    rgb = obj["rgb"]
    rgb.setColor(lcd.RED,   1)
    rgb.setColor(lcd.GREEN, 2)
    rgb.setColor(lcd.BLUE,  3)

def exrgb_end(obj):
  obj['rgb'].deinit()

prewstate.register("PREW_EXRGB", MState(start=exrgb_start, loop=exrgb_loop, end=exrgb_end))

# TODO
# -------- PREW_IR --------
def ir_start(obj):
  lcd.image(0, 0, '/flash/img/3-8.jpg', type=lcd.JPG)
  obj['rx'] = machine.Pin(36, machine.Pin.IN)
  obj['tx'] = machine.PWM(26)
  obj['tx'].init(freq=1000, duty=50)
  # obj['pir'] = units.PIR(units.PORTB)
  # lcd.rect(180, 120, 100, 60, COLOR_GRAY)
  lcd.font(lcd.FONT_Small)
  buf = []
  for i in range(0, 12):
    buf.append(i%2)
  obj['buf'] = buf

def ir_loop(obj):
  rx = obj['rx']
  buf = obj['buf']
  buf.pop()
  buf.insert(0, not rx.value())
  strc = ''
  for i in range(0, 12):
    strc += '%d' % buf[i]
  lcd.print(strc, 182, 140)

def ir_end(obj):
  obj['tx'].deinit()

prewstate.register("PREW_IR", MState(start=ir_start, loop=ir_loop, end=ir_end))

# -------- PREW_ANGLE --------
def angle_start(obj):
  lcd.image(0, 0, '/flash/img/3-9.jpg', type=lcd.JPG)
  np = machine.Neopixel(machine.Pin(15), 10)
  np.brightness(0)
  np.set(1, lcd.WHITE, num=10)
  obj['np'] = np
  obj['angle'] = units.ANGLE(units.PORTB)
  obj['prev'] = 0
  dac = machine.DAC(machine.Pin(25))
  dac.write(0)
  lcd.font(lcd.FONT_DejaVu24)

def angle_loop(obj):
  if time.ticks_ms() % 20 == 0:
    val = int(obj['angle'].read())
    if not obj['prev'] == int(val):
      if obj['prev'] == 100:
        lcd.rect(195, 138, 80, 35, lcd.WHITE, lcd.WHITE)
      obj['prev'] = val
      obj['np'].brightness(int(255*val//100))
      lcd.print("%02d%%" % (int(val)), 200, 140, COLOR_GRAY)

def angle_end(obj):
  obj['np'].deinit()
  obj['angle'].deinit()

prewstate.register("PREW_ANGLE", MState(start=angle_start, loop=angle_loop, end=angle_end))

# -------- PREW_R2CODE --------
def r2code_start(obj):
  lcd.image(0, 0, '/flash/img/3-a.jpg', type=lcd.JPG)
  while buttonC.isPressed():
    pass
  # obj['pir'] = units.PIR(units.PORTB)

def r2code_loop(obj):
  if buttonC.isPressed():
    mainstate.change("STA_WEB_QRCODE")

prewstate.register("PREW_R2CODE", MState(start=r2code_start, loop=r2code_loop))


# ======== Main State machine ========
mainstate = MStateManager()

# ----------- STA_STARTUP ----------
def startup_start(obj):
  lcd.image(0, 0, '/flash/img/1-1.jpg')
  lcd.setColor(lcd.BLACK, lcd.WHITE)
  lcd.font(lcd.FONT_DejaVu24)
  np = machine.Neopixel(machine.Pin(15), 10)
  np.brightness(1)
  np.set(1, 0xffffff, num=10)
  obj['np'] = np
  obj['brs'] = 0
  obj['lcdbrs'] = 10
  obj['dect'] = True
  obj['timeout'] = time.ticks_ms() + 4000

def startup_loop(obj):
  timeout = obj['timeout']
  np = obj['np']
  if buttonA.wasPressed() or (not exists('main.py')): # GUIDE
    mainstate.change("STA_GUIDE")
    lcd.image(0, 0, 'img/2-1.jpg', type=lcd.JPG) # Instruction img
  elif buttonC.wasPressed(): # SETUP
    mainstate.change("STA_WIFI_SETUP")
  elif time.ticks_ms() > timeout:
    mainstate.change("STA_MAIN_ENTER")
  else:
    if (time.ticks_ms() % 1000) > 950:
      lcd.print('%d' % ((timeout-time.ticks_ms())//1000), 300, 5, COLOR_GRAY)
    loading_animat()
    # ------ LED ------
    # if time.ticks_ms() % 2 == 0:
    if obj['lcdbrs'] < 500:
      obj['lcdbrs'] += 2
      lcd.setBrightness(obj['lcdbrs'])
    np.brightness(obj['brs'])
    if obj['dect'] == True:
      obj['brs'] += 1
      if obj['brs'] >= 100:
        obj['dect'] = False
    else:
      obj['brs'] -= 1
      if obj['brs'] <= 0:
        obj['dect'] = True
    gc.collect()

def startup_end(obj):
  np = obj['np']
  np.set(1, 0, num=10)
  np.deinit()
  lcd.setBrightness(500)
  obj = {}

mainstate.register("STA_STARTUP", MState(start=startup_start, loop=startup_loop, end=startup_end))

# ----------- STA_GUIDE ----------
def guide_loop(obj):
  if buttonA.wasPressed():   # Skip
    mainstate.nextState("STA_WEB_QRCODE")
    mainstate.change("STA_CONNECT_WIFI")
  elif buttonC.wasPressed(): # Next
    mainstate.change("STA_NEXT_MACHINE")
    prewstate.start(prew_state_list[0])

mainstate.register("STA_GUIDE", MState(loop=guide_loop))

# -------- STA_NEXT_MACHINE -------
def next_machine_start(obj):
  obj['now_state'] = 0

def next_machine_loop(obj):
  now_state = obj['now_state']
  if buttonA.wasPressed():
    if now_state > 0:
      now_state -= 1
      obj['now_state'] = now_state
      prewstate.change(prew_state_list[now_state])
  elif buttonC.wasPressed():
    if now_state < len(prew_state_list)-1:
      now_state += 1
      obj['now_state'] = now_state
      prewstate.change(prew_state_list[now_state])
  prewstate.run()

mainstate.register("STA_NEXT_MACHINE", MState(start=next_machine_start, loop=next_machine_loop))

# --------- STA_WIFI_SETUP --------
def wifi_setup_start(obj): #BLOCK~
  lcd.image(0, 0, 'img/4-1.jpg', type=lcd.JPG)
  ssid_name= "M5GO-"+node_id[-4:]
  lcd.font(lcd.FONT_Comic, transparent=True)
  lcd.print(ssid_name, 135, 180, lcd.RED)
  wlan_ap = network.WLAN(network.AP_IF)
  # wlan_ap.eventCB(wlan_ap_cb)
  import wificonfig
  wificonfig.webserver_start()

mainstate.register("STA_WIFI_SETUP", MState(start=wifi_setup_start))

# -------- STA_CONNECT_WIFI --------
def connect_wifi_start(obj):
  ssid, password = read_wificonfig()
  if not ssid:
    mainstate.change("STA_WIFI_SETUP")
  lcd.image(0, 0, 'img/4-3.jpg')
  lcd.rect(140, 195, 40, 20, lcd.WHITE, lcd.WHITE) # Bottoms
  lcd.font(lcd.FONT_Default, fixedwidth=False)
  txt_len = lcd.textWidth(ssid)
  lcd.print(ssid, 165+(150-txt_len)//2, 160, COLOR_GRAY)
  # wlan_sta.eventCB(wifi_sta_cb)
  wlan_sta.connect(ssid, password)
  obj['timeout'] = time.ticks_ms() + 8000 # 10s

def connect_wifi_loop(obj):
  if wlan_sta.isconnected():
    print('Connected!')
    mainstate.change(mainstate.nextState())
  else:
    loading_animat()
    if time.ticks_ms() > obj['timeout']:
      wlan_sta.disconnect()
      mainstate.change("STA_CONNECT_WIFI")
    if time.ticks_ms() % 200 == 0:
      print('.', end='')

mainstate.register("STA_CONNECT_WIFI", MState(start=connect_wifi_start, loop=connect_wifi_loop))

# --------- STA_WEB_QRCODE ---------
def web_qrcode_start(obj):
  if not wlan_sta.isconnected():
    mainstate.nextState("STA_WEB_QRCODE")
    mainstate.change("STA_CONNECT_WIFI")
  else:
    lcd.image(0,0, '/flash/img/5-1.jpg')
    url = 'http://io.m5go.com/#/'
    url += node_id
    lcd.qrcode(url, 126, 46, 175)
    if exists('main.py'): # not run the main
      os.rename('main.py', '_main.py')
    lcd.setColor(lcd.WHITE, lcd.BLACK)
    lcd.setCursor(0, 0)
    mainstate.stop()
    gc.collect()

mainstate.register("STA_WEB_QRCODE", MState(start=web_qrcode_start))

# --------- STA_MAIN_ENTER ---------
def main_enter_start(obj):
  lcd.setColor(lcd.WHITE, lcd.BLACK)
  lcd.setCursor(0, 0)
  network.WLANcallback(None)
  mainstate.stop()
  gc.collect()

mainstate.register("STA_MAIN_ENTER", MState(start=main_enter_start))


# ============= Start ==============
def start():
  global mainstate, prewstate
  mainstate.start("STA_STARTUP")
  while True:
    try:
      if not mainstate.run():
        mainstate = 0
        prewstate = 0
        break
    except Exception as e:
      print('---- Exception ----')
      print(e)