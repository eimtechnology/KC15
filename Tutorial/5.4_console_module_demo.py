import uos
from machine import Pin, SPI, ADC,PWM
import time, math, array
import random
import framebuf
from utime import sleep_ms
import struct

from buzzer_music import music
import mma7660
import st7789
from fonts import vga2_8x8 as font1
from fonts import vga1_16x32 as font2

pwm = PWM(Pin(19))
pwm.freq(50)

st7789_res = 0
st7789_dc  = 1
disp_width = 240
disp_height = 240
CENTER_Y = int(disp_width/2)
CENTER_X = int(disp_height/2)
spi_sck=Pin(2)
spi_tx=Pin(3)
spi0=SPI(0,baudrate=4000000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)

sda=Pin(10)
scl=Pin(11)
mma7660=machine.I2C(1,sda=sda,scl=scl,freq=400000)
mma7660.writeto_mem(76,7,b'1')

display = st7789.ST7789(spi0, disp_width, disp_width,
                          reset=machine.Pin(st7789_res, machine.Pin.OUT),
                          dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                          xstart=0, ystart=0, rotation=0)
display.fill(st7789.BLACK)
display.text(font2, "Evo-in-motion", 10, 10)
display.text(font2, "Technology", 10, 40)

xAxis = ADC(Pin(28))
yAxis = ADC(Pin(29))

buttonB = Pin(5,Pin.IN, Pin.PULL_UP) #B
buttonA = Pin(6,Pin.IN, Pin.PULL_UP) #A
buttonStart = Pin(7,Pin.IN, Pin.PULL_UP) #A
buttonSelect = Pin(8,Pin.IN, Pin.PULL_UP) #A

while True:

    xValue = xAxis.read_u16()
    yValue = yAxis.read_u16()
    buttonValueA = buttonA.value()
    buttonValueB = buttonB.value()
    buttonValueStart = buttonStart.value()
    buttonValueSelect = buttonSelect.value()
    
    x=mma7660.readfrom_mem(76,0,8)
    y=mma7660.readfrom_mem(76,1,8)
    z=mma7660.readfrom_mem(76,2,8)
    xout=struct.unpack('<h',x)[0]
    yout=struct.unpack('<h',y)[0]
    zout=struct.unpack('<h',z)[0]

    display.text(font1, "xVaule="+"%05d" %(xValue) , 10, 80)
    display.text(font1, "yVaule="+"%05d" %(yValue), 120, 80)
    display.text(font1, "buttonValueA="+str(buttonValueA), 10, 100)
    display.text(font1, "buttonValueB="+str(buttonValueB), 10, 120)
    display.text(font1,"buttonValueStart="+str(buttonValueStart) , 10, 140)
    display.text(font1, "buttonValueSelect="+str(buttonValueSelect), 10, 160)
    display.text(font1,"xout="+"%05d" %(xout) , 10, 180)
    display.text(font1,"yout="+"%05d" %(yout) , 10, 200)
    display.text(font1,"zout="+"%05d" %(zout) , 10, 220)
    
    #mySong.tick()




