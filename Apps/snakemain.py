import machine
from machine import Timer,PWM,ADC,Pin
import time
import random
import _thread
import st7789_snake as st7789
from test.fonts import vga2_8x8 as font1
from test.fonts import vga1_16x32 as font2
import framebuf
import sys
#from buzzer_music import music
from time import sleep
import utime

dtime=(1,1,1,1,
       1,1,1,1,
       1,1,1,1,
       1.5,0.5,2,
       1,1,1,1,
       1,1,1,1,
       1,1,1,1,
       1.5,0.5,2,
       1,1,1,1,
       1,0.5,0.5,1,1,
       1,0.5,0.5,1,1,
       1,1,1,1,
       1,1,1,1,
       1,1,1,0.5,0.5,
       1,1,1,1,
       1.5,0.5,2)

st7789_res = 0
st7789_dc  = 1
disp_width = 240
disp_height = 240
CENTER_Y = int(disp_width/2)
CENTER_X = int(disp_height/2)
spi_sck=machine.Pin(2)
spi_tx=machine.Pin(3)
spi0=machine.SPI(0,baudrate=4000000, phase=0, polarity=1, sck=spi_sck, mosi=spi_tx)
print(spi0)
display = st7789.ST7789(spi0, disp_width, disp_height,
                          reset=machine.Pin(st7789_res, machine.Pin.OUT),
                          dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                          xstart=0, ystart=0, rotation=0)

up = Pin(8, Pin.IN, Pin.PULL_UP)    # Up
#down = Pin(6, Pin.IN, Pin.PULL_UP)  # Down
#left = Pin(7, Pin.IN, Pin.PULL_UP)  # Left
start = Pin(5, Pin.IN, Pin.PULL_UP) # Right
a=machine.Pin(28,Pin.PULL_UP)
b=machine.Pin(29,Pin.PULL_UP)
BeepIO= machine.Pin(16,machine.Pin.OUT)
pwm = PWM(machine.Pin(16))

xAxis = ADC(Pin(28))
yAxis = ADC(Pin(29))

direction = 1

pup = 0
pdown = 0
pleft = 0
pright = 0

global highScore
highScore = 0

def reset_game():
    global goal, speedv, lv, direction, pup, pdown, flag, l1, snake, highScore
    snake = []
    goal = 0
    speedv = 0.5
    lv = 1
    direction = 1
    pup = 0
    pdown = 0
    flag = 0
    #display.fill(st7789.BLACK)
    #display.fill_rect(0,0,240,240,st7789.BLACK)
    food()
    l1 = intsnake()
   
    
def waitRestart():
    while True:
        if(start.value() == 0):
            time.sleep(0.3)
            reset_game()
            break
        time.sleep(0.3)
        
        
        
def pushup(Pin):
    global pup
    pup=1

def pushdown(Pin):
    global pdown
    pdown=1
    
def pushleft(Pin):
    global flag
    flag = 2
    

def pushright(Pin):
    global flag
    flag = 1

def displays(snake):
    length=len(snake)
    a=0
    while(a<length):
        display.fill_rect(snake[a],snake[a+1],10,10,st7789.WHITE)
        a+=2

def food(snake=[-1,-1]):
    global x1,y1
    x1=random.randrange(0,230)
    y1=random.randrange(0,180)
    x1=x1-x1%10
    y1=y1-y1%10
    while(x1 in snake and y1 in snake):
        x1=random.randrange(0,230)
        y1=random.randrange(0,180)
        x1=x1-x1%10
        y1=y1-y1%10        
    display.fill_rect(x1,y1,10,10,st7789.RED)
    
def intsnake():
    x2=random.randrange(0,230)
    y2=random.randrange(0,180)
    x2=x2-x2%10
    y2=y2-y2%10
    snake=[x2,y2]
    display.fill_rect(x2,y2,10,10,st7789.WHITE)
    return snake
    
def addlong(x,y,snake):
    head=[x,y]
    head.extend(snake)
    return head

def chuli(snake, x, y):

    global x1, y1, speedv, lv, crush, died, goal, highScore
    died = False
    if goal < 5:   
        speedv = 0.1
        lv = 1
    elif goal < 10:
        speedv = 0.09
        lv = 2
    elif goal < 15:
        speedv = 0.0
        lv = 3
    elif goal < 20:
        speedv = 0.1
        lv = 4
    else:
        speedv = 0.09
        lv = 5
    
    crush = 0
    length = len(snake)
    
    # Check collision with body (exclude current head at index 0 and 1)
    a = 2
    while a < length:
        if snake[a] == x and snake[a+1] == y:
            crush = 1
            break
        a += 2
    
    #death
    if crush == 1 or x > 240 or x < 0 or y > 180 or y < 0:
        if goal >= highScore:
            highScore = goal
            
        print(x, y, crush)
        display.fill(st7789.BLACK)
        display.text(font2, "Game Over!", 40, 80, st7789.RED)
        display.text(font2, "Final score:", 10, 110, st7789.BLUE)
        display.text(font2, str(goal), 200, 110, st7789.YELLOW)
        display.text(font1, "Press the B to restart!", 10, 160)
        display.text(font2, "HIGH SCORE:", 5, 190)
        display.text(font2, str(highScore),180, 190)


        #Timer.deinit()
        died = True
        waitRestart()
        reset_game()
        
        
    if died != True:
        newsnake = addlong(x, y, snake)  # Add the new head here once
        if x == x1 and y == y1:
            goal += 1
            
            newsnake = addlong(x1, y1, newsnake)  # Grow longer by adding food pos again
            displays(newsnake)
            food(newsnake)

        # Clear last tail segment
        display.fill_rect(newsnake[-2], newsnake[-1], 10, 10, st7789.BLACK)
        del newsnake[-1]
        del newsnake[-1]
        
        displays(newsnake)
        time.sleep(speedv)
        display.hline(0, 190, 240, st7789.RED)
        display.text(font2, "score:", 0, 200)
        display.text(font2, str(goal), 95, 200, st7789.YELLOW)
        display.text(font2, "level:", 125, 200)
        display.text(font2, str(lv), 215, 200, st7789.YELLOW)

        return newsnake

def read_joystick():
    global direction
    xValue = xAxis.read_u16()
    yValue = yAxis.read_u16()

    # Up
    if xValue >= 50000 and direction != 0:  # prevent reverse
        direction = 2
    # Down
    elif xValue <= 500 and direction != 2:
        direction = 0
    # Right
    elif yValue <= 500 and direction != 1:
        direction = 3
    # Left
    elif yValue >= 50000 and direction != 3:
        direction = 1

def dir(snake):
    global x, y, direction
    print(snake)
    if snake == None:
        display.fill(st7789.BLACK)
        food()
        snake = intsnake()
    x = snake[0]
    y = snake[1]
 
    read_joystick()

    # Move the snake head according to direction
    if direction == 0:  # up
        y -= 10
    elif direction == 1:  # right
        x += 10
    elif direction == 2:  # down
        y += 10
    elif direction == 3:  # left
        x -= 10

    # Pass the new coordinates and old snake to chuli, which handles adding the head
   
    return chuli(snake, x, y)
        
#global flag,r,l,goal,stop,pup,pdown,speedv,lv,fo,sx,lenm,crush
r=l=flag=goal=stop=pup=pdown=fo=sx=crush=0
speedv=0.5
lv=1
tim = Timer()

#button controls

up.irq(handler=pushup,trigger=machine.Pin.IRQ_FALLING)
start.irq(handler=pushup,trigger=machine.Pin.IRQ_FALLING)

display.text(font2, "Greedy Snake", 20, 80,st7789.YELLOW)
display.text(font1, "Press the up key to start!", 15, 120)
display.hline(0,190,240,st7789.RED)
display.text(font2, "score:", 0, 200)
display.text(font2, str(goal), 95, 200,st7789.YELLOW)
display.text(font2, "level:", 125, 200)
display.text(font2, str(lv), 215, 200,st7789.YELLOW)



while(pup==0 and pdown==0 and flag==0):
    continue
pup=0
#tim.init(freq=1, mode=Timer.PERIODIC, callback=tick)
display.fill(st7789.BLACK)
food()

direction =1
l1 = intsnake()

while True:
    if l1 != []:


        l1 = dir(l1)
        if not l1:  # empty list means game restarted
            continue  # just continue the loop with new l1 from reset_game(
  

    
    



    