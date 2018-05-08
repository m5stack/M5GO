#!/bin/bash
esptool.py --chip esp32 --port /dev/tty.SLAB_USBtoUART --baud 961200 write_flash -z 0x1000 firmware.bin
esptool.py --chip esp32 --port /dev/tty.SLAB_USBtoUART --baud 961200 --before default_reset --after no_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1b0000 spiffs_image.img