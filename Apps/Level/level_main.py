import time
import random
from breakout_colourlcd240x240 import BreakoutColourLCD240x240
from machine import I2C, Pin,ADC
from board import pin_cfg
from time import sleep
from mma7660 import MMA7660
from ws2812b import PixelDisplay
import framebuf
from math import atan,sqrt,sin,cos

#about adc
buttonB = Pin(5,Pin.IN, Pin.PULL_UP) #B
buttonA = Pin(6,Pin.IN, Pin.PULL_UP) #A
k=0.5#kalman

#about mma7660
i2c1 = I2C(1, scl=Pin(pin_cfg.i2c1_scl), sda=Pin(pin_cfg.i2c1_sda))

acc = MMA7660(i2c1)
acc.on(True)

d = bytearray(3)

r = [0 for x in range(3)]
def twos_compliment(n, nbits):
    sign_bit = 1 << nbits - 1
    sign = 1 if n & sign_bit == 0 else -1
    val = n & ~sign_bit if sign > 0 else sign * ((sign_bit << 1) - n)
    #print((n,val))
    return val

#about LCD240x240
width = BreakoutColourLCD240x240.WIDTH
height = BreakoutColourLCD240x240.HEIGHT

display_buffer = bytearray(width * height * 2)  # 2-bytes per pixel (RGB565)
display = BreakoutColourLCD240x240(display_buffer)

display.set_backlight(0)

class Ball:
    def __init__(self, x, y, r, dx, dy, pen):
        self.x = x
        self.y = y
        self.r = r
        self.dx = dx
        self.dy = dy
        self.pen = pen


# initialise shapes
balls = []
#big circle
BigCircle_x=100
BigCircle_y=140
BigCircle_r=99
BigCircle_r1=49
BigCircle_r2=51
BigCircle_r3=9
BigCircle_r4=11
BigCircle_r5=97
BigCircle_dx=0
BigCircle_dy=0
balls.append(
        Ball(
            BigCircle_x,
            BigCircle_y,
            BigCircle_r,
            BigCircle_dx,
            BigCircle_dy,
            display.create_pen(0,0,0),)
        )
#circle0
balls.append(
        Ball(
            BigCircle_x,
            BigCircle_y,
            BigCircle_r5,
            BigCircle_dx,
            BigCircle_dy,
            display.create_pen(0x00,0xff,0x00),)
        )
#circle1
balls.append(
        Ball(
            BigCircle_x,
            BigCircle_y,
            BigCircle_r2,
            BigCircle_dx,
            BigCircle_dy,
            display.create_pen(0,0,0),)
        )
#circle2
balls.append(
        Ball(
            BigCircle_x,
            BigCircle_y,
            BigCircle_r1,
            BigCircle_dx,
            BigCircle_dy,
            display.create_pen(0x00,0xff,0x00),)
        )
#circle3
balls.append(
        Ball(
            BigCircle_x,
            BigCircle_y,
            BigCircle_r4,
            BigCircle_dx,
            BigCircle_dy,
            display.create_pen(0,0,0),
        )
        )
#circle4
balls.append(
        Ball(
            BigCircle_x,
            BigCircle_y,
            BigCircle_r3,
            BigCircle_dx,
            BigCircle_dy,
            display.create_pen(0x00,0xff,0x00),
        )
        )
#circle5
Ball_x=100
Ball_y=140
Ball_r=10
Ball_dx=0
Ball_dy=0
Ball_color=(0x00,0x00,0xff)
balls.append(
        Ball(
            Ball_x,
            Ball_y,
            Ball_r,
            Ball_dx,
            Ball_dy,
            display.create_pen(0x00,0x00,0xff),)
        )
#ball
balls.append(
        Ball(
            Ball_x,
            Ball_y,
            Ball_r,
            Ball_dx,
            Ball_dy,
            display.create_pen(0x00,0x00,0xff),)
        )
#ball up
balls.append(
        Ball(
            Ball_x,
            Ball_y,
            Ball_r,
            Ball_dx,
            Ball_dy,
            display.create_pen(0x00,0x00,0xff),)
        )
#ball right
def kalman(dx_now,dx_previous,k):
    return dx_now*k+(1-k)*dx_previous

while True:
    buttonValueA = buttonA.value()
    buttonValueB = buttonB.value()
    if buttonValueA==0:
        k=round((k+0.1)%1.1,1)
    if buttonValueB==0:
        k=round((k-0.1)%1.1,1)
    #set number-k
    display.set_pen(0xff, 0x00, 0x00)
    display.clear()
    display.set_pen(0)
    display.rectangle(0,40,200,200)#mid
    display.rectangle(198,0,42,82)#right up
            
    display.set_pen(0xff,0x00,0x00)
    display.rectangle(2,42,196,196)
    #get the data
    acc.getSample(d)
    for i in range(3):
        if r[2]==0:
            r[2]=0.001
        if r[0]==0:
            r[0]=0.001
        if r[1]==0:
            r[1]=0.001
        r[i] = twos_compliment(d[i], 6)
    #get the ball from the data
    #print((r[0],r[1],r[2]))
    Range=90
    rx=180/3.1415926*atan(r[0]/sqrt(r[1]*r[1]+r[2]*r[2]))
    ry=-180/3.1415926*atan(r[1]/sqrt(r[0]*r[0]+r[2]*r[2]))
    rz=180/3.1415926*atan(r[2]/sqrt(r[1]*r[1]+r[0]*r[0]))
    rx=rx*90/Range
    ry=ry*90/Range
    rz=int(rz*90/Range)
    #start kalman
    a=rx
    rx=ry
    ry=a#turn x to y,turn y to x
    dy=ry-balls[6].y
    dx=rx-balls[6].x
    balls[6].dy=kalman(dy,balls[6].dy,k)
    balls[6].dx=kalman(dx,balls[6].dx,k)
    balls[6].y=balls[6].y+balls[6].dy
    balls[6].x=balls[6].x+balls[6].dx#record the angle
    ball_y=balls[6].y
    ball_x=balls[6].x
    #print((ball_x,ball_y))
    #end kalman
    
    if ball_x*ball_x+ball_y*ball_y>=BigCircle_r*BigCircle_r:
        if ball_x==0:
            ball_x=0.001
        theta=atan(ball_y/ball_x)
        balls[6].x=int(BigCircle_r*cos(theta))+100
        balls[6].y=int(BigCircle_r*sin(theta))+140
    else:
        balls[6].y=int(ball_y+140)
        balls[6].x=int(ball_x+100)
    for i in range (9):
        #print(i)
        display.set_pen(balls[i].pen)
        display.circle(balls[i].x, balls[i].y, balls[i].r)
        if i==4:
            display.set_pen(0)
            display.rectangle(0,139,200,2)
            display.rectangle(99,40,2,200)
            #two lines
            display.text("45",155,145,0,1)
            display.text("-45",35,145,0,1)
            display.text("45",90,80,0,1)
            display.text("-45",90,200,0,1)
            display.text("x",185,125,0,2)
            display.text("y",90,40,0,2)
            display.set_pen(0xff,0xff,0xff)
            display.rectangle(200,0,40,80)
            #right up rectangle
            display.set_pen(0)
            display.text("k:"+str(k),201,60,0,2)
            display.text("x:"+str(balls[6].x-100),201,0,0,2)
            display.text("y:"+str(-(balls[6].y-140)),201,20,0,2)
            display.text("z:"+str(-rz),201,40,0,2)
            #add the region lines-start
            display.set_pen(0,0,0)
            display.rectangle(48,8,104,24)#up
            display.rectangle(208,88,24,104)#right
            #add the region lines-end
            display.set_pen(0,0xff,0)
            display.rectangle(50,10,100,20)
            display.rectangle(210,90,20,100)
            #up and right rectangle
            balls[7].x=int((balls[6].x-100)/2+100)
            balls[7].y=20
            balls[8].y=int((balls[6].y-140)/2+140)
            balls[8].x=220
        display.set_pen(0)
        display.rectangle(100,10,2,20)
        display.rectangle(75,10,2,20)
        display.rectangle(125,10,2,20)
        display.rectangle(210,140,20,2)
        display.rectangle(210,115,20,2)
        display.rectangle(210,165,20,2)
        #up and right -lines
        
    display.update()
    time.sleep(0.1)
