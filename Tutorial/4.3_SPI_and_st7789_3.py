from machine import Pin, ADC, SPI, I2C
import st7789
from time import sleep

import vga2_8x8 as font1
import vga1_16x32 as font2

# initiate the ST7789 display
spi = SPI(0, baudrate=31250000, polarity=1, phase=1, sck=Pin(18), mosi=Pin(19))
WIDTH, HEIGHT = 240, 240
display = st7789.ST7789(
    spi, WIDTH, HEIGHT,
    reset=Pin(16, Pin.OUT),
    cs=Pin(17, Pin.OUT),
    dc=Pin(21, Pin.OUT),
    backlight=Pin(20, Pin.OUT),
    rotation=0
)
display.fill(st7789.BLACK)

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
MMA845x_ADDR = 0x1C

def init_sensor():
    i2c.writeto_mem(MMA845x_ADDR, 0x2A, b'\x00')  
    i2c.writeto_mem(MMA845x_ADDR, 0x2A, b'\x01')  

def read_accel():
    data = i2c.readfrom_mem(MMA845x_ADDR, 0x01, 6) 
    x = ((data[0] << 8) | data[1]) >> 2
    y = ((data[2] << 8) | data[3]) >> 2
    z = ((data[4] << 8) | data[5]) >> 2
    
    if x > 8191: x -= 16384
    if y > 8191: y -= 16384
    if z > 8191: z -= 16384
    x_g = x / 1024
    y_g = y / 1024
    z_g = z / 1024
    return (x_g, y_g, z_g)

init_sensor()

while True:
    x_g, y_g, z_g = read_accel()
    display.fill(st7789.BLACK)

    display.text(font2, "X: %.2f" % x_g, 10, 10, st7789.WHITE)
    display.text(font2, "Y: %.2f" % y_g, 10, 50, st7789.WHITE)
    display.text(font2, "Z: %.2f" % z_g, 10, 90, st7789.WHITE)
    sleep(0.1)
