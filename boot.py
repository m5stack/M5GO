# This file is executed on every boot (including wake-boot from deepsleep)
import sys, gc, utime

# Set default path
# Needed for importing modules and upip
sys.path[1] = '/flash/lib'

# M5G0
import M5GO
M5GO.start()

gc.collect()


# ./BUILD.sh -f16 -fs 2000 -a 2000 flash