import math
import random
import utime
import test.st7789 as welcome
import test.st7789 as st7789
import sys
print(sys.implementation)
from machine import Timer
from tanks.musicPlay import musicPlay
from tanks.tank import Tank
from tanks.shell import Shell
from tanks.land import Land
from machine import Pin,SPI
from test.fonts import vga2_8x8 as font1
from test.fonts import vga1_16x32 as font2
from tanks.my_input import Input
import time
import test.fonts.vga1_16x32 as font_text_big
from test.fonts import vga2_8x8 as font_text

my_input=Input()

st7789_res = 0
st7789_dc  = 1
disp_width = 240
disp_height = 240
spi_sck=Pin(2)
spi_tx=Pin(3)
spi0=SPI(0,baudrate=62500000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)


game='Train No.7'
choose_game=False
musicPlay=musicPlay()

welcome = welcome.ST7789(spi0, disp_width, disp_width,
                          reset=machine.Pin(st7789_res, machine.Pin.OUT),
                          dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                          xstart=0, ystart=0, rotation=0)

display = st7789.ST7789(spi0,disp_width,disp_height,
                          dc=machine.Pin(st7789_dc, machine.Pin.OUT),
                          reset=machine.Pin(st7789_res, machine.Pin.OUT),
                          rotation=0)

welcome.text(font2, "Welcome!", 60, 50)
welcome.text(font2, "TIANK BETTLE", 30, 100,st7789.RED)
welcome.text(font2, "PRESS START", 30, 150)
welcome.text(font2, "TO START", 50, 190)
while not my_input.Start():
    musicPlay.welPlay()
musicPlay.stop()

del(welcome)
time.sleep(1)

width = disp_width
height = disp_height

# display_buffer = bytearray(width * height)  # 2-bytes per pixel (RGB565)
# display.init(display_buffer)

display.fill(st7789.BLACK)

# Colour constants
SKY_COLOR = st7789.color565(165, 182, 255)
GROUND_COLOR = st7789.color565(9,84,5)     
# Different tank colors for player 1 and player 2
# These colors must be unique as well as the GROUND_COLOR
TANK_COLOR_P1 = st7789.color565(216, 216, 153)     
TANK_COLOR_P2 = st7789.color565(219, 163, 82)      
SHELL_COLOR = st7789.color565(255,255,255)
TEXT_COLOR = st7789.color565(255,255,255)
TEXT_COLOR_ACTIVE = st7789.YELLOW
CELE_COLOR = st7789.YELLOW
# States are:
# start - timed delay before start
# player1 - waiting for player to set position
# player1fire - player 1 fired
# player2 - player 2 set position
# player2fire - player 2 fired
# game_over_1 / game_over_2 - show who won 1 = player 1 won etc.
game_state = "start"

# switch button mode from angle to power
key_mode = "angle"

# Tank 1 = Left
tank1 = Tank(display, "left", TANK_COLOR_P1,SKY_COLOR)
# Tank 2 = Right
tank2 = Tank(display, "right", TANK_COLOR_P2,SKY_COLOR)

# Only fire one shell at a time, a single shell object can be used for both player 1 and player 2    
shell = Shell(display, SHELL_COLOR,SKY_COLOR)
    
ground = Land(display, GROUND_COLOR)

WinPage=1
def mycallback(t):
    musicPlay.bgmPlay()

# periodic with 100ms period
bgmTimer=Timer(period=100, mode=Timer.ONE_SHOT, callback=mycallback)
bgmTimer.init(period=200, mode=Timer.PERIODIC, callback=mycallback)
def run_game():
    


    while True:
        global key_mode, game_state,WinPage
            
        ## Draw methods
#         display.set_pen(*SKY_COLOR)
#         display.clear()
        if game_state not in ['game_over_1','game_over_2']:
            tank1.draw ()
            tank2.draw ()
        if game_state=='start':
            display.fill(SKY_COLOR)
            ground.draw()
            game_state='player1'
        
        print(game_state)
        if (game_state == "player1fire" or game_state == "player2fire"):
            shell.draw()
            utime.sleep(0.1)
#             print('shell')

#         display.set_pen(*TEXT_COLOR)
        if (game_state == "player1" or game_state == "player1fire"):
            display.text(font_text,"Player 1", 10, 10,TEXT_COLOR)
            if (key_mode == "power"):
#                 display.set_pen(*TEXT_COLOR_ACTIVE)
                display.text(font_text,"Power:{:>3d}".format(tank1.get_gun_power())+"%", 10, 20,TEXT_COLOR_ACTIVE)#
            else:
                display.text(font_text,"Power:{:>3d}".format(tank1.get_gun_power())+"%", 10, 20,TEXT_COLOR)
            if (key_mode == "angle"):
#                 display.set_pen(*TEXT_COLOR_ACTIVE)
                display.text(font_text,"Angle:{:>3d}".format(tank1.get_gun_angle())+' ', 10, 30,TEXT_COLOR_ACTIVE)

            else:
            #lay.set_pen(*TEXT_COLOR)
                display.text(font_text,"Angle:{:>3d}".format(tank1.get_gun_angle())+' ', 10, 30,TEXT_COLOR)
        if (game_state == "player2" or game_state == "player2fire"):
            display.text(font_text,"Player 2", 150, 10,TEXT_COLOR)
            if (key_mode == "power"):
#                 display.set_pen(*TEXT_COLOR_ACTIVE)
                display.text(font_text,"Power:{:>3d}".format(tank2.get_gun_power())+"%", 150, 20,TEXT_COLOR_ACTIVE)
            else:
                display.text(font_text,"Power:{:>3d}".format(tank2.get_gun_power())+"%", 150, 20,TEXT_COLOR)

            if (key_mode == "angle"):
#                 display.set_pen(*TEXT_COLOR_ACTIVE)
                display.text(font_text,"Angle:{:>3d}".format(tank2.get_gun_angle())+' ', 150, 30,TEXT_COLOR_ACTIVE)

            else:
#                 display.set_pen(*TEXT_COLOR)
                display.text(font_text,"Angle:{:>3d}".format(tank2.get_gun_angle())+' ', 150, 30,TEXT_COLOR)
                
        if (game_state == "game_over_1" and WinPage):
            display.fill(st7789.BLACK)
            display.text(font_text_big,"Game Over", 50, 20,TEXT_COLOR)
            display.text(font_text_big,"Player 1", 60, 80,CELE_COLOR)
            display.text(font_text_big,"Wins!", 80, 110,CELE_COLOR)
            display.text(font_text_big,"PRESS B", 60, 175,TEXT_COLOR)
            display.text(font_text_big,"TO CONTINUE.", 30, 200,TEXT_COLOR)
            WinPage=0
        if (game_state == "game_over_2" and WinPage):
            display.fill(st7789.BLACK)
            display.text(font_text_big,"Game Over", 50, 20,TEXT_COLOR)
            display.text(font_text_big,"Player 2", 60, 80,CELE_COLOR)
            display.text(font_text_big,"Wins!", 80, 110,CELE_COLOR)
            display.text(font_text_big,"PRESS B", 60, 175,TEXT_COLOR)
            display.text(font_text_big,"TO CONTINUE.", 30, 200,TEXT_COLOR)
            WinPage=0
#         display.update()


        ## Update methods
        # Only read keyboard in certain states
        if (game_state == 'player1'):
            player1_fired = player_keyboard("left")
            print(player1_fired)

            if (player1_fired == True):
                # Set shell position to end of gun
                # Use gun_positions so we can get start position 
                gun_positions = tank1.calc_gun_positions()
                start_shell_pos = (gun_positions[3][0],gun_positions[3][1]+2)
                shell.set_start_position(start_shell_pos)
                shell.set_current_position(start_shell_pos)
                global key_mode, game_state
                game_state = 'player1fire'
                musicPlay.shotSoundPlay()
                print(game_state)
                shell.set_angle(math.radians (tank1.get_gun_angle()))
                shell.set_power(tank1.get_gun_power() / 40)
                shell.set_time(0)
        if (game_state == 'player1fire'):
            shell.update_shell_position ("left")
            # shell value is whether the shell is inflight, hit or missed
            shell_value = detect_hit("left") 
            # shell_value 20 is if other tank hit
            if (shell_value >= 20):
                game_state = 'game_over_1'
            # 10 is offscreen and 11 is hit ground, both indicate missed
            elif (shell_value >= 10):
                # reset key mode to angle
                key_mode = "angle"
                game_state = 'player2'
        if (game_state == 'player2'):
            player2_fired = player_keyboard("right")
            if (player2_fired == True):
                # Set shell position to end of gun
                # Use gun_positions so we can get start position 
                gun_positions = tank2.calc_gun_positions ()
                start_shell_pos = (gun_positions[3][0],gun_positions[3][1]+2)
                shell.set_start_position(start_shell_pos)
                shell.set_current_position(start_shell_pos)
                game_state = 'player2fire'
                musicPlay.shotSoundPlay()
                shell.set_angle(math.radians (tank2.get_gun_angle()))
                shell.set_power(tank2.get_gun_power() / 40)
                shell.set_time(0)
        if (game_state == 'player2fire'):
            shell.update_shell_position ("right")
            # shell value is whether the shell is inflight, hit or missed
            shell_value = detect_hit("right")
            # shell_value 20 is if other tank hit
            if (shell_value >= 20):
                game_state = 'game_over_2'
            # 10 is offscreen and 11 is hit ground, both indicate missed
            elif (shell_value >= 10):
                game_state = 'player1'
                # reset key mode to angle
                key_mode = "angle"
        if (game_state == 'game_over_1' or game_state == 'game_over_2'):
            global bgmTimer
            bgmTimer.deinit()
            # Allow space key or left-shift (picade) to continue
            if (my_input.B()) :
                # Reset position of tanks and terrain
                setup()
            musicPlay.overPlay()
        if my_input.Start():
            setup()
        if (my_input.Select()==1):
            musicPlay.switch()
# Reset
def setup():
    global game_state, key_mode,WinPage,bgmTimer
    bgmTimer.init(period=200, mode=Timer.PERIODIC, callback=mycallback)
    # reset key mode to angle
    key_mode = "angle"
    ground.setup()
    # Get positions of tanks from ground generator
    tank1.set_position(ground.get_tank1_position())
    tank2.set_position(ground.get_tank2_position())
    game_state = "start"
    WinPage=1
    
    
    
    
# Detects if the shell has hit something. 
# Simple detection looks at colour of the screen at the position 
# uses an offset to not detect the actual shell
# Return 0 for in-flight, 
# 1 for offscreen temp (too high), 
# 10 for offscreen permanent (too far), 
# 11 for hit ground, 
# 20 for hit other tank
def detect_hit (left_right):
    (shell_x, shell_y) = shell.get_current_position()
    
    # Add offset (3 pixels)
    # offset left/right depending upon direction of fire
    if (left_right == "left"):      
        shell_x += 2
    else:
        shell_x -= 2
    shell_y += 2
    offset_position = (math.floor(shell_x), math.floor(shell_y))
    
    # Check whether it's off the screen 
    # may be temporary if just y axis, permanent if x
    if (shell_x > width or shell_x <= 0 or shell_y >= height):
        shell.shell_hide()
        return 10
    if (shell_y < 1):
        # special case if gone beyond size of screen then that's too far
        if (shell_y < 0-height):
            shell.shell_hide()
            return 10
        shell.shell_hide()
        return 1
        
    # Get colour at position
#     color_values = get_display_bytes(*offset_position)
#     color_values=color_to_bytes(GROUND_COLOR)
#     ground_color_bytes = color_to_bytes(GROUND_COLOR)
#     tank1_color_bytes = color_to_bytes(TANK_COLOR_P1)
#     tank2_color_bytes = color_to_bytes(TANK_COLOR_P2)
    shell_x=offset_position[0]
    shell_y=offset_position[1]
    tank1_pos=tank1.position
    tank2_pos=tank2.position
    land_pos=ground.get_land_height()
    print(shell_x, shell_y,land_pos[shell_x])
    print(tank1_pos)
    print(tank2_pos)
    if (shell_y >= land_pos[shell_x]):
        # Hit ground
        shell.shell_hide()
        return 11
    xscale=15
    y_up_scale=0
    y_down_scale=15
    if (left_right == 'left' and tank2_pos[0]+3<=shell_x <= tank2_pos[0]+xscale and tank2_pos[1]-y_down_scale<=shell_y <= tank2_pos[1]+y_up_scale):
        # Hit tank 2
        musicPlay.shotedSoundPlay()
        return 20
    if (left_right == 'right' and tank1_pos[0]<=shell_x <= tank1_pos[0]+xscale-3 and tank1_pos[1]-y_down_scale<=shell_y <= tank1_pos[1]+y_up_scale):
        # Hit tank 1
        musicPlay.shotedSoundPlay()
        return 20
    
    return 0
    
# Handles keyboard for players
# Although named keyboard (consistancy with pygame zero version) - for the pico this refers to buttons
# If player has hit fire key (space) then returns True
# Otherwise changes angle of gun if applicable and returns False
def player_keyboard(left_right):
    global key_mode
    
    # change key_mode between angle and power using B button
#     print('B:'+str(my_input.B()))

    if (my_input.B()==1) :
        if key_mode == "angle":
            key_mode = "power"
        else:
            key_mode = "angle"
        # add delay to prevent accidental double press
    utime.sleep(0.01)
    
    # A button is fire
#     print('A:'+str(my_input.A()))
    if (my_input.A()==1) :
        return True
    utime.sleep(0.1)
    # Up moves firing angle upwards or increase power
    adjustAngle=3
    if (my_input.y()==-1) :
        if (key_mode == "angle" and left_right == 'left'):
            tank1.change_gun_angle(adjustAngle)
        elif (key_mode == "angle" and left_right == 'right'):
            tank2.change_gun_angle(adjustAngle)
        elif (key_mode == "power" and left_right == 'left'):
            tank1.change_gun_power(adjustAngle)
        elif (key_mode == "power" and left_right == 'right'):
            tank2.change_gun_power(adjustAngle)
    # Down moves firing angle downwards or decrease power
    if (my_input.y()==1) :
        if (key_mode == "angle" and left_right == 'left'):
            tank1.change_gun_angle(-adjustAngle)
        elif (key_mode == "angle" and left_right == 'right'):
            tank2.change_gun_angle(-adjustAngle)
        elif (key_mode == "power" and left_right == 'left'):
            tank1.change_gun_power(-adjustAngle)
        elif (key_mode == "power" and left_right == 'right'):
            tank2.change_gun_power(-adjustAngle)

    return False

# Returns as list
# def get_display_bytes (x, y):
#     buffer_pos = (x*2) + (y*width*2)
#     byte_list = [display_buffer[buffer_pos], display_buffer[buffer_pos+1]]
#     return (byte_list)

def color_to_bytes (color):
#     r, g, b = color
#     bytes = [0,0]
#     bytes[0] = r & 0xF8
#     bytes[0] += (g & 0xE0) >> 5
#     bytes[1] = (g & 0x1C) << 3
#     bytes[1] += (b & 0xF8) >> 3
    
    return color
    
setup()
run_game()
