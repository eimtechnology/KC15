#car_game 

from machine import I2C, Pin, Timer, ADC
from board import game_kit
from time import sleep
from mma7660 import MMA7660
from breakout_colourlcd240x240 import BreakoutColourLCD240x240
import uasyncio as asyncio
import random
from button import button
from buzzer_music import music
import gc

def twos_compliment(n, nbits):
    sign_bit = 1 << nbits - 1
    sign = 1 if n & sign_bit == 0 else -1
    val = n & ~sign_bit if sign > 0 else sign * ((sign_bit << 1) - n)
    return val

def set_speed_joysick(x_val, y_val, threshold=1490):
    center = 32767
    acc = [0, 0]
        
    if abs(x_val - center) >= threshold:
        acc[0] = x_val - center
    if abs(y_val - center) >= threshold:
        acc[1] = y_val - center
            
    accx = int((acc[0])/2979)
    accy = int((acc[1])/2979)
        
    return accx, -accy
    
class car:
    def __init__(self,x_location,y_location,v1x,v1y,character1):
        self.x = x_location
        self.y = y_location 
        self.vx = v1x
        self.vy = v1y
        self.character = character1  
        self.car_track = 1          
        self.car_change = 0         
        self.blink_flag = 0         
        self.being_hit = False           
    
class car_process:
    def __init__(self):
        # bgm
        self.bgm = p_music(p_music.song, tempo=1, duty=500, pins=[Pin(game_kit.buzzer, Pin.OUT)])
        # controller
        self.k1 = button(game_kit.key_a, self.k1_callback)
        self.k2 = button(game_kit.key_b, self.k2_callback)
        
        self.tim = Timer(period=50, mode=Timer.PERIODIC, callback=self.blink)
        
        self.v_forward = 5
        
        self.y = 0
        
        self.car_player = car(100,200,0,0,'player')
            
        self.car_npc1 = car(40,0,0,self.v_forward,'block')
    
        self.car_npc2 = car(160,140,0,self.v_forward,'block')
        
        self.x_expected2 =0
        self.x_expected1 =0
        
        self.life = 1
        
        self.blink_flag = 1
        
        self.blink_s = 1
        
        self.score = 0
        
        self.restart_cw = False
        
        self.keepgoing_cw = False
        
        self.state = 1


    def k1_callback(self, p):
        print("k1 pressed")
        self.restart_cw = True
        self.restart()
        
    def k2_callback(self, p):
        print("k2 pressed")
        self.keepgoing_cw = True
        self.restart() 
        
    def blink(self,t):
        self.blink_s *= -1

    def hardware_init(self):
        width = BreakoutColourLCD240x240.WIDTH
        height = BreakoutColourLCD240x240.HEIGHT

        display_buffer = bytearray(width * height * 2)  # 2-bytes per pixel (RGB565)
        self.display = BreakoutColourLCD240x240(display_buffer)

        self.display.set_backlight(1.0)
        i2c1 = I2C(1, scl=Pin(game_kit.accelerometer_scl), sda=Pin(game_kit.accelerometer_sda))

        self.acc = MMA7660(i2c1)
        
        self.x_adc = ADC(Pin(game_kit.joy_x)) 
        self.y_adc = ADC(Pin(game_kit.joy_y))

        self.acc.on(True)

  

    async def process(self):

        bgm = asyncio.create_task(self.bgm_process())

        self.hardware_init()
        self.transition_ani_enter()
        while True:
            while self.score < 100*self.state:
                await self.judge()
                self.player_run()
                self.npc_run()
                self.draw()
                self.bgm.mute()
                await asyncio.sleep_ms(10)
                gc.collect()
            self.v_forward += 1
            self.state +=1
   
    def player_run(self):
        self.d = bytearray(3)
        '''
        self.acc.getSample(self.d)
        self.rl = twos_compliment(self.d[1], 6)
        self.fb = twos_compliment(self.d[0], 6)
        '''
        self.x_val = self.x_adc.read_u16()  # 0 - 65535
        self.y_val = self.y_adc.read_u16()
        self.acc = set_speed_joysick(self.x_val, self.y_val)
        self.car_player.vx = self.acc[0]
        self.car_player.vy = -self.acc[1]
        self.car_player.x += self.car_player.vx
        self.car_player.y += self.car_player.vy
        if self.car_player.x >165:
            self.car_player.x = 165
        if self.car_player.x <30:
            self.car_player.x = 30
        if self.car_player.y >204:
            self.car_player.y = 204
        if self.car_player.y <0:
            self.car_player.y = 0
   
    def npc1_produce(self):
        #npc1
        self.car_npc1.being_hit = False
        
        value = random.randint(1,10)
        if value == 1 :
            self.car_npc1.character = 'life'
        elif (value == 2) or (value == 3):
            self.car_npc1.character = 'score'
        else:
            self.car_npc1.character = 'block'
        
        self.car_npc1.car_track = random.randint(1,3)
        self.car_npc1.car_change = random.randint(1,3)
        if self.car_npc1.car_track == 1:
            self.car_npc1.x = 40    
        if self.car_npc1.car_track == 2:
            self.car_npc1.x = 100
        if self.car_npc1.car_track == 3:
            self.car_npc1.x = 160
        if (self.car_npc1.car_change-self.car_npc1.car_track)>0:
            self.car_npc1.vx = 5
        if (self.car_npc1.car_change-self.car_npc1.car_track)<0:
            self.car_npc1.vx = -5
        if (self.car_npc1.car_change-self.car_npc1.car_track)==0:
            self.car_npc1.vx = 0
    
    def npc2_produce(self):
        #npc2
        self.car_npc2.being_hit = False
        value = random.randint(1,10)
        
        if value == 1 :
            self.car_npc2.character = 'life'
        elif (value == 2) or (value == 3):
            self.car_npc2.character = 'score'
        else:
            self.car_npc2.character = 'block'

        self.car_npc2.car_track = random.randint(1,3)
        self.car_npc2.car_change = random.randint(1,3)
        if self.car_npc2.car_track == 1:
            self.car_npc2.x = 40
        if self.car_npc2.car_track == 2:
            self.car_npc2.x = 100
        if self.car_npc2.car_track == 3:
            self.car_npc2.x = 160
        if (self.car_npc2.car_change-self.car_npc2.car_track)>0:
            self.car_npc2.vx = 5
        if (self.car_npc2.car_change-self.car_npc2.car_track)<0:
            self.car_npc2.vx = -5
        if (self.car_npc2.car_change-self.car_npc2.car_track)==0:
            self.car_npc2.vx = 0
        
        
   
    def npc_run(self):
        self.car_npc1.vy = self.v_forward
        self.car_npc2.vy = self.v_forward
    
    
        self.car_npc1.y += self.car_npc1.vy
        self.car_npc2.y += self.car_npc2.vy
        
        if self.car_npc1.car_change == 1:
            self.x_expected1 = 40    
        if self.car_npc1.car_change == 2:
            self.x_expected1 = 100
        if self.car_npc1.car_change == 3:
            self.x_expected1 = 160
        if self.car_npc1.x == self.x_expected1:
            self.car_npc1.vx = 0
        
        if self.car_npc2.car_change == 1:
            self.x_expected2 = 40    
        if self.car_npc2.car_change == 2:
            self.x_expected2 = 100
        if self.car_npc2.car_change == 3:
            self.x_expected2 = 160
        if self.car_npc2.x == self.x_expected2:
            self.car_npc2.vx = 0
        
        if self.car_npc1.y <80 :
            self.car_npc1.blink_flag = 1
        else:
            self.car_npc1.blink_flag = 0
            self.car_npc1.x += self.car_npc1.vx
            
        if self.car_npc2.y <80 :
            self.car_npc2.blink_flag = 1
        else:
            self.car_npc2.blink_flag = 0
            self.car_npc2.x += self.car_npc2.vx
        
        if self.car_npc1.y >239:
            self.car_npc1.y = -40
            self.score += 10
            self.npc1_produce()
                
        if self.car_npc2.y >239:
            self.car_npc2.y = -40
            self.score += 10
            self.npc2_produce()
            

    async def judge(self):
        self.restart_cw = False
        self.keepgoing_cw = False
        if ((self.car_player.x > self.car_npc1.x) and (self.car_player.x<self.car_npc1.x+25)) or ((self.car_player.x+25 > self.car_npc1.x) and (self.car_player.x+25<self.car_npc1.x+25)):
            if ((self.car_player.y > self.car_npc1.y) and (self.car_player.y<self.car_npc1.y+35)) or ((self.car_player.y+35 > self.car_npc1.y) and (self.car_player.y+35<self.car_npc1.y+35)):
                if self.car_npc1.being_hit == False:
                    if self.car_npc1.character == 'block':
                        self.life -= 1
                        await self.crach()
                        self.car_npc1.being_hit = True
                    if self.car_npc1.character == 'score':
                        self.score += 10
                        self.car_npc1.being_hit = True
                        self.bgm.unmute()    
                    if self.car_npc1.character == 'life':
                        self.life += 1
                        self.car_npc1.being_hit = True
                        self.bgm.unmute()

        if((self.car_player.x > self.car_npc2.x) and (self.car_player.x<self.car_npc2.x+25)) or ((self.car_player.x+25 > self.car_npc2.x) and (self.car_player.x+25<self.car_npc2.x+25)):
            if((self.car_player.y > self.car_npc2.y) and (self.car_player.y<self.car_npc2.y+35)) or ((self.car_player.y+35 > self.car_npc2.y) and (self.car_player.y+35<self.car_npc2.y+35)):
                if self.car_npc2.being_hit == False:
                    if self.car_npc2.character == 'block':
                        self.life -= 1
                        await self.crach()
                        self.car_npc2.being_hit = True
                    if self.car_npc2.character == 'score':
                        self.score += 10
                        self.car_npc2.being_hit = True
                        self.bgm.unmute()
                    if self.car_npc2.character == 'life':
                        self.life += 1
                        self.car_npc2.being_hit = True
                        self.bgm.unmute()
    
    
    async def crach(self):
        self.bgm.unmute()
        await asyncio.sleep_ms(1000)
        self.bgm.mute()
        if self.life == 0:
            self.gg_ani()
        else:
            self.restart_ani()
        self.transition_ani_enter()
    
    def restart(self):
        self.car_npc2.vy = self.v_forward
        self.car_npc1.vy = self.v_forward        
        
    def restart_ani(self):
        s = str(self.score)
        l = str(self.life)
        self.display.set_pen(40, 40, 40)
        self.display.clear()
        self.display.update()
        self.display.set_pen(40, 40, 40)
        self.display.clear()
        self.display.set_pen(255,255,255)
        self.display.text("YOUR SCORE:",0,0,200,3)
        self.display.text(s,170,0,200,3)
        self.display.text("YOUR HP:",0,30,200,3)
        self.display.text(l,170,30,200,3)
        self.display.text("Keep GOING?", 40,70, 200, 4)
        self.display.text("press B to continue", 40,150, 200, 3)
        self.display.text("press A to give up", 40,190, 200, 3)
        self.display.update()
        gc.collect()
        while self.keepgoing_cw == False:
            pass
            if self.restart_cw == True:
                self.gg_ani()
                self.keepgoing_cw = True    

    def gg_ani(self):
        s = str(self.score)
        self.display.set_pen(40, 40, 40)
        self.display.clear()
        self.display.update()
        self.display.set_pen(40, 40, 40)
        self.display.clear()
        self.display.set_pen(255,255,255)
        self.display.text("YOUR SCORE:",0,0,200,3)
        self.display.text(s,170,0,200,3)
        self.display.text("GAME OVER!!", 40, 70, 200, 4)
        self.display.text("press A to restart", 40,150, 200, 3)
        self.display.update()
        gc.collect()
        self.restart_cw = False
        while self.restart_cw == False:
            pass
        self.score = 0
        self.v_forward = 5
        self.life = 1
        self.state = 1

    def transition_ani_enter(self):
        self.car_player.y = 274
        self.car_player.vy = -5
        self.car_player.x = 100
        self.car_npc1.y = -35
        self.car_npc2.y = -175
        self.npc1_produce()
        self.npc2_produce()
        while self.car_player.y > 150 :
            self.car_player.y += self.car_player.vy
            self.draw()
            sleep(0.02)

    def cross_line(self,y1):
        for i in range(3):
            if y1 >239:
                y1 = y1-239
            self.display.set_pen(255,255,255)
            
            if y1+50 > 239:

                self.display.rectangle(80, y1, 5,239-y1)
                self.display.rectangle(135, y1, 5,239-y1)
                self.display.rectangle(80, 0, 5,y1+50-239)
                self.display.rectangle(135, 0, 5,y1+50-239)
            else:
                self.display.set_pen(255,255,255)
                self.display.rectangle(80, y1, 5,50)
                self.display.rectangle(135, y1, 5,50)
            y1 = y1+80
 
    def draw_car(self,x,y,ch,b_flag,v):
        #body
        if ch == 'player':
            self.display.set_pen(255,0,0)
        if ch == 'block':
            self.display.set_pen(0,0,255)
        if ch == 'score':
            self.display.set_pen(255,165,0)
        if ch == 'life':
            self.display.set_pen(0,255,0)
        self.display.rectangle(x+4, y, 17,3)
        self.display.rectangle(x+1, y+3,23,7)
        self.display.rectangle(x+1, y+21,23,10)
        self.display.rectangle(x+3, y+3,19,26)
        #wheels
        self.display.set_pen(0,0,0)
        self.display.rectangle(x, y+4, 3,5)
        self.display.rectangle(x+22, y+4,3,5)
        self.display.rectangle(x, y+23,3,5)
        self.display.rectangle(x+22, y+23,3,5)
        #window
        self.display.rectangle(x+5, y+23, 15,2)
        self.display.rectangle(x+6, y+20,13,3)
        self.display.rectangle(x+7, y+18,11,2)
        self.display.rectangle(x+8, y+16,9,2)
        self.display.rectangle(x+9, y+15,7,1)
        self.display.rectangle(x+10, y+14,5,1)
        #tail
        self.display.rectangle(x+6, y+32,13,2)
        self.display.rectangle(x+7, y+30,2,2)
        self.display.rectangle(x+16, y+30,2,2)
        #前灯
        self.display.set_pen(255,255,0)
        self.display.rectangle(x+2, y+1,3,2)
        self.display.rectangle(x+20, y+1,3,2)    
        #lights
        if b_flag == 1:
            self.display.set_pen(255,255,0)
            if v>0:
                if self.blink_s >0:
                    self.display.rectangle(x+19, y+29,6,6)
            if v<0:
                if self.blink_s >0:
                    self.display.rectangle(x, y+29,6,6)



    def draw(self):
        s = str(self.score)
        l = str(self.life)
        v= str(self.v_forward*10-int(self.car_player.vy)) 
        self.display.set_pen(40, 40, 40)
        self.display.clear()
        
        self.display.set_pen(190,190,190)
        self.display.rectangle(31, 0, 160,240)
        
        self.display.set_pen(173,216,230)
        self.display.rectangle(190, 0,50,40)
        self.display.set_pen(0,139,69)
        self.display.text("sco", 190, 0, 40, 2)
        self.display.text(s, 190, 20, 40, 2)
        
        self.display.set_pen(0, 0, 255)
        self.display.rectangle(190, 40,50,40)
        self.display.set_pen(0, 255, 0)
        self.display.text(v, 190, 40, 40, 2)
        self.display.text("km/h", 190, 60, 40, 2)
        
        self.display.set_pen(54, 100, 139)
        self.display.rectangle(190, 80,50,40)        
        self.display.set_pen(255, 0, 0)
        self.display.text("HP", 190, 80, 40, 2)
        self.display.text(l, 190, 100, 40, 2)

        self.y += self.v_forward
        self.cross_line(self.y)
        if self.y>239:
            self.y=0
            
        #draw player
        self.draw_car(self.car_player.x,self.car_player.y,self.car_player.character,0,0)

        
        #draw npc
        if self.car_npc1.being_hit == False:
            self.draw_car(self.car_npc1.x,self.car_npc1.y,self.car_npc1.character,self.car_npc1.blink_flag,self.car_npc1.vx)
        if self.car_npc2.being_hit == False:
            self.draw_car(self.car_npc2.x,self.car_npc2.y,self.car_npc2.character,self.car_npc2.blink_flag,self.car_npc2.vx)

        self.display.update()
    
    async def bgm_process(self):
        while True:
            await asyncio.sleep_ms(100)
            self.bgm.tick()
    
class p_music(music):
    song = "0 E4 1 15;2 E4 1 15;1 F4 1 15;3 F4 1 15;4 F#4 2 15;6 G#4 2 15;9 G#4 1 15;8 A#4 1 15;10 F#4 1 15;11 F4 1 15;12 D#4 1 15;13 C#4 1 15;14 D#4 1 15;15 D#4 1 15;16 D#4 1 15;19 C#4 1 15;21 D#4 1 15;23 C#4 1 15;24 E4 1 15;26 E4 1 15;25 F4 1 15;27 F4 1 15;28 F#4 2 15;8 C5 1 13;6 B4 1 13;7 B4 1 13;5 A4 1 13;4 A4 1 13;3 G4 1 13;2 F#4 1 13;1 G4 1 13;0 F#4 1 13;9 A#4 1 13;10 G#4 1 13;11 G4 1 13;12 F4 1 13;17 D4 1 13;18 C#4 1 13;21 C#4 1 13;24 F#4 1 13;25 G4 1 13;26 F#4 1 13;27 G4 1 13;28 G#4 1 13;29 G#4 1 13;30 A#4 1 13;14 F4 1 13;15 F4 1 13;16 F4 1 13;19 D#4 1 13;21 F4 1 13;23 D#4 1 13"
    #sound effects
    def __init__(self, songString='0 D4 8 0', looping=True, tempo=3, duty=2512, pin=None, pins=[Pin(0)]):
        super().__init__(songString, looping, tempo, duty, pin, pins)
        self.pause = True


    def toggle_pause(self):
        self.pause = not self.pause
        if self.pause:
            print("mute\n")
            self.mute()
        else:
            print("unmute\n")
            self.unmute()
    
    def mute(self):
        for pwm in self.pwms:
            pwm.duty_u16(0)
            self.pause = True
    def unmute(self):
        for pwm in self.pwms:
            pwm.duty_u16(self.duty)
            self.pause = False
    def tick(self):
        if self.pause:
            pass
        else:
            super().tick()
        


def main():
    gc.enable()  #开启垃圾回收
    s = car_process()   
    asyncio.run(s.process())

main()

