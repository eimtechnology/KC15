import uos
import test.st7789 as st7789
from test.fonts import vga2_8x8 as font1
from test.fonts import vga1_16x32 as font2
import random
import framebuf
from machine import Pin, SPI, ADC,PWM
import time, math,array
from utime import sleep_ms
from test.buzzer_music import music
from test import mma7660
import struct
#song='0 B4 1 43 0.6456692814826965;2 B4 1 43 0.7716535329818726;3 A4 1 43 0.8661417365074158;5 B4 1 43 0.9370078444480896;7 D5 1 43;9 B4 1 43;11 F#4 1 43;12 A4 2 43;14 B4 1 43;16 B4 1 43;18 B4 1 43;19 A4 1 43;21 B4 1 43;23 F5 1 43;25 E5 1 43;27 D5 1 43;28 A4 2 43;30 B4 1 43;32 B4 1 43;34 B4 1 43;35 A4 1 43;37 B4 1 43;39 D5 1 43;41 B4 1 43;43 F#4 1 43;44 A4 2 43;46 B4 1 43;48 B4 1 43;50 B4 1 43;52 A4 1 43;53 B4 1 43;62 B4 1 43;64 B4 1 43;66 B4 1 43;67 A4 1 43;69 B4 1 43;71 D5 1 43;73 B4 1 43;75 F#4 1 43;76 A4 2 43;78 B4 1 43;80 B4 1 43;82 B4 1 43;83 A4 1 43;85 B4 1 43;87 F5 1 43;89 E5 1 43;91 D5 1 43;92 A4 2 43;94 B4 1 43;96 B4 1 43;98 B4 1 43;99 A4 1 43;101 B4 1 43;103 D5 1 43;105 B4 1 43;107 F#4 1 43;108 A4 2 43;110 B4 1 43;112 B4 1 43;114 B4 1 43;115 A4 1 43;117 B4 1 43;119 F5 1 43;121 E5 1 43;123 D5 1 43;124 A4 2 43;126 B4 1 43;128 B4 1 43;130 B4 1 43;131 A4 1 43;133 B4 1 43;135 D5 1 43;137 B4 1 43;139 F#4 1 43;140 A4 2 43;142 B4 1 43;144 B4 1 43;146 B4 1 43;147 A4 1 43;149 B4 1 43;151 F5 1 43;153 E5 1 43;155 D5 1 43;156 A4 2 43;158 B4 1 43;160 B4 1 43;162 B4 1 43;163 A4 1 43;165 B4 1 43;167 D5 1 43;169 B4 1 43;171 F#4 1 43;172 A4 2 43;174 B4 1 43;176 B4 1 43;178 B4 1 43;179 A4 1 43;180 B4 1 43;181 D5 1 43;183 F5 1 43;185 E5 1 43;187 D5 1 43;188 A4 2 43'

pwm = PWM(Pin(19))
#mySong = music(song, pins=[Pin(23)])
pwm.freq(50)

#image_file0 = "/logo.bin"

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

'''
f_image = open(image_file0, 'rb')
 
for column in range(1,240):
                buf=f_image.read(480)
                display.blit_buffer(buf, 1, column, 240, 1)
'''

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



