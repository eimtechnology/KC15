import random
import time
import uasyncio as asyncio
import uos
import machine
import framebuf
from machine import Pin, SPI, ADC

import test.st7789 as st7789
from test.fonts import vga2_8x8 as font1
from test.fonts import vga1_16x32 as font2
# import vga2_8x8 as font

from button import button
from buzzer_music import music

from board import game_kit

class hardware():
    def init():
        spi0=SPI(0,baudrate=4000000, phase=1, polarity=1,
                     sck=Pin(game_kit.lcd_sck, Pin.OUT),
                     mosi=Pin(game_kit.lcd_sda, Pin.OUT))
        display = st7789.ST7789(spi0, 240, 240,
                                  reset=Pin(game_kit.lcd_rst, Pin.OUT),
                                  dc=Pin(game_kit.lcd_dc, Pin.OUT),
                                  xstart=0, ystart=0, rotation=0)
#
        display.fill(st7789.BLACK)
        display.text(font2, "Pong!", 90, 90)
        display.text(font2, "Let's go!", 60, 140)
        time.sleep(1)
        
        hardware.display = display
        

class pong():
    def __init__(self):
        # bgm
        self.bgm = p_music(p_music.song2, tempo=1, duty=500, pins=[
            Pin(game_kit.buzzer, Pin.OUT)])
        # press x button to pause/play bgm
        self.key_start = button(game_kit.key_start, self.key_start_callback)
        
        # led control
        self.led = Pin(game_kit.led_sta, Pin.OUT)
        
        self.scoreChanged = 0
        
        self.width = 240  # Screen width
        self.height = 240  # Screen height
        self.CENTER_X = int(self.height/2)  # Horizontal coordinate of screen center
        self.pad_width = 10  # Paddle width
        self.pad_height = 60  # Paddle height
        self.player1 = 0  # Left player's score
        self.player2 = 0  # Right player's score
        self.pad1_pos = [0, self.height/2-self.pad_height/2]  # Top-left position of the left paddle
        self.pad2_pos = [self.width-self.pad_width, self.height/2-self.pad_height/2]  # Top-left position of the right paddle
        self.old_pad1_pos = [0, 0]  # Records top-left position of the left paddle before refresh
        self.old_pad2_pos = [0, 0]  # Records top-left position of the right paddle before refresh
        self.square_width = 10  # Ball width
        self.square_height = 10  # Ball height
        self.square_pos = [self.width/2-self.square_width/2, self.height/2-self.square_height/2]  # Top-left position of the ball
        self.old_square_pos = [0, 0]  # Records top-left position of the ball before refresh
        self.pad1_vel = 0  # Vertical speed of left paddle
        self.pad2_vel = 0  # Vertical speed of right paddle
        self.square_vel = [4, 4]  # Ball speed
        time.sleep(1)
    
    def key_start_callback(self, p):
        print("key_start pressed")
        self.bgm.toggle_pause()
    
    def init_run(self):
        #Enter the game, initialize each game module state
        hardware.display.fill(st7789.BLACK)
        hardware.display.text(font2, str(self.player1), 80, 10)  # left player score
        hardware.display.text(font2, str(self.player2), 135, 10)  # right player score
        hardware.display.line(self.CENTER_X, 0, self.CENTER_X, self.height, st7789.WHITE)  # mid-line
        hardware.display.line(self.pad_width, 0, self.pad_width, self.height, st7789.WHITE)  # lefg edge
        hardware.display.line(self.width-self.pad_width, 0, self.width-self.pad_width, self.height, st7789.WHITE)  # right edge
        hardware.display.fill_rect(int(self.pad1_pos[0]), int(self.pad1_pos[1]), self.pad_width, self.pad_height, st7789.BLUE)  # left paddle
        hardware.display.fill_rect(int(self.pad2_pos[0]+1), int(self.pad2_pos[1]), self.pad_width, self.pad_height, st7789.BLUE)  # right paddle
        hardware.display.fill_rect(int(self.square_pos[0]), int(self.square_pos[1]), self.square_width, self.square_width, st7789.WHITE)  # ball
    
    async def blink(self):
        self.led.value(1)
        await asyncio.sleep_ms(50)
        self.led.value(0)
        await asyncio.sleep_ms(50)
    
    async def process(self):
        bgm = asyncio.create_task(self.bgm_process())
 
        self.init_run()
         
        # main loop
        while True:
            self.dir_select()
            self.run()
            self.judge()
            self.draw()
            await self.blink()
            
    def dir_select(self):
        KEYA = Pin(game_kit.key_select, Pin.IN, Pin.PULL_UP).value() #key a to move right paddle up
        KEYB = Pin(game_kit.key_b, Pin.IN, Pin.PULL_UP).value() #key b to move right paddle down
        xAxis = ADC(Pin(game_kit.joy_y)).read_u16()
        step = 1
        if KEYA == 0:
            self.pad2_vel -= step  # Decrease right paddle speed by 1
        elif KEYB == 0:
            self.pad2_vel += step  # Increase right paddle speed by 1
        elif xAxis < 1000:
            self.pad1_vel -= step  # Decrease left paddle speed by 1
        elif xAxis > 60000:
            self.pad1_vel += step  # Increase left paddle speed by 1

    def run(self):
        # Update the position of the ball
        self.old_square_pos[0] = self.square_pos[0]
        self.old_square_pos[1] = self.square_pos[1]
        self.square_pos[0] += self.square_vel[0]
        self.square_pos[1] += self.square_vel[1]
        # Ball collision detection
        if self.square_pos[0] <= self.pad_width+1 or self.square_pos[0] >= self.width-self.pad_width-self.square_width-1:
            self.square_vel[0] = - self.square_vel[0]
        if self.square_pos[1] <= 0 or self.square_pos[1] >= self.height-self.square_height:
            self.square_vel[1] = - self.square_vel[1]
            
        # Keep paddles within the screen
        if self.pad1_pos[1] <= 0: 
            self.pad1_vel = 1
        elif self.pad1_pos[1] >= self.height-self.pad_height:
            self.pad1_vel = -1
        if self.pad2_pos[1] <= 0: 
            self.pad2_vel = 1
        elif self.pad2_pos[1] >= self.height-self.pad_height:
            self.pad2_vel = -1
            
        
        # Record paddle's previous positions for clearing
        self.old_pad1_pos[0] = self.pad1_pos[0]
        self.old_pad1_pos[1] = self.pad1_pos[1]
        self.old_pad2_pos[0] = self.pad2_pos[0]
        self.old_pad2_pos[1] = self.pad2_pos[1]
        # Update paddle positions 
        self.pad1_pos[1] += self.pad1_vel
        print("pad1_vel:", self.pad1_vel)
        print("pad2_vel:", self.pad2_vel)
        self.pad2_pos[1] += self.pad2_vel
            
        
    
    def judge(self):
        if (self.square_pos[0]<=self.pad_width+1) and ((self.square_pos[1] <=(self.pad1_pos[1]-self.square_height)) or (self.square_pos[1] >=(self.pad1_pos[1]+self.pad_height))):
            self.player2 += 1
            self.scoreChanged = 1
            print("player2:", self.player2)
            print("scoreChanged:", self.scoreChanged)
        elif (self.square_pos[0]>=self.width-self.pad_width-self.square_width-1) and ((self.square_pos[1] <=(self.pad2_pos[1]-self.square_height)) or (self.square_pos[1] >=(self.pad2_pos[1]+self.pad_height))):
            self.player1 += 1
            self.scoreChanged = 1
            print("player1:", self.player1)
            print("scoreChanged:", self.scoreChanged)
    
    def draw(self):
        # Refresh the screen
        if(self.scoreChanged == 1):
            print("scoreChanged:", self.scoreChanged)
            hardware.display.fill_rect(80, 10, 32, 32, st7789.BLACK)  # Clear original left score
            hardware.display.fill_rect(135, 10, 32, 32, st7789.BLACK)  # Clear original right score
            hardware.display.text(font2, str(self.player1), 80, 10)  # Left score
            hardware.display.text(font2, str(self.player2), 135, 10)  # Right score
            self.scoreChanged = 0
        # Draw paddles 
        hardware.display.fill_rect(int(self.old_pad1_pos[0]), int(self.old_pad1_pos[1]), self.pad_width, self.pad_height, st7789.BLACK)  # Clear original left paddle
        hardware.display.fill_rect(int(self.old_pad2_pos[0]+1), int(self.old_pad2_pos[1]), self.pad_width, self.pad_height, st7789.BLACK)  # Clear original right paddle
        hardware.display.fill_rect(int(self.pad1_pos[0]), int(self.pad1_pos[1]), self.pad_width, self.pad_height, st7789.BLUE)  # draw left paddle
        hardware.display.fill_rect(int(self.pad2_pos[0]+1), int(self.pad2_pos[1]), self.pad_width, self.pad_height, st7789.BLUE)  # draw right paddle
 
            
        # Draw ball position 
        hardware.display.fill_rect(int(self.old_square_pos[0]), int(self.old_square_pos[1]), self.square_width, self.square_height, st7789.BLACK)  # Clear original ball
        
        if((int(self.old_square_pos[0]) >= self.CENTER_X-self.square_width) and (int(self.old_square_pos[0]) <= self.CENTER_X+1)):
            hardware.display.line(self.CENTER_X, int(self.old_square_pos[1]), self.CENTER_X, int(self.old_square_pos[1])+self.square_height, st7789.WHITE)  # Redraw center line
        if(((int(self.old_square_pos[0]) >= 80-self.square_width-1) and (int(self.old_square_pos[0]) <= 80+32+1)) and ((int(self.old_square_pos[1] >= 10-self.square_height-1)) and (int(self.old_square_pos[1] <= 10+32+1)))):
            hardware.display.text(font2, str(self.player1), 80, 10)  # Redraw left score
            hardware.display.line(self.pad_width, 0, self.pad_width, self.height, st7789.WHITE) # Redraw left line
        if(((int(self.old_square_pos[0]) >= 135-self.square_width-1) and (int(self.old_square_pos[0]) <= 135+32+1)) and ((int(self.old_square_pos[1] >= 10-self.square_height-1)) and (int(self.old_square_pos[1] <= 10+32+1)))):
            hardware.display.text(font2, str(self.player2), 135, 10)  # Redraw right score
            ardware.display.line(self.width-self.pad_width, 0, self.width-self.pad_width, self.height, st7789.WHITE)  # Redraw right edge

        hardware.display.fill_rect(int(self.square_pos[0]), int(self.square_pos[1]), self.square_width, self.square_height, st7789.WHITE)  # Redraw ball
            
    async def bgm_process(self):
        while True:
            await asyncio.sleep_ms(100)
            self.bgm.tick()

class p_music(music):
    song1 = '0 A5 2 26 0.6299212574958801;2 B5 2 26 0.6299212574958801;4 C6 6 26 0.6299212574958801;10 B5 2 26 0.6299212574958801;12 C6 4 26 0.6299212574958801;16 E6 4 26 0.6299212574958801;20 B5 8 26 0.6299212574958801;32 E5 4 26 0.6299212574958801;36 A5 6 26 0.6299212574958801;42 G5 2 26 0.6299212574958801;44 A5 4 26 0.6299212574958801;48 C6 4 26 0.6299212574958801;52 G5 8 26 0.6299212574958801;64 F5 2 26 0.6299212574958801;66 E5 2 26 0.6299212574958801;68 F5 6 26 0.6299212574958801;74 E5 2 26 0.6299212574958801;76 F5 4 26 0.6299212574958801;80 C6 4 26 0.6299212574958801;84 E5 8 26 0.6299212574958801;94 C6 2 26 0.6299212574958801;96 C6 2 26 0.6299212574958801;98 C6 2 26 0.6299212574958801;100 B5 6 26 0.6299212574958801;106 F#5 2 26 0.6299212574958801;108 F#5 4 26 0.6299212574958801;112 B5 4 26 0.6299212574958801;116 B5 8 26 0.6299212574958801;128 A5 2 26 0.6299212574958801;130 B5 2 26 0.6299212574958801;132 C6 6 26 0.6299212574958801;138 B5 2 26 0.6299212574958801;140 C6 4 26 0.6299212574958801;144 E6 4 26 0.6299212574958801;148 B5 8 26 0.6299212574958801;160 E5 2 26 0.6299212574958801;162 E5 2 26 0.6299212574958801;164 A5 6 26 0.6299212574958801;170 G5 2 26 0.6299212574958801;172 A5 4 26 0.6299212574958801;176 C6 4 26 0.6299212574958801;180 G5 8 26 0.6299212574958801;192 E5 4 26 0.6299212574958801;196 F5 4 26 0.6299212574958801;200 C6 2 26 0.6299212574958801;202 B5 2 26 0.6299212574958801;204 B5 4 26 0.6299212574958801;208 C6 4 26 0.6299212574958801;212 D6 4 26 0.6299212574958801;216 E6 2 26 0.6299212574958801;218 C6 2 26 0.6299212574958801;220 C6 8 26 0.6299212574958801;228 C6 2 26 0.6299212574958801;230 B5 2 26 0.6299212574958801;232 A5 4 26 0.6299212574958801;236 B5 4 26 0.6299212574958801;240 G#5 4 26 0.6299212574958801;244 A5 11 26 0.6299212574958801;256 C6 2 26 0.6299212574958801;258 D6 2 26 0.6299212574958801;260 E6 6 26 0.6299212574958801;266 D6 2 26 0.6299212574958801;268 E6 4 26 0.6299212574958801;272 G6 4 26 0.6299212574958801;276 D6 8 26 0.6299212574958801;288 G5 2 26 0.6299212574958801;290 G5 2 26 0.6299212574958801;292 C6 6 26 0.6299212574958801;298 B5 2 26 0.6299212574958801;300 C6 4 26 0.6299212574958801;304 E6 4 26 0.6299212574958801;308 E6 11 26 0.6299212574958801;324 A5 2 26 0.6299212574958801;326 B5 2 26 0.6299212574958801;328 C6 4 26 0.6299212574958801;332 B5 2 26 0.6299212574958801;334 C6 2 26 0.6299212574958801;336 D6 4 26 0.6299212574958801;340 C6 6 26 0.6299212574958801;346 G5 2 26 0.6299212574958801;348 G5 8 26 0.6299212574958801;356 F6 4 26 0.6299212574958801;360 E6 4 26 0.6299212574958801;364 D6 4 26 0.6299212574958801;368 C6 4 26 0.6299212574958801;372 E6 15 26 0.6299212574958801;388 E6 11 26 0.6299212574958801;400 E6 4 26 0.6299212574958801;404 A6 8 26 0.6299212574958801;412 G6 8 26 0.6299212574958801;420 E6 4 26 0.6299212574958801;424 D6 2 26 0.6299212574958801;426 C6 2 26 0.6299212574958801;428 C6 8 26 0.6299212574958801;436 D6 4 26 0.6299212574958801;440 C6 2 26 0.6299212574958801;442 D6 2 26 0.6299212574958801;444 D6 4 26 0.6299212574958801;448 G6 4 26 0.6299212574958801;452 E6 11 26 0.6299212574958801;464 E6 4 26 0.6299212574958801;468 A6 8 26 0.6299212574958801;476 G6 8 26 0.6299212574958801;484 E6 4 26 0.6299212574958801;488 D6 2 26 0.6299212574958801;490 C6 2 26 0.6299212574958801;492 C6 8 26 0.6299212574958801;500 D6 4 26 0.6299212574958801;504 C6 2 26 0.6299212574958801;506 D6 2 26 0.6299212574958801;508 D6 4 26 0.6299212574958801;512 B5 4 26 0.6299212574958801;516 A5 11 26 0.6299212574958801;528 A5 2 26 0.6299212574958801;530 B5 2 26 0.6299212574958801;532 C6 6 26 0.6299212574958801;538 B5 2 26 0.6299212574958801;540 C6 4 26 0.6299212574958801;544 E6 4 26 0.6299212574958801;548 B5 8 26 0.6299212574958801;560 E5 4 26 0.6299212574958801;564 A5 6 26 0.6299212574958801;570 G5 2 26 0.6299212574958801;572 A5 4 26 0.6299212574958801;576 C6 4 26 0.6299212574958801;580 G5 8 26 0.6299212574958801;592 F5 2 26 0.6299212574958801;594 E5 2 26 0.6299212574958801;596 F5 6 26 0.6299212574958801;602 E5 2 26 0.6299212574958801;604 F5 4 26 0.6299212574958801;608 C6 4 26 0.6299212574958801;612 E5 8 26 0.6299212574958801;622 C6 2 26 0.6299212574958801;624 C6 2 26 0.6299212574958801;626 C6 2 26 0.6299212574958801;628 B5 6 26 0.6299212574958801;634 F#5 2 26 0.6299212574958801;636 F#5 4 26 0.6299212574958801;640 B5 4 26 0.6299212574958801;644 B5 8 26 0.6299212574958801;656 A5 2 26 0.6299212574958801;658 B5 2 26 0.6299212574958801;660 C6 6 26 0.6299212574958801;666 B5 2 26 0.6299212574958801;668 C6 4 26 0.6299212574958801;672 E6 4 26 0.6299212574958801;676 B5 8 26 0.6299212574958801;688 E5 2 26 0.6299212574958801;690 E5 2 26 0.6299212574958801;692 A5 6 26 0.6299212574958801;698 G5 2 26 0.6299212574958801;700 A5 4 26 0.6299212574958801;704 C6 4 26 0.6299212574958801;708 G5 8 26 0.6299212574958801;720 E5 4 26 0.6299212574958801;724 F5 4 26 0.6299212574958801;728 C6 2 26 0.6299212574958801;730 B5 2 26 0.6299212574958801;732 B5 4 26 0.6299212574958801;736 C6 4 26 0.6299212574958801;740 D6 4 26 0.6299212574958801;744 E6 2 26 0.6299212574958801;746 C6 2 26 0.6299212574958801;748 C6 8 26 0.6299212574958801;756 C6 2 26 0.6299212574958801;758 B5 2 26 0.6299212574958801;760 A5 4 26 0.6299212574958801;764 B5 4 26 0.6299212574958801;768 G#5 4 26 0.6299212574958801;772 A5 11 26 0.6299212574958801'
    song0 = '0 E5 2 14;4 B4 2 14;6 C5 2 14;8 D5 2 14;10 E5 1 14;11 D5 1 14;12 C5 2 14;14 B4 2 14;16 A4 2 14;20 A4 2 14;22 C5 2 14;24 E5 2 14;28 D5 2 14;30 C5 2 14;32 B4 2 14;38 C5 2 14;40 D5 2 14;44 E5 2 14;48 C5 2 14;52 A4 2 14;56 A4 2 14;64 D5 2 14;68 F5 2 14;70 A5 2 14;74 G5 2 14;76 F5 2 14;78 E5 2 14;84 C5 2 14;86 E5 2 14;90 D5 2 14;92 C5 2 14;94 B4 2 14;98 B4 2 14;100 C5 2 14;102 D5 2 14;106 E5 2 14;110 C5 2 14;114 A4 2 14;118 A4 2 14;248 E5 8 14;256 C5 8 14;264 D5 8 14;272 B4 8 14;280 C5 8 14;288 A4 8 14;296 G#4 8 14;304 B4 8 14;313 E5 8 14;321 C5 8 14;329 D5 8 14;337 B4 4 14;341 B4 4 14;345 C5 4 14;349 E5 4 14;353 A5 8 14;361 G#5 8 14;248 C5 8 14;256 A4 8 14;264 B4 8 14;272 G#4 8 14;280 A4 8 14;288 E4 8 14;0 B4 2 14;4 G#4 2 14;6 A4 2 14;8 B4 2 14;12 A4 2 14;14 G#4 2 14;28 B4 2 14;30 A4 2 14;32 G#4 4 14;40 B4 2 14;38 A4 2 14;44 C5 2 14;52 E4 2 14;64 F4 2 14;94 G#4 2 14;100 A4 2 14;102 B4 2 14;106 C5 2 14;110 A4 2 14;114 E4 2 14;114 E4 2 14;118 E4 2 14;98 G#4 2 14;296 E4 8 14;304 G#4 8 14;313 C5 8 14;321 A4 8 14;329 B4 8 14;337 G#4 4 14;341 G#4 4 14;345 A4 4 14;349 C5 4 14;353 E5 8 14;353 E5 8 14;361 E5 8 14;48 A4 2 14;56 E4 2 14;68 D5 2 14;70 F5 2 14;74 E5 2 14;76 D5 2 14;80 E5 2 14;78 C5 2 14;80 C5 2 14;22 A4 2 14;24 C5 2 14;84 A4 2 14;86 C5 2 14;92 A4 2 14;90 B4 2 14;0 E5 2 14;4 B4 2 14;6 C5 2 14;8 D5 2 14;10 E5 1 14;11 D5 1 14;12 C5 2 14;14 B4 2 14;16 A4 2 14;20 A4 2 14;22 C5 2 14;24 E5 2 14;28 D5 2 14;30 C5 2 14;32 B4 2 14;38 C5 2 14;40 D5 2 14;44 E5 2 14;48 C5 2 14;52 A4 2 14;56 A4 2 14;64 D5 2 14;68 F5 2 14;70 A5 2 14;74 G5 2 14;76 F5 2 14;78 E5 2 14;84 C5 2 14;86 E5 2 14;90 D5 2 14;92 C5 2 14;94 B4 2 14;98 B4 2 14;100 C5 2 14;102 D5 2 14;106 E5 2 14;110 C5 2 14;114 A4 2 14;118 A4 2 14;0 B4 2 14;4 G#4 2 14;6 A4 2 14;8 B4 2 14;12 A4 2 14;14 G#4 2 14;28 B4 2 14;30 A4 2 14;32 G#4 4 14;40 B4 2 14;38 A4 2 14;44 C5 2 14;52 E4 2 14;64 F4 2 14;94 G#4 2 14;100 A4 2 14;102 B4 2 14;106 C5 2 14;110 A4 2 14;114 E4 2 14;114 E4 2 14;118 E4 2 14;98 G#4 2 14;48 A4 2 14;56 E4 2 14;68 D5 2 14;70 F5 2 14;74 E5 2 14;76 D5 2 14;80 E5 2 14;78 C5 2 14;80 C5 2 14;22 A4 2 14;24 C5 2 14;84 A4 2 14;86 C5 2 14;92 A4 2 14;90 B4 2 14;124 E5 2 14;128 B4 2 14;130 C5 2 14;132 D5 2 14;134 E5 1 14;135 D5 1 14;136 C5 2 14;138 B4 2 14;140 A4 2 14;144 A4 2 14;146 C5 2 14;148 E5 2 14;152 D5 2 14;154 C5 2 14;156 B4 2 14;162 C5 2 14;164 D5 2 14;168 E5 2 14;172 C5 2 14;176 A4 2 14;180 A4 2 14;188 D5 2 14;192 F5 2 14;194 A5 2 14;198 G5 2 14;200 F5 2 14;202 E5 2 14;208 C5 2 14;210 E5 2 14;214 D5 2 14;216 C5 2 14;218 B4 2 14;222 B4 2 14;224 C5 2 14;226 D5 2 14;230 E5 2 14;234 C5 2 14;238 A4 2 14;242 A4 2 14;124 B4 2 14;128 G#4 2 14;130 A4 2 14;132 B4 2 14;136 A4 2 14;138 G#4 2 14;152 B4 2 14;154 A4 2 14;156 G#4 4 14;164 B4 2 14;162 A4 2 14;168 C5 2 14;176 E4 2 14;188 F4 2 14;218 G#4 2 14;224 A4 2 14;226 B4 2 14;230 C5 2 14;234 A4 2 14;238 E4 2 14;238 E4 2 14;242 E4 2 14;222 G#4 2 14;172 A4 2 14;180 E4 2 14;192 D5 2 14;194 F5 2 14;198 E5 2 14;200 D5 2 14;204 E5 2 14;202 C5 2 14;204 C5 2 14;146 A4 2 14;148 C5 2 14;208 A4 2 14;210 C5 2 14;216 A4 2 14;214 B4 2 14;124 E5 2 14;128 B4 2 14;130 C5 2 14;132 D5 2 14;134 E5 1 14;135 D5 1 14;136 C5 2 14;138 B4 2 14;140 A4 2 14;144 A4 2 14;146 C5 2 14;148 E5 2 14;152 D5 2 14;154 C5 2 14;156 B4 2 14;162 C5 2 14;164 D5 2 14;168 E5 2 14;172 C5 2 14;176 A4 2 14;180 A4 2 14;188 D5 2 14;192 F5 2 14;194 A5 2 14;198 G5 2 14;200 F5 2 14;202 E5 2 14;208 C5 2 14;210 E5 2 14;214 D5 2 14;216 C5 2 14;218 B4 2 14;222 B4 2 14;224 C5 2 14;226 D5 2 14;230 E5 2 14;234 C5 2 14;238 A4 2 14;242 A4 2 14;124 B4 2 14;128 G#4 2 14;130 A4 2 14;132 B4 2 14;136 A4 2 14;138 G#4 2 14;152 B4 2 14;154 A4 2 14;156 G#4 4 14;164 B4 2 14;162 A4 2 14;168 C5 2 14;176 E4 2 14;188 F4 2 14;218 G#4 2 14;224 A4 2 14;226 B4 2 14;230 C5 2 14;234 A4 2 14;238 E4 2 14;238 E4 2 14;242 E4 2 14;222 G#4 2 14;172 A4 2 14;180 E4 2 14;192 D5 2 14;194 F5 2 14;198 E5 2 14;200 D5 2 14;204 E5 2 14;202 C5 2 14;204 C5 2 14;146 A4 2 14;148 C5 2 14;208 A4 2 14;210 C5 2 14;216 A4 2 14;214 B4 2 14;248 C5 2 13;252 C5 2 13;254 E5 2 13;250 E5 2 13;256 C5 2 13;260 C5 2 13;258 A4 2 13;262 A4 2 13;264 D5 2 13;268 D5 2 13;266 B4 2 13;270 B4 2 13;272 G#4 2 13;276 G#4 2 13;274 B4 2 13;278 B4 2 13;280 A4 2 13;284 A4 2 13;282 C5 2 13;286 C5 2 13;347 C5 2 13;351 C5 2 13;313 C5 2 13;317 C5 2 13;319 E5 2 13;315 E5 2 13;321 C5 2 13;325 C5 2 13;323 A4 2 13;327 A4 2 13;329 D5 2 13;333 D5 2 13;331 B4 2 13;335 B4 2 13;337 G#4 2 13;341 G#4 2 13;339 B4 2 13;343 B4 2 13;345 A4 2 13;349 A4 2 13;349 E5 2 13;353 E5 2 13;355 A5 2 13;359 A5 2 13;357 E5 2 13;361 E5 2 13;363 G#5 2 13;367 G#5 2 13;365 E5 2 14;292 A4 2 13;288 A4 2 13;294 E4 2 13;290 E4 2 13;300 G#4 2 13;296 G#4 2 13;302 E4 2 13;298 E4 2 13;308 G#4 2 13;304 G#4 2 13;310 B4 2 13;306 B4 2 13'
    song2 = '0 B5 2 23;4 B5 2 23;2 B5 2 23;10 B5 2 23;8 B5 2 23;12 B5 2 23;16 D#6 2 23;18 B5 2 23;20 B5 2 23;22 A5 2 23;24 G5 2 23;26 A5 2 23;28 B5 2 23;32 B5 2 23;36 B5 2 23;34 B5 2 23;42 B5 2 23;40 B5 2 23;44 B5 2 23;58 E5 2 23;60 E5 2 23;48 B5 2 23;50 A5 2 23;52 G5 2 23;54 A5 2 23;56 G5 2 23;64 B5 2 23;68 B5 2 23;66 B5 2 23;74 B5 2 23;72 B5 2 23;76 B5 2 23;80 D#6 2 23;82 B5 2 23;84 B5 2 23;86 A5 2 23;88 G5 2 23;90 A5 2 23;92 B5 2 23;96 B5 2 23;100 B5 2 23;98 B5 2 23;106 B5 2 23;104 B5 2 23;108 B5 2 23;122 E5 2 23;124 E5 2 23;112 B5 2 23;114 A5 2 23;116 G5 2 23;118 A5 2 23;120 G5 2 23;64 B6 2 23;68 B6 2 23;66 B6 2 23;74 B6 2 23;72 B6 2 23;76 B6 2 23;80 D#7 2 23;82 B6 2 23;84 B6 2 23;86 A6 2 23;88 G6 2 23;90 A6 2 23;92 B6 2 23;96 B6 2 23;100 B6 2 23;98 B6 2 23;106 B6 2 23;104 B6 2 23;108 B6 2 23;122 E6 2 23;124 E6 2 23;112 B6 2 23;114 A6 2 23;116 G6 2 23;118 A6 2 23;120 G6 2 23;0 B6 2 23;4 B6 2 23;2 B6 2 23;10 B6 2 23;8 B6 2 23;12 B6 2 23;16 D#7 2 23;18 B6 2 23;20 B6 2 23;22 A6 2 23;24 G6 2 23;26 A6 2 23;28 B6 2 23;32 B6 2 23;36 B6 2 23;34 B6 2 23;42 B6 2 23;40 B6 2 23;44 B6 2 23;58 E6 2 23;60 E6 2 23;48 B6 2 23;50 A6 2 23;52 G6 2 23;54 A6 2 23;56 G6 2 23;0 C#7 4 2;4 C#7 4 2;8 C#7 4 2;12 C#7 4 2;0 C#7 4 2;4 C#7 4 2;8 C#7 4 2;12 C#7 4 2;0 C#7 4 2;4 C#7 4 2;8 C#7 4 2;12 C#7 4 2;32 C#7 4 2;36 C#7 4 2;40 C#7 4 2;44 C#7 4 2;32 C#7 4 2;36 C#7 4 2;40 C#7 4 2;44 C#7 4 2;32 C#7 4 2;36 C#7 4 2;40 C#7 4 2;44 C#7 4 2;64 C#7 4 2;68 C#7 4 2;72 C#7 4 2;76 C#7 4 2;64 C#7 4 2;68 C#7 4 2;72 C#7 4 2;76 C#7 4 2;64 C#7 4 2;68 C#7 4 2;72 C#7 4 2;76 C#7 4 2;96 C#7 4 2;100 C#7 4 2;104 C#7 4 2;108 C#7 4 2;96 C#7 4 2;100 C#7 4 2;104 C#7 4 2;108 C#7 4 2;96 C#7 4 2;100 C#7 4 2;104 C#7 4 2;108 C#7 4 2;8 F#4 4 2;0 F#4 4 2;8 F#4 4 2;0 F#4 4 2;8 F#4 4 2;0 F#4 4 2;8 F#4 4 2;0 F#4 4 2;40 F#4 4 2;32 F#4 4 2;40 F#4 4 2;32 F#4 4 2;40 F#4 4 2;32 F#4 4 2;40 F#4 4 2;32 F#4 4 2;72 F#4 4 2;64 F#4 4 2;72 F#4 4 2;64 F#4 4 2;72 F#4 4 2;64 F#4 4 2;72 F#4 4 2;64 F#4 4 2;104 F#4 4 2;96 F#4 4 2;104 F#4 4 2;96 F#4 4 2;104 F#4 4 2;96 F#4 4 2;104 F#4 4 2;96 F#4 4 2'
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
    def unmute(self):
        for pwm in self.pwms:
            pwm.duty_u16(self.duty)

    def tick(self):
        if self.pause:
            pass
        else:
            super().tick()

def main():
    hardware.init()
    p = pong()
    asyncio.run(p.process())

main()


