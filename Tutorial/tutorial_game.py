from machine import Pin, SPI, ADC, I2C, PWM
import math
import os
import random
import st7789
import framebuf
import machine
from font import vga1_16x32 as font
from time import sleep

#st7789 set up
WIDTH, HEIGHT = 240, 240
 # SCK = SCL
 # MOSI = SDA
BACKLIGHT_PIN = 21
CS_PIN = 20
DC_PIN = 17
RST_PIN = 16
MOSI_PIN = 19 #SDA
SCK_PIN = 18 #SCL
SPI_NUM = 0

spi = SPI(SPI_NUM, baudrate=31250000, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN))
tft = st7789.ST7789(
    spi, WIDTH, HEIGHT,
    reset=Pin(RST_PIN, Pin.OUT),
    cs=Pin(CS_PIN, Pin.OUT),
    dc=Pin(DC_PIN, Pin.OUT),
    backlight=Pin(BACKLIGHT_PIN, Pin.OUT),
    rotation=0,
)
buffer = bytearray(WIDTH * HEIGHT * 2)
nextFrame = framebuf.FrameBuffer(buffer, WIDTH, HEIGHT-40, framebuf.RGB565)
# end of st7789

#buttons
buttonA = Pin(11, Pin.IN, Pin.PULL_UP)
buttonB = Pin(10, Pin.IN, Pin.PULL_UP)
#end of buttons

# joystick set up
x_adc = ADC(Pin(27))  # GP26 = ADC0
y_adc = ADC(Pin(26))  # GP27 = ADC1

sw = Pin(28, Pin.IN, Pin.PULL_UP)

speed_up = False
#end of joystick set up

#accelerator set up
#MMA8452 3-axis accelerator default I2C address
MMA845x_ADDR = 0x1C

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
#end of accelerator set up

#buzzer wiring 
buzzer = Pin(8)
buzzer_pwm = PWM(buzzer)
buzzer_pwm.freq(4000)

# palyer information
box_size = 10
x = WIDTH // 2
y = HEIGHT // 2
player = [x, y]
box_color = st7789.WHITE

'''
functions for button
button related global switchs/variables are also stored here
'''
#True == joystick, False == Accelerator
control_method = True

def button_pressed(button):
    if button.value() == 0:
        return True
    else:
        return False
'''    
functions for accelerator
'''
def scan():
    print("I2C devices:", i2c.scan())
    
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

    return (-x_g, -y_g, -z_g)

'''
functions about palyer movment
'''
def set_speed_joysick(x_val, y_val, threshold=1490):
    center = 32767
    acc = [0, 0]
    
    if abs(x_val - center) >= threshold:
        acc[0] = x_val - center
    if abs(y_val - center) >= threshold:
        acc[1] = y_val - center
        
    accx = int((acc[0])/2979)
    accy = int((acc[1])/2979)
    
    return -accx, -accy

def set_speed_acceleraor(threshold=0.5):
    spd = [0, 0, 0]
    spd = read_accel()
    spdx, spdy = 0, 0
    
    if abs(spd[0]) >= threshold:
        spdy = -5 * int(spd[0])
    if abs(spd[1]) >= threshold:
        spdx = -5 * int(spd[1])

    return spdx, spdy

def next_box(x, y, xspd, yspd):
    offshore = box_size + 5 
    HEIGHT_bound_min = offshore + 25
    WIDTH_bound_min = offshore
    WIDTH_bound_max = WIDTH - offshore -10
    HEIGHT_bound_max = HEIGHT - offshore -35
    
    y += yspd        
    if y > WIDTH_bound_max:
        y = WIDTH_bound_max
    elif y < WIDTH_bound_min:
        y = WIDTH_bound_min
        
    x -= xspd
    if x > HEIGHT_bound_max:
        x = HEIGHT_bound_max
    elif x < HEIGHT_bound_min:
        x = HEIGHT_bound_min
    '''
    print("Height:", HEIGHT_bound_min, "-", HEIGHT_bound_max)
    print("Width:", WIDTH_bound_min, "-", WIDTH_bound_max)
    '''
    return x, y

def draw_nextPlayer(player, inputs):
    # update status
    nextX, nextY = next_box(player[0], player[1], inputs[0], inputs[1])
    
    # display prefill
    nextFrame.fill_rect(nextY, nextX, box_size, box_size, box_color)
    
    # player data updated
    player[0], player[1] = nextX, nextY

"""
Adding enemy, game start, and other game functions
"""
#a list of enemies, this is a globle variable
enemy_list = []
enemy_number = 15
color_choices = [st7789.BLUE, st7789.GREEN, st7789.YELLOW]
"""
Enemy properties:
1. Starting x axis position
2. Speed in y axis
3. Color
"""
def create_enemy():
    position = 10 * random.randint(1, 23) -5
    speed = 3 * random.randint(1, 5)
    color = random.choice(color_choices)
    ex = int(position)
    ey = 35
    
    return [ex, ey, speed, color]

def add_enemy():
    #do we need add enemy?
    if random.randint(1, 5) == 3:
        #do we have space to add enemy?
        if len(enemy_list) < enemy_number:
            enemy_list.append(create_enemy())
        else:
            pass
    else:
            pass

#in fact, this function could be divided into two functions, one dedicates to drawing
# the other one for updating enemies' status
def draw_enemies(enemies):
    if len(enemies) > 0:
        for i in range(len(enemies)):
            if enemy_list[i][1] + enemy_list[i][2] >= 240:
                enemies[i][1] = HEIGHT
            else:
                nextFrame.fill_rect(enemy_list[i][0],
                              enemy_list[i][1] + enemy_list[i][2],
                              box_size, box_size,
                              enemy_list[i][3])
                enemies[i][1] += enemies[i][2]
                    

def reduce_enemies(enemies):
    death_list = []
    if len(enemies) > 0:
        for i in range(len(enemies)):
            if enemies[i][1] >= 185:
                death_list.append(i)
            else:
                pass
    
    if len(death_list) > 0:
        for j in range(len(death_list) - 1, -1, -1):
            enemies.pop(death_list[j])
  

def draw_clearFrame():
    nextFrame.fill(0x0000)
    tft.blit_buffer(buffer, 0, 0, WIDTH, HEIGHT)

def game_start():
    pass

def game_end():
    pass

#the main loop is here
#scan()
init_sensor()
l_inputs = [0,0,0,0,0]
encountered = False

def collision(obj1,obj2):
    if abs(obj1[0] - obj2[0]) < (box_size /2) and abs(obj1[1] - obj2[1]) < (box_size /2):
    #if abs(obj1[0] - obj2[0]) < box_size and abs(obj1[1] - obj2[1]) < box_size:
        return True
    else:
        return False
    
def detect_collision(player, enemies):
    #print(len(enemies))
    for enemy in enemies:
        if collision(player, enemy):
            return True
    return False

score = [0,0,0,0]

while True:
    # start initializing for next frame
    #print("reset new frame")
    inputs = [0,0,0,0,0]
    # encountered = False    
    #clear previous frame
    
    nextFrame.fill(0x0000)
    # end of initializing
    
    #start monitoring input
    btn_pressed = not sw.value()  
    x_val = x_adc.read_u16()  
    y_val = y_adc.read_u16()
    
    if btn_pressed:
        inputs[2] = 1
    
    # monitoring button input
    if button_pressed(buttonA):
        inputs[3] = 1
        if l_inputs[3] == inputs[3]:
            pass
        else:
            control_method = not control_method
            
    if button_pressed(buttonB):
        inputs[4] = 1
        pass
        encountered = True
    #End of monitoring input

    #start updating status
    # x_direction, y_direction = set_speed(x_val, y_val, threshold=1490)
    if control_method:
        inputs[0], inputs[1] = set_speed_joysick(x_val, y_val, threshold=1490)
    else:
        inputs[0], inputs[1] = set_speed_acceleraor(threshold=0.5)

    #print("input recieved")
    # updating status
    encountered = detect_collision(player, enemy_list)
    draw_nextPlayer(player, inputs)
    add_enemy()
    draw_enemies(enemy_list)
    #print(encountered)
    #end of updating status
    #print("end of updating")
    
    #start generating next frame
    tft.blit_buffer(buffer, 0, 0, WIDTH, HEIGHT-40)
    if control_method:
        tft.text(font,str("JOY"),188,204,st7789.color565(255,0,0))
    elif not control_method:
        tft.text(font,str("ACC"),188,204,st7789.color565(255,0,0))
    else:
        pass
    
    tft.text(font,str("SCORE: "),8,204,st7789.color565(255,255,255))
    
    for i in reversed(range(1, len(score))):
        while score[i] > 9:
            score[i] = 0
            score[i - 1] += 1
    #print(score)
    score_text = str(score[0])+str(score[1])+str(score[2])
    tft.text(font,score_text,112,204,st7789.color565(255,255,255))
    #end of generating next frame
    
    if encountered:
        buzzer_pwm.duty_u16(1000)
    else:
        buzzer_pwm.duty_u16(0)
        
    
    #start postframe processing 
    #to clear trashes
    #reset temp status
    reduce_enemies(enemy_list)
    l_inputs = inputs
    #end of reset temp status
    
    #debug info
    if btn_pressed:
        draw_clearFrame()
        player = [120, 120]
        enemy_list = []
        score = [0,0,0,0]
        
    #print(inputs)
    #print(player)
    #print(enemy_list)
    #end of debug info
    #print("gap")
    score[3]+=1
    sleep(0.1)

