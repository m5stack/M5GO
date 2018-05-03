from m5stack import *
import utime as time

lcd.clear(lcd.BLACK)
lcd.font(lcd.FONT_DejaVu24)
lcd.print('Demo Game', 0, 0, lcd.WHITE)
time.sleep(1)

import examples.rps_game