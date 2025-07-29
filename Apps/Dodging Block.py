import uos
import machine
import test.st7789 as st7789
from test.fonts import vga2_8x8 as font1
from test.fonts import vga1_16x32 as font2
import random
import framebuf
from time import sleep
from button import button
from machine import I2C, Pin, Timer, SPI,ADC,PWM

xAxis = machine.ADC(machine.Pin(29))
yAxis = machine.ADC(machine.Pin(28))

st7789_res = 0
st7789_dc  = 1
disp_width = 240
disp_height = 240
CENTER_Y = int(disp_width/2)
CENTER_X = int(disp_height/2)
print(uos.uname())
spi_sck=machine.Pin(2)
spi_tx=machine.Pin(3)
spi0=machine.SPI(0,baudrate=4000000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)
#
#print(spi0)
display = st7789.ST7789(spi0, disp_width, disp_width,
                          reset=machine.Pin(st7789_res, machine.Pin.OUT),
                          dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                          xstart=0, ystart=0, rotation=0)
#car_image=open("/carar.bin", 'rb')
display.fill(st7789.BLACK)
display.text(font2, "Hello!", 72, 10)
display.text(font2, "Player", 72, 40)
display.text(font1, "Press any key to", 56, 100)
display.text(font2, "START", 80, 140)
display.text(font1, "www.luxiansheng.ltd", 44, 200)

#buttton Initialization
key_a=button(6)
key_b=button(5)
key_start=button(7)
key_select=button(8)

def any_key():
    while True:
        sleep(0.02)
        if key_a.value()==True or key_b.value()==True or key_start.value()==True or key_select.value()==True:
            print(key_a.value())
            return True
        else:
            return False
        
def player_run(self):
   
    xValue = xAxis.read_u16()
    yValue = yAxis.read_u16()

    self.mapx = (xValue *40)//65536 - 20 #map 2^16 to max speed , 50
    
        

        
   
while True:
    display.text(font2, "     ", 80, 140)
    sleep(0.2)
    display.text(font2, "START", 80, 140)
    sleep(0.2)
    keytf=any_key()
    if keytf==True:
        break

class car:
    speed=8
    score=0
    obstacle_rect=[]
    car_rect=[64,176,88,216]
    wobs=0#random number	
    collision=False
    car_speed=8
    def __init__(self,speed=1):
        car.speed=speed
    def out_frame(self):
        for i in range(0,240,8):
            for j in range(0,240,8):
                display.fill_rect(j,i,8,8,st7789.BLACK)
        display.fill_rect(0,0,8,240,st7789.color565(0xff,0,0))
        display.fill_rect(0,0,240,8,st7789.color565(0xff,0,0))
        display.fill_rect(0,232,240,8,st7789.color565(0xff,0,0))
        display.fill_rect(232,0,8,240,st7789.color565(0xff,0,0))
        display.fill_rect(144,0,8,240,st7789.color565(0xff,0,0))
        display.text(font2, "Score", 152, 20)
        display.text(font2,str(car.score),176,52)
        display.text(font2,"Speed",152,84)
        display.text(font2,str(car.speed),176,116)        
        display.text(font2,"Auth",160,148)
        display.text(font2,"L&L",168,180)
    def obstacle_frame(self):
        car.wobs=random.randint(8,104)
        car.obstacle_rect=[8,8,car.wobs,23,car.wobs+39,8,143,23]
        
        
    def obstacle_move(self):
        if car.obstacle_rect[3]>=231 :
            if car.obstacle_rect[1]<232:
                display.fill_rect(car.obstacle_rect[0],car.obstacle_rect[1],car.wobs-8,car.speed,st7789.BLACK)
                display.fill_rect(car.obstacle_rect[4],car.obstacle_rect[5],104-car.wobs,car.speed,st7789.BLACK)
            else: 
                 return -1
        else:
            display.fill_rect(car.obstacle_rect[0],car.obstacle_rect[3]+1,car.wobs-8,car.speed,st7789.YELLOW)
            display.fill_rect(car.obstacle_rect[4],car.obstacle_rect[7]+1,104-car.wobs,car.speed,st7789.YELLOW)
            display.fill_rect(car.obstacle_rect[0],car.obstacle_rect[1],car.wobs-8,car.speed,st7789.BLACK)
            display.fill_rect(car.obstacle_rect[4],car.obstacle_rect[5],104-car.wobs,car.speed,st7789.BLACK)
        for i in range(1,8,2):
            car.obstacle_rect[i]+=car.speed
    def car_move(self,yg_direction):
        if yg_direction>0:
            car.car_rect[0]+=yg_direction
            car.car_rect[2]+=yg_direction

            car.car_rect[0] = max(8, min(car.car_rect[0], 136 - 24))
            car.car_rect[2] = car.car_rect[0] + 24
            if car.car_rect[0]>=8 and car.car_rect[2]<=144:
                display.fill_rect(car.car_rect[0]-yg_direction,car.car_rect[1],24,40,st7789.BLACK)
                display.fill_rect(car.car_rect[0],car.car_rect[1],24,40,st7789.GREEN)
                '''display.fill_rect(car.car_rect[2],car.car_rect[1],car.car_speed,40,st7789.GREEN)
                display.fill_rect(car.car_rect[0],car.car_rect[1],car.car_speed,40,st7789.BLACK)
        '''
        elif yg_direction<0:
            car.car_rect[0]+=yg_direction

            # Limit left and right bounds safely
            car.car_rect[0] = max(8, min(car.car_rect[0], 144 - 24))
            car.car_rect[2] = car.car_rect[0] + 24  # Ensure width is always 24
            if car.car_rect[0]>=8 and car.car_rect[2]<=144:
                display.fill_rect(car.car_rect[0]-yg_direction,car.car_rect[1],24,40,st7789.BLACK)
                display.fill_rect(car.car_rect[0],car.car_rect[1],24,40,st7789.GREEN)
        #print(car.car_rect)
        '''
        if car.car_rect[0]<(8+car.car_speed):
                car.car_rect[0]=8+car.car_speed
                car.car_rect[2]=31+car.car_speed
        if car.car_rect[2]>(144-car.car_speed):
                car.car_rect[0]=120-car.car_speed
                car.car_rect[2]=144-car.car_speed
'''
    def car_obstacle(self):#Car and obstacle collision detection
        if car.obstacle_rect[1]<216 and car.obstacle_rect[3]>176:
            if car.car_rect[0]<car.wobs or car.car_rect[0]>(16+car.wobs):
                car.collision=True
if __name__=="__main__":
    pause=False
    ad=car()
    ad.out_frame()
    display.fill_rect(car.car_rect[0],car.car_rect[1],24,40,st7789.GREEN)
    while True:
        if car.collision==True:
            print(4545)
            break
        ad.obstacle_frame()
        display.text(font2,"  ",176,52)
        display.text(font2,str(car.score),176,52)
        while True:
            xValue = xAxis.read_u16()
            mapx = (xValue *40)//65536 - 20 #map 2^16 to max speed , 50
            if car.collision==True:
                break
            ad.car_obstacle()
            sleep(0.02)
            if abs(mapx) < 5:
                mapx = 0 #adds deadzone
            car.car_speed = mapx
        
            
         #here it moves
            ad.car_move(car.car_speed // 4)
        
            ad.obstacle_move()
            #print(car.obstacle_rect)
            if car.obstacle_rect[1]>231:
                car.score+=1
                break
    while True:
        display.text(font2,"GameOver",10,104)
        sleep(0.2)
        display.text(font2,"        ",10,104)
