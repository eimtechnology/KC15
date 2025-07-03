from machine import Pin, SPI, ADC
import time
import framebuf

from button import button
from buzzer_music import music
from board import game_kit

import test.st7789 as st7789
from test.fonts import vga2_8x8 as font1
from test.fonts import vga1_16x32 as font2

# ADC4
sensor_temp = machine.ADC(4)

conversion_factor = 3.3 / (65535)

spi0=SPI(0,baudrate=4000000, phase=1, polarity=1,
        sck=Pin(game_kit.lcd_sck, Pin.OUT),
        mosi=Pin(game_kit.lcd_sda, Pin.OUT))

display = st7789.ST7789(spi0, 240, 240,
                        reset=Pin(game_kit.lcd_rst, Pin.OUT),
                        dc=Pin(game_kit.lcd_dc, Pin.OUT),
                        xstart=0, ystart=0, rotation=0)
#
display.fill(st7789.BLACK)
display.text(font2, "Chip Temp:", 10, 10)
while True:
    reading = sensor_temp.read_u16() 
    voltage = reading * conversion_factor

    temperature = 27 - (voltage - 0.706) / 0.001721
    print("Temperature: {:.2f} C".format(temperature))
    temp = "{:.2f} C".format(temperature)
    display.text(font2, temp, 10, 50)
    time.sleep(1)
