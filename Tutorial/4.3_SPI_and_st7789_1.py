"""
Chapter 4.3.2
Set up SPI communication and initialize the display driver
"""

from machine import Pin, SPI
import st7789
import time

# initialize SPI communication
spi = SPI(0, baudrate=31250000, polarity=1, phase=1, sck=Pin(18), mosi=Pin(19))

WIDTH, HEIGHT = 240, 240

# initialize st7789 object
display = st7789.ST7789(
    spi, WIDTH, HEIGHT,
    reset=Pin(16, Pin.OUT),
    cs=Pin(17, Pin.OUT),
    dc=Pin(21, Pin.OUT),
    backlight=Pin(20, Pin.OUT),
    rotation=0
)

# draw a red pixel
display.pixel(170, 180, st7789.RED)
# draw a yellow line 
display.line(30, 40, 150, 160, st7789.YELLOW)
# draw a white rectangle 
display.rect(10, 20, 30, 40, st7789.WHITE)
# draw a filled green rectangle shape
display.fill_rect(70, 80, 30, 40, st7789.GREEN)
