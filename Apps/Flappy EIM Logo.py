import framebuf
from machine import Pin, SPI, ADC,PWM
import time
import st7789
import random
import test.st7789 as init
import vga1_16x32 as font
import gc
import vga2_8x16 as fontSml

gc.enable()

#converts image bin file to bytearray for framebuffer
def bin_to_bytearray(bin_path):
    with open(bin_path, 'rb') as f:
        buffer = bytearray(f.read())
    
    return buffer

#color correction for colors used in framebuffers
def frame_buff_color565(r, g, b):
    val16 = (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3
    return (val16 >> 8) | ((val16 & 0xff) << 8)


GAP_HEIGHT = 90 #Gap for between top and bottom pipes
JUMP_VELOCITY = -6.6 #Velocity to set player whenever jump button is pressed
GRAVITY = -0.85 #How strong to pull down the player
PIPE_WIDTH = 30 
PIPE_SCROLL_SPEED = 6 #unit: pixels per while loop cycle
BG_COLOR = frame_buff_color565(113,197,207) 
    


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
spi0=SPI(0,baudrate = 80_000_000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)

buttonStart = Pin(7,Pin.IN, Pin.PULL_UP)
buttonRestart = Pin(8,Pin.IN, Pin.PULL_UP)


display = init.ST7789(spi0, disp_width, disp_width,
                          reset=machine.Pin(st7789_res, machine.Pin.OUT),
                          dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                          rotation=0)

display = st7789.ST7789(spi0, disp_width, disp_width,
                          reset=machine.Pin(st7789_res, machine.Pin.OUT),
                          dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                          rotation=0)

display.init()

display.fill(st7789.WHITE)



#screenBuffer contains contents to render to screen
screenBuffer = framebuf.FrameBuffer(bytearray(240*240*2),240,240, framebuf.RGB565)
#bgBuffer = framebuf.FrameBuffer(bin_to_bytearray('bg.bin'),240,58, framebuf.RGB565)


logo = framebuf.FrameBuffer(bin_to_bytearray('logo.bin'),40,40, framebuf.RGB565)
pipe = framebuf.FrameBuffer(bin_to_bytearray('pipe_u.bin'),50,163, framebuf.RGB565)
gc.collect()


score = 0
high_score = 0
velocity = -4.6


current_pos = 100

debounce = False
gap_pos = random.randint(20,121)

pipe_pos = 230


def reset_game_variables():
    global velocity
    global current_pos
    global pipe_pos
    global score
    global gap_pos
    velocity = JUMP_VELOCITY
    current_pos = 100
    pipe_pos = 230
    score = 0
    gap_pos = random.randint(20,121)

def game_over_screen():
    global score
    global high_score
    if score > high_score:
        high_score = score
    display.fill(st7789.BLACK)
    display.text(font, 'GAME OVER', 50,0, st7789.WHITE, st7789.BLACK)
    display.text(font, 'SCORE: ' + str(score), 50,38, st7789.WHITE, st7789.BLACK)
    
    display.text(font, 'HIGH SCORE: ' + str(high_score), 10,110, st7789.WHITE, st7789.BLACK)
    display.text(fontSml, 'PRESS Y TO RESTART', 45,170, st7789.WHITE, st7789.BLACK)
    

while True:
    
    if(buttonStart.value() == 0 and debounce == False):
        velocity = JUMP_VELOCITY
        debounce = True
    elif (buttonStart.value() == 1):
        debounce = False
    
    current_pos += velocity
    
    velocity-= GRAVITY
   
    screenBuffer.fill(BG_COLOR)
    
    #OLD CODE FOR LESS DETAILED PIPES
    #screenBuffer.rect(pipe_pos,0,PIPE_WIDTH,240,st7789.BLUE, True)
    #screenBuffer.rect(pipe_pos - 5,gap_pos - 10,40,10,st7789.BLUE, True)
    #screenBuffer.rect(pipe_pos - 5,gap_pos + GAP_HEIGHT,40,10,st7789.BLUE, True)
    #screenBuffer.rect(pipe_pos,gap_pos,PIPE_WIDTH,GAP_HEIGHT,st7789.WHITE, True)
    
    screenBuffer.blit(pipe,pipe_pos,gap_pos - 163) #top pipe
    screenBuffer.blit(pipe,pipe_pos,gap_pos + GAP_HEIGHT) #bottom pipe
    
    
    
    screenBuffer.blit(logo,20,int(current_pos))
    screenBuffer.text(str(score), 112, 4, st7789.BLACK)
    
    
    
    
        
    
    
    pipe_pos -= PIPE_SCROLL_SPEED
    
    if(pipe_pos < -PIPE_WIDTH):
        pipe_pos = 230
        gap_pos = random.randint(20,121)        
        score += 1
    
    display.blit_buffer(screenBuffer,0,0,240,240)
    
    #bounds detection if
    if(current_pos > 202 or current_pos < -50):
        game_over_screen()
        while(buttonRestart.value() == 1):
            time.sleep(0.01)
        reset_game_variables()
        
    
    if((current_pos < gap_pos and (pipe_pos < 72 and pipe_pos > -10)) or ((current_pos + 40) > (gap_pos + GAP_HEIGHT) and (pipe_pos < 72 and pipe_pos > -10))):    
        game_over_screen()
        while(buttonRestart.value() == 1):
            time.sleep(0.01)
        reset_game_variables()    
    
