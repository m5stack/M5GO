# Authors: Paul Cunnane 2016, Peter Dahlebrg 2016
#
# This module borrows from the Adafruit BME280 Python library. Original
# Copyright notices are reproduced below.
#
# Those libraries were written for the Raspberry Pi. This modification is
# intended for the MicroPython and esp8266 boards.
#
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Based on the BMP280 driver with BME280 changes provided by
# David J Taylor, Edinburgh (www.satsignal.eu)
# converted back to BMP280 by Sebastian Bachmann <hello@reox.at>
#
# Based on Adafruit_I2C.py created by Kevin Townsend.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import utime as time
from ustruct import unpack, unpack_from
from array import array

# BMP280 default address.
# To use this address, you need to tie SDO to GND.
# using VDDIO, the address is 0x77
BMP280_I2CADDR = 0x76

# Operating Modes
BMP280_OSAMPLE_1 = 1
BMP280_OSAMPLE_2 = 2
BMP280_OSAMPLE_4 = 3
BMP280_OSAMPLE_8 = 4
BMP280_OSAMPLE_16 = 5

BMP280_POWER_MODE_SLEEP = 0
BMP280_POWER_MODE_FORCED = 1
# 2 corresponds also to FORCED mode
BMP280_POWER_MODE_NORMAL = 3


# Contains the ID of the chip, which is always 0x58
BMP280_REGISTER_ID = 0xD0

# You can reset the chip by writing 0xB6 to this register
BMP280_REGISTER_RESET = 0xE0

BMP280_REGISTER_STATUS = 0xF3

# Register 0xF4 ... "ctr_meas"
# 7 6 5 4 3 2 1 0
# | | | | | | | +- power mode = 0b11 (Normal mode)
# | | | | | | +--- power mode
# | | | | | +----- oversampling pressure = 0b101 (OSP x16)
# | | | | +------- oversampling pressure
# | | | +--------- oversampling pressure
# | | +----------- oversampling temperature = 0b111 (OSP x16)
# | +------------- oversampling temperature
# +--------------- oversampling temperature
BMP280_REGISTER_CONTROL = 0xF4

# Register 0xF5 ... "config"
# 7 6 5 4 3 2 1 0
# | | | | | | | +- spi3w_en: Enable 3-wire SPI
# | | | | | | +--- not used
# | | | | | +----- filter: time constant for IIR filter
# | | | | +------- filter
# | | | +--------- filter
# | | +----------- t_sb: Standby time in normal mode
# | +------------- t_sb
# +--------------- t_sb
BMP280_REGISTER_CONFIG = 0xF5

# We use microseconds instead
# 1.25 ms
T_INIT_MAX = 1250
# 2.3125 ms
T_MEASURE_PER_OSRS_MAX = 2313
# 0.625 ms
T_SETUP_PRESSURE_MAX = 625


class BMP280:
    def __init__(self,
                 i2c=None,
                 mode_pressure=BMP280_OSAMPLE_1,
                 mode_temperature=BMP280_OSAMPLE_1,
                 address=BMP280_I2CADDR,
                 **kwargs):
        """
        Note that there are several suggested pairs of modes!

        Setting Name        Pressure    Temperature
        Ultra low pwer      x1          x1
        Low power           x2          x1
        Standard res.       x4          x1
        High res.           x8          x1
        Ultra high res      x16         x2

        for the temperature setting, usually higher values of x2 oversampling
        are not required, as x2 already provides a typ. resolution of 0.0025 deg C.
        The datasheet states, that higher values than x2 will not significantly
        improve the accuracy.

        TODO:
        add the IIR Filter mode
        """
        # Check that mode is valid.
        if mode_pressure not in [BMP280_OSAMPLE_1, BMP280_OSAMPLE_2, BMP280_OSAMPLE_4,
                        BMP280_OSAMPLE_8, BMP280_OSAMPLE_16]:
            raise ValueError(
                'Unexpected mode pressure value {0}. Set mode to one of '
                'BMP280_ULTRALOWPOWER, BMP280_STANDARD, BMP280_HIGHRES, or '
                'BMP280_ULTRAHIGHRES'.format(mode_pressure))
        if mode_temperature not in [BMP280_OSAMPLE_1, BMP280_OSAMPLE_2, BMP280_OSAMPLE_4,
                        BMP280_OSAMPLE_8, BMP280_OSAMPLE_16]:
            raise ValueError(
                'Unexpected mode temperature value {0}. Set mode to one of '
                'BMP280_ULTRALOWPOWER, BMP280_STANDARD, BMP280_HIGHRES, or '
                'BMP280_ULTRAHIGHRES'.format(mode_temperature))
        self._mode_pressure = mode_pressure
        self._mode_temperature = mode_temperature
        self.address = address
        if i2c is None:
            raise ValueError('An I2C object is required.')
        self.i2c = i2c

        # load calibration data
        # Calibration data is stored in the 8bit registers 0x88 to 0xA1
        # where the two last ones are not used.
        dig_88_a1 = self.i2c.readfrom_mem(self.address, 0x88, 24)
        self.dig_T1, self.dig_T2, self.dig_T3, self.dig_P1, \
            self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, \
            self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9, = unpack("<HhhHhhhhhhhh", dig_88_a1)


        # FIXME why do we need to send this here?
        #self.i2c.writeto_mem(self.address, BMP280_REGISTER_CONTROL,
        #                     bytearray([0b11110111]))
        self.t_fine = 0

        # temporary data holders which stay allocated
        self._l1_barray = bytearray(1)
        self._l8_barray = bytearray(6)
        self._l3_resultarray = array("i", [0, 0])

    def compute_delay_time(self):
        """
        Compute the delay time in microseconds until the measurement is ready
        """
        return T_INIT_MAX + T_SETUP_PRESSURE_MAX + \
               T_MEASURE_PER_OSRS_MAX * ((1 << self._mode_temperature) >> 1) + \
               T_MEASURE_PER_OSRS_MAX * ((1 << self._mode_pressure) >> 1)

    def read_raw_data(self, result):
        """ Reads the raw (uncompensated) data from the sensor.

            Args:
                result: array of length 3 or alike where the result will be
                stored, in temperature, pressure, humidity order
            Returns:
                None
        """

        self._l1_barray[0] = self._mode_temperature << 5 | self._mode_pressure << 2 | BMP280_POWER_MODE_FORCED
        self.i2c.writeto_mem(self.address, BMP280_REGISTER_CONTROL, self._l1_barray)

        time.sleep_us(self.compute_delay_time())  # Wait the required time

        # burst readout from 0xF7 to 0xFC, recommended by datasheet
        # we read the 6 bytes (3 bytes each)
        self.i2c.readfrom_mem_into(self.address, 0xF7, self._l8_barray)
        readout = self._l8_barray
        # pressure(0xF7): ((msb << 16) | (lsb << 8) | xlsb) >> 4
        raw_press = ((readout[0] << 16) | (readout[1] << 8) | readout[2]) >> 4
        # temperature(0xFA): ((msb << 16) | (lsb << 8) | xlsb) >> 4
        raw_temp = ((readout[3] << 16) | (readout[4] << 8) | readout[5]) >> 4

        result[0] = raw_temp
        result[1] = raw_press

    def read_compensated_data(self, result=None):
        """ Reads the data from the sensor and returns the compensated data.

            Args:
                result: array of length 3 or alike where the result will be
                stored, in temperature, pressure, humidity order. You may use
                this to read out the sensor without allocating heap memory

            Returns:
                array with temperature, pressure, humidity. Will be the one from
                the result parameter if not None
        """
        self.read_raw_data(self._l3_resultarray)
        raw_temp, raw_press = self._l3_resultarray
        # temperature
        var1 = ((raw_temp >> 3) - (self.dig_T1 << 1)) * (self.dig_T2 >> 11)
        var2 = (((((raw_temp >> 4) - self.dig_T1) *
                  ((raw_temp >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        temp = (self.t_fine * 5 + 128) >> 8

        # pressure
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = (((var1 * var1 * self.dig_P3) >> 8) +
                ((var1 * self.dig_P2) << 12))
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            pressure = 0
        else:
            p = 1048576 - raw_press
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

        if result:
            result[0] = temp
            result[1] = pressure
            return result

        return array("i", (temp, pressure))

    @property
    def values(self):
        """ human readable values """

        t, p = self.read_compensated_data()
        return t / 100, p / 25600