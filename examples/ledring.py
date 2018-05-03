import machine, time
led_bar = machine.Neopixel(15, 10)
while True:
  for i in range(1, 11):
    if i > 0:
      led_bar.set(i, led_bar.BLACK) # OFF
    if i+1 <= 10:
      led_bar.set(i+1, led_bar.WHITE) # ON
    time.sleep(0.1)