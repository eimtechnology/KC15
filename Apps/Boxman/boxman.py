import uos
import machine
from machine import Pin, ADC, Timer
from time import sleep_us 
import test.st7789 as st7789
import test.fonts.vga2_8x8 as font1
import test.fonts.vga1_16x32 as font2
import test.fonts.vga3_16x16 as font3
import random
import framebuf
import uasyncio as asyncio
from buzzer_music import music

xAxis = ADC(Pin(28))
yAxis = ADC(Pin(29))
buttonB = Pin(5,Pin.IN, Pin.PULL_UP) 
buttonA = Pin(6,Pin.IN, Pin.PULL_UP)
led = Pin(4, Pin.OUT)

song = '0 A5 2 26 0.6299212574958801;2 B5 2 26 0.6299212574958801;4 C6 6 26 0.6299212574958801;10 B5 2 26 0.6299212574958801;12 C6 4 26 0.6299212574958801;16 E6 4 26 0.6299212574958801;20 B5 8 26 0.6299212574958801;32 E5 4 26 0.6299212574958801;36 A5 6 26 0.6299212574958801;42 G5 2 26 0.6299212574958801;44 A5 4 26 0.6299212574958801;48 C6 4 26 0.6299212574958801;52 G5 8 26 0.6299212574958801;64 F5 2 26 0.6299212574958801;66 E5 2 26 0.6299212574958801;68 F5 6 26 0.6299212574958801;74 E5 2 26 0.6299212574958801;76 F5 4 26 0.6299212574958801;80 C6 4 26 0.6299212574958801;84 E5 8 26 0.6299212574958801;94 C6 2 26 0.6299212574958801;96 C6 2 26 0.6299212574958801;98 C6 2 26 0.6299212574958801;100 B5 6 26 0.6299212574958801;106 F#5 2 26 0.6299212574958801;108 F#5 4 26 0.6299212574958801;112 B5 4 26 0.6299212574958801;116 B5 8 26 0.6299212574958801;128 A5 2 26 0.6299212574958801;130 B5 2 26 0.6299212574958801;132 C6 6 26 0.6299212574958801;138 B5 2 26 0.6299212574958801;140 C6 4 26 0.6299212574958801;144 E6 4 26 0.6299212574958801;148 B5 8 26 0.6299212574958801;160 E5 2 26 0.6299212574958801;162 E5 2 26 0.6299212574958801;164 A5 6 26 0.6299212574958801;170 G5 2 26 0.6299212574958801;172 A5 4 26 0.6299212574958801;176 C6 4 26 0.6299212574958801;180 G5 8 26 0.6299212574958801;192 E5 4 26 0.6299212574958801;196 F5 4 26 0.6299212574958801;200 C6 2 26 0.6299212574958801;202 B5 2 26 0.6299212574958801;204 B5 4 26 0.6299212574958801;208 C6 4 26 0.6299212574958801;212 D6 4 26 0.6299212574958801;216 E6 2 26 0.6299212574958801;218 C6 2 26 0.6299212574958801;220 C6 8 26 0.6299212574958801;228 C6 2 26 0.6299212574958801;230 B5 2 26 0.6299212574958801;232 A5 4 26 0.6299212574958801;236 B5 4 26 0.6299212574958801;240 G#5 4 26 0.6299212574958801;244 A5 11 26 0.6299212574958801;256 C6 2 26 0.6299212574958801;258 D6 2 26 0.6299212574958801;260 E6 6 26 0.6299212574958801;266 D6 2 26 0.6299212574958801;268 E6 4 26 0.6299212574958801;272 G6 4 26 0.6299212574958801;276 D6 8 26 0.6299212574958801;288 G5 2 26 0.6299212574958801;290 G5 2 26 0.6299212574958801;292 C6 6 26 0.6299212574958801;298 B5 2 26 0.6299212574958801;300 C6 4 26 0.6299212574958801;304 E6 4 26 0.6299212574958801;308 E6 11 26 0.6299212574958801;324 A5 2 26 0.6299212574958801;326 B5 2 26 0.6299212574958801;328 C6 4 26 0.6299212574958801;332 B5 2 26 0.6299212574958801;334 C6 2 26 0.6299212574958801;336 D6 4 26 0.6299212574958801;340 C6 6 26 0.6299212574958801;346 G5 2 26 0.6299212574958801;348 G5 8 26 0.6299212574958801;356 F6 4 26 0.6299212574958801;360 E6 4 26 0.6299212574958801;364 D6 4 26 0.6299212574958801;368 C6 4 26 0.6299212574958801;372 E6 15 26 0.6299212574958801;388 E6 11 26 0.6299212574958801;400 E6 4 26 0.6299212574958801;404 A6 8 26 0.6299212574958801;412 G6 8 26 0.6299212574958801;420 E6 4 26 0.6299212574958801;424 D6 2 26 0.6299212574958801;426 C6 2 26 0.6299212574958801;428 C6 8 26 0.6299212574958801;436 D6 4 26 0.6299212574958801;440 C6 2 26 0.6299212574958801;442 D6 2 26 0.6299212574958801;444 D6 4 26 0.6299212574958801;448 G6 4 26 0.6299212574958801;452 E6 11 26 0.6299212574958801;464 E6 4 26 0.6299212574958801;468 A6 8 26 0.6299212574958801;476 G6 8 26 0.6299212574958801;484 E6 4 26 0.6299212574958801;488 D6 2 26 0.6299212574958801;490 C6 2 26 0.6299212574958801;492 C6 8 26 0.6299212574958801;500 D6 4 26 0.6299212574958801;504 C6 2 26 0.6299212574958801;506 D6 2 26 0.6299212574958801;508 D6 4 26 0.6299212574958801;512 B5 4 26 0.6299212574958801;516 A5 11 26 0.6299212574958801;528 A5 2 26 0.6299212574958801;530 B5 2 26 0.6299212574958801;532 C6 6 26 0.6299212574958801;538 B5 2 26 0.6299212574958801;540 C6 4 26 0.6299212574958801;544 E6 4 26 0.6299212574958801;548 B5 8 26 0.6299212574958801;560 E5 4 26 0.6299212574958801;564 A5 6 26 0.6299212574958801;570 G5 2 26 0.6299212574958801;572 A5 4 26 0.6299212574958801;576 C6 4 26 0.6299212574958801;580 G5 8 26 0.6299212574958801;592 F5 2 26 0.6299212574958801;594 E5 2 26 0.6299212574958801;596 F5 6 26 0.6299212574958801;602 E5 2 26 0.6299212574958801;604 F5 4 26 0.6299212574958801;608 C6 4 26 0.6299212574958801;612 E5 8 26 0.6299212574958801;622 C6 2 26 0.6299212574958801;624 C6 2 26 0.6299212574958801;626 C6 2 26 0.6299212574958801;628 B5 6 26 0.6299212574958801;634 F#5 2 26 0.6299212574958801;636 F#5 4 26 0.6299212574958801;640 B5 4 26 0.6299212574958801;644 B5 8 26 0.6299212574958801;656 A5 2 26 0.6299212574958801;658 B5 2 26 0.6299212574958801;660 C6 6 26 0.6299212574958801;666 B5 2 26 0.6299212574958801;668 C6 4 26 0.6299212574958801;672 E6 4 26 0.6299212574958801;676 B5 8 26 0.6299212574958801;688 E5 2 26 0.6299212574958801;690 E5 2 26 0.6299212574958801;692 A5 6 26 0.6299212574958801;698 G5 2 26 0.6299212574958801;700 A5 4 26 0.6299212574958801;704 C6 4 26 0.6299212574958801;708 G5 8 26 0.6299212574958801;720 E5 4 26 0.6299212574958801;724 F5 4 26 0.6299212574958801;728 C6 2 26 0.6299212574958801;730 B5 2 26 0.6299212574958801;732 B5 4 26 0.6299212574958801;736 C6 4 26 0.6299212574958801;740 D6 4 26 0.6299212574958801;744 E6 2 26 0.6299212574958801;746 C6 2 26 0.6299212574958801;748 C6 8 26 0.6299212574958801;756 C6 2 26 0.6299212574958801;758 B5 2 26 0.6299212574958801;760 A5 4 26 0.6299212574958801;764 B5 4 26 0.6299212574958801;768 G#5 4 26 0.6299212574958801;772 A5 11 26 0.6299212574958801'


class color_cfg: #Color settings
    wall = st7789.WHITE
    box = st7789.YELLOW
    blue = st7789.BLUE
    man = st7789.CYAN
    sym = st7789.RED
    background = st7789.color565(128, 0, 128)

def outtextxy(x, y, c, color): #drawing
    global pen_color
    hardware.tft.text(font3, c, x*16, y*16, pen_color, color)

def setcolor(c): #Set plot color
    global pen_color
    pen_color = c
    
class hardware(): #Initialize screen driver
    def init():
        # screen
        st7789_res = 0
        st7789_dc  = 1
        spi_sck=machine.Pin(2)
        spi_tx=machine.Pin(3)
        spi = machine.SPI(0,baudrate=4000000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)
        tft = st7789.ST7789(
            spi,
            240,
            240,
            reset=machine.Pin(st7789_res, machine.Pin.OUT),
            dc=machine.Pin(st7789_dc, machine.Pin.OUT),
            #xstart=0,
            #ystart=0,
            rotation=0)

        tft.fill(color_cfg.background)
        tft.fill_rect(0, 232, 240, 8, color_cfg.blue)

        hardware.tft = tft
        
#Draw the map as a raised glyph
m = [
    0,0,0,0,-1,-1,-1,-1,
    0,1,3,0,0,0,0,0,
    0,1,1,1,1,1,1,0,
    0,1,1,1,1,1,1,0,
    0,1,1,3,1,1,1,0,
    0,1,1,1,1,1,1,0,
    0,1,1,0,0,0,0,0,
    0,0,0,0,-1,-1,-1,-1,]

class game():
    ma = []
    d = 0
    x = 1
    y = 1
    mySong = music(song, pins=[Pin(23)])
    
    def draw(self): #Draw a map based on the above settings
        for i in range(8):
            for n in range(8):
                if self.ma[n*8+i] == 0:  #draw walls
                    setcolor(color_cfg.wall)
                    outtextxy(i+1, n+1, '0',color_cfg.wall)
                if self.ma[n*8+i] == 1:  #draw channel
                    setcolor(color_cfg.background)
                    outtextxy(i+1, n+1, '0',color_cfg.background)
                if self.ma[n*8+i] == 2:  #Draw a box and place it at the initial position

                    setcolor(color_cfg.box)
                    outtextxy(i+1, n+1, 'b',color_cfg.blue)
                if self.ma[n*8+i] == 3:  #draw goal
                    setcolor(color_cfg.sym)
                    outtextxy(i+1, n+1, 'o',color_cfg.background)
                if self.ma[n*8+i] == 4:  #draw initial posistion 
                    setcolor(color_cfg.background)
                    outtextxy(i+1, n+1, 'm',color_cfg.man)
                    
    def title(self): #title screen
        hardware.tft.text(font2, 'BOXMAN', 2*16, 1*32, color_cfg.wall, color_cfg.background) 
        hardware.tft.text(font1, 'Note:', 1*16, 3*32, color_cfg.wall, color_cfg.background) 
        hardware.tft.text(font1, 'Push boxes to the red flag,', 1*16, 4*32, color_cfg.wall, color_cfg.background)
        hardware.tft.text(font1, 'and then you win the game.', 1*16, 5*32, color_cfg.wall, color_cfg.background)
        hardware.tft.text(font1, 'START:buttonA on the right', 2*16, 6*32, color_cfg.wall, color_cfg.background)
    
    def init_run(self): 
        self.ma = [
        0,0,0,0,-1,-1,-1,-1,
        0,1,3,0,0,0,0,0,
        0,1,1,1,1,1,1,0,
        0,1,2,1,1,0,1,0,
        0,1,1,3,1,0,1,0,
        0,1,1,1,1,2,1,0,
        0,1,1,0,0,0,0,0,
        0,0,0,0,-1,-1,-1,-1,]
        self.d = 0 
        self.x = 1
        self.y = 1
        self.ma[self.y*8+self.x] = 4
        self.draw() 
    
    async def process(self): 
        bgm = asyncio.create_task(self.bgm_process()) 
        self.title()
        while True:
            buttonValueA = buttonA.value() 
            if buttonValueA == 0: 
                hardware.init()
                self.init_run()
                print('go')
                
                while True: 
                    self.d = 0
                    self.dir_select() 
                    self.run() 
                    self.draw() 
                    self.judge() 
                    await self.blink()
    
    def dir_select(self):
        xValue = xAxis.read_u16()
        yValue = yAxis.read_u16()
        buttonValueB = buttonB.value()
        
        #摇杆方向感知
        if xValue <1000: 
            self.d = 1
        elif xValue >40000: 
            self.d = 3
    
        if yValue <1000: 
            self.d = 4
        elif yValue >40000: 
            self.d = 2
        if buttonValueB == 0: 
            self.init_run()
            
    def run(self):
        if self.d == 1: #上
            if self.ma[(self.y-1)*8 + self.x] == 0:
                return
            elif self.ma[(self.y-1)*8 + self.x] == 2:
                if self.ma[(self.y-2)*8 + self.x] == 0 or self.ma[(self.y-2)*8 + self.x] == 2:
                    return
                else:
                    self.ma[(self.y-2)*8 + self.x] = 2
                    self.ma[(self.y-1)*8 + self.x] = 4
                    self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                    self.y = self.y - 1
            else:
                self.ma[(self.y-1)*8 + self.x] = 4
                self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                self.y = self.y - 1
        elif self.d == 3: #下
            if self.ma[(self.y+1)*8 + self.x] == 0:
                return
            elif self.ma[(self.y+1)*8 + self.x] == 2:
                if self.ma[(self.y+2)*8 + self.x] == 0 or self.ma[(self.y+2)*8 + self.x] == 2:
                    return
                else:
                    self.ma[(self.y+2)*8 + self.x] = 2
                    self.ma[(self.y+1)*8 + self.x] = 4
                    self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                    self.y = self.y + 1
            else:
                self.ma[(self.y+1)*8 + self.x] = 4
                self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                self.y = self.y + 1
        elif self.d == 4: #左
            if self.ma[self.y*8 + self.x-1] == 0:
                return
            elif self.ma[self.y*8 + self.x-1] == 2:
                if self.ma[self.y*8 + self.x-2] == 0 or self.ma[self.y*8 + self.x-2] == 2:
                    return
                else:
                    self.ma[self.y*8 + self.x-2] = 2
                    self.ma[self.y*8 + self.x-1] = 4
                    self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                    self.x = self.x - 1
            else:
                self.ma[self.y*8 + self.x-1] = 4
                self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                self.x = self.x - 1
        elif self.d == 2: #右
            if self.ma[self.y*8 + self.x+1] == 0:
                return
            elif self.ma[self.y*8 + self.x+1] == 2:
                if self.ma[self.y*8 + self.x+2] == 0 or self.ma[self.y*8 + self.x+2] == 2:
                    return
                else:
                    self.ma[self.y*8 + self.x+2] = 2
                    self.ma[self.y*8 + self.x+1] = 4
                    self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                    self.x = self.x + 1
            else:
                self.ma[self.y*8 + self.x+1] = 4
                self.ma[self.y*8 + self.x] = m[self.y*8 + self.x]
                self.x = self.x + 1
        
    
    def judge(self):
        if self.ma[1*8+2] == 2 and self.ma[4*8+3] == 2:  
            self.win()
    
    def win(self):
        hardware.tft.text(font1, 'Win!Press B to RESTART!', 2*16, 6*32, color_cfg.wall, color_cfg.background)
        
    async def blink(self):
        led.value(1)
        await asyncio.sleep_ms(50)
        led.value(0)
        await asyncio.sleep_ms(50)
        
    async def bgm_process(self):
        while True:
            self.mySong.tick()
            await asyncio.sleep(0.04)
            
            
def main():
    hardware.init()
    s = game()
    asyncio.run(s.process())
                
main()
